package services

import (
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"os"
	"strings"
	"testing"
)

func TestExporter(t *testing.T) {
	tempDir, _ := os.MkdirTemp("", "export_test")
	defer os.RemoveAll(tempDir)
	database.InitDB(tempDir)

	movie := models.Movie{Title: "Export Movie", Year: 2022}
	database.DB.Create(&movie)

	csv := ExportCSV()
	if !strings.Contains(csv, "Export Movie") {
		t.Error("CSV export missing movie title")
	}

	html := ExportHTML()
	if !strings.Contains(html, "Export Movie") {
		t.Error("HTML export missing movie title")
	}
}
