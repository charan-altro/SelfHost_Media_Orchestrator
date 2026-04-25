// Wails Native API Bindings
import * as App from '../../wailsjs/go/main/App';

export const getMovies = async () => {
  return await App.GetMovies();
};

export const updateMovie = async (id: number, data: any) => {
    return await App.UpdateMovie(id, data);
};

export const getTVShows = async () => {
  return await App.GetTVShows();
};

export const getLibraries = async () => {
  return await App.GetLibraries();
};

export const updateTVShow = async (id: number, data: any) => {
    return await App.UpdateTVShow(id, data);
};

export const getTVShowDetails = async (id: number) => {
  return await App.GetTVShowDetails(id);
};

// Media Extras
export const getTrailerUrl = async (type: 'movie' | 'tv', id: number) => {
    // Current Go implementation returns trailer_url in the model, but we can have a specific call
    return "";
};

export const triggerTrailerFetch = async (type: 'movie' | 'tv', id: number) => {
    return {};
};

export const downloadSubtitles = async (type: 'movie' | 'episode', id: number, lang: string = 'en') => {
    return {};
};

export const createLibrary = async (name: string, path: string, type: 'movie' | 'tv') => {
    return await App.AddLibrary(name, path, type);
};

export const deleteLibrary = async (id: number) => {
  return await App.DeleteLibrary(id);
};

export const updateLibrary = async (id: number, name?: string, path?: string) => {
    return await App.UpdateLibrary(id, { name, path });
};

export const scanLibrary = async (id: number) => {
    return await App.ScanLibrary(id);
};

export const triggerScrape = async (movieId: number) => {
    return await App.TriggerScrape(movieId);
};

export const triggerTVScrape = async (showId: number) => {
    return await App.TriggerTVScrape(showId);
};

export const browseFileSystem = async (path: string) => {
    return await App.BrowseFileSystem(path);
};

export const getDrives = async () => {
    return await App.GetDrives();
};

export const getLocalArtwork = async (path: string) => {
    return await App.GetLocalArtwork(path);
};

export const getTasks = async () => {
    return await App.GetTasks();
};

export const bulkScrape = async (movieIds: number[]) => {
    return await App.BulkScrapeMovies(movieIds);
};

export const bulkScrapeTV = async (showIds: number[]) => {
    return await App.BulkScrapeTVShows(showIds);
};

export const cleanupLibrary = async (libraryId: number) => {
    return await App.CleanupLibrary(libraryId);
};

export const analyzeLibrary = async (libraryId: number) => {
    // Stub
    return {};
};

export const renameMovie = async (movieId: number) => {
    return await App.RenameMovie(movieId);
};

export const downloadSubtitle = async (movieId: number, language = 'en') => {
    return {};
};

export const fetchTrailer = async (movieId: number) => {
    return {};
};

export const searchExternalMovies = async (query: string, year?: number) => {
    return await App.SearchExternalMovie(query, year || 0);
};

export const manualMatchMovie = async (movieId: number, tmdbId: number) => {
    return await App.MatchMovie(movieId, String(tmdbId));
};

export const searchExternalTV = async (query: string, year?: number) => {
    return await App.SearchExternalTV(query, year || 0);
};

export const manualMatchTV = async (showId: number, tmdbId: number) => {
    return await App.MatchTVShow(showId, String(tmdbId));
};

export const getSettings = async () => {
    return await App.GetSettings();
};

export const patchSettings = async (data: Record<string, any>) => {
    return await App.PatchSettings(data);
};

export const getDownloadUrl = (type: 'movie' | 'episode', id: number) => {
    // In Wails, we don't use download URLs, we use App.DownloadMedia
    return "";
};

export const exportLibraryCSV = async () => {
    return await App.ExportCSV();
};

export const exportLibraryHTML = async () => {
    return await App.ExportHTML();
};

export const downloadMediaNative = async (type: 'movie' | 'episode', id: number) => {
    return await App.DownloadMedia(type, id);
};

export const showInFolder = async (path: string) => {
    return await App.ShowInFolder(path);
};

export const openInPlayer = async (path: string) => {
    return await App.OpenInPlayer(path);
};

export const playMovie = async (id: number) => {
    return await App.PlayMovie(id);
};

export const playEpisode = async (id: number) => {
    return await App.PlayEpisode(id);
};
