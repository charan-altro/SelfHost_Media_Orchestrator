package services

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

type Settings struct {
	APIKeys map[string]string `json:"api_keys"`
	General map[string]interface{} `json:"general"`
}

var (
	settingsInstance *Settings
	settingsMutex    sync.RWMutex
	settingsPath     string
)

func InitSettings(configDir string) {
	settingsPath = filepath.Join(configDir, "settings.json")
	LoadSettings()
}

func LoadSettings() {
	settingsMutex.Lock()
	defer settingsMutex.Unlock()

	settingsInstance = &Settings{
		APIKeys: make(map[string]string),
		General: make(map[string]interface{}),
	}

	if _, err := os.Stat(settingsPath); err == nil {
		data, err := os.ReadFile(settingsPath)
		if err == nil {
			json.Unmarshal(data, settingsInstance)
		}
	}

	// Override with env variables
	if tmdbKey := os.Getenv("TMDB_API_KEY"); tmdbKey != "" {
		settingsInstance.APIKeys["tmdb"] = tmdbKey
	}
}

func GetSettings() *Settings {
	settingsMutex.RLock()
	defer settingsMutex.RUnlock()
	return settingsInstance
}

func SaveSettings(s *Settings) error {
	settingsMutex.Lock()
	defer settingsMutex.Unlock()

	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}

	err = os.WriteFile(settingsPath, data, 0644)
	if err == nil {
		settingsInstance = s
	}
	return err
}

func GetTMDBKey() string {
	s := GetSettings()
	return s.APIKeys["tmdb"]
}
