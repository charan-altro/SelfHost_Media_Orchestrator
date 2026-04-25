package services

import (
	"os"
	"testing"
)

func TestSettings(t *testing.T) {
	// Clear env var to avoid interference
	oldKey := os.Getenv("TMDB_API_KEY")
	os.Setenv("TMDB_API_KEY", "")
	defer os.Setenv("TMDB_API_KEY", oldKey)

	tempDir, _ := os.MkdirTemp("", "settings_test")
	defer os.RemoveAll(tempDir)

	InitSettings(tempDir)

	s := GetSettings()
	s.APIKeys["tmdb"] = "test-key"
	err := SaveSettings(s)
	if err != nil {
		t.Fatalf("SaveSettings failed: %v", err)
	}

	// Reload to verify
	LoadSettings()
	if GetTMDBKey() != "test-key" {
		t.Errorf("Expected test-key, got %s", GetTMDBKey())
	}
}
