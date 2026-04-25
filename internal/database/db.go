package database

import (
	"log"
	"path/filepath"
	"os"

	"media-orchestrator/internal/models"
	"github.com/glebarez/sqlite"
	"gorm.io/gorm"
)

var DB *gorm.DB

func InitDB(dataDir string) {
	dbPath := filepath.Join(dataDir, "orchestrator.db")
	
	// Ensure directory exists
	if err := os.MkdirAll(dataDir, 0755); err != nil {
		log.Fatal("Failed to create data directory:", err)
	}

	var err error
	DB, err = gorm.Open(sqlite.Open(dbPath), &gorm.Config{})
	if err != nil {
		log.Fatal("Failed to connect database:", err)
	}

	// Auto Migrate the schema
	err = DB.AutoMigrate(
		&models.Library{},
		&models.Movie{},
		&models.MovieFile{},
		&models.TVShow{},
		&models.Season{},
		&models.Episode{},
		&models.BackgroundTask{},
	)
	if err != nil {
		log.Fatal("Failed to auto-migrate database:", err)
	}
}
