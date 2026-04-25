package database

import (
	"os"
	"path/filepath"
	"testing"
)

func TestInitDB(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "db_test")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	InitDB(tempDir)

	if DB == nil {
		t.Fatal("DB instance is nil after InitDB")
	}

	dbFile := filepath.Join(tempDir, "orchestrator.db")
	if _, err := os.Stat(dbFile); os.IsNotExist(err) {
		t.Errorf("Database file was not created at %s", dbFile)
	}
}
