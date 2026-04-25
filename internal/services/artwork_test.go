package services

import (
	"bytes"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"path/filepath"
	"testing"
)

func TestArtwork(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "artwork_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	movieDir := filepath.Join(tempDir, "Movie")
	os.Mkdir(movieDir, 0755)
	moviePath := filepath.Join(movieDir, "movie.mkv")
	os.WriteFile(moviePath, []byte("fake"), 0644)

	movie := models.Movie{Title: "Movie"}
	database.DB.Create(&movie)
	mfile := models.MovieFile{MovieID: movie.ID, FilePath: moviePath}
	database.DB.Create(&mfile)

	// Test Upload
	buf := bytes.NewBuffer([]byte("fake image"))
	dest, err := UploadArtwork(movie.ID, "poster", buf, "image.jpg")
	if err != nil {
		t.Fatalf("UploadArtwork failed: %v", err)
	}
	if _, err := os.Stat(dest); os.IsNotExist(err) {
		t.Error("Uploaded file does not exist")
	}

	// Test List
	list, err := ListArtwork(movie.ID)
	if err != nil || len(list) != 1 {
		t.Errorf("ListArtwork failed: %v, len: %d", err, len(list))
	}

	// Test Delete
	err = DeleteArtwork(movie.ID, "poster")
	if err != nil {
		t.Errorf("DeleteArtwork failed: %v", err)
	}
}
