# Minimum Viable Product (MVP) Scope

This document sets the definitive boundaries for the SelfHost Media Orchestrator 1.0 (MVP). It outlines what the platform currently guarantees to do, and clearly demarcates what features are definitively excluded from the initial release to maintain focus.

## The Core Product Vision
The goal of the MVP is to provide a "Netflix-like" experience over local files. It should swiftly identify local media, fetch gorgeous posters, and allow the user to manage their collection inside an elegant interface, before eventually launching the media natively on their device.

---

## 1. IN-SCOPE: Core MVP Features

### Ingestion & Display
- **Automated Directory Scanning**: Supports massive libraries. Will scan specified directories and sync to the local database.
- **Cinematic Frontend UI**: Interactive React dashboard displaying visually rich movie/show cards, ratings, synopsis, and cast lists.
- **Universal Local Matching (NFO Support)**: If `.nfo` files exist locally, the system will prioritize them for 100% accurate ingestion without API calls.

### Scraping & Enrichment
- **Automated API Lookups**: Deep integration with TMDB and OMDb to pull posters, fanart, ratings, genre lists, and trailers. 
- **Concurrent Scraping Architecture**: High-speed, rate-limited downloads to populate the database without crashing public APIs.

### Library Management
- **File Renaming Utility**: Standardize raw/messy scene release filenames into a cleaner formal structure.
- **Subtitle Scraper**: Ability to pinpoint and download matching `.srt` files for specific media using hashed endpoints.
- **Database Self-Healing**: Hardened SQLite setups to manage container lifecycle and volume mapping safely.

---

## 2. OUT-OF-SCOPE: Post-MVP Features (v2.0+)

The following features, while highly desirable, represent significant technical overhead and are strictly out-of-scope for the 1.0 release boundary.

- **On-the-Fly Video Transcoding**: The MVP will not convert media to web-friendly formats (like H.264 / AAC) in real-time. The MVP assumes the user has a client capable of direct playback, or handles transcoding through a separate service (like Tdarr).
- **Multi-Tenant User Accounts**: The MVP acts as a single-user "Admin" interface. There are no bespoke profiles, distinct watch histories, or restricted permission levels for children/guests.
- **Embedded Web Video Streaming**: The MVP will serve metadata, but will not force the user to stream a raw `.mkv` file directly through the browser. Native file launching is preferred (see Roadmap).
- **Live TV / DVR Functions**: Support for IPTV links, XMLTV, or live recording hardware.
