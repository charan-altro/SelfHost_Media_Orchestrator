import React, { useEffect, useState, useMemo } from 'react';
import { useStore } from '../store/store';
import { TVShowCard } from '../components/TVShowCard';
import { BulkOpsToolbar } from '../components/BulkOpsToolbar';
import { RefreshCw, FolderSearch, Search, Filter, Play, Info } from 'lucide-react';
import { MediaDetailsModal } from '../components/MediaDetailsModal';

export const TVShowsPage = () => {
  const { tvShows, libraries, isLoading, fetchData, scanLibrary, scrapeTVShow, selectedTVShowIds, toggleTVShowSelection } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'matched' | 'unmatched'>('all');
  const [featuredShow, setFeaturedShow] = useState<any>(null);
  const [showFeaturedDetails, setShowFeaturedDetails] = useState(false);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    // Pick a random matched TV show as the featured hero
    const matched = tvShows.filter(s => s.status === 'matched' && s.fanart_path);
    if (matched.length > 0 && !featuredShow) {
      const random = matched[Math.floor(Math.random() * matched.length)];
      setFeaturedShow(random);
    }
  }, [tvShows, featuredShow]);

  const filteredShows = useMemo(() => {
    return tvShows.filter(show => {
      const matchesSearch = show.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus = statusFilter === 'all' || 
                           (statusFilter === 'matched' && show.status === 'matched') ||
                           (statusFilter === 'unmatched' && show.status === 'unmatched');
      return matchesSearch && matchesStatus;
    });
  }, [tvShows, searchQuery, statusFilter]);

  const tvLibraries = libraries.filter(l => l.type === 'tv');
  const tmdbImageBase = 'https://image.tmdb.org/t/p/original';

  return (
    <div className="min-h-screen bg-[#141414]">
      {/* Hero Section */}
      {featuredShow && !searchQuery && statusFilter === 'all' ? (
        <div className="relative h-[80vh] w-full mb-12">
          <div className="absolute inset-0">
            <img 
              src={`${tmdbImageBase}${featuredShow.fanart_path}`} 
              alt={featuredShow.title} 
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-[#141414] via-[#141414]/60 to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-t from-[#141414] via-transparent to-transparent" />
          </div>
          
          <div className="absolute bottom-[15%] left-0 w-full px-4 md:px-12 z-10 flex flex-col items-start max-w-3xl">
            <h1 className="text-5xl md:text-7xl font-black text-white mb-4 drop-shadow-xl tracking-tighter">
              {featuredShow.title}
            </h1>
            <p className="text-lg md:text-xl text-zinc-300 mb-8 line-clamp-3 drop-shadow-md font-medium max-w-2xl">
              {featuredShow.plot}
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
              {searchQuery ? 'Search Results' : 'Your TV Shows'}
            </h2>
            <p className="text-zinc-500 text-sm">
              {filteredShows.length} series found across {tvLibraries.length} libraries.
            </p>
          </div>
          
          <div className="flex flex-wrap gap-3">
            <div className="flex bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input 
                  type="text"
                  placeholder="Search TV shows..."
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
            
            {tvLibraries.map(lib => (
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

        {filteredShows.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 bg-zinc-900/30 rounded-lg border border-zinc-800/50">
            <FolderSearch className="w-16 h-16 text-zinc-700 mb-4" />
            <h2 className="text-xl font-medium text-zinc-400 mb-2">No TV shows found</h2>
            <p className="text-zinc-600 text-center max-w-md text-sm">
              {searchQuery || statusFilter !== 'all' 
                ? "Adjust your filters to see more results." 
                : "Add a TV Show library in Settings and click Scan to build your collection."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-x-4 gap-y-10">
            {filteredShows.map(show => (
              <TVShowCard 
                key={show.id} 
                show={show} 
                onScrape={scrapeTVShow} 
                isSelected={selectedTVShowIds.includes(show.id)}
                onToggleSelect={toggleTVShowSelection}
              />
            ))}
          </div>
        )}

        <BulkOpsToolbar type="tv" />
      </div>

      {featuredShow && (
        <MediaDetailsModal 
          isOpen={showFeaturedDetails}
          onClose={() => setShowFeaturedDetails(false)}
          media={featuredShow}
          type="tv"
        />
      )}
    </div>
  );
};
