import React, { useState } from 'react';
import { useStore } from '../store/store';
import { createLibrary, updateLibrary, analyzeLibrary } from '../api/client';
import { exportLibraryCSV, exportLibraryHTML, patchSettings } from '../api/client';
import { FolderPlus, Settings as SettingsIcon, Trash2, FolderSearch, Sparkles, Download, Key, Edit3, Database, Search } from 'lucide-react';
import { FolderBrowserModal } from '../components/FolderBrowserModal';
import { EditLibraryModal } from '../components/EditLibraryModal';
import { cleanupLibrary } from '../api/client';

export const SettingsPage = () => {
  const { libraries, fetchData, removeLibrary, addNotification, scanLibrary } = useStore();
  const [newLibName, setNewLibName] = useState('');
  const [newLibPath, setNewLibPath] = useState('');
  const [isBrowserOpen, setIsBrowserOpen] = useState(false);
  const [newLibType, setNewLibType] = useState<'movie' | 'tv'>('movie');
  const [cleaningId, setCleaningId] = useState<number | null>(null);
  
  const [editingLib, setEditingLib] = useState<any>(null);
  const [analyzingId, setAnalyzingId] = useState<number | null>(null);

  const handleCleanup = async (libId: number) => {
    setCleaningId(libId);
    try {
      await cleanupLibrary(libId);
      addNotification('Deep Cleanup queued! Deduplicating database records, removing orphans, and cleaning artwork...', 'info');
    } catch (err) {
      addNotification('Failed to start cleanup.', 'error');
    } finally {
      setCleaningId(null);
    }
  };

  const handleAnalyze = async (libId: number) => {
    setAnalyzingId(libId);
    try {
      await analyzeLibrary(libId);
      addNotification('Deep Media Analysis queued! Checking resolution and codecs...', 'info');
    } catch (err) {
      addNotification('Failed to start analysis.', 'error');
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleEditSave = async (id: number, name: string, path: string) => {
    try {
      await updateLibrary(id, name, path);
      addNotification('Library updated successfully.', 'success');
      fetchData();
    } catch (err) {
      addNotification('Failed to update library.', 'error');
    }
  };

  const handleBackup = (libId: number) => {
    window.open(`/api/export/library/${libId}/backup`, '_blank');
    addNotification('Backup download started.', 'success');
  };

  const handleAddLibrary = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newLibName || !newLibPath) return;
    
    try {
      const newLib = await createLibrary(newLibName, newLibPath, newLibType);
      setNewLibName('');
      setNewLibPath('');
      fetchData();
      addNotification('Library added successfully. Scan started...', 'success');
      
      if (newLib && newLib.id) {
        scanLibrary(newLib.id);
      }
    } catch (err) {
      addNotification('Failed to add library.', 'error');
    }
  };

  return (
    <div className="min-h-screen bg-[#141414] px-4 md:px-12 pt-32 pb-24 text-white">
      <div className="max-w-4xl mx-auto">
        <div className="mb-12">
          <h1 className="text-3xl font-black tracking-tighter text-white mb-2 flex items-center gap-3">
            <SettingsIcon className="w-8 h-8 text-red-600" /> Settings
          </h1>
          <p className="text-zinc-400 font-medium">Manage your library paths and system configuration.</p>
        </div>

        <div className="bg-zinc-900 rounded-xl border border-white/5 overflow-hidden shadow-2xl mb-12">
          <div className="p-6 border-b border-white/5 bg-black/20">
            <h2 className="text-xl font-bold text-white">Library Paths</h2>
            <p className="text-sm text-zinc-400 mt-1">Directories SelfHost Media Orchestrator will monitor for changes.</p>
          </div>
          
          <div className="p-6">
            <ul className="mb-8 space-y-4">
              {libraries.length === 0 && <li className="text-zinc-500 text-center py-4">No libraries mapped yet.</li>}
              {libraries.map(lib => (
                <li key={lib.id} className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 p-5 bg-black/40 rounded-lg border border-white/5 hover:border-white/10 transition-colors">
                  <div>
                    <h3 className="font-bold text-white text-lg">{lib.name}</h3>
                    <p className="text-xs text-zinc-500 font-mono mt-1 bg-zinc-900/80 px-2 py-1 rounded inline-block">{lib.path}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`uppercase text-[10px] font-black tracking-widest px-3 py-1 rounded ${lib.type === 'movie' ? 'bg-red-900/30 text-red-500 border border-red-900/50' : 'bg-green-900/30 text-green-500 border border-green-900/50'}`}>
                      {lib.type === 'movie' ? 'Movie' : 'TV Show'}
                    </span>
                    <button 
                      onClick={() => handleBackup(lib.id)}
                      title="Backup Library Metadata (JSON)"
                      className="p-2 text-blue-400 hover:text-white hover:bg-blue-600 rounded transition-colors border border-white/5"
                    >
                      <Database className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => setEditingLib(lib)}
                      title="Edit Library Name/Path"
                      className="p-2 text-orange-400 hover:text-white hover:bg-orange-600 rounded transition-colors border border-white/5"
                    >
                      <Edit3 className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => handleCleanup(lib.id)}
                      disabled={cleaningId === lib.id}
                      title="Deep Database & Artwork Cleanup"
                      className="p-2 text-purple-400 hover:text-white hover:bg-purple-600 rounded transition-colors disabled:opacity-40 border border-white/5"
                    >
                      <Sparkles className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => handleAnalyze(lib.id)}
                      disabled={analyzingId === lib.id}
                      title="Deep Technical Analysis (Resolution/Codecs)"
                      className="p-2 text-cyan-400 hover:text-white hover:bg-cyan-600 rounded transition-colors disabled:opacity-40 border border-white/5"
                    >
                      <Search className="w-4 h-4" />
                    </button>
                    <button onClick={() => removeLibrary(lib.id)} className="p-2 text-zinc-400 hover:text-white hover:bg-red-600 rounded transition-colors border border-white/5">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>

            <form onSubmit={handleAddLibrary} className="bg-black/20 p-6 rounded-xl border border-white/5 space-y-5">
              <h3 className="text-xs font-black text-zinc-500 uppercase tracking-widest flex items-center gap-2">
                <FolderPlus className="w-4 h-4"/> Add New Library
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-zinc-400 uppercase mb-2">Display Name</label>
                  <input 
                    type="text" 
                    value={newLibName}
                    onChange={e => setNewLibName(e.target.value)}
                    placeholder="e.g. My Movies"
                    className="w-full bg-zinc-900 border border-white/10 rounded px-4 py-2.5 text-white focus:outline-none focus:border-red-500 transition-colors placeholder:text-zinc-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-zinc-400 uppercase mb-2">Library Type</label>
                  <select 
                    value={newLibType}
                    onChange={e => setNewLibType(e.target.value as 'movie' | 'tv')}
                    className="w-full bg-zinc-900 border border-white/10 rounded px-4 py-2.5 text-white focus:outline-none focus:border-red-500 transition-colors"
                  >
                    <option value="movie">Movies</option>
                    <option value="tv">TV Shows</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-zinc-400 uppercase mb-2">Server Path</label>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    value={newLibPath}
                    onChange={e => setNewLibPath(e.target.value)}
                    placeholder="/media/movies"
                    className="flex-1 bg-zinc-900 border border-white/10 rounded px-4 py-2.5 font-mono text-sm text-white focus:outline-none focus:border-red-500 transition-colors placeholder:text-zinc-600"
                  />
                  <button
                    type="button"
                    onClick={() => setIsBrowserOpen(true)}
                    className="px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-white font-bold rounded transition-colors border border-white/10"
                  >
                    Browse
                  </button>
                </div>
              </div>
              <button 
                type="submit"
                className="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded font-bold transition-all shadow-lg mt-2"
              >
                Add Library
              </button>
            </form>
          </div>
        </div>
        
        <FolderBrowserModal 
          isOpen={isBrowserOpen}
          onClose={() => setIsBrowserOpen(false)}
          onSelect={(path: string) => {
            setNewLibPath(path);
            setIsBrowserOpen(false);
          }}
        />

        <EditLibraryModal
          isOpen={!!editingLib}
          onClose={() => setEditingLib(null)}
          library={editingLib}
          onSave={handleEditSave}
        />

        {/* Export Section */}
        <div className="bg-zinc-900 rounded-xl border border-white/5 overflow-hidden shadow-2xl mb-12">
          <div className="p-6 border-b border-white/5 bg-black/20">
            <h2 className="text-xl font-bold text-white">Export Library</h2>
            <p className="text-sm text-zinc-400 mt-1">Download your entire movie library as a file.</p>
          </div>
          <div className="p-6 flex flex-wrap gap-4">
            <button
              onClick={exportLibraryCSV}
              className="flex items-center gap-2 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded font-bold transition-colors border border-white/10"
            >
              <Download className="w-5 h-5" /> Export CSV
            </button>
            <button
              onClick={exportLibraryHTML}
              className="flex items-center gap-2 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded font-bold transition-colors border border-white/10"
            >
              <Download className="w-5 h-5" /> Export HTML Report
            </button>
          </div>
        </div>

        {/* API Keys Section */}
        <ApiKeysSection />
      </div>
    </div>
  );
};

const ApiKeysSection = () => {
  const [tmdb, setTmdb] = useState('');
  const [omdb, setOmdb] = useState('');
  const [osubs, setOsubs] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    await patchSettings({
      api_keys: { tmdb, omdb, opensubtitles: osubs },
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="bg-zinc-900 rounded-xl border border-white/5 overflow-hidden shadow-2xl">
      <div className="p-6 border-b border-white/5 bg-black/20">
        <h2 className="text-xl font-bold text-white">API Keys</h2>
        <p className="text-sm text-zinc-400 mt-1">Stored in config/settings.json on the server.</p>
      </div>
      <div className="p-6 space-y-5">
        {[
          { label: 'TMDB API Key', value: tmdb, setter: setTmdb, placeholder: 'Enter TMDB key…' },
          { label: 'OMDb API Key', value: omdb, setter: setOmdb, placeholder: 'Enter OMDb key…' },
          { label: 'OpenSubtitles API Key', value: osubs, setter: setOsubs, placeholder: 'Enter OpenSubtitles key…' },
        ].map(({ label, value, setter, placeholder }) => (
          <div key={label}>
            <label className="block text-xs font-bold text-zinc-400 uppercase mb-2">{label}</label>
            <input
              type="password"
              value={value}
              onChange={e => setter(e.target.value)}
              placeholder={placeholder}
              className="w-full bg-zinc-950 border border-white/10 rounded px-4 py-3 text-white font-mono text-sm focus:outline-none focus:border-red-500 transition-colors placeholder:text-zinc-700"
            />
          </div>
        ))}
        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-8 py-3 bg-red-600 hover:bg-red-700 text-white rounded font-bold transition-colors shadow-lg mt-4"
        >
          <Key className="w-5 h-5" /> {saved ? 'Saved Successfully!' : 'Save API Keys'}
        </button>
      </div>
    </div>
  );
};
