package services

import (
	"os"

	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
)

func CleanupLibrary(libraryID uint) map[string]interface{} {
	var lib models.Library
	if err := database.DB.First(&lib, libraryID).Error; err != nil {
		return map[string]interface{}{"error": "Library not found"}
	}

	removedFiles := 0
	removedMovies := 0
	mergedGroups := 0

	// 1. Clean up movie files
	var mfiles []models.MovieFile
	database.DB.Joins("JOIN movies ON movies.id = movie_files.movie_id").Where("movies.library_id = ?", libraryID).Find(&mfiles)

	for _, mf := range mfiles {
		if _, err := os.Stat(mf.FilePath); os.IsNotExist(err) {
			database.DB.Delete(&mf)
			removedFiles++
		}
	}

	// 2. Merge duplicate movies
	type Duplicate struct {
		LowerTitle string
		Year       int
		MCount     int
	}
	var duplicates []Duplicate
	database.DB.Raw("SELECT LOWER(title) as lower_title, year, COUNT(id) as m_count FROM movies WHERE library_id = ? GROUP BY LOWER(title), year HAVING COUNT(id) > 1", libraryID).Scan(&duplicates)

	for _, dup := range duplicates {
		var mList []models.Movie
		database.DB.Where("LOWER(title) = ? AND year = ? AND library_id = ?", dup.LowerTitle, dup.Year, libraryID).Order("id ASC").Find(&mList)

		if len(mList) > 1 {
			canonical := mList[0]
			others := mList[1:]

			for _, other := range others {
				database.DB.Model(&models.MovieFile{}).Where("movie_id = ?", other.ID).Update("movie_id", canonical.ID)
				database.DB.Delete(&other)
				removedMovies++
			}
			mergedGroups++
		}
	}

	// 2b. Merge movies with same title where one has year 0 and another has year > 0
	var sameTitles []struct {
		LowerTitle string
	}
	database.DB.Raw("SELECT LOWER(title) as lower_title FROM movies WHERE library_id = ? GROUP BY LOWER(title) HAVING COUNT(DISTINCT year) > 1", libraryID).Scan(&sameTitles)

	for _, st := range sameTitles {
		var moviesWithYear []models.Movie
		database.DB.Where("LOWER(title) = ? AND library_id = ? AND year > 0", st.LowerTitle, libraryID).Order("id ASC").Find(&moviesWithYear)
		
		var moviesWithoutYear []models.Movie
		database.DB.Where("LOWER(title) = ? AND library_id = ? AND (year = 0 OR year IS NULL)", st.LowerTitle, libraryID).Find(&moviesWithoutYear)

		if len(moviesWithYear) > 0 && len(moviesWithoutYear) > 0 {
			canonical := moviesWithYear[0]
			for _, other := range moviesWithoutYear {
				database.DB.Model(&models.MovieFile{}).Where("movie_id = ?", other.ID).Update("movie_id", canonical.ID)
				database.DB.Delete(&other)
				removedMovies++
			}
			mergedGroups++
		}
	}

	// 3. Clean up empty movies
	var emptyMovies []models.Movie
	database.DB.Raw("SELECT m.* FROM movies m LEFT JOIN movie_files mf ON m.id = mf.movie_id WHERE m.library_id = ? AND mf.id IS NULL", libraryID).Scan(&emptyMovies)
	
	for _, m := range emptyMovies {
		database.DB.Delete(&m)
		removedMovies++
	}

	// For TV Shows
	removedEps := 0
	removedShows := 0
	
	var episodes []models.Episode
	database.DB.Joins("JOIN seasons ON seasons.id = episodes.season_id").Joins("JOIN tv_shows ON tv_shows.id = seasons.show_id").Where("tv_shows.library_id = ?", libraryID).Find(&episodes)

	for _, ep := range episodes {
		if _, err := os.Stat(ep.FilePath); os.IsNotExist(err) {
			database.DB.Delete(&ep)
			removedEps++
		}
	}

	return map[string]interface{}{
		"removed_movie_files": removedFiles,
		"removed_movies":      removedMovies,
		"merged_groups":       mergedGroups,
		"removed_episodes":    removedEps,
		"removed_shows":       removedShows,
	}
}
