package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"strings"
)

func UpdateLibrary(libraryID uint, name *string, path *string) (*models.Library, error) {
	var lib models.Library
	if err := database.DB.First(&lib, libraryID).Error; err != nil {
		return nil, err
	}

	oldPath := lib.Path

	if name != nil {
		lib.Name = *name
	}

	if path != nil {
		newPath := *path
		if newPath != oldPath {
			// Update all associated file paths
			if lib.Type == "movie" {
				var files []models.MovieFile
				database.DB.Joins("JOIN movies ON movies.id = movie_files.movie_id").Where("movies.library_id = ?", libraryID).Find(&files)
				for _, f := range files {
					if strings.HasPrefix(f.FilePath, oldPath) {
						f.FilePath = strings.Replace(f.FilePath, oldPath, newPath, 1)
						database.DB.Save(&f)
					}
				}
			} else {
				var episodes []models.Episode
				database.DB.Joins("JOIN seasons ON seasons.id = episodes.season_id").Joins("JOIN tv_shows ON tv_shows.id = seasons.show_id").Where("tv_shows.library_id = ?", libraryID).Find(&episodes)
				for _, ep := range episodes {
					if strings.HasPrefix(ep.FilePath, oldPath) {
						ep.FilePath = strings.Replace(ep.FilePath, oldPath, newPath, 1)
						database.DB.Save(&ep)
					}
				}
			}
			lib.Path = newPath
		}
	}

	database.DB.Save(&lib)
	return &lib, nil
}
