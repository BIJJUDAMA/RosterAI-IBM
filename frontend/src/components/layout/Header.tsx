import React from 'react';
import { Database, Play, Loader2, Network, Terminal } from 'lucide-react';
import { useData } from '../../hooks/useData';
import { ZenButton } from '../ui/ZenButton';

interface HeaderProps {
  showGraph?: boolean;
  setShowGraph?: (show: boolean) => void;
}

export const Header: React.FC<HeaderProps> = ({ 
  showGraph, setShowGraph
}) => {
  const { 
    ingesting, 
    loading, 
    progress, 
    currentTask, 
    handleIngest, 
    handleMatch,
    members,
    projects,
    isLLMReady 
  } = useData();

  const isBusy = ingesting || loading;
  const canAlign = members.length > 0 && projects.length > 0 && isLLMReady;

  return (
    <header className="flex items-center justify-between py-8">
      <div className="flex items-center gap-6">
        <h1 className="font-display text-[128px] tracking-tight leading-none m-0 text-ink">Roster</h1>
      </div>

      <div className="flex items-center gap-8">
        {!isLLMReady && (
          <div className="flex items-center gap-3 px-4 py-2 bg-clay/5 border border-clay/10 rounded-full animate-pulse">
            <Loader2 size={12} className="animate-spin text-clay" />
            <span className="text-[10px] font-black uppercase tracking-widest text-clay/60">Warming up AI Engine...</span>
          </div>
        )}

        <div className="flex items-center gap-3 animate-in fade-in zoom-in-95 duration-500">
            {!isBusy && (
              <>
                <ZenButton 
                  variant="ghost" 
                  onClick={handleIngest} 
                  disabled={ingesting || !isLLMReady}
                  title={!isLLMReady ? "Waiting for AI engine to initialize..." : "Start Ingestion"}
                  className={`flex items-center gap-2 px-5 py-2.5 text-[12px] font-bold uppercase tracking-wider ${!isLLMReady ? 'opacity-40 grayscale' : ''}`}
                >
                  <Database size={16} /> Ingest
                </ZenButton>
                <ZenButton 
                  onClick={handleMatch} 
                  disabled={loading || !canAlign}
                  title={!isLLMReady ? "AI Engine Offline" : !canAlign ? "Need members and projects" : "Run Optimization"}
                  className={`flex items-center gap-2 px-6 py-2.5 text-[12px] font-bold uppercase tracking-wider bg-ink text-paper ${!canAlign ? 'opacity-40 grayscale' : ''}`}
                >
                  <Play size={16} className="fill-current" /> Align
                </ZenButton>
              </>
            )}
        </div>

        {isBusy && (
          <div className="flex flex-col items-end gap-1 animate-in fade-in slide-in-from-right-4">
            <div className="flex items-center gap-3">
              <span className="text-[11px] font-bold uppercase tracking-widest text-clay">{currentTask}</span>
              <Loader2 size={14} className="animate-spin text-clay" />
            </div>
            <div className="w-[180px] h-1.5 bg-paper rounded-full overflow-hidden border border-line">
              <div 
                className="h-full bg-clay transition-all duration-500 ease-out" 
                style={{ width: `${progress * 100}%` }} 
              />
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
