import React, { useState, useEffect } from 'react';
import { X, Save, Folder } from 'lucide-react';
import { Library } from '../store/store';
import { FolderBrowserModal } from './FolderBrowserModal';

interface EditLibraryModalProps {
  isOpen: boolean;
  onClose: () => void;
  library: Library | null;
  onSave: (id: number, name: string, path: string) => Promise<void>;
}

export const EditLibraryModal: React.FC<EditLibraryModalProps> = ({ isOpen, onClose, library, onSave }) => {
  const [name, setName] = useState('');
  const [path, setPath] = useState('');
  const [isBrowserOpen, setIsBrowserOpen] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (library) {
      setName(library.name);
      setPath(library.path);
    }
  }, [library, isOpen]);

  if (!isOpen || !library) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !path) return;
    
    setIsSaving(true);
    try {
      await onSave(library.id, name, path);
      onClose();
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-zinc-900 border border-white/10 rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-black/20">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Edit Library
          </h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-white transition">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="block text-xs font-black text-zinc-500 uppercase tracking-widest mb-2">
              Library Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-zinc-950 border border-white/10 rounded px-4 py-3 text-white focus:outline-none focus:border-red-500 transition-colors"
              placeholder="e.g. My Movies"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-black text-zinc-500 uppercase tracking-widest mb-2">
              Server Path
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={path}
                onChange={(e) => setPath(e.target.value)}
                className="flex-1 bg-zinc-950 border border-white/10 rounded px-4 py-3 text-white font-mono text-sm focus:outline-none focus:border-red-500 transition-colors"
                placeholder="/media/movies"
                required
              />
              <button
                type="button"
                onClick={() => setIsBrowserOpen(true)}
                className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded transition-colors border border-white/10"
              >
                <Folder size={18} />
              </button>
            </div>
            <p className="mt-2 text-[10px] text-zinc-500 leading-tight">
              <span className="text-orange-500 font-bold uppercase mr-1">Warning:</span> 
              Changing the path will update all associated media records in the database.
            </p>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded font-bold transition-colors border border-white/5"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded font-bold transition-all shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <Save size={18} /> {isSaving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>

        <FolderBrowserModal
          isOpen={isBrowserOpen}
          onClose={() => setIsBrowserOpen(false)}
          onSelect={(selectedPath) => {
            setPath(selectedPath);
            setIsBrowserOpen(false);
          }}
        />
      </div>
    </div>
  );
};
