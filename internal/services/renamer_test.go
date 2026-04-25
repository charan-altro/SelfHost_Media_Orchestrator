package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"path/filepath"
	"testing"
)

func TestRenamer(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "rename_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	lib := models.Library{Name: "Lib", Path: tempDir}
	database.DB.Create(&lib)

	oldDir := filepath.Join(tempDir, "OldFolder")
	os.Mkdir(oldDir, 0755)
	oldPath := filepath.Join(oldDir, "oldfile.mkv")
	os.WriteFile(oldPath, []byte("fake"), 0644)

	movie := models.Movie{LibraryID: lib.ID, Title: "Renamed Movie", Year: 2021}
	database.DB.Create(&movie)
	mfile := models.MovieFile{MovieID: movie.ID, FilePath: oldPath}
	database.DB.Create(&mfile)

	newPath, err := RenameMovie(movie.ID)
	if err != nil {
		t.Fatalf("RenameMovie failed: %v", err)
	}

	expectedName := "Renamed Movie (2021).mkv"
	if filepath.Base(newPath) != expectedName {
		t.Errorf("Expected %s, got %s", expectedName, filepath.Base(newPath))
	}

	if _, err := os.Stat(newPath); os.IsNotExist(err) {
		t.Error("New file does not exist")
	}
}
