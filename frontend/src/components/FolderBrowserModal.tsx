import React, { useState, useEffect } from 'react';
import { X, Folder, ChevronRight, CornerLeftUp, HardDrive } from 'lucide-react';
import { browseFileSystem, apiClient } from '../api/client';

interface Drive { label: string; path: string; }

interface FolderBrowserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (path: string) => void;
}

export const FolderBrowserModal: React.FC<FolderBrowserModalProps> = ({ isOpen, onClose, onSelect }) => {
  const [currentPath, setCurrentPath] = useState('/');
  const [parentPath, setParentPath] = useState('/');
  const [directories, setDirectories] = useState<{name: string, path: string}[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [drives, setDrives] = useState<Drive[]>([]);

  useEffect(() => {
    if (isOpen) {
      loadPath(currentPath);
      // Fetch Windows drive mounts (D:\ → /d_drive, etc.)
      apiClient.get('/libraries/drives')
        .then(r => setDrives(r.data.drives))
        .catch(() => {});
    }
  }, [isOpen]);

  const loadPath = async (path: string) => {
    setLoading(true);
    setError('');
    try {
      const data = await browseFileSystem(path);
      setCurrentPath(data.current_path);
      setParentPath(data.parent_path);
      setDirectories(data.directories);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load directory');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center z-50">
      <div className="bg-slate-800 p-6 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col border border-slate-700">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">Browse Server File System</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X size={24} />
          </button>
        </div>

        {/* Quick Access – Windows Drives */}
        {drives.length > 0 && (
          <div className="mb-3">
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-2 font-semibold">
              Quick Access — Drives
            </p>
            <div className="flex flex-wrap gap-2">
              {drives.map(d => (
                <button
                  key={d.path}
                  onClick={() => loadPath(d.path)}
                  title={`${d.label} → ${d.path}`}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                    currentPath === d.path || currentPath.startsWith(d.path + '/')
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'bg-slate-700 border-slate-600 text-slate-300 hover:bg-slate-600 hover:text-white'
                  }`}
                >
                  <HardDrive size={14} />
                  {d.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Current path breadcrumb */}
        <div className="mb-4 bg-slate-900 p-2 text-sm text-slate-300 rounded border border-slate-700 flex items-center font-mono overflow-x-auto whitespace-nowrap">
          <ChevronRight size={16} className="text-slate-500 mr-2 flex-shrink-0" />
          {currentPath}
        </div>

        {error && (
          <div className="mb-4 bg-red-900 bg-opacity-50 text-red-200 p-3 rounded text-sm text-center">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-y-auto mb-4 bg-slate-900 p-2 rounded border border-slate-700" style={{minHeight: '160px'}}>
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <ul className="space-y-1">
              {currentPath !== parentPath && (
                <li>
                  <button
                    onClick={() => loadPath(parentPath)}
                    className="flex items-center w-full p-2 hover:bg-slate-800 rounded text-left transition select-none"
                  >
                    <CornerLeftUp size={18} className="text-slate-400 mr-3" />
                    <span className="text-slate-300 font-medium">..</span>
                  </button>
                </li>
              )}
              {directories.length === 0 && (
                <li className="text-slate-500 text-center p-4">No subdirectories found or permission denied</li>
              )}
              {directories.map((dir) => (
                <li key={dir.path}>
                  <button
                    onClick={() => loadPath(dir.path)}
                    className="flex items-center w-full p-2 hover:bg-slate-800 rounded text-left transition select-none group"
                  >
                    <Folder size={18} className="text-blue-400 mr-3 group-hover:text-blue-300" />
                    <span className="text-slate-300 group-hover:text-white font-medium">{dir.name}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="flex justify-end space-x-3 mt-auto pt-4 border-t border-slate-700">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded transition font-medium"
          >
            Cancel
          </button>
          <button
            onClick={() => onSelect(currentPath)}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded transition shadow font-medium"
          >
            Select This Folder
          </button>
        </div>
      </div>
    </div>
  );
};
