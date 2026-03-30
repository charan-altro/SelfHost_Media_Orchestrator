import React, { useEffect } from 'react';
import { useStore } from '../store/store';
import { RefreshCw, CheckCircle2, AlertCircle, Clock, Loader2, Activity, Trash2 } from 'lucide-react';

const STATUS_ICON = {
  queued: <Clock className="w-4 h-4 text-zinc-400" />,
  running: <Loader2 className="w-4 h-4 text-red-500 animate-spin" />,
  done: <CheckCircle2 className="w-4 h-4 text-green-500" />,
  error: <AlertCircle className="w-4 h-4 text-red-500" />,
};

const STATUS_BADGE = {
  queued: 'bg-zinc-800 text-zinc-300',
  running: 'bg-red-900/30 text-red-500',
  done: 'bg-green-900/30 text-green-500',
  error: 'bg-red-900/30 text-red-500',
};

export const TasksPage = () => {
  const { tasks, isLoadingTasks, fetchTasks, clearTasks } = useStore();

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  const hasRunning = tasks.some(t => t.status === 'running' || t.status === 'queued');

  return (
    <div className="min-h-screen bg-[#141414] px-4 md:px-12 pt-32 pb-24 text-white">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-12">
          <div>
            <h1 className="text-3xl font-black tracking-tighter text-white mb-2 flex items-center gap-3">
              <Activity className="w-8 h-8 text-red-600" /> Background Tasks
            </h1>
            <p className="text-zinc-400 text-sm font-medium">
              {hasRunning ? (
                <span className="flex items-center gap-2 text-red-500">
                  <Loader2 className="w-4 h-4 animate-spin" /> Tasks are running…
                </span>
              ) : `${tasks.length} tasks total`}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => fetchTasks()}
              className="flex items-center gap-2 px-5 py-2.5 bg-zinc-900 hover:bg-zinc-800 text-white rounded font-bold transition-colors border border-white/5 shadow-lg"
            >
              <RefreshCw className={`w-4 h-4 ${isLoadingTasks ? 'animate-spin' : ''}`} /> Refresh
            </button>
            {tasks.length > 0 && (
              <button
                onClick={() => {
                  if (window.confirm('Are you sure you want to clear all task history?')) {
                    clearTasks();
                  }
                }}
                className="flex items-center gap-2 px-5 py-2.5 bg-red-900/20 hover:bg-red-900/40 text-red-500 rounded font-bold transition-colors border border-red-500/20 shadow-lg"
              >
                <Trash2 className="w-4 h-4" /> Clear All
              </button>
            )}
          </div>
        </div>

        {tasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-32 bg-zinc-900/30 rounded-2xl border border-zinc-800/50">
            <Clock className="w-16 h-16 text-zinc-700 mb-6" />
            <h2 className="text-xl font-bold text-zinc-300 mb-2">No active tasks</h2>
            <p className="text-zinc-500 text-sm">Tasks appear here when you trigger scraping or scanning.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {tasks.map(task => (
              <div key={task.id} className="bg-zinc-900 border border-white/5 rounded-xl p-6 shadow-xl transition-all hover:border-white/10">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-black/40 rounded-lg">
                      {STATUS_ICON[task.status]}
                    </div>
                    <div>
                      <span className="font-bold text-zinc-100 text-lg block mb-1">{task.name}</span>
                      <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded ${STATUS_BADGE[task.status]}`}>
                        {task.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2">
                    <span className="text-xs text-zinc-500 font-mono bg-black/40 px-3 py-1.5 rounded">
                      {new Date(task.created_at).toLocaleTimeString()}
                    </span>
                    {(task.status === 'done' || task.status === 'error') && (task as any).duration && (
                      <span className="text-[10px] text-zinc-500 font-bold bg-zinc-800/50 px-2 py-1 rounded">
                        Took { (task as any).duration }s
                      </span>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-black/50 rounded-full h-2 mb-3 overflow-hidden border border-white/5">
                  <div
                    className={`${task.status === 'done' ? 'bg-green-500' : task.status === 'error' ? 'bg-red-600' : 'bg-red-600'} h-full rounded-full transition-all duration-500 ease-out`}
                    style={{ width: `${Math.min(100, (task.progress / Math.max(1, task.total)) * 100)}%` }}
                  />
                </div>

                <div className="flex justify-between items-center text-xs font-medium text-zinc-400">
                  <span className="truncate pr-4">{task.message || 'Waiting…'}</span>
                  <span className="flex-shrink-0 font-mono bg-black/40 px-2 py-0.5 rounded">
                    {task.progress} / {task.total}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
