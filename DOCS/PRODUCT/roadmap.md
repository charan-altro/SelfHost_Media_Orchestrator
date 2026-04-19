# Product Roadmap & Future Technical Objectives

The SelfHost Media Orchestrator roadmap details the strategic evolution from an organizational library app to a fully integrated media delivery hub.

## Phase 1: MVP Stabilization (Current)

The primary goal is ensuring the 1.0 core functions flawlessly across different Docker environments and host filesystems.

- [x] High-speed multi-threaded scanning
- [x] Real-time SSE integration for frontend progress bars
- [x] Deep TMDB / OMDb scraping integration
- [x] Resilient SQLite setup in Docker containers

## Phase 2: Playback & Accessibility (v1.5)

To bridge the gap between "management" and "viewing", the platform needs an integrated way to actually consume the files. 

- **Hybrid Media Playback**: Implementing a dual-mode playback system.
  - *Native Launch*: A local bridge or daemon that tells the host Windows / Mac environment to natively open VLC or MPV for the file, providing the highest fidelity hardware decoding.
  - *Fallback Browser Streaming*: Basic HTML5 chunked streaming (`<video src="...">`) for universally supported MP4 and WebM formats, specifically for users accessing the dashboard away from the host server.

- **Real-Time Directory Monitoring**: Moving away from "Refresh Scans" to integrating utilities like `watchdog` to monitor `/mnt/media` for file drops, triggering instant ingestion pipelines without user input.

## Phase 3: Desktop Packaging & Ecosystem (v2.0)

Providing true "Self-Hosted" capabilities directly on user desktops without demanding deep Docker knowledge.

- **Native Windows Build**: Wrapping the FastAPI backend and Vite frontend into an Electron or Tauri execution shell, or utilizing PyInstaller. This ensures zero-setup installation for casual Windows users.
- **Advanced Ecosystem Interoperability**:
  - Tdarr webhook communication (syncing library state when Tdarr finishes a transcode).
  - Radarr / Sonarr ingestion endpoints to safely accept webhook notifications rather than arbitrary folder scanning.

## Phase 4: Expansion Modules (v2.5+)

- Custom plugin architecture for metadata (Anime endpoints like AniDB).
- Personal analytics dashboards (Watch times, size analytics over time, bitrate density charts).
