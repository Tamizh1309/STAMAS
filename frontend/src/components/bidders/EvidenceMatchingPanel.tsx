import React, { useState, useEffect } from 'react';
import {
  Search, FileText, CheckCircle, AlertTriangle, HelpCircle,
  XCircle, RefreshCw, Eye, Sparkles, Filter, ChevronRight
} from 'lucide-react';

import type { Bidder, Requirement, EvidenceMatch, EvidenceSummary } from '../../types';
import {
  fetchRequirements,
  fetchBidderEvidenceSummary,
  fetchBidderEvidenceMatches,
  runBatchEvidenceMatching,
  matchRequirement
} from '../../services/api';

interface EvidenceMatchingPanelProps {
  tenderId: number;
  bidder: Bidder;
  onOpenDocumentPage: (documentId: number, pageNumber: number) => void;
}

export const EvidenceMatchingPanel: React.FC<EvidenceMatchingPanelProps> = ({
  tenderId,
  bidder,
  onOpenDocumentPage
}) => {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [evidenceMatches, setEvidenceMatches] = useState<EvidenceMatch[]>([]);
  const [summary, setSummary] = useState<EvidenceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [matchingLoading, setMatchingLoading] = useState(false);
  const [matchingReqId, setMatchingReqId] = useState<number | null>(null);
  const [selectedMatchDetail, setSelectedMatchDetail] = useState<EvidenceMatch | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('ALL');

  const loadData = async () => {
    try {
      setLoading(true);
      const [reqs, matches] = await Promise.all([
        fetchRequirements(tenderId),
        fetchBidderEvidenceMatches(bidder.id, tenderId)
      ]);
      setRequirements(reqs);
      setEvidenceMatches(matches);

      try {
        const sumData = await fetchBidderEvidenceSummary(bidder.id, tenderId);
        setSummary(sumData);
      } catch {
        setSummary(null);
      }
    } catch (err) {
      console.error('Failed to load evidence matching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tenderId, bidder.id]);

  const handleRunBatchMatching = async () => {
    try {
      setMatchingLoading(true);
      await runBatchEvidenceMatching(tenderId, bidder.id);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to run batch matching');
    } finally {
      setMatchingLoading(false);
    }
  };

  const handleMatchSingle = async (reqId: number) => {
    try {
      setMatchingReqId(reqId);
      await matchRequirement(tenderId, bidder.id, reqId);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to match evidence for requirement');
    } finally {
      setMatchingReqId(null);
    }
  };

  const getStatusBadge = (status: EvidenceMatch['match_status']) => {
    switch (status) {
      case 'MATCHED':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />,
          label: 'MATCHED'
        };
      case 'PARTIAL':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />,
          label: 'PARTIAL'
        };
      case 'LOW_CONFIDENCE':
        return {
          bg: 'bg-yellow-500/10 text-yellow-300 border-yellow-500/30',
          icon: <HelpCircle className="w-3.5 h-3.5 text-yellow-300" />,
          label: 'LOW CONFIDENCE'
        };
      case 'NOT_FOUND':
      default:
        return {
          bg: 'bg-slate-800 text-slate-400 border-slate-700',
          icon: <XCircle className="w-3.5 h-3.5 text-slate-400" />,
          label: 'NOT FOUND'
        };
    }
  };

  const filteredRequirements = requirements.filter(req => {
    if (activeFilter === 'ALL') return true;
    const reqMatches = evidenceMatches.filter(m => m.requirement_id === req.id);
    if (activeFilter === 'NOT_FOUND') {
      return reqMatches.length === 0 || reqMatches.every(m => m.match_status === 'NOT_FOUND');
    }
    return reqMatches.some(m => m.match_status === activeFilter);
  });

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-extrabold text-white">Evidence Matching Engine</h3>
            <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              PHASE 5 — TRACEABILITY
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Automatically maps tender requirements against bidder document pages with verbatim evidence extraction, exact page traceability, and confidence scoring.
          </p>
        </div>

        <button
          onClick={handleRunBatchMatching}
          disabled={matchingLoading || requirements.length === 0}
          className="flex items-center space-x-2 px-5 py-3 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-lg shadow-cyan-500/25 transition disabled:opacity-50 shrink-0"
        >
          {matchingLoading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-cyan-200" />
              <span>Matching Requirements...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-cyan-200" />
              <span>Match All Requirements</span>
            </>
          )}
        </button>
      </div>

      {/* Summary Statistics Dashboard */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Total Requirements</div>
            <div className="text-2xl font-extrabold text-white mt-1">{summary.total_requirements}</div>
          </div>
          <div className="bg-slate-900 border border-emerald-900/40 rounded-xl p-4">
            <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Evidence Matched</div>
            <div className="text-2xl font-extrabold text-emerald-400 mt-1">{summary.matched_count}</div>
          </div>
          <div className="bg-slate-900 border border-amber-900/40 rounded-xl p-4">
            <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Partial</div>
            <div className="text-2xl font-extrabold text-amber-400 mt-1">{summary.partial_count}</div>
          </div>
          <div className="bg-slate-900 border border-yellow-900/40 rounded-xl p-4">
            <div className="text-[10px] font-bold text-yellow-300 uppercase tracking-wider">Low Confidence</div>
            <div className="text-2xl font-extrabold text-yellow-300 mt-1">{summary.low_confidence_count}</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Not Found</div>
            <div className="text-2xl font-extrabold text-slate-400 mt-1">{summary.not_found_count}</div>
          </div>
        </div>
      )}

      {/* Category/Status Filters */}
      <div className="flex items-center justify-between bg-slate-900/60 p-2 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Filter className="w-4 h-4 text-cyan-400 ml-2" />
          <span>Filter Status:</span>
          {['ALL', 'MATCHED', 'PARTIAL', 'LOW_CONFIDENCE', 'NOT_FOUND'].map(st => (
            <button
              key={st}
              onClick={() => setActiveFilter(st)}
              className={`px-3 py-1 rounded-lg text-[11px] font-semibold transition ${
                activeFilter === st
                  ? 'bg-cyan-500 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Requirement Evidence Matching List */}
      {loading ? (
        <div className="text-center py-12 text-slate-400 text-sm">Loading evidence matches...</div>
      ) : requirements.length === 0 ? (
        <div className="text-center py-12 bg-slate-900 border border-slate-800 rounded-2xl text-slate-400 text-sm">
          No requirements found for this tender.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRequirements.map(req => {
            const matchesForReq = evidenceMatches.filter(m => m.requirement_id === req.id);
            const isSingleMatching = matchingReqId === req.id;

            return (
              <div key={req.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
                
                {/* Requirement Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950/80 px-2.5 py-1 rounded border border-cyan-800/40">
                        {req.req_code}
                      </span>
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-slate-800 text-slate-300 border border-slate-700">
                        {req.category}
                      </span>
                      {req.mandatory && (
                        <span className="px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          MANDATORY
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-semibold text-slate-100 mt-2">{req.text}</p>
                  </div>

                  <button
                    onClick={() => handleMatchSingle(req.id)}
                    disabled={isSingleMatching}
                    className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-800/50 transition self-start md:self-auto shrink-0"
                  >
                    {isSingleMatching ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Search className="w-3.5 h-3.5" />
                    )}
                    <span>{isSingleMatching ? 'Searching...' : 'Find Evidence'}</span>
                  </button>
                </div>

                {/* Evidence Results for Requirement */}
                {matchesForReq.length === 0 ? (
                  <div className="text-xs text-slate-400 italic bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
                    No evidence matched yet for this requirement. Click "Find Evidence" to run matching engine.
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Evidence Found ({matchesForReq.length} candidate sources)
                    </div>

                    {matchesForReq.map(match => {
                      const badge = getStatusBadge(match.match_status as any);

                      return (
                        <div
                          key={match.id}
                          className="bg-slate-950 border border-slate-800/90 rounded-xl p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-slate-700 transition"
                        >
                          <div className="space-y-2 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[10px] font-bold border ${badge.bg}`}>
                                {badge.icon}
                                <span>{badge.label}</span>
                              </span>

                              <span className="text-xs font-mono font-bold text-cyan-300 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                                Confidence: {Math.round(match.confidence_score * 100)}%
                              </span>

                              <span className="text-[10px] font-mono text-slate-400">
                                Method: {match.matching_method}
                              </span>

                              {match.document_name && (
                                <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
                                  <FileText className="w-3.5 h-3.5 text-blue-400 inline" />
                                  <span>{match.document_name} — Page {match.page_number || 1}</span>
                                </span>
                              )}
                            </div>

                            {/* Evidence Snippet */}
                            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 font-mono leading-relaxed">
                              "{match.evidence_text}"
                            </div>

                            {/* Human Readable Reason */}
                            {match.reason && (
                              <p className="text-[11px] text-slate-400 italic">
                                <strong className="text-slate-300">Reason:</strong> {match.reason}
                              </p>
                            )}
                          </div>

                          {/* View Source Page Action */}
                          {match.document_id && match.page_number && (
                            <button
                              onClick={() => onOpenDocumentPage(match.document_id!, match.page_number!)}
                              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-bold text-white bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 transition shrink-0 self-end md:self-center"
                            >
                              <Eye className="w-3.5 h-3.5 text-blue-400" />
                              <span>View Page {match.page_number}</span>
                              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

              </div>
            );
          })}
        </div>
      )}

      {/* Evidence Detail Modal */}
      {selectedMatchDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h4 className="text-sm font-bold text-white">Evidence Detail Panel</h4>
              <button onClick={() => setSelectedMatchDetail(null)} className="text-slate-400 hover:text-white">
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="text-xs space-y-2 text-slate-300">
              <div><strong className="text-slate-400">Match Status:</strong> {selectedMatchDetail.match_status}</div>
              <div><strong className="text-slate-400">Confidence:</strong> {Math.round(selectedMatchDetail.confidence_score * 100)}%</div>
              <div><strong className="text-slate-400">Method:</strong> {selectedMatchDetail.matching_method}</div>
              <div><strong className="text-slate-400">Document:</strong> {selectedMatchDetail.document_name}</div>
              <div><strong className="text-slate-400">Page:</strong> {selectedMatchDetail.page_number}</div>
              <div><strong className="text-slate-400">Reason:</strong> {selectedMatchDetail.reason}</div>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-xs font-mono text-slate-200">
              "{selectedMatchDetail.evidence_text}"
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button
                onClick={() => {
                  if (selectedMatchDetail.document_id && selectedMatchDetail.page_number) {
                    onOpenDocumentPage(selectedMatchDetail.document_id, selectedMatchDetail.page_number);
                    setSelectedMatchDetail(null);
                  }
                }}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-500"
              >
                View Document Page
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
