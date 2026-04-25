package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"path/filepath"
	"testing"
)

func TestScanner(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "scanner_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	lib := models.Library{Name: "Lib", Path: tempDir, Type: "movie"}
	database.DB.Create(&lib)

	os.WriteFile(filepath.Join(tempDir, "Movie (2020).mkv"), []byte("fake"), 0644)

	progressChan := make(chan int, 10)
	ScanLibrary(lib.ID, "task-scan", progressChan)

	var movie models.Movie
	res := database.DB.Where("title LIKE ?", "%Movie%").First(&movie)
	if res.Error != nil {
		t.Errorf("Scanner failed to register movie: %v", res.Error)
	}
}
