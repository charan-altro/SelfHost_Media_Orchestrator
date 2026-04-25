package services

import (
	"fmt"
	"io"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

var IMAGE_EXTS = map[string]bool{
	".jpg": true, ".jpeg": true, ".png": true, ".webp": true,
}

type ArtworkInfo struct {
	Filename  string `json:"filename"`
	Path      string `json:"path"`
	SizeBytes int64  `json:"size_bytes"`
}

func ListArtwork(movieID uint) ([]ArtworkInfo, error) {
	var movie models.Movie
	if err := database.DB.Preload("Files").First(&movie, movieID).Error; err != nil {
		return nil, err
	}

	if len(movie.Files) == 0 {
		return []ArtworkInfo{}, nil
	}

	folder := filepath.Dir(movie.Files[0].FilePath)
	entries, err := os.ReadDir(folder)
	if err != nil {
		return nil, err
	}

	var results []ArtworkInfo
	for _, entry := range entries {
		if !entry.IsDir() {
			ext := strings.ToLower(filepath.Ext(entry.Name()))
			if IMAGE_EXTS[ext] {
				full := filepath.Join(folder, entry.Name())
				info, _ := entry.Info()
				results = append(results, ArtworkInfo{
					Filename:  entry.Name(),
					Path:      filepath.ToSlash(full),
					SizeBytes: info.Size(),
				})
			}
		}
	}
	return results, nil
}

func UploadArtwork(movieID uint, artworkType string, r io.Reader, originalFilename string) (string, error) {
	var movie models.Movie
	if err := database.DB.Preload("Files").First(&movie, movieID).Error; err != nil {
		return "", err
	}

	if len(movie.Files) == 0 {
		return "", fmt.Errorf("no file associated with movie")
	}

	folder := filepath.Dir(movie.Files[0].FilePath)
	baseName := strings.TrimSuffix(filepath.Base(movie.Files[0].FilePath), filepath.Ext(movie.Files[0].FilePath))
	ext := filepath.Ext(originalFilename)
	if ext == "" {
		ext = ".jpg"
	}

	destPath := filepath.Join(folder, fmt.Sprintf("%s_%s%s", baseName, artworkType, ext))
	
	f, err := os.Create(destPath)
	if err != nil {
		return "", err
	}
	defer f.Close()

	_, err = io.Copy(f, r)
	if err != nil {
		return "", err
	}

	return filepath.ToSlash(destPath), nil
}

func DeleteArtwork(movieID uint, artworkType string) error {
	var movie models.Movie
	if err := database.DB.Preload("Files").First(&movie, movieID).Error; err != nil {
		return err
	}

	if len(movie.Files) == 0 {
		return fmt.Errorf("no file associated")
	}

	folder := filepath.Dir(movie.Files[0].FilePath)
	baseName := strings.TrimSuffix(filepath.Base(movie.Files[0].FilePath), filepath.Ext(movie.Files[0].FilePath))

	found := false
	for ext := range IMAGE_EXTS {
		candidate := filepath.Join(folder, fmt.Sprintf("%s_%s%s", baseName, artworkType, ext))
		if _, err := os.Stat(candidate); err == nil {
			os.Remove(candidate)
			found = true
		}
	}

	if !found {
		return fmt.Errorf("artwork not found")
	}
	return nil
}

func DownloadMovieArtwork(movieID uint) error {
	var movie models.Movie
	if err := database.DB.Preload("Files").First(&movie, movieID).Error; err != nil {
		return err
	}
	if len(movie.Files) == 0 {
		return nil
	}

	folder := filepath.Dir(movie.Files[0].FilePath)
	baseName := strings.TrimSuffix(filepath.Base(movie.Files[0].FilePath), filepath.Ext(movie.Files[0].FilePath))
	
	if movie.PosterPath != "" && strings.HasPrefix(movie.PosterPath, "http") {
		dest := filepath.Join(folder, baseName+"_poster.jpg")
		err := downloadFile(movie.PosterPath, dest)
		if err == nil {
			database.DB.Model(&movie).Update("poster_path", "local://" + filepath.ToSlash(dest))
		}
	}

	if movie.FanartPath != "" && strings.HasPrefix(movie.FanartPath, "http") {
		dest := filepath.Join(folder, baseName+"_fanart.jpg")
		err := downloadFile(movie.FanartPath, dest)
		if err == nil {
			database.DB.Model(&movie).Update("fanart_path", "local://" + filepath.ToSlash(dest))
		}
	}

	DownloadActorArtwork(folder, movie.CastDetails)

	return nil
}

func DownloadActorArtwork(folder string, cast []models.CastMember) {
	if len(cast) == 0 {
		return
	}
	actorDir := filepath.Join(folder, ".actors")
	os.MkdirAll(actorDir, 0755)

	for _, actor := range cast {
		if actor.Thumb != "" && strings.HasPrefix(actor.Thumb, "http") {
			cleanName := strings.ReplaceAll(actor.Name, " ", "_")
			dest := filepath.Join(actorDir, cleanName+".jpg")
			if _, err := os.Stat(dest); os.IsNotExist(err) {
				downloadFile(actor.Thumb, dest)
			}
		}
	}
}

func DownloadTVArtwork(showID uint) error {
	var show models.TVShow
	if err := database.DB.Preload("Seasons.Episodes").First(&show, showID).Error; err != nil {
		return err
	}
	if len(show.Seasons) == 0 || len(show.Seasons[0].Episodes) == 0 {
		return nil
	}

	fPath := show.Seasons[0].Episodes[0].FilePath
	folder := filepath.Dir(fPath)
	if strings.Contains(strings.ToLower(filepath.Base(folder)), "season") {
		folder = filepath.Dir(folder)
	}

	if show.PosterPath != "" && strings.HasPrefix(show.PosterPath, "http") {
		dest := filepath.Join(folder, "poster.jpg")
		err := downloadFile(show.PosterPath, dest)
		if err == nil {
			database.DB.Model(&show).Update("poster_path", "local://" + filepath.ToSlash(dest))
		}
	}

	if show.FanartPath != "" && strings.HasPrefix(show.FanartPath, "http") {
		dest := filepath.Join(folder, "fanart.jpg")
		err := downloadFile(show.FanartPath, dest)
		if err == nil {
			database.DB.Model(&show).Update("fanart_path", "local://" + filepath.ToSlash(dest))
		}
	}

	DownloadActorArtwork(folder, show.CastDetails)

	return nil
}

func downloadFile(url string, dest string) error {
	resp, err := http.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	out, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer out.Close()

	_, err = io.Copy(out, resp.Body)
	return err
}
