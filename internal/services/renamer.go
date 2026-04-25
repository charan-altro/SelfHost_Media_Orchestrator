package services

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
)

func sanitize(s string) string {
	re := regexp.MustCompile(`[\\/*?:"<>|]`)
	return strings.TrimSpace(re.ReplaceAllString(s, ""))
}

func RenameMovie(movieID uint) (string, error) {
	var movie models.Movie
	if err := database.DB.Preload("Files").First(&movie, movieID).Error; err != nil {
		return "", err
	}

	if len(movie.Files) == 0 {
		return "", fmt.Errorf("no files found for movie")
	}

	var lib models.Library
	if err := database.DB.First(&lib, movie.LibraryID).Error; err != nil {
		return "", err
	}

	mfile := movie.Files[0]
	currentPath := mfile.FilePath

	safeTitle := sanitize(movie.Title)
	folderName := safeTitle
	if movie.Year > 0 {
		folderName = fmt.Sprintf("%s (%d)", safeTitle, movie.Year)
	}

	tags := []string{}
	if mfile.Resolution != "" {
		tags = append(tags, mfile.Resolution)
	}
	if mfile.VideoCodec != "" {
		tags = append(tags, mfile.VideoCodec)
	}
	if mfile.AudioCodec != "" {
		tags = append(tags, mfile.AudioCodec)
	}

	fileStem := folderName
	tagStr := strings.Join(tags, " ")
	if tagStr != "" {
		fileStem = fmt.Sprintf("%s [%s]", folderName, tagStr)
	}

	// Clean up empty brackets
	fileStem = strings.ReplaceAll(fileStem, "[]", "")
	fileStem = strings.ReplaceAll(fileStem, "[ ]", "")
	fileStem = strings.ReplaceAll(fileStem, "()", "")
	fileStem = strings.ReplaceAll(fileStem, "( )", "")
	fileStem = regexp.MustCompile(`\s+`).ReplaceAllString(fileStem, " ")
	fileStem = strings.TrimSpace(fileStem)

	ext := filepath.Ext(currentPath)
	newFilename := fileStem + ext

	destFolder := filepath.Join(lib.Path, folderName)
	destFile := filepath.Join(destFolder, newFilename)

	if filepath.ToSlash(currentPath) == filepath.ToSlash(destFile) {
		return destFile, nil
	}

	os.MkdirAll(destFolder, os.ModePerm)
	err := os.Rename(currentPath, destFile)
	if err != nil {
		// Fallback to copy/delete if across drives, but os.Rename works most times on same drive
		return "", err
	}

	oldDir := filepath.Dir(currentPath)
	oldStem := strings.TrimSuffix(filepath.Base(currentPath), ext)
	newStem := fileStem

	entries, _ := os.ReadDir(oldDir)
	for _, entry := range entries {
		cPath := filepath.Join(oldDir, entry.Name())
		if cPath == destFile {
			continue
		}
		if strings.HasPrefix(entry.Name(), oldStem) {
			newCompanionName := strings.Replace(entry.Name(), oldStem, newStem, 1)
			os.Rename(cPath, filepath.Join(destFolder, newCompanionName))
		}
	}

	// Clean empty old dir
	entries, _ = os.ReadDir(oldDir)
	if len(entries) == 0 {
		os.Remove(oldDir)
	}

	// Update DB
	mfile.FilePath = filepath.ToSlash(destFile)
	database.DB.Save(&mfile)

	return destFile, nil
}
