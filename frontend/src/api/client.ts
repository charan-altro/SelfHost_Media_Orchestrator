import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getMovies = async () => {
  const res = await apiClient.get('/movies/');
  return res.data;
};

export const updateMovie = async (id: number, data: any) => {
    const res = await apiClient.patch(`/movies/${id}`, data);
    return res.data;
};

export const getTVShows = async () => {
  const res = await apiClient.get('/tvshows/');
  return res.data;
};

export const getLibraries = async () => {
  const res = await apiClient.get('/libraries/');
  return res.data;
};

export const updateTVShow = async (id: number, data: any) => {
    const res = await apiClient.patch(`/tvshows/${id}`, data);
    return res.data;
};


export const getTVShowDetails = async (id: number) => {
  const res = await apiClient.get(`/tvshows/${id}`);
  return res.data;
};

// Media Extras
export const getTrailerUrl = async (type: 'movie' | 'tv', id: number) => {
    const res = await apiClient.get(`/media/${type}/${id}/trailer`);
    return res.data.trailer_url;
};

export const triggerTrailerFetch = async (type: 'movie' | 'tv', id: number) => {
    const res = await apiClient.post(`/media/${type}/${id}/trailer`);
    return res.data;
};

export const downloadSubtitles = async (type: 'movie' | 'episode', id: number, lang: string = 'en') => {
    const endpoint = type === 'movie' ? `/movies/${id}/subtitles` : `/episodes/${id}/subtitles`;
    const res = await apiClient.post(endpoint, null, { params: { language: lang } });
    return res.data;
};

export const createLibrary = async (name: string, path: string, type: 'movie' | 'tv') => {
    const response = await apiClient.post('/libraries/', { name, path, type, language: 'en' });
    return response.data;
};

export const deleteLibrary = async (id: number) => {
  const response = await apiClient.delete(`/libraries/${id}`);
  return response.data;
};

export const updateLibrary = async (id: number, name?: string, path?: string) => {
    const response = await apiClient.patch(`/libraries/${id}`, { name, path });
    return response.data;
};

export const scanLibrary = async (id: number) => {
    const res = await apiClient.post(`/libraries/${id}/scan`);
    return res.data;
};

export const triggerScrape = async (movieId: number) => {
    const res = await apiClient.post(`/movies/${movieId}/scrape`);
    return res.data;
};

export const triggerTVScrape = async (showId: number) => {
    const res = await apiClient.post(`/tvshows/${showId}/scrape`);
    return res.data;
};

export const browseFileSystem = async (path: string) => {
    const res = await apiClient.get('/libraries/browse', { params: { path } });
    return res.data;
};

export const bulkScrape = async (movieIds: number[]) => {
    const res = await apiClient.post('/movies/scrape/bulk', { movie_ids: movieIds });
    return res.data;
};

export const bulkScrapeTV = async (showIds: number[]) => {
    const res = await apiClient.post('/tvshows/scrape/bulk', { show_ids: showIds });
    return res.data;
};

export const cleanupLibrary = async (libraryId: number) => {
    const res = await apiClient.post(`/libraries/${libraryId}/cleanup`);
    return res.data;
};

export const analyzeLibrary = async (libraryId: number) => {
    const res = await apiClient.post(`/libraries/${libraryId}/analyze`);
    return res.data;
};

export const renameMovie = async (movieId: number) => {
    const res = await apiClient.post(`/movies/${movieId}/rename`);
    return res.data;
};

export const downloadSubtitle = async (movieId: number, language = 'en') => {
    const res = await apiClient.post(`/movies/${movieId}/subtitles`, null, { params: { language } });
    return res.data;
};

export const fetchTrailer = async (movieId: number) => {
    const res = await apiClient.post(`/movies/${movieId}/trailer`);
    return res.data;
};

export const searchExternalMovies = async (query: string, year?: number) => {
    const res = await apiClient.get('/movies/search/external', { params: { query, year } });
    return res.data;
};

export const manualMatchMovie = async (movieId: number, tmdbId: number) => {
    const res = await apiClient.post(`/movies/${movieId}/match`, null, { params: { tmdb_id: tmdbId } });
    return res.data;
};

export const searchExternalTV = async (query: string, year?: number) => {
    const res = await apiClient.get('/tvshows/search/external', { params: { query, year } });
    return res.data;
};

export const manualMatchTV = async (showId: number, tmdbId: number) => {
    const res = await apiClient.post(`/tvshows/${showId}/match`, null, { params: { tmdb_id: tmdbId } });
    return res.data;
};

export const getSettings = async () => {
    const res = await apiClient.get('/settings/');
    return res.data;
};

export const patchSettings = async (data: Record<string, any>) => {
    const res = await apiClient.patch('/settings/', data);
    return res.data;
};

export const exportLibraryCSV = () =>
    window.open('/api/export/csv', '_blank');

export const exportLibraryHTML = () =>
    window.open('/api/export/html', '_blank');
