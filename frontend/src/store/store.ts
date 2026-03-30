import { create } from 'zustand';
import { 
  getMovies, 
  getLibraries, 
  scanLibrary, 
  triggerScrape, 
  deleteLibrary, 
  bulkScrape, 
  getTVShows, 
  triggerTVScrape,
  apiClient,
  updateLibrary,
  bulkScrapeTV
} from '../api/client';

export interface MovieFile {
  id: number;
  original_filename: string;
  file_path: string;
  resolution: string;
  video_codec: string;
}

export interface ScanProgress {
  total: number;
  current: number;
  file: string;
  status: string;
}

export interface Task {
  id: string;
  name: string;
  status: 'queued' | 'running' | 'done' | 'error';
  progress: number;
  total: number;
  message: string;
  created_at: string;
}

export interface Movie {
  id: number;
  title: string;
  year: number;
  status: string;
  poster_path: string;
  fanart_path: string;
  plot: string;
  tmdb_rating?: number;
  imdb_rating?: number;
  runtime?: number;
  genres?: string[];
  cast?: any[];
  director?: string;
  nfo_generated: boolean;
  file_renamed: boolean;
  trailer_url?: string;
  files: MovieFile[];
}

export interface Library {
  id: number;
  name: string;
  path: string;
  type: string;
}

export interface Episode {
  id: number;
  season_id: number;
  episode_number: number;
  title: string;
  plot?: string;
  air_date?: string;
  file_path?: string;
  thumbnail_path?: string;
  resolution?: string;
  video_codec?: string;
}

export interface Season {
  id: number;
  show_id: number;
  season_number: number;
  episode_count: number;
  poster_path?: string;
  episodes?: Episode[];
}

export interface TVShow {
  id: number;
  title: string;
  year: number;
  status: string;
  poster_path: string;
  fanart_path: string;
  plot: string;
  tmdb_rating?: number;
  imdb_rating?: number;
  runtime?: number;
  genres?: string[];
  cast?: any[];
  director?: string;
  seasons?: Season[];
}

export interface Notification {
  id: string;
  message: string;
  type: 'info' | 'success' | 'error';
}

interface AppState {
  movies: Movie[];
  tvShows: TVShow[];
  libraries: Library[];
  isLoading: boolean;
  fetchData: () => Promise<void>;
  scanLibrary: (id: number) => Promise<void>;
  scrapeMovie: (id: number) => Promise<void>;
  scrapeTVShow: (id: number) => Promise<void>;
  removeLibrary: (id: number) => Promise<void>;
  editLibrary: (id: number, name?: string, path?: string) => Promise<void>;
  
  // Bulk selection state
  selectedMovieIds: number[];
  selectedTVShowIds: number[];
  toggleMovieSelection: (id: number) => void;
  toggleTVShowSelection: (id: number) => void;
  selectMovies: (ids: number[]) => void;
  selectTVShows: (ids: number[]) => void;
  clearMovieSelection: () => void;
  clearTVShowSelection: () => void;
  bulkScrapeMovies: () => Promise<void>;
  bulkScrapeTVShows: () => Promise<void>;
  bulkAnalyzeMovies: () => Promise<void>;
  bulkAnalyzeTVShows: () => Promise<void>;

  // Scan progress state
  scanProgress: Record<number, ScanProgress>;
  setScanProgress: (id: number, progress: ScanProgress | null) => void;

  // Task state
  tasks: Task[];
  isLoadingTasks: boolean;
  fetchTasks: () => Promise<void>;
  clearTasks: () => Promise<void>;

  // Notification state
  notifications: Notification[];
  addNotification: (message: string, type?: 'info' | 'success' | 'error') => void;
  removeNotification: (id: string) => void;
}

export const useStore = create<AppState>((set, get) => ({
  movies: [],
  tvShows: [],
  libraries: [],
  isLoading: false,
  selectedMovieIds: [],
  selectedTVShowIds: [],
  notifications: [],
  tasks: [],
  isLoadingTasks: false,
  
  addNotification: (message, type = 'info') => {
    const id = Math.random().toString(36).substring(7);
    set((state) => ({
      notifications: [...state.notifications, { id, message, type }]
    }));
    setTimeout(() => get().removeNotification(id), 5000);
  },

  removeNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id)
    }));
  },

  fetchTasks: async () => {
    set({ isLoadingTasks: true });
    try {
      const res = await apiClient.get('/tasks/');
      set({ tasks: res.data, isLoadingTasks: false });
    } catch (error) {
      console.error(error);
      set({ isLoadingTasks: false });
    }
  },

  clearTasks: async () => {
    try {
      await apiClient.delete('/tasks/');
      set({ tasks: [] });
      get().addNotification('All tasks cleared.', 'success');
    } catch (error) {
      console.error(error);
      get().addNotification('Failed to clear tasks.', 'error');
    }
  },

  fetchData: async () => {
    set({ isLoading: true });
    try {
      const [movies, tvShows, libraries] = await Promise.all([getMovies(), getTVShows(), getLibraries()]);
      set({ movies, tvShows, libraries, isLoading: false });
    } catch (error) {
      console.error(error);
      set({ isLoading: false });
    }
  },

  scanProgress: {},

  setScanProgress: (id: number, progress: ScanProgress | null) => {
    set((state) => {
      const newProgress = { ...state.scanProgress };
      if (progress === null) {
        delete newProgress[id];
      } else {
        newProgress[id] = progress;
      }
      return { scanProgress: newProgress };
    });
  },

  scanLibrary: async (id: number) => {
    // 1. SET IMMEDIATE UI STATE (Don't wait for SSE)
    get().setScanProgress(id, {
        status: 'scanning',
        file: 'Connecting to server...',
        current: 0,
        total: 0
    });

    await scanLibrary(id);
    
    const es = new EventSource(`/api/libraries/${id}/scan/progress`);
    
    es.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === 'waiting') return;

        get().setScanProgress(id, data);

        if (data.status === 'done' || data.status === 'error') {
            es.close();
            // Wait 5 seconds (up from 3) to let user see "Finished"
            setTimeout(() => {
                get().setScanProgress(id, null);
                get().fetchData(); // Final refresh
            }, 5000);
        }
    };
    es.onerror = () => {
        es.close();
        get().setScanProgress(id, null);
    };
  },

  scrapeMovie: async (id: number) => {
    await triggerScrape(id);
    setTimeout(() => {
        get().fetchData();
    }, 2000);
  },

  scrapeTVShow: async (id: number) => {
    await triggerTVScrape(id);
    setTimeout(() => {
        get().fetchData();
    }, 2000);
  },

  removeLibrary: async (id: number) => {
    await deleteLibrary(id);
    get().fetchData();
  },

  editLibrary: async (id: number, name?: string, path?: string) => {
    await updateLibrary(id, name, path);
    get().fetchData();
  },

  toggleMovieSelection: (id: number) => {
    set((state) => ({
      selectedMovieIds: state.selectedMovieIds.includes(id)
        ? state.selectedMovieIds.filter(mId => mId !== id)
        : [...state.selectedMovieIds, id]
    }));
  },

  toggleTVShowSelection: (id: number) => {
    set((state) => ({
      selectedTVShowIds: state.selectedTVShowIds.includes(id)
        ? state.selectedTVShowIds.filter(sId => sId !== id)
        : [...state.selectedTVShowIds, id]
    }));
  },

  selectMovies: (ids: number[]) => {
    set({ selectedMovieIds: ids });
  },

  selectTVShows: (ids: number[]) => {
    set({ selectedTVShowIds: ids });
  },

  clearMovieSelection: () => {
    set({ selectedMovieIds: [] });
  },

  clearTVShowSelection: () => {
    set({ selectedTVShowIds: [] });
  },

  bulkScrapeMovies: async () => {
    const { selectedMovieIds } = get();
    if (selectedMovieIds.length === 0) return;
    
    await bulkScrape(selectedMovieIds);
    get().clearMovieSelection();
    
    // Poll for changes
    setTimeout(() => {
      get().fetchData();
    }, 2000);
  },

  bulkScrapeTVShows: async () => {
    const { selectedTVShowIds } = get();
    if (selectedTVShowIds.length === 0) return;
    
    await bulkScrapeTV(selectedTVShowIds);
    get().clearTVShowSelection();
    
    // Poll for changes
    setTimeout(() => {
      get().fetchData();
    }, 2000);
  },

  bulkAnalyzeMovies: async () => {
    const { selectedMovieIds, addNotification } = get();
    if (selectedMovieIds.length === 0) return;
    
    await apiClient.post('/libraries/analyze/bulk', { movie_ids: selectedMovieIds });
    get().clearMovieSelection();
    addNotification(`Queued analysis for ${selectedMovieIds.length} movies.`, 'info');
  },

  bulkAnalyzeTVShows: async () => {
    const { selectedTVShowIds, addNotification } = get();
    if (selectedTVShowIds.length === 0) return;
    
    await apiClient.post('/libraries/analyze/bulk', { show_ids: selectedTVShowIds });
    get().clearTVShowSelection();
    addNotification(`Queued analysis for ${selectedTVShowIds.length} TV shows.`, 'info');
  }
}));
