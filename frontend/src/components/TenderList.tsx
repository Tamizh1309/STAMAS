import React from 'react';
import { FileText, Upload, Eye, CheckCircle2, Clock, AlertTriangle, Building2 } from 'lucide-react';
import type { Tender } from '../types';

interface TenderListProps {
  tenders: Tender[];
  onSelectTender: (tender: Tender) => void;
  onCreateNew: () => void;
}

export const TenderList: React.FC<TenderListProps> = ({
  tenders,
  onSelectTender,
  onCreateNew,
}) => {
  const getStatusBadge = (status: Tender['status']) => {
    switch (status) {
      case 'PROCESSED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            <span>Extracted</span>
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 animate-pulse">
            <Clock className="w-3 h-3" />
            <span>Parsing PDF...</span>
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
            <AlertTriangle className="w-3 h-3" />
            <span>Failed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <Clock className="w-3 h-3" />
            <span>PDF Pending</span>
          </span>
        );
    }
  };

  if (tenders.length === 0) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-12 text-center max-w-xl mx-auto my-8">
        <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mx-auto mb-4 border border-cyan-500/20">
          <FileText className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">No Tender Workspaces Found</h3>
        <p className="text-sm text-slate-400 mb-6">
          Initialize your first tender workspace to upload tender documents and extract structured compliance requirements.
        </p>
        <button
          onClick={onCreateNew}
          className="px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/20 transition"
        >
          + Create First Tender Workspace
        </button>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {tenders.map((tender) => (
        <div
          key={tender.id}
          className="group bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 shadow-lg hover:shadow-cyan-500/5 transition-all flex flex-col justify-between"
        >
          <div>
            {/* Status & ID Header */}
            <div className="flex items-center justify-between mb-3">
              <span className="font-mono text-xs font-semibold text-cyan-400 bg-cyan-950/60 px-2.5 py-1 rounded-lg border border-cyan-800/40">
                {tender.tender_id}
              </span>
              {getStatusBadge(tender.status)}
            </div>

            {/* Title */}
            <h4 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors line-clamp-2 mb-2">
              {tender.title}
            </h4>

            {/* Department */}
            <div className="flex items-center space-x-2 text-slate-400 text-xs mb-4">
              <Building2 className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              <span className="truncate">{tender.department}</span>
            </div>

            {/* Details */}
            <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/80 space-y-1.5 text-xs text-slate-400 mb-4">
              <div className="flex justify-between items-center">
                <span>Uploaded File:</span>
                <span className="font-medium text-slate-200 truncate max-w-[140px]">
                  {tender.file_name || 'None'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span>Extracted Pages:</span>
                <span className="font-mono font-semibold text-cyan-400">
                  {tender.page_count} pages
                </span>
              </div>
              {tender.closing_date && (
                <div className="flex justify-between items-center">
                  <span>Closing Date:</span>
                  <span className="text-slate-300 font-mono">{tender.closing_date}</span>
                </div>
              )}
            </div>
          </div>

          {/* Action button */}
          <button
            onClick={() => onSelectTender(tender)}
            className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-slate-800 hover:bg-cyan-600 hover:text-white border border-slate-700 transition"
          >
            {tender.status === 'PROCESSED' ? (
              <>
                <Eye className="w-4 h-4" />
                <span>Open Tender Workspace</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Upload & Extract PDF</span>
              </>
            )}
          </button>
        </div>
      ))}
    </div>
  );
};
