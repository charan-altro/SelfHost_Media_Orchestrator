import React, { useState } from 'react';
import { Movie, useStore } from '../store/store';
import { CheckCircle2, AlertCircle, Play, Info, ChevronDown } from 'lucide-react';
import { MediaDetailsModal } from './MediaDetailsModal';
import { Artwork } from './Artwork';
import { playMovie } from '../api/client';

interface Props {
  movie: Movie;
  onScrape: (id: number) => void;
  isSelected?: boolean;
  onToggleSelect?: (id: number) => void;
}

export const MediaCard = ({ movie, onScrape, isSelected = false, onToggleSelect }: Props) => {
  const [showDetails, setShowDetails] = useState(false);
  const isMatched = movie.status === 'matched';
  
  return (
    <>
    <div 
      className={`relative rounded-md overflow-hidden transition-all duration-300 transform hover:scale-105 hover:z-50 cursor-pointer group bg-zinc-900 ${isSelected ? 'ring-2 ring-red-600' : ''}`}
      onClick={() => setShowDetails(true)}
    >
      <div className="aspect-[2/3] w-full relative">
        {movie.poster_path ? (
          <Artwork 
            path={movie.poster_path} 
            type="poster" 
            alt={movie.title}
            className="w-full h-full object-cover transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-zinc-800 text-zinc-600 p-4 text-center">
            <span className="font-bold text-sm">{movie.title}</span>
            <span className="text-xs mt-2">No Image</span>
          </div>
        )}

        {/* Gradient Overlay on Hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
          <div className="flex items-center gap-2 mb-2 translate-y-4 group-hover:translate-y-0 transition-transform duration-300">
            <button 
              onClick={(e) => { e.stopPropagation(); playMovie(movie.id); }}
              className="w-8 h-8 rounded-full bg-white flex items-center justify-center hover:bg-zinc-200 transition-colors"
              title="Play Movie"
            >
              <Play className="w-4 h-4 text-black ml-1" fill="currentColor" />
            </button>
            <button className="w-8 h-8 rounded-full bg-zinc-800/80 border border-zinc-500 flex items-center justify-center hover:border-white transition-colors">
              <ChevronDown className="w-5 h-5 text-white" />
            </button>
          </div>
          
          <div className="translate-y-4 group-hover:translate-y-0 transition-transform duration-300 delay-75">
            <h3 className="font-bold text-white text-sm line-clamp-1 mb-1">{movie.title}</h3>
            <div className="flex items-center gap-2 text-[10px] font-semibold text-zinc-300">
              <span className="text-green-400">{Math.round((movie.tmdb_rating || 0) * 10)}% Match</span>
              <span>{movie.year}</span>
              {movie.files?.[0]?.resolution && (
                <span className="border border-zinc-500 px-1 rounded text-[8px] uppercase">
                  {movie.files[0].resolution}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Checkbox Overlay (Visible only when hovering or selected) */}
        {onToggleSelect && (
          <div 
            className={`absolute top-2 left-2 z-10 p-1 rounded cursor-pointer transition-opacity ${isSelected ? 'opacity-100 bg-red-600 shadow' : 'opacity-0 group-hover:opacity-100 bg-black/50 hover:bg-black/80'}`}
            onClick={(e) => {
              e.stopPropagation();
              onToggleSelect(movie.id);
            }}
          >
            <div className={`w-4 h-4 rounded border flex items-center justify-center ${isSelected ? 'border-transparent text-white' : 'border-zinc-400 text-transparent'}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="w-3 h-3">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
          </div>
        )}
        
        {/* Status Badge */}
        {!isMatched && (
          <div className="absolute top-2 right-2 bg-red-600 text-white p-1 rounded-full shadow-lg" title="Unmatched">
            <AlertCircle className="w-3 h-3" />
          </div>
        )}
      </div>
    </div>

    <MediaDetailsModal 
      isOpen={showDetails}
      onClose={() => setShowDetails(false)}
      media={movie}
      type="movie"
    />
    </>
  );
};
