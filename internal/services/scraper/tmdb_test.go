package scraper

import (
	"fmt"
	"media-orchestrator/internal/models"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestTMDBScraper_SearchMovies(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, `{"results": [{"id": 123, "title": "Mock Movie"}]}`)
	}))
	defer server.Close()

	s := NewTMDBScraper("fake_key")
	s.BaseURL = server.URL

	results, err := s.SearchMovies("test", 0)
	if err != nil {
		t.Fatalf("SearchMovies failed: %v", err)
	}

	if len(results) != 1 || results[0]["title"] != "Mock Movie" {
		t.Errorf("Expected 1 result with title 'Mock Movie', got %v", results)
	}
}

func TestTMDBScraper_ScrapeMovieByID(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, `{"title": "Detailed Movie", "overview": "A plot", "vote_average": 7.5}`)
	}))
	defer server.Close()

	s := NewTMDBScraper("fake_key")
	s.BaseURL = server.URL

	movie := &models.Movie{TmdbID: "123"}
	err := s.ScrapeMovieByID(movie)
	if err != nil {
		t.Fatalf("ScrapeMovieByID failed: %v", err)
	}

	if movie.Title != "Detailed Movie" || movie.Plot != "A plot" || movie.TmdbRating != 7.5 {
		t.Errorf("Movie data mismatch: %+v", movie)
	}
}

func TestTMDBScraper_TV(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprintln(w, `{"name": "Detailed TV", "overview": "TV Plot", "vote_average": 8.0}`)
	}))
	defer server.Close()

	s := NewTMDBScraper("fake_key")
	s.BaseURL = server.URL

	show := &models.TVShow{TmdbID: "456"}
	err := s.ScrapeTVByID(show)
	if err != nil {
		t.Fatalf("ScrapeTVByID failed: %v", err)
	}

	if show.Title != "Detailed TV" || show.Plot != "TV Plot" || show.TmdbRating != 8.0 {
		t.Errorf("Show data mismatch: %+v", show)
	}
}
