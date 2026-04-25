package services

import (
	"regexp"
	"strconv"
	"strings"
)

type ParsedMedia struct {
	Title     string
	Year      int
	Season    int
	Episode   int
	IsTV      bool
	ExtraTags []string
}

var (
	movieRE   = regexp.MustCompile(`(?i)^(.*?)(?:[. (\[]+((?:19|20)\d{2}))[. )\]]*(.*)$`)
	episodeRE = regexp.MustCompile(`(?i)^(.*?)[\. _-]*S(\d{2})E(\d{2})[\. _-]?(.*)$`)
	tagRE     = regexp.MustCompile(`[\. \-\[\]()]+`)
)

func ParseFilename(filename string) ParsedMedia {
	// Remove extension
	name := filename
	if idx := strings.LastIndex(filename, "."); idx != -1 {
		name = filename[:idx]
	}

	// Try Episode first
	if epMatch := episodeRE.FindStringSubmatch(name); epMatch != nil {
		title := strings.ReplaceAll(epMatch[1], ".", " ")
		season, _ := strconv.Atoi(epMatch[2])
		episode, _ := strconv.Atoi(epMatch[3])
		tags := tagRE.Split(epMatch[4], -1)
		
		var cleanTags []string
		for _, t := range tags {
			if t != "" {
				cleanTags = append(cleanTags, t)
			}
		}

		return ParsedMedia{
			Title:     strings.TrimSpace(title),
			Season:    season,
			Episode:   episode,
			IsTV:      true,
			ExtraTags: cleanTags,
		}
	}

	// Try Movie
	if movMatch := movieRE.FindStringSubmatch(name); movMatch != nil {
		title := strings.ReplaceAll(movMatch[1], ".", " ")
		year, _ := strconv.Atoi(movMatch[2])
		tags := tagRE.Split(movMatch[3], -1)

		var cleanTags []string
		for _, t := range tags {
			if t != "" {
				cleanTags = append(cleanTags, t)
			}
		}

		return ParsedMedia{
			Title:     strings.TrimSpace(title),
			Year:      year,
			IsTV:      false,
			ExtraTags: cleanTags,
		}
	}

	// Fallback
	return ParsedMedia{
		Title: strings.TrimSpace(strings.ReplaceAll(name, ".", " ")),
	}
}
