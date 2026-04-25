package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"path/filepath"
	"testing"
)

func TestUpdateLibrary(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "lib_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	oldPath := filepath.Join(tempDir, "old")
	newPath := filepath.Join(tempDir, "new")
	os.Mkdir(oldPath, 0755)
	os.Mkdir(newPath, 0755)

	lib := models.Library{Name: "Old Lib", Path: oldPath, Type: "movie"}
	database.DB.Create(&lib)

	movie := models.Movie{LibraryID: lib.ID, Title: "Test"}
	database.DB.Create(&movie)
	
	mfile := models.MovieFile{MovieID: movie.ID, FilePath: filepath.Join(oldPath, "movie.mkv")}
	database.DB.Create(&mfile)

	newName := "New Lib"
	updatedLib, err := UpdateLibrary(lib.ID, &newName, &newPath)
	if err != nil {
		t.Fatalf("UpdateLibrary failed: %v", err)
	}

	if updatedLib.Name != "New Lib" || updatedLib.Path != newPath {
		t.Errorf("Library update mismatch")
	}

	var updatedFile models.MovieFile
	database.DB.First(&updatedFile, mfile.ID)
	expectedPath := filepath.Join(newPath, "movie.mkv")
	if updatedFile.FilePath != expectedPath {
		t.Errorf("Cascading path update failed: expected %s, got %s", expectedPath, updatedFile.FilePath)
	}
}
