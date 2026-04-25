package services

import (
	"encoding/xml"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
)

type NFOMetadata struct {
	Title      string
	SortTitle  string
	Year       int
	Plot       string
	TmdbID     string
	ImdbID     string
	Runtime    int
	PosterPath string
	FanartPath string
	Cast       models.StringList
}

type XMLActor struct {
	Name  string `xml:"name"`
	Role  string `xml:"role,omitempty"`
	Thumb string `xml:"thumb,omitempty"`
}

type XMLMovie struct {
	XMLName   xml.Name   `xml:"movie"`
	Title     string     `xml:"title"`
	SortTitle string     `xml:"sorttitle"`
	Year      string     `xml:"year"`
	Plot      string     `xml:"plot"`
	TmdbID    string     `xml:"tmdbid"`
	ImdbID    string     `xml:"imdbid"`
	Runtime   string     `xml:"runtime"`
	UniqueIDs []struct {
		Type string `xml:"type,attr"`
		ID   string `xml:",chardata"`
	} `xml:"uniqueid"`
	Actors []XMLActor `xml:"actor"`
}

type XMLTVShow struct {
	XMLName   xml.Name   `xml:"tvshow"`
	Title     string     `xml:"title"`
	Year      string     `xml:"year"`
	Plot      string     `xml:"plot"`
	TmdbID    string     `xml:"tmdbid"`
	ImdbID    string     `xml:"imdbid"`
	UniqueIDs []struct {
		Type string `xml:"type,attr"`
		ID   string `xml:",chardata"`
	} `xml:"uniqueid"`
	Actors []XMLActor `xml:"actor"`
}

func ParseMovieNFO(videoPath string) *NFOMetadata {
	dir := filepath.Dir(videoPath)
	base := strings.TrimSuffix(filepath.Base(videoPath), filepath.Ext(videoPath))

	nfoCandidates := []string{
		filepath.Join(dir, base+"_.nfo"),
		filepath.Join(dir, base+".nfo"),
		filepath.Join(dir, "movie.nfo"),
	}

	meta := &NFOMetadata{
		Cast: models.StringList{},
	}

	// Local Artwork Detection
	posterCandidates := []string{base + "_poster.jpg", base + "-poster.jpg", "poster.jpg", "poster.png", "folder.jpg"}
	fanartCandidates := []string{base + "_fanart.jpg", base + "-fanart.jpg", "fanart.jpg", "backdrop.jpg"}

	for _, c := range posterCandidates {
		p := filepath.Join(dir, c)
		if _, err := os.Stat(p); err == nil {
			meta.PosterPath = "local://" + filepath.ToSlash(p)
			break
		}
	}

	for _, c := range fanartCandidates {
		p := filepath.Join(dir, c)
		if _, err := os.Stat(p); err == nil {
			meta.FanartPath = "local://" + filepath.ToSlash(p)
			break
		}
	}

	// NFO Parsing
	var nfoFile string
	for _, c := range nfoCandidates {
		if _, err := os.Stat(c); err == nil {
			nfoFile = c
			break
		}
	}

	if nfoFile != "" {
		data, err := os.ReadFile(nfoFile)
		if err == nil {
			var x XMLMovie
			if err := xml.Unmarshal(data, &x); err == nil {
				meta.Title = x.Title
				meta.SortTitle = x.SortTitle
				meta.Plot = x.Plot
				meta.TmdbID = x.TmdbID
				meta.ImdbID = x.ImdbID
				meta.Year, _ = strconv.Atoi(x.Year)
				meta.Runtime, _ = strconv.Atoi(x.Runtime)

				for _, uid := range x.UniqueIDs {
					if strings.ToLower(uid.Type) == "tmdb" {
						meta.TmdbID = uid.ID
					} else if strings.ToLower(uid.Type) == "imdb" {
						meta.ImdbID = uid.ID
					}
				}
				
				for _, actor := range x.Actors {
					meta.Cast = append(meta.Cast, actor.Name)
				}
			}
		}
	}

	if meta.Title == "" && meta.PosterPath == "" {
		return nil
	}
	return meta
}

func ParseTVShowNFO(videoPath string) *NFOMetadata {
	dir := filepath.Dir(videoPath)
	if strings.Contains(strings.ToLower(filepath.Base(dir)), "season") {
		dir = filepath.Dir(dir)
	}

	meta := &NFOMetadata{
		Cast: models.StringList{},
	}

	if _, err := os.Stat(filepath.Join(dir, "poster.jpg")); err == nil {
		meta.PosterPath = "local://" + filepath.ToSlash(filepath.Join(dir, "poster.jpg"))
	}
	if _, err := os.Stat(filepath.Join(dir, "fanart.jpg")); err == nil {
		meta.FanartPath = "local://" + filepath.ToSlash(filepath.Join(dir, "fanart.jpg"))
	}

	nfoFile := filepath.Join(dir, "tvshow_.nfo")
	if _, err := os.Stat(nfoFile); err == nil {
		// Found!
	} else {
		nfoFile = filepath.Join(dir, "tvshow.nfo")
	}

	if _, err := os.Stat(nfoFile); err == nil {
		data, err := os.ReadFile(nfoFile)
		if err == nil {
			var x XMLTVShow
			if err := xml.Unmarshal(data, &x); err == nil {
				meta.Title = x.Title
				meta.Plot = x.Plot
				meta.TmdbID = x.TmdbID
				meta.ImdbID = x.ImdbID
				meta.Year, _ = strconv.Atoi(x.Year)

				for _, uid := range x.UniqueIDs {
					if strings.ToLower(uid.Type) == "tmdb" {
						meta.TmdbID = uid.ID
					} else if strings.ToLower(uid.Type) == "imdb" {
						meta.ImdbID = uid.ID
					}
				}

				for _, actor := range x.Actors {
					meta.Cast = append(meta.Cast, actor.Name)
				}
			}
		}
	}

	if meta.Title == "" && meta.PosterPath == "" {
		return nil
	}
	return meta
}

func GenerateMovieNFO(movieID uint) error {
	var movie models.Movie
	if err := database.DB.Preload("Files").First(&movie, movieID).Error; err != nil {
		return err
	}
	if len(movie.Files) == 0 {
		return nil
	}
	
	x := XMLMovie{
		Title:     movie.Title,
		SortTitle: movie.Title,
		Plot:      movie.Plot,
		TmdbID:    movie.TmdbID,
		ImdbID:    movie.ImdbID,
		Year:      strconv.Itoa(movie.Year),
		Runtime:   strconv.Itoa(movie.Runtime),
	}
	
	for _, actor := range movie.CastDetails {
		x.Actors = append(x.Actors, XMLActor{
			Name:  actor.Name,
			Role:  actor.Role,
			Thumb: actor.Thumb,
		})
	}
	
	// Fallback to plain Cast list if details are empty
	if len(x.Actors) == 0 {
		for _, name := range movie.Cast {
			x.Actors = append(x.Actors, XMLActor{Name: name})
		}
	}
	
	if movie.TmdbID != "" {
		x.UniqueIDs = append(x.UniqueIDs, struct{Type string `xml:"type,attr"`; ID string `xml:",chardata"`}{Type: "tmdb", ID: movie.TmdbID})
	}
	if movie.ImdbID != "" {
		x.UniqueIDs = append(x.UniqueIDs, struct{Type string `xml:"type,attr"`; ID string `xml:",chardata"`}{Type: "imdb", ID: movie.ImdbID})
	}

	data, err := xml.MarshalIndent(x, "", "  ")
	if err != nil {
		return err
	}
	
	fPath := movie.Files[0].FilePath
	base := strings.TrimSuffix(fPath, filepath.Ext(fPath))
	nfoPath := base + "_.nfo"
	
	finalData := []byte(xml.Header + string(data))
	return os.WriteFile(nfoPath, finalData, 0644)
}

func GenerateTVShowNFO(showID uint) error {
	var show models.TVShow
	if err := database.DB.Preload("Seasons.Episodes").First(&show, showID).Error; err != nil {
		return err
	}
	if len(show.Seasons) == 0 || len(show.Seasons[0].Episodes) == 0 {
		return nil
	}
	
	x := XMLTVShow{
		Title:  show.Title,
		Plot:   show.Plot,
		TmdbID: show.TmdbID,
		ImdbID: show.ImdbID,
		Year:   strconv.Itoa(show.Year),
	}

	for _, actor := range show.CastDetails {
		x.Actors = append(x.Actors, XMLActor{
			Name:  actor.Name,
			Role:  actor.Role,
			Thumb: actor.Thumb,
		})
	}

	// Fallback
	if len(x.Actors) == 0 {
		for _, name := range show.Cast {
			x.Actors = append(x.Actors, XMLActor{Name: name})
		}
	}
	
	if show.TmdbID != "" {
		x.UniqueIDs = append(x.UniqueIDs, struct{Type string `xml:"type,attr"`; ID string `xml:",chardata"`}{Type: "tmdb", ID: show.TmdbID})
	}
	if show.ImdbID != "" {
		x.UniqueIDs = append(x.UniqueIDs, struct{Type string `xml:"type,attr"`; ID string `xml:",chardata"`}{Type: "imdb", ID: show.ImdbID})
	}

	data, err := xml.MarshalIndent(x, "", "  ")
	if err != nil {
		return err
	}
	
	fPath := show.Seasons[0].Episodes[0].FilePath
	dir := filepath.Dir(fPath)
	if strings.Contains(strings.ToLower(filepath.Base(dir)), "season") {
		dir = filepath.Dir(dir)
	}
	nfoPath := filepath.Join(dir, "tvshow_.nfo")
	
	finalData := []byte(xml.Header + string(data))
	return os.WriteFile(nfoPath, finalData, 0644)
}
