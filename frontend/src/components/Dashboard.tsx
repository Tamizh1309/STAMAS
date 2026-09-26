import React from 'react';
import { FileText, FileCheck, Layers, Activity, PlusCircle, Search, ShieldCheck, CheckCircle2 } from 'lucide-react';
import type { Tender } from '../types';
import { TenderList } from './TenderList';

interface DashboardProps {
  tenders: Tender[];
  onSelectTender: (tender: Tender) => void;
  onCreateNew: () => void;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  tenders,
  onSelectTender,
  onCreateNew,
  searchQuery,
  setSearchQuery,
}) => {
  const totalTenders = tenders.length;
  const processedTenders = tenders.filter((t) => t.status === 'PROCESSED').length;
  const totalPages = tenders.reduce((acc, t) => acc + (t.page_count || 0), 0);

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Hero Banner / Intro */}
      <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>AI-Powered Integrated Bid Compliance Verification Platform</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Smart Tender Analysis & <span className="bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">Management Assessment System</span>
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed">
            Upload tender RFP documents, parse text & tabular requirements via PyMuPDF document intelligence, and verify bidder compliance with deterministic rules and traceable evidence.
          </p>
          <div className="pt-2 flex flex-wrap gap-4">
            <button
              onClick={onCreateNew}
              className="flex items-center space-x-2 px-6 py-3 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/25 transition"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create Tender Workspace</span>
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Total Tenders</p>
            <h3 className="text-2xl font-extrabold text-white font-mono">{totalTenders}</h3>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <FileCheck className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">PDFs Processed</p>
            <h3 className="text-2xl font-extrabold text-white font-mono">{processedTenders}</h3>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Layers className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Extracted Pages</p>
            <h3 className="text-2xl font-extrabold text-white font-mono">{totalPages}</h3>
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg flex items-center space-x-4">
          <div className="p-3 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-400 font-medium">Engine Status</p>
            <h3 className="text-sm font-bold text-emerald-400 flex items-center space-x-1.5 mt-1">
              <CheckCircle2 className="w-4 h-4" />
              <span>Active V1 Engine</span>
            </h3>
          </div>
        </div>

      </div>

      {/* Tender Search & List Header */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white">Active Tender Workspaces</h2>
            <p className="text-xs text-slate-400">Manage procurement document extraction targets</p>
          </div>

          <div className="flex items-center space-x-3">
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter tenders..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              onClick={onCreateNew}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition shrink-0"
            >
              + New Workspace
            </button>
          </div>
        </div>

        {/* List of Tenders */}
        <TenderList
          tenders={tenders}
          onSelectTender={onSelectTender}
          onCreateNew={onCreateNew}
        />
      </div>

    </div>
  );
};
