import React, { useState } from 'react';
import {
  Sparkles,
  Search,
  BookOpen,
  AlertTriangle,
  HelpCircle,
  CheckCircle2,
  Brain,
  ExternalLink,
  Cpu
} from 'lucide-react';
import type { RAGQueryResponse, SourceCitation } from '../../types';
import { queryRAG } from '../../services/api';

interface RAGAssistantPanelProps {
  tenderId: number;
  bidderId: number;
  bidderName: string;
  onSelectDocumentPage?: (documentId: number, pageNumber: number) => void;
}

const PRESET_QUESTIONS = [
  "Where is the bidder's GST registration mentioned?",
  "What is the average annual turnover reported in financial statements?",
  "What data center project experience is documented?",
  "Which pages mention ISO certifications?",
  "Are audited financial statements attached?"
];

export const RAGAssistantPanel: React.FC<RAGAssistantPanelProps> = ({
  tenderId,
  bidderId,
  bidderName,
  onSelectDocumentPage
}) => {
  const [query, setQuery] = useState('');
  const [retrievalMethod, setRetrievalMethod] = useState<'HYBRID' | 'KEYWORD' | 'SEMANTIC'>('HYBRID');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<RAGQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunQuery = async (customQuery?: string) => {
    const activeQuery = customQuery || query;
    if (!activeQuery.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await queryRAG({
        tender_id: tenderId,
        bidder_id: bidderId,
        query: activeQuery,
        top_k: 5,
        retrieval_method: retrievalMethod
      });
      setResponse(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate grounded AI response');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'GROUNDED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" /> Grounded Evidence
          </span>
        );
      case 'PARTIAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> Partial Information
          </span>
        );
      case 'INSUFFICIENT_CONTEXT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
            <HelpCircle className="w-3.5 h-3.5" /> Insufficient Context
          </span>
        );
      case 'CONFLICTING_SOURCES':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> Conflicting Evidence
          </span>
        );
      case 'AI_UNAVAILABLE':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-500/15 text-slate-300 border border-slate-500/30">
            <Cpu className="w-3.5 h-3.5" /> AI Unavailable (Deterministic Fallback)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-500/15 text-slate-300 border border-slate-500/30">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-900/40 via-slate-900 to-indigo-900/40 border border-purple-500/20 rounded-xl p-5 shadow-lg backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                STAMAS AI — Grounded Intelligence Assistant
              </h3>
              <p className="text-xs text-slate-400">
                Grounded Document Q&A for <span className="text-purple-300 font-semibold">{bidderName}</span>. Answers strictly cited from retrieved documents.
              </p>
            </div>
          </div>

          {/* Retrieval Method Toggle */}
          <div className="flex items-center bg-slate-800/80 p-1 rounded-lg border border-slate-700">
            <button
              onClick={() => setRetrievalMethod('HYBRID')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                retrievalMethod === 'HYBRID'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Hybrid
            </button>

            <button
              onClick={() => setRetrievalMethod('KEYWORD')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                retrievalMethod === 'KEYWORD'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Keyword
            </button>

            <button
              onClick={() => setRetrievalMethod('SEMANTIC')}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                retrievalMethod === 'SEMANTIC'
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Semantic
            </button>
          </div>
        </div>

        {/* Preset Questions */}
        <div className="mt-4 pt-4 border-t border-slate-800 flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
            <HelpCircle className="w-3.5 h-3.5" /> Suggested Questions:
          </span>
          {PRESET_QUESTIONS.map((q, idx) => (
            <button
              key={idx}
              onClick={() => {
                setQuery(q);
                handleRunQuery(q);
              }}
              className="text-xs bg-slate-800/60 hover:bg-purple-950/60 border border-slate-700/60 hover:border-purple-500/40 text-slate-300 hover:text-purple-200 px-3 py-1.5 rounded-full transition-all text-left"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Query Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleRunQuery()}
            placeholder="Ask a question about this bidder's uploaded documents (e.g., GST registration, ISO certificates, turnover)..."
            className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all shadow-inner"
          />
        </div>
        <button
          onClick={() => handleRunQuery()}
          disabled={loading || !query.trim()}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-medium text-sm rounded-xl shadow-lg shadow-purple-500/20 disabled:opacity-50 transition-all flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Analyzing...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" /> Ask STAMAS AI
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          {error}
        </div>
      )}

      {/* AI Response View */}
      {response && (
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl backdrop-blur-md">
          {/* Answer Top Bar */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-800">
            <div className="flex items-center gap-3">
              {getStatusBadge(response.status)}
              <span className="text-xs text-slate-400">
                Provider: <strong className="text-slate-200">{response.ai_provider_used}</strong> ({response.retrieval_method_used} search)
              </span>
            </div>
            {response.retrieval_score && (
              <span className="text-xs bg-slate-800 px-2.5 py-1 rounded-md text-slate-300 border border-slate-700">
                Retrieval Score: {(response.retrieval_score * 100).toFixed(0)}%
              </span>
            )}
          </div>

          {/* Conflict or Missing Context Alerts */}
          {response.conflicts && response.conflicts.length > 0 && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-300 space-y-1">
              <span className="font-bold flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" /> Conflicting Evidence Detected:
              </span>
              <ul className="list-disc pl-5 space-y-0.5">
                {response.conflicts.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </div>
          )}

          {response.missing_information && response.missing_information.length > 0 && (
            <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs text-amber-300 space-y-1">
              <span className="font-bold flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4" /> Note / Missing Details:
              </span>
              <ul className="list-disc pl-5 space-y-0.5">
                {response.missing_information.map((m, i) => (
                  <li key={i}>{m}</li>
                ))}
              </ul>
            </div>
          )}

          {/* AI Grounded Text */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-purple-300 flex items-center gap-2">
              <Brain className="w-4 h-4" /> Grounded Analysis & Response:
            </h4>
            <div className="text-sm text-slate-200 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 whitespace-pre-wrap font-sans">
              {response.answer}
            </div>
          </div>

          {/* Sources Section */}
          {response.sources && response.sources.length > 0 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-purple-400" /> Grounded Document Citations ({response.sources.length}):
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {response.sources.map((src: SourceCitation) => (
                  <div
                    key={src.source_id}
                    className="p-4 bg-slate-950/80 border border-slate-800 hover:border-purple-500/40 rounded-xl space-y-2.5 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono">
                          [{src.source_id}]
                        </span>
                        <span className="text-xs font-semibold text-slate-200 truncate max-w-[160px]" title={src.document_name}>
                          {src.document_name}
                        </span>
                      </div>
                      <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-mono">
                        Page {src.page_number}
                      </span>
                    </div>

                    <p className="text-xs text-slate-400 italic bg-slate-900/60 p-2.5 rounded-lg border border-slate-800 line-clamp-3 font-mono">
                      "{src.text_snippet}"
                    </p>

                    {onSelectDocumentPage && (
                      <button
                        onClick={() => onSelectDocumentPage(src.document_id, src.page_number)}
                        className="w-full text-xs bg-slate-800/80 hover:bg-purple-900/40 text-purple-300 hover:text-purple-200 border border-slate-700/80 hover:border-purple-500/40 py-1.5 rounded-lg font-medium transition-all flex items-center justify-center gap-1.5"
                      >
                        <ExternalLink className="w-3.5 h-3.5" /> Open Page {src.page_number} in PDF View
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
