package services

import (
	"fmt"
	"media-orchestrator/internal/core"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"media-orchestrator/internal/services/scraper"
)

func BulkScrapeTVShows(showIDs []uint, taskID string) {
	total := len(showIDs)
	if total == 0 {
		return
	}

	core.GlobalTaskManager.UpdateTask(taskID, 0, "running", fmt.Sprintf("Starting bulk scrape for %d shows", total))

	apiKey := GetTMDBKey()
	s := scraper.NewTMDBScraper(apiKey)

	for i, id := range showIDs {
		var show models.TVShow
		if err := database.DB.First(&show, id).Error; err == nil {
			core.GlobalTaskManager.UpdateTask(taskID, int(float64(i)/float64(total)*100), "running", fmt.Sprintf("Scraping %s (%d/%d)", show.Title, i+1, total))
			s.ScrapeTVShow(&show)
			database.DB.Save(&show)
			
			GenerateTVShowNFO(show.ID)
			DownloadTVArtwork(show.ID)
		}
	}

	core.GlobalTaskManager.UpdateTask(taskID, 100, "done", fmt.Sprintf("Bulk scrape complete for %d shows", total))
}
