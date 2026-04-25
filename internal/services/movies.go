package services

import (
	"fmt"
	"media-orchestrator/internal/core"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"media-orchestrator/internal/services/scraper"
)

func BulkScrapeMovies(movieIDs []uint, taskID string) {
	total := len(movieIDs)
	if total == 0 {
		return
	}

	core.GlobalTaskManager.UpdateTask(taskID, 0, "running", fmt.Sprintf("Starting bulk scrape for %d movies", total))

	apiKey := GetTMDBKey()
	s := scraper.NewTMDBScraper(apiKey)

	for i, id := range movieIDs {
		var movie models.Movie
		if err := database.DB.First(&movie, id).Error; err == nil {
			core.GlobalTaskManager.UpdateTask(taskID, int(float64(i)/float64(total)*100), "running", fmt.Sprintf("Scraping %s (%d/%d)", movie.Title, i+1, total))
			s.ScrapeMovie(&movie)
			database.DB.Save(&movie)
			
			GenerateMovieNFO(movie.ID)
			DownloadMovieArtwork(movie.ID)
		}
	}

	core.GlobalTaskManager.UpdateTask(taskID, 100, "done", fmt.Sprintf("Bulk scrape complete for %d movies", total))
}

func BulkRenameMovies(movieIDs []uint, taskID string) {
	total := len(movieIDs)
	if total == 0 {
		return
	}

	core.GlobalTaskManager.UpdateTask(taskID, 0, "running", fmt.Sprintf("Starting bulk rename for %d movies", total))

	for i, id := range movieIDs {
		var movie models.Movie
		if err := database.DB.First(&movie, id).Error; err == nil {
			core.GlobalTaskManager.UpdateTask(taskID, int(float64(i)/float64(total)*100), "running", fmt.Sprintf("Renaming %s (%d/%d)", movie.Title, i+1, total))
			RenameMovie(movie.ID)
		}
	}

	core.GlobalTaskManager.UpdateTask(taskID, 100, "done", fmt.Sprintf("Bulk rename complete for %d movies", total))
}
