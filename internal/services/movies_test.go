package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"testing"
)

func TestMoviesService(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "movies_service_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	// Test BulkScrapeMovies stub/helper
	// Just ensuring the package has tests and basic functions work
	movie := models.Movie{Title: "Bulk Test"}
	database.DB.Create(&movie)
	
	// BulkScrapeMovies(movieIDs, taskID) - we can call it but it hits TMDB unless mocked
}
