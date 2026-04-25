package models

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"time"
)

type StringList []string

func (sl *StringList) Scan(value interface{}) error {
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New("type assertion to []byte failed")
	}
	return json.Unmarshal(bytes, sl)
}

func (sl StringList) Value() (driver.Value, error) {
	return json.Marshal(sl)
}

type CastMember struct {
	Name  string `json:"name"`
	Role  string `json:"role"`
	Thumb string `json:"thumb"`
}

type Library struct {
	ID       uint   `gorm:"primaryKey;index" json:"id"`
	Name     string `gorm:"index" json:"name"`
	Path     string `gorm:"uniqueIndex" json:"path"`
	Type     string `json:"type"`
	Language string `gorm:"default:'en'" json:"language"`
}

type Movie struct {
	ID             uint       `gorm:"primaryKey;index" json:"id"`
	LibraryID      uint       `gorm:"index" json:"library_id"`
	Library        Library    `json:"library"`
	Title          string     `gorm:"index" json:"title"`
	SortTitle      string     `json:"sort_title"`
	OriginalTitle  string     `json:"original_title"`
	Year           int        `gorm:"index" json:"year"`
	TmdbID         string     `gorm:"index" json:"tmdb_id"`
	ImdbID         string     `gorm:"index" json:"imdb_id"`
	Plot           string     `json:"plot"`
	Tagline        string     `json:"tagline"`
	Genres         StringList `gorm:"type:text" json:"genres"`
	Cast           StringList `gorm:"type:text" json:"cast"`
	CastDetails    []CastMember `gorm:"serializer:json" json:"cast_details"`
	Director       string     `json:"director"`
	ContentRating  string     `json:"content_rating"`
	Runtime        int        `json:"runtime"`
	TmdbRating     float64    `json:"tmdb_rating"`
	ImdbRating     float64    `json:"imdb_rating"`
	TmdbVotes      int        `json:"tmdb_votes"`
	ImdbVotes      int        `json:"imdb_votes"`
	Metascore      int        `json:"metascore"`
	PosterPath     string     `json:"poster_path"`
	FanartPath     string     `json:"fanart_path"`
	Status         string     `gorm:"default:'unmatched'" json:"status"`
	NfoGenerated   bool       `gorm:"default:false" json:"nfo_generated"`
	FileRenamed    bool       `gorm:"default:false" json:"file_renamed"`
	TrailerURL     string     `json:"trailer_url"`
	Files          []MovieFile `gorm:"foreignKey:MovieID" json:"files"`
}

type MovieFile struct {
	ID               uint   `gorm:"primaryKey;index" json:"id"`
	MovieID          uint   `gorm:"index" json:"movie_id"`
	FilePath         string `gorm:"uniqueIndex" json:"file_path"`
	OriginalFilename string `json:"original_filename"`
	SizeBytes        int64  `json:"size_bytes"`
	Resolution       string `json:"resolution"`
	HdrType          string `json:"hdr_type"`
	VideoCodec       string `json:"video_codec"`
	AudioCodec       string `json:"audio_codec"`
	AudioChannels    string `json:"audio_channels"`
	PartNumber       int    `json:"part_number"`
	SubtitlePath     string `json:"subtitle_path"`
}

type TVShow struct {
	ID              uint       `gorm:"primaryKey;index" json:"id"`
	LibraryID       uint       `gorm:"index" json:"library_id"`
	Library         Library    `json:"library"`
	Title           string     `gorm:"index" json:"title"`
	Year            int        `gorm:"index" json:"year"`
	TmdbID          string     `json:"tmdb_id"`
	TvdbID          string     `json:"tvdb_id"`
	ImdbID          string     `json:"imdb_id"`
	Plot            string     `json:"plot"`
	Genres          StringList `gorm:"type:text" json:"genres"`
	Cast            StringList `gorm:"type:text" json:"cast"`
	CastDetails     []CastMember `gorm:"serializer:json" json:"cast_details"`
	Director        string     `json:"director"`
	Runtime         int        `json:"runtime"`
	ContentRating   string     `json:"content_rating"`
	TmdbRating      float64    `json:"tmdb_rating"`
	ImdbRating      float64    `json:"imdb_rating"`
	TmdbVotes       int        `json:"tmdb_votes"`
	Metascore       int        `json:"metascore"`
	PosterPath      string     `json:"poster_path"`
	FanartPath      string     `json:"fanart_path"`
	Status          string     `gorm:"default:'unmatched'" json:"status"`
	EpisodeOrdering string     `gorm:"default:'aired'" json:"episode_ordering"`
	TrailerURL      string     `json:"trailer_url"`
	Seasons         []Season   `gorm:"foreignKey:ShowID" json:"seasons"`
}

type Season struct {
	ID           uint   `gorm:"primaryKey;index" json:"id"`
	ShowID       uint   `gorm:"index" json:"show_id"`
	SeasonNumber int    `gorm:"index" json:"season_number"`
	EpisodeCount int    `gorm:"default:0" json:"episode_count"`
	PosterPath   string `json:"poster_path"`
	Episodes     []Episode `gorm:"foreignKey:SeasonID" json:"episodes"`
}

type Episode struct {
	ID               uint   `gorm:"primaryKey;index" json:"id"`
	SeasonID         uint   `gorm:"index" json:"season_id"`
	EpisodeNumber    int    `gorm:"index" json:"episode_number"`
	Title            string `json:"title"`
	Plot             string `json:"plot"`
	AirDate          string `json:"air_date"`
	FilePath         string `gorm:"uniqueIndex" json:"file_path"`
	OriginalFilename string `json:"original_filename"`
	ThumbnailPath    string `json:"thumbnail_path"`
	Resolution       string `json:"resolution"`
	VideoCodec       string `json:"video_codec"`
	AudioCodec       string `json:"audio_codec"`
	Missing          bool `gorm:"default:false" json:"missing"`
}

type BackgroundTask struct {
	ID        string `gorm:"primaryKey;index" json:"id"`
	Name      string `json:"name"`
	Status    string `gorm:"default:'queued'" json:"status"`
	Progress  int    `gorm:"default:0" json:"progress"`
	Total     int    `gorm:"default:100" json:"total"`
	Message   string `json:"message"`
	Duration  float64 `json:"duration"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}
