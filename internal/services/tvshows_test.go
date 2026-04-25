package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"testing"
)

func TestTVShowsService(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "tvshows_service_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	show := models.TVShow{Title: "TV Bulk Test"}
	database.DB.Create(&show)
}
