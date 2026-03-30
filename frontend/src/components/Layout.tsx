import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Film, Settings, Tv, Activity, Loader, Search, Bell, User } from 'lucide-react';
import { useStore } from '../store/store';
import { NotificationOverlay } from './NotificationOverlay';

const ScanProgressToast = () => {
  const { scanProgress, libraries, tasks, fetchTasks } = useStore();
  const activeScans = Object.entries(scanProgress);
  const activeTasks = tasks.filter(t => t.status === 'running' || t.status === 'queued');
  
  useEffect(() => {
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, [fetchTasks]);

  if (activeScans.length === 0 && activeTasks.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[70] flex flex-col gap-3 w-80">
      {/* Fast Scans (SSE) */}
      {activeScans.map(([libIdStr, progress]) => {
        const lib = libraries.find(l => l.id.toString() === libIdStr);
        const name = lib ? lib.name : `Library ${libIdStr}`;
        const pct = progress.total > 0 ? Math.round((progress.current / progress.total) * 100) : 0;
        
        return (
          <div key={`scan-${libIdStr}`} className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm text-zinc-200">
              <span className="font-semibold text-red-500 flex items-center gap-2">
                {progress.status === 'done' ? null : <Loader className="w-4 h-4 animate-spin" />}
                {progress.status === 'done' ? `Finished ${name}` : `Scanning ${name}`}
              </span>
              <span className="text-zinc-400 font-mono text-xs">{progress.current}{progress.total > 0 ? `/${progress.total}` : ''}</span>
            </div>
            
            <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden">
              <div 
                className={`h-1.5 rounded-full transition-all duration-300 ${progress.status === 'done' ? 'bg-green-500' : 'bg-red-600'}`}
                style={{ width: `${Math.max(2, pct)}%` }}
              />
            </div>
            
            <div className="text-xs text-zinc-500 truncate" title={progress.file}>
              {progress.status === 'done' ? 'Refreshing view...' : progress.file}
            </div>
          </div>
        );
      })}

      {/* Task Manager Tasks (Polling) */}
      {activeTasks.map((task) => {
        const pct = task.total > 0 ? Math.round((task.progress / task.total) * 100) : 0;
        
        return (
          <div key={`task-${task.id}`} className="bg-zinc-900 border border-zinc-800 rounded-lg shadow-2xl p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between text-sm text-zinc-200">
              <span className="font-semibold text-orange-500 flex items-center gap-2">
                <Activity className="w-4 h-4 animate-pulse" />
                {task.name}
              </span>
              <span className="text-zinc-400 font-mono text-xs">{pct}%</span>
            </div>
            
            <div className="w-full bg-zinc-950 rounded-full h-1.5 overflow-hidden">
              <div 
                className="h-1.5 rounded-full transition-all duration-300 bg-orange-600"
                style={{ width: `${pct}%` }}
              />
            </div>
            
            <div className="text-xs text-zinc-500 truncate" title={task.message}>
              {task.message || 'Processing...'}
            </div>
          </div>
        );
      })}
    </div>
  );
};

const Layout = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 0);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-[#141414] text-white font-sans selection:bg-red-600 selection:text-white pb-20">
      {/* Top Navigation */}
      <header 
        className={`fixed top-0 w-full z-[60] transition-colors duration-500 ${isScrolled ? 'bg-[#141414] shadow-md' : 'bg-gradient-to-b from-black/80 to-transparent'}`}
      >
        <div className="flex items-center justify-between px-4 md:px-12 py-4">
          <div className="flex items-center gap-8">
            <h1 className="text-2xl md:text-3xl font-black text-red-600 tracking-tighter cursor-pointer uppercase flex items-center gap-2">
              SelfHost Media Orchestrator
            </h1>
            
            <nav className="hidden md:flex items-center gap-5 text-sm font-medium">
              <NavLink 
                to="/" 
                className={({isActive}) => `transition-colors duration-300 ${isActive ? 'text-white font-bold' : 'text-zinc-300 hover:text-zinc-400'}`}
              >
                Movies
              </NavLink>
              <NavLink 
                to="/tv" 
                className={({isActive}) => `transition-colors duration-300 ${isActive ? 'text-white font-bold' : 'text-zinc-300 hover:text-zinc-400'}`}
              >
                TV Shows
              </NavLink>
              <NavLink 
                to="/tasks" 
                className={({isActive}) => `transition-colors duration-300 ${isActive ? 'text-white font-bold' : 'text-zinc-300 hover:text-zinc-400'}`}
              >
                Tasks
              </NavLink>
              <NavLink 
                to="/settings" 
                className={({isActive}) => `transition-colors duration-300 ${isActive ? 'text-white font-bold' : 'text-zinc-300 hover:text-zinc-400'}`}
              >
                Settings
              </NavLink>
            </nav>
          </div>

          <div className="flex items-center gap-6">
            <Search className="w-5 h-5 text-white cursor-pointer hover:text-zinc-300 transition" />
            <Bell className="w-5 h-5 text-white cursor-pointer hover:text-zinc-300 transition" />
            <div className="flex items-center gap-2 cursor-pointer group">
              <div className="w-8 h-8 rounded bg-red-600 flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              <span className="hidden md:block text-white text-xs group-hover:text-zinc-300 transition">▼</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full">
        <Outlet />
      </main>
      
      {/* Global Overlays */}
      <ScanProgressToast />
      <NotificationOverlay />
    </div>
  );
};

export default Layout;
