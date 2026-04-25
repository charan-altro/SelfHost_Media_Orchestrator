package services

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"

	"media-orchestrator/internal/core"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
)

var SupportedExts = map[string]bool{
	".mkv": true, ".mp4": true, ".avi": true, ".mov": true,
	".webm": true, ".flv": true, ".iso": true, ".m2ts": true,
	".ts": true,
}

func ScanLibrary(libraryID uint, taskID string, progressChan chan<- int) {
	var lib models.Library
	if err := database.DB.First(&lib, libraryID).Error; err != nil {
		if taskID != "" {
			core.GlobalTaskManager.UpdateTask(taskID, 0, "error", "Library not found")
		}
		return
	}

	normPath := filepath.ToSlash(lib.Path)
	if _, err := os.Stat(normPath); os.IsNotExist(err) {
		if taskID != "" {
			core.GlobalTaskManager.UpdateTask(taskID, 0, "error", "Path does not exist")
		}
		return
	}

	if taskID != "" {
		core.GlobalTaskManager.UpdateTask(taskID, 5, "running", "Discovering files...")
	}

	// 1. Build Caches
	existingPaths := make(map[string]bool)
	if lib.Type == "tv" {
		var episodes []models.Episode
		database.DB.Joins("JOIN seasons ON seasons.id = episodes.season_id").
			Joins("JOIN tv_shows ON tv_shows.id = seasons.show_id").
			Where("tv_shows.library_id = ?", libraryID).
			Select("episodes.file_path").Find(&episodes)
		for _, ep := range episodes {
			existingPaths[ep.FilePath] = true
		}
	} else {
		var mfiles []models.MovieFile
		database.DB.Joins("JOIN movies ON movies.id = movie_files.movie_id").
			Where("movies.library_id = ?", libraryID).
			Select("movie_files.file_path").Find(&mfiles)
		for _, mf := range mfiles {
			existingPaths[mf.FilePath] = true
		}
	}

	var filesToProcess []string
	skipDirs := map[string]bool{
		".git": true, "node_modules": true, "@eaDir": true, "#recycle": true, ".actors": true,
	}

	filepath.WalkDir(normPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			name := d.Name()
			if strings.HasPrefix(name, ".") || skipDirs[name] {
				return filepath.SkipDir
			}
			return nil
		}
		ext := strings.ToLower(filepath.Ext(path))
		if SupportedExts[ext] {
			fPath := filepath.ToSlash(path)
			if !existingPaths[fPath] {
				filesToProcess = append(filesToProcess, fPath)
			}
		}
		return nil
	})

	total := len(filesToProcess)
	if total == 0 {
		if taskID != "" {
			core.GlobalTaskManager.UpdateTask(taskID, 100, "done", "No new media files found")
		}
		return
	}

	// 2. Parallel Processing with Worker Pool
	numWorkers := 4
	jobs := make(chan string, total)
	var processedCount int32
	var wg sync.WaitGroup

	// Mutexes for cache-like lookups during registration to avoid DB race conditions on FirstOrCreate patterns
	var registrationMu sync.Mutex

	worker := func() {
		defer wg.Done()
		for fPath := range jobs {
			filename := filepath.Base(fPath)
			parsed := ParseFilename(filename)

			registrationMu.Lock()
			if lib.Type == "tv" {
				processTVFile(lib, fPath, filename, parsed)
			} else {
				processMovieFile(lib, fPath, filename, parsed)
			}
			registrationMu.Unlock()

			newCount := atomic.AddInt32(&processedCount, 1)
			if newCount%10 == 0 || int(newCount) == total {
				progress := 10 + int((float64(newCount)/float64(total))*90)
				if progressChan != nil {
					progressChan <- progress
				}
				if taskID != "" {
					core.GlobalTaskManager.UpdateTask(taskID, progress, "running", fmt.Sprintf("Processing %d/%d: %s", newCount, total, filename))
				}
			}
		}
	}

	for w := 1; w <= numWorkers; w++ {
		wg.Add(1)
		go worker()
	}

	for _, fPath := range filesToProcess {
		jobs <- fPath
	}
	close(jobs)
	wg.Wait()

	if taskID != "" {
		core.GlobalTaskManager.UpdateTask(taskID, 100, "done", fmt.Sprintf("Scan complete. Processed %d new items.", total))
	}
}

func processTVFile(lib models.Library, fPath string, filename string, parsed ParsedMedia) {
	meta := ParseTVShowNFO(fPath)
	title := parsed.Title
	if meta != nil && meta.Title != "" {
		title = meta.Title
	}

	var show models.TVShow
	database.DB.Where("LOWER(title) = ? AND library_id = ?", strings.ToLower(title), lib.ID).First(&show)
	if show.ID == 0 {
		show = models.TVShow{LibraryID: lib.ID, Title: title, Year: parsed.Year}
		database.DB.Create(&show)
	}

	if meta != nil && show.Status != "matched" {
		updates := map[string]interface{}{}
		if meta.Plot != "" { updates["plot"] = meta.Plot }
		if meta.Year != 0 { updates["year"] = meta.Year }
		if meta.TmdbID != "" { updates["tmdb_id"] = meta.TmdbID }
		if meta.ImdbID != "" { updates["imdb_id"] = meta.ImdbID }
		if meta.PosterPath != "" { updates["poster_path"] = meta.PosterPath }
		if meta.FanartPath != "" { updates["fanart_path"] = meta.FanartPath }
		if len(meta.Cast) > 0 { updates["cast"] = meta.Cast }
		if len(updates) > 0 {
			updates["status"] = "matched"
			database.DB.Model(&show).Updates(updates)
		}
	}

	seasonNum := parsed.Season
	if seasonNum == 0 { seasonNum = 1 }
	var season models.Season
	database.DB.Where(models.Season{ShowID: show.ID, SeasonNumber: seasonNum}).FirstOrCreate(&season)

	epNum := parsed.Episode
	if epNum == 0 { epNum = 1 }
	var ep models.Episode
	if err := database.DB.Where("file_path = ?", fPath).First(&ep).Error; err != nil {
		ep = models.Episode{
			SeasonID:         season.ID,
			EpisodeNumber:    epNum,
			Title:            fmt.Sprintf("Episode %d", epNum),
			FilePath:         fPath,
			OriginalFilename: filename,
		}
		database.DB.Create(&ep)
	}
}

func processMovieFile(lib models.Library, fPath string, filename string, parsed ParsedMedia) {
	meta := ParseMovieNFO(fPath)
	title := parsed.Title
	year := parsed.Year
	if meta != nil && meta.Title != "" {
		title = meta.Title
		if meta.Year != 0 {
			year = meta.Year
		}
	}

	var movie models.Movie
	query := database.DB.Where("LOWER(title) = ? AND library_id = ?", strings.ToLower(title), lib.ID)
	if year > 0 {
		query = query.Where("year = ?", year)
	}
	query.First(&movie)

	if movie.ID == 0 && year > 0 {
		database.DB.Where("LOWER(title) = ? AND library_id = ? AND (year = 0 OR year IS NULL)", strings.ToLower(title), lib.ID).First(&movie)
		if movie.ID != 0 {
			movie.Year = year
			database.DB.Model(&movie).Update("year", year)
		}
	}

	if movie.ID == 0 {
		movie = models.Movie{LibraryID: lib.ID, Title: title, Year: year}
		database.DB.Create(&movie)
	}

	if meta != nil && movie.Status != "matched" {
		updates := map[string]interface{}{}
		if meta.Plot != "" { updates["plot"] = meta.Plot }
		if meta.Year != 0 { updates["year"] = meta.Year }
		if meta.TmdbID != "" { updates["tmdb_id"] = meta.TmdbID }
		if meta.ImdbID != "" { updates["imdb_id"] = meta.ImdbID }
		if meta.PosterPath != "" { updates["poster_path"] = meta.PosterPath }
		if meta.FanartPath != "" { updates["fanart_path"] = meta.FanartPath }
		if meta.Runtime != 0 { updates["runtime"] = meta.Runtime }
		if len(meta.Cast) > 0 { updates["cast"] = meta.Cast }
		if len(updates) > 0 {
			updates["status"] = "matched"
			database.DB.Model(&movie).Updates(updates)
		}
	}

	var mfile models.MovieFile
	if err := database.DB.Where("file_path = ?", fPath).First(&mfile).Error; err != nil {
		mfile = models.MovieFile{
			MovieID:          movie.ID,
			FilePath:         fPath,
			OriginalFilename: filename,
		}
		database.DB.Create(&mfile)
	}
}

