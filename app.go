package main

import (
	"context"
	"encoding/base64"
	"fmt"
	"io"
	"os"
	"os/exec"
	filepath "path/filepath"
	go_runtime "runtime"
	"sort"
	"strings"
	"time"

	"media-orchestrator/internal/core"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"media-orchestrator/internal/services"
	"media-orchestrator/internal/services/scraper"

	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// nativeOpen opens a file with the system default application
func (a *App) nativeOpen(path string) {
	var cmd *exec.Cmd

	// Convert to OS specific path
	path = filepath.FromSlash(path)

	switch go_runtime.GOOS {
	case "windows":
		cmd = exec.Command("cmd", "/c", "start", "", path)
	case "darwin":
		cmd = exec.Command("open", path)
	default: // linux and others
		cmd = exec.Command("xdg-open", path)
	}

	_ = cmd.Start()
}

// --- LIBRARIES ---

type App struct {
	ctx context.Context
}

// NewApp creates a new App application struct
func NewApp() *App {
	return &App{}
}

// startup is called when the app starts.
func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	database.InitDB("data")
	services.InitSettings("config")
}

// --- LIBRARIES ---

func (a *App) GetLibraries() []models.Library {
	var libraries []models.Library
	database.DB.Find(&libraries)
	return libraries
}

func (a *App) AddLibrary(name string, path string, libType string) models.Library {
	lib := models.Library{Name: name, Path: path, Type: libType}
	database.DB.Create(&lib)
	return lib
}

func (a *App) UpdateLibrary(id uint, data map[string]interface{}) models.Library {
	var name *string
	var path *string

	if n, ok := data["name"].(string); ok {
		name = &n
	}
	if p, ok := data["path"].(string); ok {
		path = &p
	}

	lib, err := services.UpdateLibrary(id, name, path)
	if err != nil {
		// Return empty lib or handle error. For now, following existing pattern.
		return models.Library{}
	}
	return *lib
}

func (a *App) DeleteLibrary(id uint) bool {
	database.DB.Delete(&models.Library{}, id)
	return true
}

func (a *App) CleanupLibrary(libraryID uint) map[string]interface{} {
	return services.CleanupLibrary(libraryID)
}

func (a *App) ScanLibrary(libraryID uint) string {
	taskID := fmt.Sprintf("%s-%d-%d", "scan", libraryID, time.Now().UnixNano())
	
	// Check if already running
	tasks := core.GlobalTaskManager.GetTasks()
	for _, t := range tasks {
		if t.ID == taskID && t.Status == "running" {
			return fmt.Sprintf("Scan already running for library %d", libraryID)
		}
	}

	core.GlobalTaskManager.CreateTask(taskID, "Library Scan")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		progressChan := make(chan int)
		go func() {
			for progress := range progressChan {
				runtime.EventsEmit(a.ctx, "scan-progress", map[string]interface{}{"library_id": libraryID, "progress": progress})
			}
		}()
		services.ScanLibrary(libraryID, taskID, progressChan)
		close(progressChan)
		runtime.EventsEmit(a.ctx, "scan-complete", map[string]interface{}{"library_id": libraryID})
		runtime.EventsEmit(a.ctx, "tasks-updated", nil)
	}()
	return fmt.Sprintf("Started scanning library ID: %d", libraryID)
}

// --- MOVIES ---

func (a *App) GetMovies() []models.Movie {
	var movies []models.Movie
	err := database.DB.Preload("Files").Find(&movies).Error
	if err != nil {
		fmt.Printf("DB Error in GetMovies: %v\n", err)
		return []models.Movie{}
	}
	return movies
}

func (a *App) GetMovieDetails(id uint) models.Movie {
	var movie models.Movie
	database.DB.Preload("Files").First(&movie, id)
	return movie
}

func (a *App) PlayMovie(id uint) {
	var movie models.Movie
	database.DB.Preload("Files").First(&movie, id)
	if len(movie.Files) > 0 {
		a.nativeOpen(movie.Files[0].FilePath)
	}
}

func (a *App) PlayEpisode(id uint) {
	var ep models.Episode
	database.DB.First(&ep, id)
	if ep.FilePath != "" {
		a.nativeOpen(ep.FilePath)
	}
}

func (a *App) UpdateMovie(id uint, data map[string]interface{}) models.Movie {
	var movie models.Movie
	database.DB.First(&movie, id)
	database.DB.Model(&movie).Updates(data)
	return movie
}

func (a *App) TriggerScrape(movieID uint) string {
	taskID := fmt.Sprintf("scrape-movie-%d-%d", movieID, time.Now().UnixNano())
	core.GlobalTaskManager.CreateTask(taskID, "Movie Metadata Scrape")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		var movie models.Movie
		if err := database.DB.First(&movie, movieID).Error; err == nil {
			core.GlobalTaskManager.UpdateTask(taskID, 20, "running", fmt.Sprintf("Scraping %s", movie.Title))
			apiKey := services.GetTMDBKey()
			s := scraper.NewTMDBScraper(apiKey)
			err := s.ScrapeMovie(&movie)
			if err != nil {
				core.GlobalTaskManager.UpdateTask(taskID, 0, "error", err.Error())
				return
			}
			database.DB.Save(&movie)
			services.GenerateMovieNFO(movie.ID)
			services.DownloadMovieArtwork(movie.ID)
			core.GlobalTaskManager.UpdateTask(taskID, 100, "done", "Scrape complete")
			runtime.EventsEmit(a.ctx, "media-updated", map[string]interface{}{"type": "movie", "id": movieID})
			runtime.EventsEmit(a.ctx, "tasks-updated", nil)
		} else {
			core.GlobalTaskManager.UpdateTask(taskID, 0, "error", "Movie not found")
		}
	}()
	return fmt.Sprintf("Started scraping movie %d", movieID)
}

func (a *App) SearchExternalMovie(title string, year int) []map[string]interface{} {
	apiKey := services.GetTMDBKey()
	s := scraper.NewTMDBScraper(apiKey)
	results, err := s.SearchMovies(title, year)
	if err != nil {
		return []map[string]interface{}{}
	}
	return results
}

func (a *App) MatchMovie(movieID uint, tmdbID string) bool {
	var movie models.Movie
	if err := database.DB.First(&movie, movieID).Error; err != nil {
		return false
	}
	movie.TmdbID = tmdbID
	database.DB.Save(&movie)
	
	// Trigger a scrape to populate details based on new ID
	taskID := fmt.Sprintf("match-movie-%d-%d", movieID, time.Now().UnixNano())
	core.GlobalTaskManager.CreateTask(taskID, "Movie Manual Match")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		apiKey := services.GetTMDBKey()
		s := scraper.NewTMDBScraper(apiKey)
		s.ScrapeMovieByID(&movie)
		database.DB.Save(&movie)
		services.GenerateMovieNFO(movie.ID)
		services.DownloadMovieArtwork(movie.ID)
		core.GlobalTaskManager.UpdateTask(taskID, 100, "done", "Match complete")
		runtime.EventsEmit(a.ctx, "media-updated", map[string]interface{}{"type": "movie", "id": movieID})
		runtime.EventsEmit(a.ctx, "tasks-updated", nil)
	}()
	return true
}

func (a *App) RenameMovie(movieID uint) map[string]interface{} {
	newPath, err := services.RenameMovie(movieID)
	if err != nil {
		return map[string]interface{}{"success": false, "error": err.Error()}
	}
	return map[string]interface{}{"success": true, "new_path": newPath}
}

func (a *App) BulkScrapeMovies(movieIDs []uint) string {
	taskID := fmt.Sprintf("bulk-scrape-%d", os.Getpid())
	core.GlobalTaskManager.CreateTask(taskID, "Bulk Movie Scrape")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		services.BulkScrapeMovies(movieIDs, taskID)
		runtime.EventsEmit(a.ctx, "tasks-updated", nil)
		runtime.EventsEmit(a.ctx, "media-updated", map[string]interface{}{"type": "movie", "bulk": true})
	}()
	return taskID
}

func (a *App) BulkRenameMovies(movieIDs []uint) string {
	taskID := fmt.Sprintf("bulk-rename-%d", os.Getpid())
	core.GlobalTaskManager.CreateTask(taskID, "Bulk Movie Rename")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		services.BulkRenameMovies(movieIDs, taskID)
		runtime.EventsEmit(a.ctx, "tasks-updated", nil)
		runtime.EventsEmit(a.ctx, "media-updated", map[string]interface{}{"type": "movie", "bulk": true})
	}()
	return taskID
}

func (a *App) GenerateMovieNFO(movieID uint) bool {
	err := services.GenerateMovieNFO(movieID)
	return err == nil
}

// --- TV SHOWS ---

func (a *App) GetTVShows() []models.TVShow {
	var shows []models.TVShow
	database.DB.Find(&shows)
	return shows
}

func (a *App) GetTVShowDetails(id uint) models.TVShow {
	var show models.TVShow
	database.DB.Preload("Seasons.Episodes").First(&show, id)
	return show
}

func (a *App) UpdateTVShow(id uint, data map[string]interface{}) models.TVShow {
	var show models.TVShow
	database.DB.First(&show, id)
	database.DB.Model(&show).Updates(data)
	return show
}

func (a *App) TriggerTVScrape(showID uint) string {
	taskID := fmt.Sprintf("scrape-tv-%d-%d", showID, time.Now().UnixNano())
	core.GlobalTaskManager.CreateTask(taskID, "TV Metadata Scrape")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		var show models.TVShow
		if err := database.DB.First(&show, showID).Error; err == nil {
			core.GlobalTaskManager.UpdateTask(taskID, 20, "running", fmt.Sprintf("Scraping %s", show.Title))
			apiKey := services.GetTMDBKey()
			s := scraper.NewTMDBScraper(apiKey)
			err := s.ScrapeTVShow(&show)
			if err != nil {
				core.GlobalTaskManager.UpdateTask(taskID, 0, "error", err.Error())
				return
			}
			database.DB.Save(&show)
			services.GenerateTVShowNFO(show.ID)
			services.DownloadTVArtwork(show.ID)
			core.GlobalTaskManager.UpdateTask(taskID, 100, "done", "Scrape complete")
			runtime.EventsEmit(a.ctx, "media-updated", map[string]interface{}{"type": "tv", "id": showID})
			runtime.EventsEmit(a.ctx, "tasks-updated", nil)
		} else {
			core.GlobalTaskManager.UpdateTask(taskID, 0, "error", "Show not found")
		}
	}()
	return fmt.Sprintf("Started scraping show %d", showID)
}

func (a *App) SearchExternalTV(title string, year int) []map[string]interface{} {
	apiKey := services.GetTMDBKey()
	s := scraper.NewTMDBScraper(apiKey)
	results, err := s.SearchTV(title, year)
	if err != nil {
		return []map[string]interface{}{}
	}
	return results
}

func (a *App) MatchTVShow(showID uint, tmdbID string) bool {
	var show models.TVShow
	if err := database.DB.First(&show, showID).Error; err != nil {
		return false
	}
	show.TmdbID = tmdbID
	database.DB.Save(&show)
	
	taskID := fmt.Sprintf("match-tv-%d-%d", showID, time.Now().UnixNano())
	core.GlobalTaskManager.CreateTask(taskID, "TV Manual Match")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		apiKey := services.GetTMDBKey()
		s := scraper.NewTMDBScraper(apiKey)
		s.ScrapeTVByID(&show)
		database.DB.Save(&show)
		services.GenerateTVShowNFO(show.ID)
		services.DownloadTVArtwork(show.ID)
		core.GlobalTaskManager.UpdateTask(taskID, 100, "done", "Match complete")
		runtime.EventsEmit(a.ctx, "media-updated", map[string]interface{}{"type": "tv", "id": showID})
		runtime.EventsEmit(a.ctx, "tasks-updated", nil)
	}()
	return true
}

func (a *App) BulkScrapeTVShows(showIDs []uint) string {
	taskID := fmt.Sprintf("bulk-scrape-tv-%d", os.Getpid())
	core.GlobalTaskManager.CreateTask(taskID, "Bulk TV Scrape")
	runtime.EventsEmit(a.ctx, "tasks-updated", nil)

	go func() {
		services.BulkScrapeTVShows(showIDs, taskID)
		runtime.EventsEmit(a.ctx, "tasks-updated", nil)
		runtime.EventsEmit(a.ctx, "media-updated", map[string]interface{}{"type": "tv", "bulk": true})
	}()
	return taskID
}

func (a *App) GenerateTVShowNFO(showID uint) bool {
	err := services.GenerateTVShowNFO(showID)
	return err == nil
}

// --- SYSTEM ---

type DirectoryItem struct {
	Name string `json:"name"`
	Path string `json:"path"`
}

type FileSystemNode struct {
	CurrentPath string          `json:"current_path"`
	ParentPath  string          `json:"parent_path"`
	Directories []DirectoryItem `json:"directories"`
}

func (a *App) BrowseFileSystem(path string) FileSystemNode {
	if path == "" || path == "/" {
		// Default to C:\ on Windows if empty
		path = "C:\\"
	}

	entries, err := os.ReadDir(path)
	if err != nil {
		return FileSystemNode{
			CurrentPath: path,
			ParentPath:  filepath.Dir(path),
			Directories: []DirectoryItem{},
		}
	}

	var dirs []DirectoryItem
	for _, entry := range entries {
		if entry.IsDir() {
			dirs = append(dirs, DirectoryItem{
				Name: entry.Name(),
				Path: filepath.Join(path, entry.Name()),
			})
		}
	}

	sort.Slice(dirs, func(i, j int) bool {
		return strings.ToLower(dirs[i].Name) < strings.ToLower(dirs[j].Name)
	})

	return FileSystemNode{
		CurrentPath: path,
		ParentPath:  filepath.Dir(path),
		Directories: dirs,
	}
}

type Drive struct {
	Label string `json:"label"`
	Path  string `json:"path"`
}

func (a *App) GetDrives() []Drive {
	var drives []Drive
	for _, drive := range "ABCDEFGHIJKLMNOPQRSTUVWXYZ" {
		path := string(drive) + ":\\"
		if _, err := os.Stat(path); err == nil {
			drives = append(drives, Drive{
				Label: string(drive) + ":",
				Path:  path,
			})
		}
	}
	return drives
}

func (a *App) ListArtwork(movieID uint) []services.ArtworkInfo {
	artwork, err := services.ListArtwork(movieID)
	if err != nil {
		return []services.ArtworkInfo{}
	}
	return artwork
}

func (a *App) PickAndUploadArtwork(movieID uint, artworkType string) string {
	filePath, err := runtime.OpenFileDialog(a.ctx, runtime.OpenDialogOptions{
		Title: "Select Artwork",
		Filters: []runtime.FileFilter{
			{DisplayName: "Images", Pattern: "*.jpg;*.jpeg;*.png;*.webp"},
		},
	})
	if err != nil || filePath == "" {
		return ""
	}

	f, err := os.Open(filePath)
	if err != nil {
		return ""
	}
	defer f.Close()

	newPath, err := services.UploadArtwork(movieID, artworkType, f, filePath)
	if err != nil {
		return ""
	}
	return newPath
}

func (a *App) DeleteArtwork(movieID uint, artworkType string) bool {
	err := services.DeleteArtwork(movieID, artworkType)
	return err == nil
}

func (a *App) GetLocalArtwork(path string) string {
	path = strings.TrimPrefix(path, "local://")
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	ext := strings.ToLower(filepath.Ext(path))
	contentType := "image/jpeg"
	if ext == ".png" {
		contentType = "image/png"
	} else if ext == ".webp" {
		contentType = "image/webp"
	}
	return fmt.Sprintf("data:%s;base64,%s", contentType, base64.StdEncoding.EncodeToString(data))
}

func (a *App) ShowInFolder(filePath string) {
	a.nativeOpen(filepath.Dir(filePath))
}

func (a *App) OpenInPlayer(filePath string) {
	a.nativeOpen(filePath)
}

func (a *App) DownloadMedia(mediaType string, itemID uint) string {
	var filePath string
	if mediaType == "movie" {
		var movie models.Movie
		database.DB.Preload("Files").First(&movie, itemID)
		if len(movie.Files) > 0 {
			filePath = movie.Files[0].FilePath
		}
	} else if mediaType == "episode" {
		var ep models.Episode
		database.DB.First(&ep, itemID)
		filePath = ep.FilePath
	}

	if filePath == "" {
		return "File not found"
	}

	destPath, err := runtime.SaveFileDialog(a.ctx, runtime.SaveDialogOptions{
		Title: "Save Media File",
		DefaultFilename: filepath.Base(filePath),
	})
	if err != nil || destPath == "" {
		return "Cancelled"
	}

	// Copy file
	src, err := os.Open(filePath)
	if err != nil {
		return "Error opening source"
	}
	defer src.Close()

	dst, err := os.Create(destPath)
	if err != nil {
		return "Error creating destination"
	}
	defer dst.Close()

	_, err = io.Copy(dst, src)
	if err != nil {
		return "Error copying file"
	}

	return "Downloaded to " + destPath
}

func (a *App) GetTasks() []*models.BackgroundTask {
	return core.GlobalTaskManager.GetTasks()
}

func (a *App) DeleteTask(taskID string) bool {
	core.GlobalTaskManager.RemoveTask(taskID)
	return true
}

func (a *App) ExportCSV() string {
	return services.ExportCSV()
}

func (a *App) ExportHTML() string {
	return services.ExportHTML()
}

func (a *App) GetSettings() map[string]interface{} {
	s := services.GetSettings()
	return map[string]interface{}{
		"api_keys": s.APIKeys,
		"general":  s.General,
	}
}

func (a *App) PatchSettings(data map[string]interface{}) map[string]interface{} {
	s := services.GetSettings()
	
	if keys, ok := data["api_keys"].(map[string]interface{}); ok {
		for k, v := range keys {
			if val, ok := v.(string); ok {
				s.APIKeys[k] = val
			}
		}
	}
	
	if gen, ok := data["general"].(map[string]interface{}); ok {
		for k, v := range gen {
			s.General[k] = v
		}
	}
	
	services.SaveSettings(s)
	return data
}
