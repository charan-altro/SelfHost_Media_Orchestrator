import React, { useEffect, useState, useMemo } from 'react';
import { useStore } from '../store/store';
import { MediaCard } from '../components/MediaCard';
import { BulkOpsToolbar } from '../components/BulkOpsToolbar';
import { RefreshCw, FolderSearch, Search, Filter, Play, Info } from 'lucide-react';
import { MediaDetailsModal } from '../components/MediaDetailsModal';

export const LibraryPage = () => {
  const { movies, libraries, isLoading, fetchData, scanLibrary, scrapeMovie, selectedMovieIds, toggleMovieSelection } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'matched' | 'unmatched'>('all');
  const [featuredMovie, setFeaturedMovie] = useState<any>(null);
  const [showFeaturedDetails, setShowFeaturedDetails] = useState(false);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    // Pick a random matched movie as the featured hero
    const matched = movies.filter(m => m.status === 'matched' && m.fanart_path);
    if (matched.length > 0 && !featuredMovie) {
      const random = matched[Math.floor(Math.random() * matched.length)];
      setFeaturedMovie(random);
    }
  }, [movies, featuredMovie]);

  const filteredMovies = useMemo(() => {
    return movies.filter(movie => {
      const matchesSearch = movie.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || 
                           (statusFilter === 'matched' && movie.status === 'matched') ||
                           (statusFilter === 'unmatched' && movie.status === 'unmatched');
      return matchesSearch && matchesStatus;
    });
  }, [movies, searchQuery, statusFilter]);

  const movieLibraries = libraries.filter(l => l.type === 'movie');
  const tmdbImageBase = 'https://image.tmdb.org/t/p/original';

  return (
    <div className="min-h-screen bg-[#141414]">
      {/* Hero Section */}
      {featuredMovie && !searchQuery && statusFilter === 'all' ? (
        <div className="relative h-[80vh] w-full mb-12">
          <div className="absolute inset-0">
            <img 
              src={`${tmdbImageBase}${featuredMovie.fanart_path}`} 
              alt={featuredMovie.title} 
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/60 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#141414] via-transparent to-transparent" />
          </div>
          
          <div className="absolute bottom-[15%] left-0 w-full px-4 md:px-12 z-10 flex flex-col items-start max-w-3xl">
            <h1 className="text-5xl md:text-7xl font-black text-white mb-4 drop-shadow-xl tracking-tighter">
              {featuredMovie.title}
            </h1>
            <p className="text-lg md:text-xl text-zinc-300 mb-8 line-clamp-3 drop-shadow-md font-medium max-w-2xl">
              {featuredMovie.plot}
            </p>
            <div className="flex gap-4">
              <button className="flex items-center gap-2 px-8 py-3 bg-white text-black rounded font-bold hover:bg-white/80 transition-colors text-lg">
                <Play className="w-6 h-6 fill-current" /> Play
              </button>
              <button 
                onClick={() => setShowFeaturedDetails(true)}
                className="flex items-center gap-2 px-8 py-3 bg-zinc-500/70 text-white rounded font-bold hover:bg-zinc-500/90 transition-colors text-lg backdrop-blur-sm"
              >
                <Info className="w-6 h-6" /> More Info
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="pt-32" /> // Spacing when no hero
      )}

      {/* Main Content */}
      <div className="px-4 md:px-12 pb-24 -mt-8 relative z-20">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white mb-1">
              {searchQuery ? 'Search Results' : 'Your Movies'}
            </h2>
            <p className="text-zinc-500 text-sm">
              {filteredMovies.length} items found across {movieLibraries.length} libraries.
            </p>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input 
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="bg-transparent pl-10 pr-4 py-2 text-white text-sm focus:outline-none w-48 focus:w-64 transition-all"
                />
              </div>
              <select 
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as any)}
                className="bg-zinc-800 text-zinc-300 text-sm px-3 py-2 border-l border-zinc-700 focus:outline-none cursor-pointer"
              >
                <option value="all">All</option>
                <option value="matched">Matched</option>
                <option value="unmatched">Unmatched</option>
              </select>
            </div>

            <button 
              onClick={() => fetchData()}
              disabled={isLoading}
              className="flex items-center justify-center p-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded-lg border border-zinc-800 transition-colors disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            
            {movieLibraries.map(lib => (
              <button 
                key={lib.id}
                onClick={() => scanLibrary(lib.id)}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold transition-colors text-sm"
              >
                <FolderSearch className="w-4 h-4" /> Scan {lib.name}
              </button>
            ))}
          </div>
        </div>

        {searchQuery && (
          <div className="mb-6 flex items-center gap-2 text-sm text-zinc-400">
            <span>Results for "<span className="text-white font-medium">{searchQuery}</span>"</span>
            <button 
              onClick={() => setSearchQuery('')}
              className="ml-2 text-xs text-red-500 hover:text-red-400 font-bold uppercase transition-colors"
            >
              Clear
            </button>
          </div>
        )}

        {filteredMovies.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 bg-zinc-900/30 rounded-lg border border-zinc-800/50">
            <FolderSearch className="w-16 h-16 text-zinc-700 mb-4" />
            <h2 className="text-xl font-medium text-zinc-400 mb-2">No movies found</h2>
            <p className="text-zinc-600 text-center max-w-md text-sm">
              {searchQuery || statusFilter !== 'all' 
                ? "Adjust your filters to see more results." 
                : "Click the Scan button above to analyze your mapped library paths, or add a new path in Settings."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-x-4 gap-y-10">
            {filteredMovies.map(movie => (
              <MediaCard 
                key={movie.id} 
                movie={movie} 
                onScrape={scrapeMovie} 
                isSelected={selectedMovieIds.includes(movie.id)}
                onToggleSelect={toggleMovieSelection}
              />
            ))}
          </div>
        )}

        <BulkOpsToolbar type="movie" />
      </div>

      {featuredMovie && (
        <MediaDetailsModal 
          isOpen={showFeaturedDetails}
          onClose={() => setShowFeaturedDetails(false)}
          media={featuredMovie}
          type="movie"
        />
      )}
    </div>
  );
};
