import React from 'react';
import { X, RefreshCw, CheckSquare, Search } from 'lucide-react';
import { useStore } from '../store/store';

interface Props {
  type: 'movie' | 'tv';
}

export const BulkOpsToolbar = ({ type }: Props) => {
  const { 
    selectedMovieIds, clearMovieSelection, bulkScrapeMovies, movies, selectMovies, bulkAnalyzeMovies,
    selectedTVShowIds, clearTVShowSelection, bulkScrapeTVShows, tvShows, selectTVShows, bulkAnalyzeTVShows
  } = useStore();

  const isMovie = type === 'movie';
  const selection = isMovie ? selectedMovieIds : selectedTVShowIds;
  const items = isMovie ? movies : tvShows;
  const clearSelection = isMovie ? clearMovieSelection : clearTVShowSelection;
  const bulkScrape = isMovie ? bulkScrapeMovies : bulkScrapeTVShows;
  const bulkAnalyze = isMovie ? bulkAnalyzeMovies : bulkAnalyzeTVShows;
  const selectAll = isMovie ? selectMovies : selectTVShows;

  if (selection.length === 0) return null;

  const allSelected = selection.length === items.length;

  return (
    <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-40">
      <div className="bg-slate-800 rounded-2xl shadow-2xl border border-blue-500/50 p-3 flex items-center gap-4 backdrop-blur-md bg-opacity-95">
        <div className="flex items-center gap-3 px-3">
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
            {selection.length}
          </div>
          <span className="text-white font-medium">{isMovie ? 'Movies' : 'TV Shows'} Selected</span>
        </div>

        <div className="h-8 w-px bg-slate-700"></div>

        <button
          onClick={() => allSelected ? clearSelection() : selectAll(items.map(i => i.id))}
          className="flex items-center gap-2 px-3 py-2 hover:bg-slate-700 rounded-lg text-slate-300 transition"
        >
          <CheckSquare className="w-4 h-4" />
          {allSelected ? 'Deselect All' : 'Select All'}
        </button>

        <button
          onClick={() => bulkScrape()}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow font-medium transition"
        >
          <RefreshCw className="w-4 h-4" /> Bulk Scrape
        </button>

        <button
          onClick={() => bulkAnalyze()}
          className="flex items-center gap-2 px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg shadow font-medium transition border border-white/5"
        >
          <Search className="w-4 h-4" /> Analyze Technical Specs
        </button>

        <div className="h-8 w-px bg-slate-700"></div>

        <button
          onClick={clearSelection}
          className="p-2 hover:bg-red-500/20 hover:text-red-400 text-slate-400 rounded-lg transition"
          title="Clear Selection"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

