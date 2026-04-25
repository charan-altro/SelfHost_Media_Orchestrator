package scraper

import (
	"encoding/json"
	"fmt"
	"io"
	"media-orchestrator/internal/models"
	"net/http"
	"net/url"
	"strings"
	"time"
)

type TMDBScraper struct {
	APIKey  string
	BaseURL string
}

func NewTMDBScraper(apiKey string) *TMDBScraper {
	return &TMDBScraper{
		APIKey:  apiKey,
		BaseURL: "https://api.themoviedb.org/3",
	}
}

func (s *TMDBScraper) doRequest(endpoint string, params url.Values) ([]byte, error) {
	cleanKey := strings.TrimSpace(s.APIKey)
	isBearer := len(cleanKey) > 50

	u, err := url.Parse(s.BaseURL + endpoint)
	if err != nil {
		return nil, err
	}

	if !isBearer {
		params.Add("api_key", cleanKey)
	}
	u.RawQuery = params.Encode()
	fullURL := u.String()

	var lastErr error
	for i := 0; i < 3; i++ {
		fmt.Printf("[TMDB] Requesting (Attempt %d): %s\n", i+1, fullURL)
		req, err := http.NewRequest("GET", fullURL, nil)
		if err != nil {
			return nil, err
		}

		if isBearer {
			req.Header.Set("Authorization", "Bearer "+cleanKey)
		}
		req.Header.Set("Accept", "application/json")

		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("network error: %w", err)
			time.Sleep(time.Duration(i+1) * 500 * time.Millisecond)
			continue
		}
		defer resp.Body.Close()

		body, err := io.ReadAll(resp.Body)
		if err != nil {
			lastErr = err
			continue
		}

		if resp.StatusCode != http.StatusOK {
			lastErr = fmt.Errorf("TMDB API returned %d: %s", resp.StatusCode, string(body))
			if resp.StatusCode == 429 || resp.StatusCode >= 500 {
				time.Sleep(time.Duration(i+1) * time.Second)
				continue
			}
			return nil, lastErr
		}
		return body, nil
	}
	return nil, lastErr
}

func (s *TMDBScraper) SearchMovies(query string, year int) ([]map[string]interface{}, error) {
	if s.APIKey == "" {
		return nil, fmt.Errorf("TMDB API Key missing")
	}

	params := url.Values{}
	params.Add("query", query)
	if year > 0 {
		params.Add("year", fmt.Sprintf("%d", year))
	}

	body, err := s.doRequest("/search/movie", params)
	if err != nil {
		return nil, err
	}

	var result struct {
		Results []map[string]interface{} `json:"results"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}

	return result.Results, nil
}

func (s *TMDBScraper) ScrapeMovie(movie *models.Movie) error {
	if movie.TmdbID != "" {
		return s.ScrapeMovieByID(movie)
	}
	
	results, err := s.SearchMovies(movie.Title, movie.Year)
	if (err != nil || len(results) == 0) && movie.Year > 0 {
		results, err = s.SearchMovies(movie.Title, 0)
	}

	if err != nil || len(results) == 0 {
		return fmt.Errorf("movie not found")
	}
	
	first := results[0]
	movie.TmdbID = fmt.Sprintf("%.0f", first["id"].(float64))
	return s.ScrapeMovieByID(movie)
}

func (s *TMDBScraper) ScrapeMovieByID(movie *models.Movie) error {
	if s.APIKey == "" {
		return fmt.Errorf("TMDB API Key missing")
	}

	params := url.Values{}
	params.Add("append_to_response", "credits")
	body, err := s.doRequest(fmt.Sprintf("/movie/%s", movie.TmdbID), params)
	if err != nil {
		return err
	}

	var data map[string]interface{}
	json.Unmarshal(body, &data)

	if title, ok := data["title"].(string); ok {
		movie.Title = title
	}
	if plot, ok := data["overview"].(string); ok {
		movie.Plot = plot
	}
	if rating, ok := data["vote_average"].(float64); ok {
		movie.TmdbRating = rating
	}
	if poster, ok := data["poster_path"].(string); ok {
		movie.PosterPath = "https://image.tmdb.org/t/p/original" + poster
	}
	if backdrop, ok := data["backdrop_path"].(string); ok {
		movie.FanartPath = "https://image.tmdb.org/t/p/original" + backdrop
	}

	if credits, ok := data["credits"].(map[string]interface{}); ok {
		if cast, ok := credits["cast"].([]interface{}); ok {
			var castList []string
			var castDetails []models.CastMember
			for i, c := range cast {
				if i >= 15 {
					break
				}
				if person, ok := c.(map[string]interface{}); ok {
					name, _ := person["name"].(string)
					role, _ := person["character"].(string)
					profile, _ := person["profile_path"].(string)
					
					castList = append(castList, name)
					
					thumb := ""
					if profile != "" {
						thumb = "https://image.tmdb.org/t/p/original" + profile
					}
					
					castDetails = append(castDetails, models.CastMember{
						Name:  name,
						Role:  role,
						Thumb: thumb,
					})
				}
			}
			movie.Cast = castList
			movie.CastDetails = castDetails
		}
	}
	
	movie.Status = "matched"
	return nil
}

func (s *TMDBScraper) SearchTV(query string, year int) ([]map[string]interface{}, error) {
	if s.APIKey == "" {
		return nil, fmt.Errorf("TMDB API Key missing")
	}

	params := url.Values{}
	params.Add("query", query)
	if year > 0 {
		params.Add("first_air_date_year", fmt.Sprintf("%d", year))
	}

	body, err := s.doRequest("/search/tv", params)
	if err != nil {
		return nil, err
	}

	var result struct {
		Results []map[string]interface{} `json:"results"`
	}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, err
	}

	return result.Results, nil
}

func (s *TMDBScraper) ScrapeTVShow(show *models.TVShow) error {
	if show.TmdbID != "" {
		return s.ScrapeTVByID(show)
	}
	
	results, err := s.SearchTV(show.Title, show.Year)
	if (err != nil || len(results) == 0) && show.Year > 0 {
		results, err = s.SearchTV(show.Title, 0)
	}

	if err != nil || len(results) == 0 {
		return fmt.Errorf("show not found")
	}
	
	first := results[0]
	show.TmdbID = fmt.Sprintf("%.0f", first["id"].(float64))
	return s.ScrapeTVByID(show)
}

func (s *TMDBScraper) ScrapeTVByID(show *models.TVShow) error {
	if s.APIKey == "" {
		return fmt.Errorf("TMDB API Key missing")
	}

	params := url.Values{}
	params.Add("append_to_response", "credits")
	body, err := s.doRequest(fmt.Sprintf("/tv/%s", show.TmdbID), params)
	if err != nil {
		return err
	}

	var data map[string]interface{}
	json.Unmarshal(body, &data)

	if title, ok := data["name"].(string); ok {
		show.Title = title
	}
	if plot, ok := data["overview"].(string); ok {
		show.Plot = plot
	}
	if rating, ok := data["vote_average"].(float64); ok {
		show.TmdbRating = rating
	}
	if poster, ok := data["poster_path"].(string); ok {
		show.PosterPath = "https://image.tmdb.org/t/p/original" + poster
	}
	if backdrop, ok := data["backdrop_path"].(string); ok {
		show.FanartPath = "https://image.tmdb.org/t/p/original" + backdrop
	}

	if credits, ok := data["credits"].(map[string]interface{}); ok {
		if cast, ok := credits["cast"].([]interface{}); ok {
			var castList []string
			var castDetails []models.CastMember
			for i, c := range cast {
				if i >= 15 {
					break
				}
				if person, ok := c.(map[string]interface{}); ok {
					name, _ := person["name"].(string)
					role, _ := person["character"].(string)
					profile, _ := person["profile_path"].(string)
					
					castList = append(castList, name)
					
					thumb := ""
					if profile != "" {
						thumb = "https://image.tmdb.org/t/p/original" + profile
					}
					
					castDetails = append(castDetails, models.CastMember{
						Name:  name,
						Role:  role,
						Thumb: thumb,
					})
				}
			}
			show.Cast = castList
			show.CastDetails = castDetails
		}
	}
	
	show.Status = "matched"
	return nil
}
