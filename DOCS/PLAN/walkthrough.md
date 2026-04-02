# SelfHost Media Orchestrator – Project Evolution & Feature Guide

SelfHost Media Orchestrator has evolved from a simple media scanner into a premium, feature-rich management suite. This guide documents the major milestones and current features of the application.

---

## Phase 1: Milestone 1 (M1) MVP
The initial version of SelfHost Media Orchestrator was focused on basic functionality and a simple browser UI.

- **FastAPI Core**: A high-performance Python backend for managing media records in a SQLite database.
- **Robust Scanning**: A basic recursive scanner that identifies video files and adds them to the database.
- **Regex Parsing**: A filename parser that extracts titles and years from scene naming patterns.
- **Initial TMDB Integration**: Simple metadata retrieval (Title, Overview, Poster) for movies.
- **Kodi NFO Support**: Generation of XML-based NFO files for local metadata persistence.
- **React Basic UI**: A functional grid view for browsing and matching movies.

---

## Phase 2: Advanced Feature Set (M2)

### 1. Netflix-Style UI Overhaul
The entire frontend was redesigned to provide a cinematic web experience inspired by modern streaming platforms.
- **Sleek Layout**: A transparent top-bar navigation and dark-theme aesthetic throughout.
- **Hero Banners**: Massive backdrop images with title typography and "Play" buttons.
- **Hover Animations**: Smooth scaling (`hover:scale-105`) and gradient overlays on all media cards.
- **Premium Details Modal**: Full-screen overlay featuring cast profile images, high-res fanart, and season/episode browsers for TV series.

### 2. Deep Metadata & Media Extras
- **Expanded Scrapers**: Added support for **OMDb** (IMDb ratings, votes, awards) and **Cinemagoer** fallback.
- **Cast/Crew Management**: Automatically downloads actor profile images into `.actors` folders in your library.
- **Subtitles & Trailers**: Integrated **OpenSubtitles** for automatic SRT downloads and **TMDB/YouTube** for instant trailer playback.
- **Manual Metadata Editor**: Built-in UI to manually correct titles, years, plots, and other records directly from the browser.

### 3. Library Management & Performance
- **Edit Library Paths**: Support for renaming and moving library directories with automatic path migration in the database.
- **Fast Scanning & Background Tasks**: Refactored the library scan into a two-phase process (Instant DB Sync -> Background Enrichment) to handle libraries larger than 10,000 items without UI lag.
- **JSON Metadata Backups**: A one-click button in Settings to download a complete backup of the media database for safety.

---

## How to Run and Test

### 1. Configuration & .env Setup
Before running the application, you must configure your environment:
1. Copy the `.env.example` file to a new file named `.env`.
2. Open `.env` and configure your drive paths. For example, to map your Windows `D:` and `E:` drives:
   ```env
   DRIVE_D_PATH=D:\
   DRIVE_E_PATH=E:\
   TMDB_API_KEY=your_key_here
   OMDB_API_KEY=your_key_here
   ```
3. **Universal Drive Mapping**: Inside the container, these drives are automatically mounted to `/mnt/d`, `/mnt/e`, etc. When adding a library in the UI, use these `/mnt/x` paths.

### 2. Deployment via Docker

#### Option A: Run from Docker Hub (Recommended)
The fastest way to get started is by using the pre-built image:
1. Create a `docker-compose.yml` file:
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
       restart: unless-stopped 
   ```
2. Run `docker-compose up -d`.

#### Option B: Build from Source
If you want to contribute or modify the code:
```bash
git clone https://github.com/charankumarbs/SelfHost_Media_Orchestrator.git
cd SelfHost_Media_Orchestrator
docker-compose up --build -d
```
The system will be accessible at **`http://localhost:8000`**.

---

## Phase 3: Open Source & CI/CD


SelfHost Media Orchestrator is now a professional open-source project with automated distribution.

### 1. GitHub Actions (CI/CD)
The project includes a `docker-publish.yml` workflow that automatically:
- Builds the Docker image on every push to `main`.
- Pushes the image to **Docker Hub** (`charankumarbs/selfhost-media-orchestrator`).

### 2. Security & Secrets
To maintain security, API keys and Docker tokens are never stored in the repository. If you are forking the project, ensure you set up the following **GitHub Secrets**:
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

### 3. Adding Your First Library
1. Navigate to the **Settings** page.
2. Click **Add Library** and provide a name and path (e.g., `/mnt/d/Movies`).
3. The system will start a **Fast Scan** instantly.
4. Go to the **Movies** or **TV Shows** tab to view your items.
5. Click **Scrape** on a media card or use **Bulk Scrape** to start fetching high-quality metadata and artwork.

### 3. Verifying Results
Observe the **Tasks Page** for real-time progress updates. Once a task is complete, you will see high-resolution posters, backdrops, and detailed plot overviews in the UI.