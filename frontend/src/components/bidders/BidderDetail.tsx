import React, { useState, useEffect } from 'react';
import { ArrowLeft, Upload, Trash2, CheckCircle, Clock, AlertCircle, Loader2, FileText, Search, Layers, Sparkles, ShieldCheck, UserCheck } from 'lucide-react';

import type { Bidder, BidderDocument } from '../../types';
import { fetchBidder, fetchBidderDocuments, uploadBidderDocument, processBidderDocument, deleteBidderDocument } from '../../services/api';
import { BidderDocumentViewer } from './BidderDocumentViewer';
import { EvidenceMatchingPanel } from './EvidenceMatchingPanel';
import { RuleEnginePanel } from './RuleEnginePanel';
import { RAGAssistantPanel } from './RAGAssistantPanel';
import { DecisionEnginePanel } from './DecisionEnginePanel';
import { OfficerReviewPanel } from './OfficerReviewPanel';

interface BidderDetailProps {
  tenderId: number;
  bidderId: number;
  onBack: () => void;
}

export const BidderDetail: React.FC<BidderDetailProps> = ({ tenderId, bidderId, onBack }) => {
  const [bidder, setBidder] = useState<Bidder | null>(null);
  const [documents, setDocuments] = useState<BidderDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('TECHNICAL');
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [selectedPageNumber, setSelectedPageNumber] = useState<number>(1);
  const [activeTab, setActiveTab] = useState<'OFFICER_REVIEW' | 'DECISION_ENGINE' | 'RAG_AI' | 'RULE_ENGINE' | 'EVIDENCE_MATCHING' | 'DOCUMENTS'>('OFFICER_REVIEW');

  const DOCUMENT_CATEGORIES = [
    'FINANCIAL', 'TECHNICAL', 'ELIGIBILITY', 'CERTIFICATION', 
    'EXPERIENCE', 'REGISTRATION', 'TAX', 'ANNEXURE', 'OTHER'
  ];

  const loadBidderData = async () => {
    try {
      setLoading(true);
      const [bidderData, docsData] = await Promise.all([
        fetchBidder(bidderId),
        fetchBidderDocuments(bidderId)
      ]);
      setBidder(bidderData);
      setDocuments(docsData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBidderData();
  }, [bidderId]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      alert('Only PDF files are supported.');
      return;
    }

    try {
      setUploading(true);
      await uploadBidderDocument(bidderId, selectedCategory, file);
      await loadBidderData();
    } catch (err) {
      console.error(err);
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleProcess = async (docId: number) => {
    try {
      setDocuments(docs => docs.map(d => d.id === docId ? { ...d, processing_status: 'PROCESSING' } : d));
      await processBidderDocument(bidderId, docId);
      await loadBidderData();
    } catch (err) {
      console.error(err);
      alert('Processing failed');
      await loadBidderData();
    }
  };

  const handleDelete = async (docId: number) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await deleteBidderDocument(bidderId, docId);
      await loadBidderData();
    } catch (err) {
      console.error(err);
      alert('Delete failed');
    }
  };

  const handleOpenDocumentPage = (docId: number, pageNum: number) => {
    setSelectedDocumentId(docId);
    setSelectedPageNumber(pageNum);
  };

  if (selectedDocumentId) {
    return (
      <BidderDocumentViewer 
        bidderId={bidderId} 
        documentId={selectedDocumentId} 
        initialPageNumber={selectedPageNumber}
        onBack={() => setSelectedDocumentId(null)} 
      />
    );
  }

  if (loading) return <div className="text-slate-400 text-sm">Loading bidder...</div>;
  if (!bidder) return <div className="text-red-400 text-sm">Bidder not found</div>;

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-900 border border-slate-800 hover:border-slate-700 px-3.5 py-2 rounded-xl transition"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Bidders</span>
        </button>

        <div className="flex items-center space-x-3">
          <span className="text-xs text-slate-400 hidden sm:inline">
            Tender ID: <strong className="text-slate-200">{tenderId}</strong>
          </span>
          <span className="font-mono text-xs font-bold text-purple-400 bg-purple-950/80 px-3 py-1.5 rounded-lg border border-purple-800/40">
            Bidder: {bidder.company_name}
          </span>
        </div>
      </div>

      {/* Bidder Profile & Document Upload Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row justify-between gap-6">
        <div>
          <h2 className="text-xl font-extrabold text-white mb-2">{bidder.company_name}</h2>
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-xs text-slate-400">
            <div><strong className="text-slate-300">Name:</strong> {bidder.bidder_name}</div>
            <div><strong className="text-slate-300">Status:</strong> <span className="text-cyan-400">{bidder.status}</span></div>
            <div><strong className="text-slate-300">Reg No:</strong> {bidder.registration_number || 'N/A'}</div>
            <div><strong className="text-slate-300">GSTIN:</strong> {bidder.gstin || 'N/A'}</div>
            <div><strong className="text-slate-300">Email:</strong> {bidder.email || 'N/A'}</div>
            <div><strong className="text-slate-300">Phone:</strong> {bidder.phone || 'N/A'}</div>
          </div>
        </div>

        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 md:w-72 flex flex-col justify-center">
          <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Upload Document</label>
          <select 
            value={selectedCategory} 
            onChange={e => setSelectedCategory(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 mb-3"
          >
            {DOCUMENT_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <label className="cursor-pointer flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 transition">
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            <span>{uploading ? 'Uploading...' : 'Upload PDF'}</span>
            <input type="file" accept=".pdf" className="hidden" onChange={handleFileUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      {/* Main Tabs Header */}
      <div className="flex border-b border-slate-800 space-x-4 overflow-x-auto">
        <button
          onClick={() => setActiveTab('OFFICER_REVIEW')}
          className={`flex items-center space-x-2 px-4 py-3 text-xs font-bold border-b-2 transition shrink-0 ${
            activeTab === 'OFFICER_REVIEW'
              ? 'border-indigo-400 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <UserCheck className="w-4 h-4 text-indigo-400" />
          <span>Officer Review (Phase 9)</span>
        </button>

        <button
          onClick={() => setActiveTab('DECISION_ENGINE')}
          className={`flex items-center space-x-2 px-4 py-3 text-xs font-bold border-b-2 transition shrink-0 ${
            activeTab === 'DECISION_ENGINE'
              ? 'border-emerald-400 text-emerald-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Compliance Assessment (Phase 8)</span>
        </button>

        <button
          onClick={() => setActiveTab('RAG_AI')}
          className={`flex items-center space-x-2 px-4 py-3 text-xs font-bold border-b-2 transition shrink-0 ${
            activeTab === 'RAG_AI'
              ? 'border-purple-400 text-purple-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>STAMAS AI Assistant (Phase 7)</span>
        </button>

        <button
          onClick={() => setActiveTab('RULE_ENGINE')}
          className={`flex items-center space-x-2 px-4 py-3 text-xs font-bold border-b-2 transition shrink-0 ${
            activeTab === 'RULE_ENGINE'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Compliance Rule Engine (Phase 6)</span>
        </button>

        <button
          onClick={() => setActiveTab('EVIDENCE_MATCHING')}
          className={`flex items-center space-x-2 px-4 py-3 text-xs font-bold border-b-2 transition shrink-0 ${
            activeTab === 'EVIDENCE_MATCHING'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Search className="w-4 h-4" />
          <span>Evidence Matching (Phase 5)</span>
        </button>

        <button
          onClick={() => setActiveTab('DOCUMENTS')}
          className={`flex items-center space-x-2 px-4 py-3 text-xs font-bold border-b-2 transition shrink-0 ${
            activeTab === 'DOCUMENTS'
              ? 'border-cyan-400 text-cyan-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <FileText className="w-4 h-4" />
          <span>Uploaded Documents ({documents.length})</span>
        </button>
      </div>

      {/* Tab Content */}
      {activeTab === 'OFFICER_REVIEW' ? (
        <OfficerReviewPanel
          tenderId={tenderId}
          bidderId={bidderId}
        />
      ) : activeTab === 'DECISION_ENGINE' ? (
        <DecisionEnginePanel
          tenderId={tenderId}
          bidder={bidder}
          onOpenDocumentPage={handleOpenDocumentPage}
        />
      ) : activeTab === 'RAG_AI' ? (
        <RAGAssistantPanel
          tenderId={tenderId}
          bidderId={bidderId}
          bidderName={bidder.company_name}
          onSelectDocumentPage={handleOpenDocumentPage}
        />
      ) : activeTab === 'RULE_ENGINE' ? (
        <RuleEnginePanel
          tenderId={tenderId}
          bidder={bidder}
          onOpenDocumentPage={handleOpenDocumentPage}
        />
      ) : activeTab === 'EVIDENCE_MATCHING' ? (
        <EvidenceMatchingPanel
          tenderId={tenderId}
          bidder={bidder}
          onOpenDocumentPage={handleOpenDocumentPage}
        />
      ) : (
        <div>
          <h3 className="text-lg font-bold text-white mb-4">Bidder Documents</h3>
          {documents.length === 0 ? (
            <div className="text-center p-8 bg-slate-900 rounded-2xl border border-slate-800 text-slate-400 text-sm">
              No documents uploaded for this bidder yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {documents.map(doc => (
                <div key={doc.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="text-white text-sm font-bold break-all pr-2">{doc.filename}</h4>
                      <span className="px-2 py-1 text-[9px] font-bold rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {doc.category}
                      </span>
                    </div>
                    <div className="text-xs text-slate-400 space-y-1 mb-4">
                      <div>Pages: <span className="text-white">{doc.page_count}</span></div>
                      <div>Method: <span className={doc.extraction_status === 'TEXT_LAYER' ? 'text-cyan-400' : 'text-slate-300'}>{doc.extraction_status}</span></div>
                      {doc.error_message && <div className="text-red-400 text-[10px] mt-1 bg-red-500/10 p-2 rounded">Error: {doc.error_message}</div>}
                    </div>
                  </div>

                  <div className="flex items-center justify-between border-t border-slate-800/80 pt-3">
                    <div className="flex items-center space-x-1.5">
                      {doc.processing_status === 'PROCESSED' ? (
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                      ) : doc.processing_status === 'PROCESSING' ? (
                        <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                      ) : doc.processing_status === 'FAILED' ? (
                        <AlertCircle className="w-4 h-4 text-red-400" />
                      ) : (
                        <Clock className="w-4 h-4 text-amber-400" />
                      )}
                      <span className="text-[10px] font-bold text-slate-300 uppercase">{doc.processing_status}</span>
                    </div>

                    <div className="flex space-x-2">
                      {doc.processing_status === 'PROCESSED' ? (
                        <button onClick={() => handleOpenDocumentPage(doc.id, 1)} className="px-3 py-1.5 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 text-xs font-bold rounded-lg transition">
                          View
                        </button>
                      ) : (
                        <button 
                          onClick={() => handleProcess(doc.id)} 
                          disabled={doc.processing_status === 'PROCESSING'}
                          className="px-3 py-1.5 bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 text-xs font-bold rounded-lg transition disabled:opacity-50"
                        >
                          {doc.processing_status === 'FAILED' ? 'Retry' : 'Process'}
                        </button>
                      )}
                      <button onClick={() => handleDelete(doc.id)} className="px-3 py-1.5 bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 text-xs font-bold rounded-lg transition">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
