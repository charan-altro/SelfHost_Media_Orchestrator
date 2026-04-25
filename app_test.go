package main

import (
	"context"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"testing"
)

func TestApp_Libraries(t *testing.T) {
	// Setup temp DB
	tempDir, _ := os.MkdirTemp("", "app_test")
	defer os.RemoveAll(tempDir)
	
	database.InitDB(tempDir)
	
	app := NewApp()
	app.startup(context.Background())
	
	// Test AddLibrary
	lib := app.AddLibrary("Test Lib", tempDir, "movie")
	if lib.ID == 0 {
		t.Errorf("Expected library ID > 0, got %d", lib.ID)
	}
	
	// Test GetLibraries
	libs := app.GetLibraries()
	if len(libs) != 1 {
		t.Errorf("Expected 1 library, got %d", len(libs))
	}
	
	// Test UpdateLibrary
	updated := app.UpdateLibrary(lib.ID, map[string]interface{}{"name": "Updated Name"})
	if updated.Name != "Updated Name" {
		t.Errorf("Expected updated name 'Updated Name', got '%s'", updated.Name)
	}
	
	// Test DeleteLibrary
	app.DeleteLibrary(lib.ID)
	libs = app.GetLibraries()
	if len(libs) != 0 {
		t.Errorf("Expected 0 libraries after deletion, got %d", len(libs))
	}
}

func TestApp_Movies(t *testing.T) {
	// Setup temp DB
	tempDir, _ := os.MkdirTemp("", "app_movie_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)
	
	app := NewApp()
	
	// Seed a movie
	movie := models.Movie{Title: "Inception", Year: 2010}
	database.DB.Create(&movie)
	
	movies := app.GetMovies()
	if len(movies) != 1 {
		t.Errorf("Expected 1 movie, got %d", len(movies))
	}
	
	details := app.GetMovieDetails(movie.ID)
	if details.Title != "Inception" {
		t.Errorf("Expected title 'Inception', got '%s'", details.Title)
	}
}
