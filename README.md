# SelfHost Media Orchestrator

[![Docker Build](https://github.com/charankumarbs/SelfHost_Media_Orchestrator/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/charankumarbs/SelfHost_Media_Orchestrator/actions/workflows/docker-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker Pulls](https://img.shields.io/docker/pulls/charankumarbs/selfhost-media-orchestrator.svg)](https://hub.docker.com/r/charankumarbs/selfhost-media-orchestrator)

**SelfHost Media Orchestrator** is a professional, Docker-native media management suite designed for large-scale movie and TV show libraries. It provides a cinematic, Netflix-style interface for browsing, managing, and automating your local media collection.

## Key Features

- 🎬 **Cinematic UI**: A high-performance, responsive React frontend inspired by premium streaming platforms.
- 🔍 **Automated Scraping**: Seamless integration with TMDB and OMDB for metadata, posters, and backdrops.
- 📂 **Smart Scanner**: Optimized for massive libraries (10,000+ items) with deep folder scanning and NFO support.
- 🛠️ **Management Tools**: Built-in file renamer, subtitle downloader, trailer scraper, and NFO generator.
- 📦 **Docker Ready**: Zero-configuration deployment with a single `docker-compose.yml`.
- 💾 **Portability**: All metadata and settings are stored locally, ensuring your library remains yours.

## Quick Start

### 1. Prerequisites
- Docker and Docker Compose installed on your system.

### 2. Run with Docker (Recommended)
The easiest way to get started is by using the pre-built image from Docker Hub.

Create a `docker-compose.yml` file:
```yaml
services:
  orchestrator:
    image: charankumarbs/selfhost-media-orchestrator:latest
    ports:
      - "8000:8000"
    volumes:
      - ./config:/config
      - ./media:/media
      - ./data:/data
      # Map your host drives here (Example for Windows)
      - D:\:/mnt/d
    environment:
      - TZ=UTC
    restart: unless-stopped
```

Run it:
```bash
docker-compose up -d
```
Access the UI at `http://localhost:8000`.

### 3. Build from Source
```bash
# Clone the repository
git clone https://github.com/charankumarbs/SelfHost_Media_Orchestrator.git
cd SelfHost_Media_Orchestrator

# Start the application
docker-compose up -d
```

## Configuration
The application works out-of-the-box. To enable metadata scraping, add your API keys in the **Settings** tab within the UI or via environment variables in `docker-compose.yml`:
- `TMDB_API_KEY`
- `OMDB_API_KEY`

## Project Structure

- `backend/`: FastAPI server handling scanning, metadata, and database operations.
- `frontend/`: Vite-powered React application with TailwindCSS.
- `docker/`: Deployment configurations.
- `config/`: Application settings and logs (locally mapped).
- `data/`: SQLite database (locally mapped).

## License
MIT License. See [LICENSE](LICENSE) for details.
