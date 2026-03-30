import React from 'react';
import { useStore } from '../store/store';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';

export const NotificationOverlay = () => {
  const { notifications, removeNotification } = useStore();

  if (notifications.length === 0) return null;

  return (
    <div className="fixed top-6 right-6 z-[60] flex flex-col gap-3 w-80">
      {notifications.map((n) => (
        <div 
          key={n.id} 
          className={`p-4 rounded-lg shadow-2xl border flex items-start gap-3 animate-in slide-in-from-right duration-300 ${
            n.type === 'success' ? 'bg-zinc-900 border-green-500/50 text-green-400' :
            n.type === 'error' ? 'bg-zinc-900 border-red-500/50 text-red-400' :
            'bg-zinc-900 border-zinc-700 text-zinc-300'
          }`}
        >
          {n.type === 'success' && <CheckCircle className="w-5 h-5 flex-shrink-0" />}
          {n.type === 'error' && <AlertCircle className="w-5 h-5 flex-shrink-0" />}
          {n.type === 'info' && <Info className="w-5 h-5 flex-shrink-0" />}
          
          <div className="flex-1 text-sm font-medium leading-tight">
            {n.message}
          </div>

          <button 
            onClick={() => removeNotification(n.id)}
            className="text-zinc-500 hover:text-white transition-colors p-0.5"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
};
