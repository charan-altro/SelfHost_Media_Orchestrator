import React, { useEffect, useState, useRef } from 'react';
import { Movie, TVShow, useStore, Episode } from '../store/store';
import { X, Star, Clock, Calendar, Film, User, RefreshCw, Search, ArrowLeft, ChevronDown, Play, Share2, Info, ChevronRight, ChevronLeft } from 'lucide-react';
import { triggerScrape, getTVShowDetails, playMovie, playEpisode } from '../api/client';
import { Artwork } from './Artwork';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  media: Movie | TVShow;
  type: 'movie' | 'tv';
}

export const MediaDetailsModal = ({ isOpen, onClose, media, type }: Props) => {
  const { fetchData } = useStore();
  const castScrollRef = useRef<HTMLDivElement>(null);
  
  // TV Specific State
  const [fullShow, setFullShow] = useState<TVShow | null>(null);
  const [selectedSeason, setSelectedSeason] = useState<number>(1);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  
  const isMovie = type === 'movie';
  const isMatched = media.status === 'matched';

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      if (!isMovie && media.id) {
        loadShowDetails();
      }
    } else {
      document.body.style.overflow = 'unset';
    }

    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);

    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleEsc);
    };
  }, [isOpen, media, isMovie, onClose]);

  const loadShowDetails = async () => {
    setIsLoadingDetails(true);
    try {
      const data = await getTVShowDetails(media.id);
      setFullShow(data);
      if (data.seasons && data.seasons.length > 0) {
        setSelectedSeason(data.seasons[0].season_number);
      }
    } catch (err) {
      console.error("Failed to load show details", err);
    } finally {
      setIsLoadingDetails(false);
    }
  };

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setIsScrolled(e.currentTarget.scrollTop > 50);
  };

  const scrollCast = (direction: 'left' | 'right') => {
    if (castScrollRef.current) {
      const scrollAmount = 500;
      castScrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  if (!isOpen) return null;

  const currentSeason = fullShow?.seasons?.find(s => s.season_number === selectedSeason);
  const episodes = currentSeason?.episodes || [];

  return (
    <div 
      className="fixed inset-0 z-[200] bg-zinc-950 overflow-y-auto animate-in fade-in duration-500"
      onScroll={handleScroll}
      onClick={onClose}
    >
      {/* Background Ambient Blur */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-40">
        {media.fanart_path && (
            <Artwork 
                path={media.fanart_path} 
                type="fanart" 
                className="w-full h-full object-cover blur-[100px] scale-110" 
            />
        )}
      </div>

      <div 
        className="relative min-h-screen w-full flex flex-col z-10"
        onClick={e => e.stopPropagation()}
      >

        {/* Improved Sticky Header */}
        <header className={`fixed top-0 left-0 w-full z-[250] px-8 pt-20 pb-10 flex justify-between items-center transition-all duration-300 ${isScrolled ? 'bg-zinc-950 shadow-2xl pt-10 pb-6' : 'bg-gradient-to-b from-black/90 via-black/20 to-transparent'}`}>
          <button
            onClick={onClose}
            className="group flex items-center gap-4 px-10 py-5 bg-white text-black hover:bg-red-600 hover:text-white rounded-full transition-all border border-white/10 font-black text-lg uppercase tracking-tight shadow-[0_20px_50px_rgba(0,0,0,0.5)] active:scale-95"
          >
            <ArrowLeft className="w-7 h-7 transition-transform group-hover:-translate-x-3" /> Back
          </button>

          <div className="flex items-center gap-3">
             <button
                className="p-3 bg-white/10 backdrop-blur-md hover:bg-white/20 text-white rounded-full transition-all border border-white/10 shadow-xl"
                title="Share"
              >
                <Share2 className="w-5 h-5" />
              </button>
              <button
                onClick={onClose}
                className="p-3 bg-white/10 backdrop-blur-md hover:bg-red-600 text-white rounded-full transition-all border border-white/10 shadow-xl"
                title="Close"
              >
                <X className="w-5 h-5" />
              </button>
          </div>
        </header>

        {/* Hero Section */}
        <section className="relative w-full h-[75vh] md:h-[90vh] flex-shrink-0 overflow-hidden">
          {media.fanart_path ? (
            <Artwork
              path={media.fanart_path}
              type="fanart"
              className="w-full h-full object-cover scale-100 animate-in zoom-in-110 duration-[3000ms]"
            />
          ) : (
            <div className="w-full h-full bg-zinc-900 flex items-center justify-center">
              <Film className="w-32 h-32 text-zinc-800" />
            </div>
          )}
          
          {/* Gradients */}
          <div className="absolute inset-0 bg-gradient-to-t from-zinc-950 via-zinc-950/40 to-transparent" />
          <div className="absolute inset-0 bg-gradient-to-r from-zinc-950/60 via-transparent to-transparent hidden md:block" />

          <div className="absolute bottom-0 left-0 w-full p-8 md:p-24">
            <div className="max-w-screen-2xl mx-auto flex flex-col md:flex-row gap-16 items-end">
              <div className="hidden md:block w-72 aspect-[2/3] rounded-2xl overflow-hidden shadow-[0_0_80px_rgba(0,0,0,0.9)] border border-white/10 flex-shrink-0 translate-y-24 transition-all hover:scale-[1.05] duration-500">
                <Artwork path={media.poster_path} type="poster" className="w-full h-full object-cover" />
              </div>
              
              <div className="flex-1 space-y-8 pb-10">
                <div className="space-y-4">
                    <h1 className="text-6xl md:text-9xl font-black tracking-tighter text-white uppercase italic leading-[0.85] drop-shadow-[0_10px_10px_rgba(0,0,0,0.8)]">
                    {media.title}
                    </h1>
                    {media.tagline && (
                        <p className="text-2xl md:text-3xl font-bold text-zinc-400 italic tracking-tight opacity-90">{media.tagline}</p>
                    )}
                </div>
                
                <div className="flex flex-wrap items-center gap-6 text-lg md:text-xl font-black text-white">
                  <span className="flex items-center gap-2 text-green-400 drop-shadow-md">
                    <Star className="w-6 h-6 fill-current" />
                    <span>{Math.round((media.tmdb_rating || 0) * 10)}% Match</span>
                  </span>
                  <span className="text-zinc-300 drop-shadow-md">{media.year}</span>
                  {media.runtime && (
                    <span className="text-zinc-300 drop-shadow-md">{media.runtime}m</span>
                  )}
                  {media.content_rating && (
                    <span className="px-3 py-1 bg-white/10 backdrop-blur-md border border-white/20 text-white text-sm rounded-md font-black">
                        {media.content_rating}
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap gap-4 pt-4">
                  {isMovie ? (
                    <button 
                      onClick={() => playMovie(media.id)}
                      className="flex items-center justify-center gap-4 px-14 py-6 bg-white text-black rounded-xl font-black text-2xl hover:bg-red-600 hover:text-white transition-all shadow-2xl group active:scale-95"
                    >
                      <Play className="w-8 h-8 fill-current transition-transform group-hover:scale-110" /> Play Now
                    </button>
                  ) : (
                    <button 
                      onClick={() => {
                        const firstEp = episodes[0];
                        if (firstEp) playEpisode(firstEp.id);
                      }}
                      className="flex items-center justify-center gap-4 px-14 py-6 bg-white text-black rounded-xl font-black text-2xl hover:bg-red-600 hover:text-white transition-all shadow-2xl group active:scale-95"
                    >
                      <Play className="w-8 h-8 fill-current transition-transform group-hover:scale-110" /> Start S{selectedSeason} E01
                    </button>
                  )}
                  <button 
                    className="flex items-center justify-center gap-4 px-10 py-6 bg-white/10 backdrop-blur-md text-white rounded-xl font-black text-xl hover:bg-white/20 transition-all border border-white/10 active:scale-95 shadow-xl"
                  >
                    <Info className="w-7 h-7" /> More Info
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Content Section */}
        <div className="relative flex-1 w-full max-w-screen-2xl mx-auto px-8 md:px-24 py-32 bg-zinc-950 rounded-t-[4rem] -translate-y-12 shadow-[0_-80px_100px_-20px_rgba(0,0,0,1)] border-t border-white/5">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-24">
            <div className="lg:col-span-3 space-y-32">
              
              {/* Overview */}
              <section className="space-y-10">
                <div className="flex items-center gap-4">
                    <div className="w-2.5 h-10 bg-red-600 rounded-full" />
                    <h3 className="text-3xl font-black text-white uppercase tracking-tighter italic">Storyline</h3>
                </div>
                <p className="text-2xl md:text-3xl text-zinc-400 leading-[1.5] font-medium max-w-5xl tracking-tight">
                  {media.plot || "No overview available for this title."}
                </p>
              </section>

              {/* Cast Section */}
              {media.cast_details && media.cast_details.length > 0 && (
                <section className="space-y-12 relative group/cast">
                   <div className="flex justify-between items-center pr-4">
                        <div className="flex items-center gap-4">
                            <div className="w-2.5 h-10 bg-red-600 rounded-full" />
                            <h3 className="text-3xl font-black text-white uppercase tracking-tighter italic">Cast</h3>
                        </div>
                        <div className="flex gap-2">
                            <button 
                                onClick={() => scrollCast('left')}
                                className="p-3 rounded-full bg-zinc-900 border border-white/5 text-white hover:bg-white hover:text-black transition-all shadow-xl"
                            >
                                <ChevronLeft className="w-6 h-6" />
                            </button>
                            <button 
                                onClick={() => scrollCast('right')}
                                className="p-3 rounded-full bg-zinc-900 border border-white/5 text-white hover:bg-white hover:text-black transition-all shadow-xl"
                            >
                                <ChevronRight className="w-6 h-6" />
                            </button>
                        </div>
                    </div>
                  
                  <div 
                    ref={castScrollRef}
                    className="flex gap-8 overflow-x-auto pb-12 scroll-smooth px-2 no-scrollbar"
                    style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                  >
                    {media.cast_details.slice(0, 30).map((person: any) => (
                      <div key={person.name} className="flex-shrink-0 w-44 md:w-56 group cursor-default">
                        <div className="aspect-[3/4] rounded-2xl overflow-hidden mb-6 border border-white/5 transition-all duration-500 shadow-[0_10px_30px_rgba(0,0,0,0.5)] group-hover:border-red-600 group-hover:-translate-y-3">
                          {person.thumb ? (
                            <Artwork path={person.thumb} type="profile" alt={person.name} className="w-full h-full object-cover grayscale-[30%] group-hover:grayscale-0 group-hover:scale-110 transition-all duration-700" />
                          ) : (
                            <div className="w-full h-full bg-zinc-900 flex items-center justify-center"><User className="w-20 h-20 text-zinc-800" /></div>
                          )}
                        </div>
                        <p className="text-xl font-black text-white italic tracking-tight truncate">{person.name}</p>
                        <p className="text-sm font-bold text-zinc-500 uppercase tracking-widest mt-2 truncate">{person.role}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* TV Episodes */}
              {!isMovie && (
                <section className="space-y-16">
                  <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
                    <div className="flex items-center gap-4">
                        <div className="w-2.5 h-10 bg-red-600 rounded-full" />
                        <h3 className="text-3xl font-black text-white uppercase tracking-tighter italic">Episodes</h3>
                    </div>
                    {fullShow?.seasons && (
                      <div className="relative min-w-[280px] group">
                        <select 
                          value={selectedSeason}
                          onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
                          className="w-full appearance-none bg-zinc-900/80 hover:bg-zinc-800 text-white px-8 py-5 rounded-2xl font-black border border-white/10 focus:outline-none focus:ring-4 ring-red-600/20 transition-all cursor-pointer uppercase text-sm tracking-[0.2em] shadow-xl"
                        >
                          {fullShow.seasons.map(s => (
                            <option key={s.id} value={s.season_number}>Season {s.season_number}</option>
                          ))}
                        </select>
                        <ChevronDown className="absolute right-6 top-1/2 -translate-y-1/2 w-7 h-7 text-zinc-500 group-hover:text-white transition-colors pointer-events-none" />
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-10">
                    {episodes.map((ep) => (
                      <div 
                        key={ep.id} 
                        onClick={() => playEpisode(ep.id)}
                        className="group flex flex-col md:flex-row gap-12 p-8 rounded-[2.5rem] bg-white/[0.03] hover:bg-white/[0.07] transition-all duration-500 border border-white/5 cursor-pointer shadow-2xl"
                      >
                        <div className="relative flex-shrink-0 w-full md:w-[26rem] aspect-video rounded-3xl overflow-hidden bg-zinc-900 shadow-2xl">
                          {ep.thumbnail_path ? (
                            <Artwork path={ep.thumbnail_path} type="thumb" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-zinc-800">
                              <Film className="w-20 h-20" />
                            </div>
                          )}
                          <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 group-hover:opacity-100 transition-all duration-500 backdrop-blur-sm">
                            <div className="w-24 h-24 rounded-full bg-white flex items-center justify-center shadow-2xl transform scale-50 group-hover:scale-100 transition-all duration-500">
                                <Play className="w-12 h-12 text-black fill-current ml-1.5" />
                            </div>
                          </div>
                          <div className="absolute top-6 left-6 text-5xl font-black text-white opacity-20 group-hover:opacity-100 transition-opacity italic">
                            {ep.episode_number}
                          </div>
                        </div>
                        <div className="flex-1 space-y-6 py-2">
                          <div className="flex justify-between items-start">
                            <h4 className="font-black text-white text-4xl uppercase italic tracking-tighter group-hover:text-red-500 transition-colors">{ep.title}</h4>
                            <span className="text-zinc-500 font-black text-base tracking-widest uppercase mt-2">{ep.air_date}</span>
                          </div>
                          <p className="text-xl md:text-2xl text-zinc-400 font-medium leading-relaxed line-clamp-3 group-hover:text-zinc-200 transition-colors">{ep.plot}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>

            {/* Sidebar */}
            <aside className="space-y-16">
              <div className="space-y-8">
                <h4 className="text-sm font-black uppercase tracking-[0.4em] text-zinc-500 border-b border-white/10 pb-5 italic">Actions</h4>
                <div className="grid grid-cols-1 gap-4">
                  <button 
                    onClick={() => triggerScrape(media.id)}
                    className="flex items-center justify-center gap-4 w-full py-6 bg-zinc-900/50 text-white rounded-2xl font-black border border-white/10 hover:bg-white hover:text-black transition-all uppercase tracking-widest text-xs shadow-xl"
                  >
                    <RefreshCw className="w-5 h-5" /> Refresh Meta
                  </button>
                  <button 
                    className="flex items-center justify-center gap-4 w-full py-6 bg-zinc-900/50 text-white rounded-2xl font-black border border-white/10 hover:bg-white hover:text-black transition-all uppercase tracking-widest text-xs shadow-xl"
                  >
                    <Search className="w-5 h-5" /> Match Media
                  </button>
                </div>
              </div>

              <div className="space-y-8">
                <h4 className="text-sm font-black uppercase tracking-[0.4em] text-zinc-500 border-b border-white/10 pb-5 italic">Metadata</h4>
                <div className="space-y-2 bg-zinc-900/40 rounded-[2.5rem] p-10 border border-white/5 shadow-2xl backdrop-blur-md">
                  <div className="flex flex-col gap-3 pb-8 border-b border-white/5">
                    <span className="text-zinc-500 text-xs font-black uppercase tracking-[0.25em]">Director</span>
                    <span className="text-white text-2xl font-black italic tracking-tighter leading-tight">{media.director || 'N/A'}</span>
                  </div>
                  
                  <div className="py-8 border-b border-white/5 space-y-6">
                        <span className="text-zinc-500 text-xs font-black uppercase tracking-[0.25em]">Genres</span>
                        <div className="flex flex-wrap gap-2.5">
                            {media.genres?.map((g: string) => (
                                <span key={g} className="px-5 py-2 bg-white/5 hover:bg-white/10 text-white text-xs font-black uppercase rounded-xl border border-white/10 transition-colors cursor-default tracking-widest">{g}</span>
                            ))}
                        </div>
                  </div>

                  <div className="pt-8 flex flex-col gap-3">
                    <span className="text-zinc-500 text-xs font-black uppercase tracking-[0.25em]">Status</span>
                    <span className={`text-base font-black uppercase tracking-[0.25em] italic ${media.status === 'matched' ? 'text-green-500' : 'text-red-500'}`}>
                      {media.status}
                    </span>
                  </div>
                </div>
              </div>
            </aside>
          </div>
        </div>
      </div>
    </div>
  );
};
