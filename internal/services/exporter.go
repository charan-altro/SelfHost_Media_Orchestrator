package services

import (
	"bytes"
	"encoding/csv"
	"fmt"
	"html"
	"media-orchestrator/internal/database"
	"media-orchestrator/internal/models"
	"strings"
	"time"
)

const HTML_TEMPLATE = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SelfHost Media Orchestrator Library Export</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }
  h1 { font-size: 2rem; font-weight: 700; color: #6c63ff; margin-bottom: 0.25rem; }
  .meta { color: #888; margin-bottom: 2rem; font-size: 0.9rem; }
  table { width: 100%; border-collapse: collapse; background: #16213e; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.4); }
  thead { background: #6c63ff; color: #fff; }
  th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #0f3460; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #0f3460; }
  .badge { padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
  .matched { background: #155724; color: #d4edda; }
  .unmatched { background: #721c24; color: #f8d7da; }
</style>
</head>
<body>
<h1>🎬 SelfHost Media Orchestrator Library</h1>
<p class="meta">Exported {{COUNT}} movies &nbsp;•&nbsp; {{DATE}}</p>
<table>
<thead><tr>
  <th>#</th><th>Title</th><th>Year</th><th>Rating</th><th>Status</th><th>File</th>
</tr></thead>
<tbody>
{{ROWS}}
</tbody>
</table>
</body>
</html>`

const ROW_TEMPLATE = `<tr>
  <td>%d</td>
  <td><strong>%s</strong></td>
  <td>%v</td>
  <td>%.1f</td>
  <td><span class="badge %s">%s</span></td>
  <td><small>%s</small></td>
</tr>`

func ExportCSV() string {
	var movies []models.Movie
	database.DB.Preload("Files").Order("title asc").Find(&movies)

	b := &bytes.Buffer{}
	w := csv.NewWriter(b)

	w.Write([]string{"ID", "Title", "Year", "Status", "TMDB ID", "Rating", "File Path"})

	for _, m := range movies {
		filePath := ""
		if len(m.Files) > 0 {
			filePath = m.Files[0].FilePath
		}
		w.Write([]string{
			fmt.Sprintf("%d", m.ID),
			m.Title,
			fmt.Sprintf("%d", m.Year),
			m.Status,
			m.TmdbID,
			fmt.Sprintf("%.1f", m.TmdbRating),
			filePath,
		})
	}
	w.Flush()
	return b.String()
}

func ExportHTML() string {
	var movies []models.Movie
	database.DB.Preload("Files").Order("title asc").Find(&movies)

	rowsHTML := ""
	for i, m := range movies {
		filePath := "—"
		if len(m.Files) > 0 {
			filePath = m.Files[0].FilePath
		}
		statusCls := "unmatched"
		if m.Status == "matched" {
			statusCls = "matched"
		}
		rowsHTML += fmt.Sprintf(ROW_TEMPLATE,
			i+1,
			html.EscapeString(m.Title),
			m.Year,
			m.TmdbRating,
			statusCls,
			m.Status,
			html.EscapeString(filePath),
		)
	}

	dateStr := time.Now().Format("2006-01-02 15:04 MST")
	
	result := HTML_TEMPLATE
	result = strings.Replace(result, "{{COUNT}}", fmt.Sprintf("%d", len(movies)), 1)
	result = strings.Replace(result, "{{DATE}}", dateStr, 1)
	result = strings.Replace(result, "{{ROWS}}", rowsHTML, 1)
	
	return result
}
