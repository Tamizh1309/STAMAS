import React, { useEffect, useState } from 'react';
import { ShieldCheck, Server, CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';
import { fetchHealth, isBackendConfigured } from '../services/api';
import type { SystemHealth } from '../types';

interface HeaderProps {
  activeTab: 'dashboard' | 'tenders' | 'benchmark';
  setActiveTab: (tab: 'dashboard' | 'tenders' | 'benchmark') => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [statusState, setStatusState] = useState<'connecting' | 'online' | 'unconfigured' | 'unavailable'>(
    !isBackendConfigured() ? 'unconfigured' : 'connecting'
  );

  useEffect(() => {
    if (!isBackendConfigured()) {
      setStatusState('unconfigured');
      setHealth(null);
      return;
    }
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setStatusState('online');
      })
      .catch(() => {
        setHealth(null);
        setStatusState('unavailable');
      });
  }, []);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-900/80 border-b border-slate-800 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Name */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold text-xl tracking-tight text-white font-mono">
                STAMAS
              </span>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                v1.0 MVP
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Smart Tender Analysis & Management Assessment System
            </p>
          </div>
        </div>

        {/* Navigation links */}
        <nav className="hidden md:flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'dashboard'
                ? 'bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('tenders')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'tenders'
                ? 'bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            Tenders & Workspaces
          </button>
          <button
            onClick={() => setActiveTab('benchmark')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'benchmark'
                ? 'bg-slate-800 text-cyan-400 border border-slate-700 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            Evaluation & Benchmarks
          </button>
        </nav>

        {/* System Diagnostics Status */}
        <div className="flex items-center space-x-3">
          <div className="hidden sm:flex items-center space-x-2 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">PyMuPDF:</span>
            <span className={`font-mono ${
              statusState === 'online' ? 'text-cyan-400' : statusState === 'unconfigured' ? 'text-amber-400' : statusState === 'connecting' ? 'text-slate-400' : 'text-rose-400'
            }`}>
              {health?.components.pdf_parser || (statusState === 'unconfigured' ? 'Config Required' : statusState === 'connecting' ? 'Connecting...' : 'Unavailable')}
            </span>
          </div>

          <div className="flex items-center space-x-2 bg-slate-950/80 px-3 py-1.5 rounded-lg border border-slate-800 text-xs">
            {statusState === 'online' ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-emerald-400 font-medium">Backend Online</span>
              </>
            ) : statusState === 'unconfigured' ? (
              <>
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-amber-400 font-medium">Configuration Required</span>
              </>
            ) : statusState === 'connecting' ? (
              <>
                <Server className="w-3.5 h-3.5 text-slate-400 animate-pulse" />
                <span className="text-slate-400 font-medium">Connecting...</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                <span className="text-rose-400 font-medium">Backend Unavailable</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
