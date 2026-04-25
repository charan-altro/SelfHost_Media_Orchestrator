package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"path/filepath"
	"testing"
)

func TestCleanup(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "cleanup_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	lib := models.Library{Name: "Lib", Path: tempDir}
	database.DB.Create(&lib)

	// 1. Create duplicate movies
	m1 := models.Movie{LibraryID: lib.ID, Title: "Dup", Year: 2020}
	database.DB.Create(&m1)
	m2 := models.Movie{LibraryID: lib.ID, Title: "Dup", Year: 2020}
	database.DB.Create(&m2)
	
	// Add file to m2
	realPath := filepath.Join(tempDir, "movie.mkv")
	os.WriteFile(realPath, []byte("fake"), 0644)
	mf2 := models.MovieFile{MovieID: m2.ID, FilePath: realPath}
	database.DB.Create(&mf2)

	// Run cleanup (merging)
	stats := CleanupLibrary(lib.ID)
	if stats["merged_groups"].(int) != 1 {
		t.Errorf("Expected 1 merged group, got %v", stats["merged_groups"])
	}

	// Verify m2's file now belongs to m1
	var updatedMF models.MovieFile
	database.DB.First(&updatedMF, mf2.ID)
	if updatedMF.MovieID != m1.ID {
		t.Errorf("Expected file to be merged into m1, but it belongs to %d", updatedMF.MovieID)
	}

	// Verify m2 is deleted
	var deletedMovie models.Movie
	res := database.DB.First(&deletedMovie, m2.ID)
	if res.Error == nil {
		t.Error("Duplicate movie m2 was not deleted")
	}
}
