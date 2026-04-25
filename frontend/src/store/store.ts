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
  updateLibrary,
  bulkScrapeTV,
  getTasks
} from '../api/client';
import { EventsOn, EventsOff } from '../../wailsjs/runtime/runtime';

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

export interface CastMember {
  name: string;
  role: string;
  thumb: string;
}

export interface Movie {
  id: number;
  title: string;
  year: number;
  status: string;
  tmdb_id?: string;
  imdb_id?: string;
  poster_path: string;
  fanart_path: string;
  plot: string;
  tagline?: string;
  content_rating?: string;
  tmdb_rating?: number;
  imdb_rating?: number;
  runtime?: number;
  genres?: string[];
  cast?: string[];
  cast_details?: CastMember[];
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
  tmdb_id?: string;
  imdb_id?: string;
  tvdb_id?: string;
  poster_path: string;
  fanart_path: string;
  plot: string;
  tagline?: string;
  content_rating?: string;
  tmdb_rating?: number;
  imdb_rating?: number;
  runtime?: number;
  genres?: string[];
  cast?: string[];
  cast_details?: CastMember[];
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
      const tasks = await getTasks();
      set({ tasks: tasks as any, isLoadingTasks: false });
    } catch (error) {
      console.error(error);
      set({ isLoadingTasks: false });
    }
  },

  clearTasks: async () => {
    try {
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
      set({ movies: movies as any, tvShows: tvShows as any, libraries: libraries as any, isLoading: false });
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
    get().setScanProgress(id, {
        status: 'scanning',
        file: 'Connecting to native scanner...',
        current: 0,
        total: 100
    });

    await scanLibrary(id);
    get().fetchTasks();
    
    EventsOn('scan-progress', (data: any) => {
        if (data.library_id === id) {
            get().setScanProgress(id, {
                status: 'scanning',
                file: 'Processing...',
                current: data.progress,
                total: 100
            });
        }
    });

    EventsOn('tasks-updated', () => {
        get().fetchTasks();
    });

    EventsOn('media-updated', () => {
        get().fetchData();
    });

    EventsOn('scan-complete', (data: any) => {
        if (data.library_id === id) {
            get().setScanProgress(id, {
                status: 'done',
                file: 'Complete',
                current: 100,
                total: 100
            });
            setTimeout(() => {
                get().setScanProgress(id, null);
                get().fetchData();
            }, 5000);
            EventsOff('scan-progress');
            EventsOff('scan-complete');
        }
    });
  },

  scrapeMovie: async (id: number) => {
    await triggerScrape(id);
    get().fetchTasks();
  },

  scrapeTVShow: async (id: number) => {
    await triggerTVScrape(id);
    get().fetchTasks();
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
    get().fetchTasks();
  },

  bulkScrapeTVShows: async () => {
    const { selectedTVShowIds } = get();
    if (selectedTVShowIds.length === 0) return;
    
    await bulkScrapeTV(selectedTVShowIds);
    get().clearTVShowSelection();
    get().fetchTasks();
  },

  bulkAnalyzeMovies: async () => {
    const { selectedMovieIds, addNotification } = get();
    if (selectedMovieIds.length === 0) return;
    
    get().clearMovieSelection();
    addNotification(`Queued analysis for ${selectedMovieIds.length} movies.`, 'info');
  },

  bulkAnalyzeTVShows: async () => {
    const { selectedTVShowIds, addNotification } = get();
    if (selectedTVShowIds.length === 0) return;
    
    get().clearTVShowSelection();
    addNotification(`Queued analysis for ${selectedTVShowIds.length} TV shows.`, 'info');
  }
}));
