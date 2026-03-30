import React, { useState } from 'react';
import { Search, Loader, CheckCircle } from 'lucide-react';
import { searchExternalMovies, searchExternalTV, manualMatchMovie, manualMatchTV } from '../api/client';

interface FixMatchModalProps {
  isOpen: boolean;
  onClose: () => void;
  mediaId: number;
  initialTitle: string;
  type: 'movie' | 'tv';
  onMatchComplete: () => void;
}

export const FixMatchModal = ({ isOpen, onClose, mediaId, initialTitle, type, onMatchComplete }: FixMatchModalProps) => {
  const [query, setQuery] = useState(initialTitle);
  const [results, setResults] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isMatching, setIsMatching] = useState<number | null>(null);

  if (!isOpen) return null;

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;
    
    setIsLoading(true);
    try {
      const data = type === 'movie' 
        ? await searchExternalMovies(query)
        : await searchExternalTV(query);
      setResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelect = async (tmdbId: number) => {
    setIsMatching(tmdbId);
    try {
      if (type === 'movie') {
        await manualMatchMovie(mediaId, tmdbId);
      } else {
        await manualMatchTV(mediaId, tmdbId);
      }
      onMatchComplete();
      onClose();
    } catch (err) {
      console.error(err);
    } finally {
      setIsMatching(null);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-gray-800 border border-gray-700 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[80vh]">
        <div className="p-6 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">Fix Match: {initialTitle}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            ✕
          </button>
        </div>

        <div className="p-6">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input 
                type="text"
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search TMDB..."
                className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
            <button 
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-bold transition-all disabled:opacity-50"
            >
              {isLoading ? <Loader className="w-5 h-5 animate-spin" /> : 'Search'}
            </button>
          </form>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {results.length === 0 && !isLoading && (
            <div className="text-center py-10 text-gray-500">
              Enter a title above and click Search to find matches on TMDB.
            </div>
          )}
          
          {results.map((item) => (
            <div 
              key={item.id} 
              className="flex gap-4 p-4 bg-gray-900/50 border border-gray-700 rounded-xl hover:border-blue-500/50 hover:bg-gray-900 transition-all cursor-pointer group"
              onClick={() => handleSelect(item.id)}
            >
              <div className="w-16 h-24 bg-gray-800 rounded flex-shrink-0 overflow-hidden">
                {item.poster_path ? (
                  <img src={`https://image.tmdb.org/t/p/w92${item.poster_path}`} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-600 text-[10px] text-center p-1">No Image</div>
                )}
              </div>
              <div className="flex-1">
                <h3 className="font-bold text-white group-hover:text-blue-400 transition-colors">
                  {item.title || item.name}
                  <span className="ml-2 text-gray-500 font-normal">
                    ({(item.release_date || item.first_air_date || '').substring(0, 4)})
                  </span>
                </h3>
                <p className="text-sm text-gray-400 line-clamp-2 mt-1 leading-relaxed">
                  {item.overview}
                </p>
              </div>
              <div className="flex items-center">
                {isMatching === item.id ? (
                  <Loader className="w-5 h-5 text-blue-500 animate-spin" />
                ) : (
                  <CheckCircle className="w-5 h-5 text-gray-700 group-hover:text-blue-500 transition-colors" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
