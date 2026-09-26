import React, { useState, useEffect } from 'react';
import { ArrowLeft, Upload, FileText, Search, AlertCircle, Loader2, Copy, Check, FileCheck, Sparkles, BarChart3 } from 'lucide-react';
import type { TenderDetail, TenderPage } from '../types';
import { fetchTenderDetail, uploadTenderPDF, searchExtractedText } from '../services/api';
import { RequirementReview } from './RequirementReview';
import { BidderList } from './bidders/BidderList';
import { ReportsDashboard } from './reports/ReportsDashboard';

interface TenderDetailViewProps {
  tenderId: number;
  onBack: () => void;
}

export const TenderDetailView: React.FC<TenderDetailViewProps> = ({ tenderId, onBack }) => {
  const [tender, setTender] = useState<TenderDetail | null>(null);
  const [pages, setPages] = useState<TenderPage[]>([]);
  const [selectedPageNum, setSelectedPageNum] = useState<number>(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Tab state: 'requirements', 'bidders', 'reports', 'explorer'
  const [activeTab, setActiveTab] = useState<'requirements' | 'bidders' | 'reports' | 'explorer'>('requirements');

  const loadData = async () => {
    try {
      setLoading(true);
      const detail = await fetchTenderDetail(tenderId);
      setTender(detail);
      setPages(detail.pages || []);
      if (detail.pages.length > 0) {
        setSelectedPageNum(detail.pages[0].page_number);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load tender details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tenderId]);

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    try {
      const filtered = await searchExtractedText(tenderId, query);
      setPages(filtered);
      if (filtered.length > 0 && !filtered.some(p => p.page_number === selectedPageNum)) {
        setSelectedPageNum(filtered[0].page_number);
      }
    } catch (err) {
      console.error('Search failed', err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Please select a valid PDF file.');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      await uploadTenderPDF(tenderId, file);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to upload and extract PDF');
    } finally {
      setUploading(false);
    }
  };

  const currentPage = pages.find((p) => p.page_number === selectedPageNum) || pages[0];

  const handleCopyText = () => {
    if (currentPage?.text_content) {
      navigator.clipboard.writeText(currentPage.text_content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Back Navigation Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 px-3.5 py-2 rounded-xl transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Tenders</span>
        </button>

        <div className="flex items-center space-x-3">
          <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/80 px-3 py-1.5 rounded-lg border border-cyan-800/40">
            ID: {tender?.tender_id}
          </span>
          <span className="text-xs text-slate-400 hidden sm:inline">
            Department: <strong className="text-slate-200">{tender?.department}</strong>
          </span>
        </div>
      </div>

      {/* Main Card Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-extrabold text-white mb-1">{tender?.title}</h2>
            <p className="text-xs text-slate-400 flex items-center space-x-3">
              <span>File: <strong className="text-cyan-300 font-mono">{tender?.file_name || 'No PDF Uploaded'}</strong></span>
              <span>•</span>
              <span>Extracted Pages: <strong className="text-white font-mono">{tender?.page_count || 0}</strong></span>
              <span>•</span>
              <span>Status: <strong className="text-emerald-400">{tender?.status}</strong></span>
            </p>
          </div>

          {/* Upload PDF Button */}
          <label className="cursor-pointer flex items-center justify-center space-x-2 px-5 py-3 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/20 transition shrink-0">
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Extracting Text...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>{tender?.file_name ? 'Re-upload PDF' : 'Upload Tender PDF'}</span>
              </>
            )}
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
        </div>

        {/* Tab Navigation Controls */}
        <div className="flex items-center space-x-2 mt-6 pt-4 border-t border-slate-800/80 overflow-x-auto">
          <button
            onClick={() => setActiveTab('requirements')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
              activeTab === 'requirements'
                ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>Requirement Intelligence</span>
          </button>

          <button
            onClick={() => setActiveTab('bidders')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
              activeTab === 'bidders'
                ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <FileCheck className="w-4 h-4" />
            <span>Bidders</span>
          </button>

          <button
            onClick={() => setActiveTab('reports')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
              activeTab === 'reports'
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <BarChart3 className="w-4 h-4 text-purple-300" />
            <span>Reports & Audit (Phase 10)</span>
          </button>

          <button
            onClick={() => setActiveTab('explorer')}
            className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold transition whitespace-nowrap ${
              activeTab === 'explorer'
                ? 'bg-cyan-500 text-white shadow-lg shadow-cyan-500/20'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Document Text Explorer</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Tab Views */}
      {tender?.status === 'CREATED' && !tender.file_name ? (
        <div className="bg-slate-900/60 border-2 border-dashed border-slate-800 rounded-2xl p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center mx-auto mb-4 border border-cyan-500/20">
            <Upload className="w-8 h-8" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Upload Tender Document (PDF)</h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto mb-6">
            Upload the official GeM RFP / Tender PDF document to run PyMuPDF document intelligence and extract requirements.
          </p>
          <label className="cursor-pointer inline-flex items-center space-x-2 px-6 py-3 rounded-xl text-xs font-bold text-white bg-cyan-500 hover:bg-cyan-400 shadow-lg shadow-cyan-500/20 transition">
            <Upload className="w-4 h-4" />
            <span>Select PDF File</span>
            <input
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={handleFileUpload}
            />
          </label>
        </div>
      ) : activeTab === 'bidders' ? (
        <BidderList tenderId={tenderId} />
      ) : activeTab === 'reports' ? (
        <ReportsDashboard tenderId={tenderId} />
      ) : activeTab === 'requirements' ? (
        /* Phase 2: Requirement Intelligence & Review UI */
        <RequirementReview
          tenderId={tenderId}
          hasExtractedText={pages.length > 0}
        />
      ) : (
        /* Phase 1: Document Text Explorer */
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          
          {/* Sidebar */}
          <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-4">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search PDF text..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 px-1 font-medium">
              <span>Extracted Pages:</span>
              <span className="font-mono text-cyan-400">{pages.length} found</span>
            </div>

            <div className="space-y-1.5 max-h-[460px] overflow-y-auto pr-1">
              {pages.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setSelectedPageNum(p.page_number)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition ${
                    selectedPageNum === p.page_number
                      ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-bold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center space-x-2 truncate">
                    <FileText className="w-3.5 h-3.5 shrink-0" />
                    <span>Page {p.page_number}</span>
                  </div>
                  <span className="text-[10px] opacity-60 font-mono">
                    {p.text_content.length} chars
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Page Viewer */}
          <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl">
            {currentPage ? (
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-slate-800 text-cyan-400">
                      <FileCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        Page {currentPage.page_number} Content
                      </h4>
                      <p className="text-[11px] text-slate-400 font-mono">
                        {currentPage.text_content.length} Characters • PyMuPDF Real-time Extraction
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={handleCopyText}
                    className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                  >
                    {copied ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                        <span className="text-emerald-400">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5" />
                        <span>Copy Text</span>
                      </>
                    )}
                  </button>
                </div>

                <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-5 font-mono text-xs text-slate-200 leading-relaxed overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap selection:bg-cyan-500 selection:text-white">
                  {currentPage.text_content || 'No text extracted on this page.'}
                </div>

                {currentPage.tables_data && currentPage.tables_data.length > 0 && (
                  <div className="mt-6">
                    <h5 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2">
                      Detected Tabular Structures ({currentPage.tables_data.length})
                    </h5>
                    {currentPage.tables_data.map((table: string[][], tidx: number) => (
                      <div key={tidx} className="overflow-x-auto bg-slate-950 border border-slate-800 rounded-xl p-3 mb-3">
                        <table className="w-full text-xs text-slate-300 border-collapse">
                          <tbody>
                            {table.map((row, ridx) => (
                              <tr key={ridx} className="border-b border-slate-800/60 last:border-0">
                                {row.map((cell, cidx) => (
                                  <td key={cidx} className="px-3 py-1.5 border-r border-slate-800/60 last:border-0">
                                    {cell}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500">
                Select a page from the sidebar to inspect extracted document text.
              </div>
            )}
          </div>

        </div>
      )}
    </div>
  );
};
