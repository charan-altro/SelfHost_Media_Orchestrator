import React, { useEffect, useState } from 'react';
import { Movie, TVShow, useStore, Episode } from '../store/store';
import { X, Star, Clock, Calendar, Film, User, RefreshCw, Search, FolderInput, Play, ChevronDown, Edit2, Save, XCircle, Languages, Youtube } from 'lucide-react';
import { renameMovie, triggerTVScrape, triggerScrape, getTVShowDetails, updateMovie, updateTVShow, getTrailerUrl, triggerTrailerFetch, downloadSubtitles } from '../api/client';
import { FixMatchModal } from './FixMatchModal';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  media: Movie | TVShow;
  type: 'movie' | 'tv';
}

export const MediaDetailsModal = ({ isOpen, onClose, media, type }: Props) => {
  const { fetchData, addNotification } = useStore();
  const [showFixMatch, setShowFixMatch] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameResult, setRenameResult] = useState<string | null>(null);
  
  // Edit Mode State
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState<any>({});
  const [isSaving, setIsSaving] = useState(false);
  
  // TV Specific State
  const [fullShow, setFullShow] = useState<TVShow | null>(null);
  const [selectedSeason, setSelectedSeason] = useState<number>(1);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);

  // Extras State
  const [trailerUrl, setTrailerUrl] = useState<string | null>(null);
  const [isFetchingTrailer, setIsFetchingTrailer] = useState(false);
  const [subtitleStatus, setSubtitleStatus] = useState<string | null>(null);
  
  const isMovie = type === 'movie';
  const movie = isMovie ? (media as Movie) : null;
  const show = !isMovie ? (media as TVShow) : null;
  
  const isMatched = media.status === 'matched';
  
  const resolveArtwork = (path: string | null | undefined, type: 'poster' | 'fanart' | 'profile' | 'thumb' = 'poster') => {
    if (!path) return null;
    if (path.startsWith('local://')) {
      return `/api/artwork/local?path=${encodeURIComponent(path.replace('local://', ''))}`;
    }
    const baseMap = {
      poster: 'https://image.tmdb.org/t/p/w500',
      fanart: 'https://image.tmdb.org/t/p/original',
      profile: 'https://image.tmdb.org/t/p/w185',
      thumb: 'https://image.tmdb.org/t/p/w300'
    };
    return `${baseMap[type]}${path}`;
  };

  useEffect(() => {
    if (isOpen) {
      if (!isMovie) loadShowDetails();
      loadTrailer();
    }
  }, [isOpen, media.id]);

  const loadTrailer = async () => {
    try {
      const url = await getTrailerUrl(type, media.id);
      setTrailerUrl(url);
    } catch (err) {
      console.error("Failed to load trailer", err);
    }
  };

  const handleFetchTrailer = async () => {
    setIsFetchingTrailer(true);
    try {
      await triggerTrailerFetch(type, media.id);
      addNotification("Trailer search queued! Check back in a few seconds.", "info");
    } finally {
      setIsFetchingTrailer(false);
    }
  };

  const handleDownloadSubtitles = async (targetType: 'movie' | 'episode', id: number) => {
    setSubtitleStatus("Searching...");
    try {
      await downloadSubtitles(targetType, id);
      setSubtitleStatus("Queued!");
      addNotification("Subtitle search queued!", "info");
      setTimeout(() => setSubtitleStatus(null), 3000);
    } catch (err) {
      setSubtitleStatus("Failed");
      addNotification("Failed to search for subtitles.", "error");
      setTimeout(() => setSubtitleStatus(null), 3000);
    }
  };

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

  if (!isOpen) return null;

  const currentSeason = fullShow?.seasons?.find(s => s.season_number === selectedSeason);
  const episodes = currentSeason?.episodes || [];

  const startEditing = () => {
    setEditForm({
      title: media.title,
      year: media.year,
      plot: media.plot,
      director: media.director,
      runtime: media.runtime,
      tmdb_rating: media.tmdb_rating
    });
    setIsEditing(true);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      if (isMovie) {
        await updateMovie(media.id, editForm);
      } else {
        await updateTVShow(media.id, editForm);
      }
      setIsEditing(false);
      fetchData();
      addNotification("Changes saved successfully.", "success");
      if (!isMovie) loadShowDetails();
    } catch (err) {
      console.error("Save failed", err);
      addNotification("Failed to save changes.", "error");
    } finally {
      setIsSaving(false);
    }
  };

  const handleScrape = async () => {
    if (isMovie) await triggerScrape(media.id);
    else await triggerTVScrape(media.id);
    setTimeout(() => {
      fetchData();
      if (!isMovie) loadShowDetails();
    }, 2000);
  };

  const handleRename = async () => {
    if (!isMovie) return;
    setRenaming(true);
    setRenameResult(null);
    try {
      const result = await renameMovie(media.id);
      setRenameResult(`✅ Renamed to: ${result.new_path}`);
      fetchData();
    } catch (e: any) {
      setRenameResult(`❌ ${e?.response?.data?.detail || 'Rename failed'}`);
    } finally {
      setRenaming(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-0 md:p-10 bg-black/90 backdrop-blur-md overflow-y-auto" onClick={onClose}>
      <div 
        className="bg-zinc-900 w-full max-w-5xl min-h-screen md:min-h-0 md:rounded-2xl overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] relative"
        onClick={e => e.stopPropagation()}
      >
        {/* Close Button */}
        <button 
          onClick={onClose}
          className="absolute top-6 right-6 z-50 p-2 bg-black/50 hover:bg-zinc-800 text-white rounded-full transition-all border border-white/10"
        >
          <X className="w-6 h-6" />
        </button>

        {/* Hero Section (Backdrop) */}
        <div className="relative aspect-video md:aspect-[21/9] w-full overflow-hidden">
          {media.fanart_path ? (
            <img 
              src={resolveArtwork(media.fanart_path, 'fanart')!} 
              alt="" 
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-zinc-800 flex items-center justify-center">
              <Film className="w-20 h-20 text-zinc-700" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 via-zinc-900/40 to-transparent" />
          
          <div className="absolute bottom-0 left-0 w-full p-8 md:p-12">
            {isEditing ? (
              <input 
                type="text"
                value={editForm.title}
                onChange={e => setEditForm({...editForm, title: e.target.value})}
                className="text-4xl md:text-6xl font-black text-white mb-4 bg-zinc-800 border border-white/20 rounded px-4 py-2 w-full focus:outline-none focus:border-red-500"
              />
            ) : (
              <h1 className="text-4xl md:text-6xl font-black text-white mb-4 drop-shadow-lg tracking-tighter">
                {media.title}
              </h1>
            )}
            
            <div className="flex flex-wrap items-center gap-4 text-sm md:text-base text-zinc-300 font-semibold mb-8">
              <span className="text-green-400 font-bold">{Math.round((media.tmdb_rating || 0) * 10)}% Match</span>
              {isEditing ? (
                <input 
                  type="number"
                  value={editForm.year}
                  onChange={e => setEditForm({...editForm, year: parseInt(e.target.value)})}
                  className="bg-zinc-800 border border-white/20 rounded px-2 py-0.5 w-20 text-white focus:outline-none"
                />
              ) : (
                <span>{media.year}</span>
              )}
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <input 
                    type="number"
                    value={editForm.runtime}
                    onChange={e => setEditForm({...editForm, runtime: parseInt(e.target.value)})}
                    className="bg-zinc-800 border border-white/20 rounded px-2 py-0.5 w-20 text-white focus:outline-none"
                  />
                  <span>m</span>
                </div>
              ) : (
                media.runtime && (
                  <span className="flex items-center gap-1.5 bg-zinc-800/80 px-2 py-0.5 rounded text-xs uppercase tracking-wider border border-white/10">
                    {isMovie ? `${media.runtime}m` : `${media.runtime}m per ep`}
                  </span>
                )
              )}
              {isMovie && movie?.files?.[0]?.resolution && (
                <span className="border border-zinc-500 px-1.5 py-0.5 rounded text-[10px] uppercase font-black">
                  {movie.files[0].resolution}
                </span>
              )}
            </div>

            <div className="flex flex-wrap gap-4">
              {isEditing ? (
                <>
                  <button 
                    onClick={handleSave}
                    disabled={isSaving}
                    className="flex items-center gap-3 px-8 py-3 bg-red-600 text-white rounded-lg font-bold hover:bg-red-700 transition-all shadow-xl disabled:opacity-50"
                  >
                    <Save className="w-6 h-6" /> {isSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button 
                    onClick={() => setIsEditing(false)}
                    className="flex items-center gap-3 px-6 py-3 bg-zinc-700/80 text-white rounded-lg font-bold hover:bg-zinc-600 transition-all border border-white/10 backdrop-blur-md"
                  >
                    <XCircle className="w-5 h-5" /> Cancel
                  </button>
                </>
              ) : (
                <>
                  <button className="flex items-center gap-3 px-8 py-3 bg-white text-black rounded-lg font-bold hover:bg-zinc-200 transition-all shadow-xl">
                    <Play className="w-6 h-6 fill-current" /> Play
                  </button>
                  {trailerUrl ? (
                    <a 
                      href={trailerUrl} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 px-6 py-3 bg-zinc-700/80 text-white rounded-lg font-bold hover:bg-zinc-600 transition-all border border-white/10 backdrop-blur-md"
                    >
                      <Youtube className="w-5 h-5 text-red-500" /> Watch Trailer
                    </a>
                  ) : (
                    <button 
                      onClick={handleFetchTrailer}
                      disabled={isFetchingTrailer}
                      className="flex items-center gap-3 px-6 py-3 bg-zinc-700/80 text-white rounded-lg font-bold hover:bg-zinc-600 transition-all border border-white/10 backdrop-blur-md disabled:opacity-50"
                    >
                      <Youtube className="w-5 h-5" /> {isFetchingTrailer ? 'Finding...' : 'Find Trailer'}
                    </button>
                  )}
                  <button 
                    onClick={startEditing}
                    className="flex items-center gap-3 px-6 py-3 bg-zinc-700/80 text-white rounded-lg font-bold hover:bg-zinc-600 transition-all border border-white/10 backdrop-blur-md"
                  >
                    <Edit2 className="w-5 h-5" /> Edit
                  </button>
                  <button 
                    onClick={handleScrape}
                    className="flex items-center gap-3 px-6 py-3 bg-zinc-700/80 text-white rounded-lg font-bold hover:bg-zinc-600 transition-all border border-white/10 backdrop-blur-md"
                  >
                    <RefreshCw className="w-5 h-5" /> {isMatched ? 'Refresh' : 'Scrape'}
                  </button>
                  <button 
                    onClick={() => setShowFixMatch(true)}
                    className="flex items-center gap-3 px-6 py-3 bg-zinc-700/80 text-white rounded-lg font-bold hover:bg-zinc-600 transition-all border border-white/10 backdrop-blur-md"
                  >
                    <Search className="w-5 h-5" /> Fix Match
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Content Section */}
        <div className="p-8 md:p-12 pt-0 grid grid-cols-1 lg:grid-cols-3 gap-12">
          <div className="lg:col-span-2">
            {isEditing ? (
              <div className="mb-10">
                <label className="block text-zinc-500 text-sm font-bold uppercase tracking-widest mb-3">Synopsis</label>
                <textarea 
                  rows={8}
                  value={editForm.plot}
                  onChange={e => setEditForm({...editForm, plot: e.target.value})}
                  className="w-full bg-zinc-800 border border-white/10 rounded-xl p-4 text-white focus:outline-none focus:border-red-500 leading-relaxed"
                  placeholder="Enter plot summary..."
                />
              </div>
            ) : (
              <p className="text-lg text-zinc-200 leading-relaxed mb-10 max-w-3xl">
                {media.plot || 'No synopsis available for this title.'}
              </p>
            )}

            {/* Episodes Section (TV Only) - Hide during editing series meta */}
            {!isMovie && !isEditing && (
              <div className="mb-12">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="text-2xl font-bold text-white">Episodes</h3>
                  {fullShow?.seasons && fullShow.seasons.length > 1 && (
                    <div className="relative group">
                      <select 
                        value={selectedSeason}
                        onChange={(e) => setSelectedSeason(parseInt(e.target.value))}
                        className="appearance-none bg-zinc-800 text-white font-bold py-2 pl-4 pr-10 rounded border border-white/10 hover:bg-zinc-700 transition-colors focus:outline-none"
                      >
                        {fullShow.seasons.map(s => (
                          <option key={s.id} value={s.season_number}>Season {s.season_number}</option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-400 pointer-events-none" />
                    </div>
                  )}
                </div>

                <div className="space-y-1">
                  {episodes.map((ep) => (
                    <div 
                      key={ep.id} 
                      className="group flex flex-col md:flex-row gap-6 p-4 md:p-6 rounded-xl hover:bg-zinc-800/50 transition-all border border-transparent hover:border-white/5"
                    >
                      <div className="text-2xl font-light text-zinc-500 w-8 hidden md:block">{ep.episode_number}</div>
                      <div className="relative flex-shrink-0 w-full md:w-48 aspect-video rounded-lg overflow-hidden bg-zinc-800 border border-white/5 shadow-lg">
                        {ep.thumbnail_path ? (
                          <img src={resolveArtwork(ep.thumbnail_path, 'thumb')!} alt="" className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-zinc-700">
                            <Film className="w-8 h-8" />
                          </div>
                        )}
                        <div className="absolute inset-0 bg-black/20 group-hover:bg-black/0 transition-all" />
                      </div>
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-bold text-white text-lg">{ep.title}</h4>
                          <span className="text-zinc-500 text-sm font-medium">{ep.air_date}</span>
                        </div>
                        <p className="text-sm text-zinc-400 leading-relaxed line-clamp-3 md:line-clamp-2">
                          {ep.plot || "No description available for this episode."}
                        </p>
                        <button 
                          onClick={() => handleDownloadSubtitles('episode', ep.id)}
                          className="mt-3 flex items-center gap-2 text-[10px] uppercase font-black text-zinc-500 hover:text-white transition-colors"
                        >
                          <Languages className="w-3 h-3" /> Get Subtitles
                        </button>
                      </div>
                    </div>
                  ))}
                  {episodes.length === 0 && !isLoadingDetails && (
                    <div className="text-center py-12 text-zinc-500 bg-zinc-800/20 rounded-2xl border border-dashed border-zinc-800">
                      No episodes found for this season. Try rescanning your library.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Cast Section */}
            {media.cast && media.cast.length > 0 && (
              <div className="mb-12">
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <User className="w-5 h-5 text-zinc-500" /> Top Cast
                </h3>
                <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
                  {media.cast.slice(0, 10).map((person: any) => (
                    <div key={person.id || person.name} className="flex-shrink-0 w-28 text-center group">
                      <div className="aspect-square rounded-full overflow-hidden mb-3 border-2 border-transparent group-hover:border-white/50 transition-all shadow-lg">
                        {person.profile_path || person.thumb ? (
                          <img src={resolveArtwork(person.profile_path || person.thumb, 'profile')!} alt={person.name} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full bg-zinc-800 flex items-center justify-center"><User className="text-zinc-600" /></div>
                        )}
                      </div>
                      <p className="text-xs font-bold text-zinc-200 truncate">{person.name}</p>
                      <p className="text-[10px] text-zinc-500 truncate mt-0.5">{person.character}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-8">
            <div>
              <h4 className="text-zinc-500 text-sm font-bold uppercase tracking-widest mb-2">{isMovie ? 'Director' : 'Creator'}</h4>
              {isEditing ? (
                <input 
                  type="text"
                  value={editForm.director}
                  onChange={e => setEditForm({...editForm, director: e.target.value})}
                  className="bg-zinc-800 border border-white/20 rounded px-3 py-1.5 w-full text-white focus:outline-none"
                />
              ) : (
                <p className="text-zinc-200 font-medium">{media.director}</p>
              )}
            </div>
            
            {media.genres && media.genres.length > 0 && (
              <div>
                <h4 className="text-zinc-500 text-sm font-bold uppercase tracking-widest mb-2">Genres</h4>
                <div className="flex flex-wrap gap-2 mt-2">
                  {media.genres.map(g => (
                    <span key={g} className="px-2 py-1 bg-zinc-800 rounded text-xs text-zinc-300 border border-white/5">{g}</span>
                  ))}
                </div>
              </div>
            )}

            {isMovie && (
              <div>
                <h4 className="text-zinc-500 text-sm font-bold uppercase tracking-widest mb-2">File Info</h4>
                <div className="bg-black/30 rounded-xl p-4 border border-white/5">
                  {movie?.files?.map(file => (
                    <div key={file.id} className="space-y-3">
                      <p className="text-[10px] font-mono text-zinc-500 break-all bg-black/20 p-2 rounded">{file.file_path}</p>
                      <div className="flex justify-between text-xs text-zinc-400">
                        <span>Codec: {file.video_codec}</span>
                        <span>Res: {file.resolution}</span>
                      </div>
                    </div>
                  ))}
                  <button 
                    onClick={handleRename}
                    disabled={renaming}
                    className="w-full mt-4 flex items-center justify-center gap-2 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs rounded transition-all border border-white/10"
                  >
                    <FolderInput className="w-3.5 h-3.5" /> {renaming ? 'Renaming...' : 'Rename to Title'}
                  </button>
                  {renameResult && <p className="mt-2 text-[10px] text-zinc-500">{renameResult}</p>}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <FixMatchModal 
        isOpen={showFixMatch}
        onClose={() => setShowFixMatch(false)}
        mediaId={media.id}
        initialTitle={media.title}
        type={type}
        onMatchComplete={() => {
          fetchData();
          onClose();
        }}
      />
    </div>
  );
};
