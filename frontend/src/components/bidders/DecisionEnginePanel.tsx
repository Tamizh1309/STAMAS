import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCw,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  Brain,
  ExternalLink,
  Layers,
  Info
} from 'lucide-react';
import type { Bidder, ComplianceDecisionResponse } from '../../types';
import { evaluateComplianceDecisions, fetchBidderComplianceSummary } from '../../services/api';

interface DecisionEnginePanelProps {
  tenderId: number;
  bidder: Bidder;
  onOpenDocumentPage?: (documentId: number, pageNumber: number) => void;
}

export const DecisionEnginePanel: React.FC<DecisionEnginePanelProps> = ({
  tenderId,
  bidder,
  onOpenDocumentPage
}) => {
  const [data, setData] = useState<ComplianceDecisionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterScope, setFilterScope] = useState<'ALL' | 'MANDATORY' | 'OPTIONAL'>('MANDATORY');
  const [filterState, setFilterState] = useState<'ALL' | 'PASS' | 'FAIL' | 'REVIEW'>('ALL');
  const [expandedReqId, setExpandedReqId] = useState<number | null>(null);

  const loadDecisions = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchBidderComplianceSummary(bidder.id, tenderId);
      setData(res);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load compliance decisions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDecisions();
  }, [bidder.id, tenderId]);

  const handleEvaluateAll = async () => {
    try {
      setEvaluating(true);
      setError(null);
      const res = await evaluateComplianceDecisions(tenderId, bidder.id);
      setData(res);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to evaluate compliance decisions');
    } finally {
      setEvaluating(false);
    }
  };

  const toggleExpand = (reqId: number) => {
    setExpandedReqId(prev => (prev === reqId ? null : reqId));
  };

  const getOverallBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-black bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-lg shadow-emerald-500/10">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" /> SYSTEM DECISION: PASS
          </span>
        );
      case 'FAIL':
        return (
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-black bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-lg shadow-rose-500/10">
            <XCircle className="w-5 h-5 text-rose-400" /> SYSTEM DECISION: FAIL
          </span>
        );
      case 'REVIEW':
      default:
        return (
          <span className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-black bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-lg shadow-amber-500/10">
            <AlertTriangle className="w-5 h-5 text-amber-400" /> SYSTEM DECISION: REVIEW REQUIRED
          </span>
        );
    }
  };

  const getReqBadge = (status: string) => {
    switch (status) {
      case 'PASS':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-extrabold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> PASS
          </span>
        );
      case 'FAIL':
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-extrabold bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1">
            <XCircle className="w-3.5 h-3.5" /> FAIL
          </span>
        );
      case 'REVIEW':
      default:
        return (
          <span className="px-2.5 py-1 rounded-md text-xs font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> REVIEW
          </span>
        );
    }
  };

  if (loading) {
    return <div className="text-slate-400 text-sm p-6">Evaluating compliance decisions...</div>;
  }

  const summary = data?.summary || {
    total_requirements: 0,
    mandatory_requirements: 0,
    optional_requirements: 0,
    pass_count: 0,
    fail_count: 0,
    review_count: 0,
    optional_pass_count: 0,
    optional_fail_count: 0,
    optional_review_count: 0
  };

  const requirements = data?.requirements || [];

  const filteredRequirements = requirements.filter(req => {
    if (filterScope === 'MANDATORY' && !req.is_mandatory) return false;
    if (filterScope === 'OPTIONAL' && req.is_mandatory) return false;
    if (filterState !== 'ALL' && req.decision !== filterState) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      
      {/* Notice Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/60 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              {getOverallBadge(data?.overall_decision || 'REVIEW')}
              <span className="text-xs font-mono px-2 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Type: {data?.decision_type || 'SYSTEM_DECISION'}
              </span>
            </div>
            <p className="text-sm text-slate-200 font-medium">
              {data?.reason || 'Compliance assessment system decision evaluated.'}
            </p>
            <div className="flex items-center gap-1.5 text-xs text-amber-400/90 font-medium pt-1">
              <Info className="w-3.5 h-3.5 shrink-0" />
              <span>System-generated assessment. Final procurement determination requires officer review (Phase 9).</span>
            </div>
          </div>

          <button
            onClick={handleEvaluateAll}
            disabled={evaluating}
            className="px-5 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs rounded-xl shadow-lg shadow-purple-500/20 disabled:opacity-50 transition-all flex items-center gap-2 shrink-0"
          >
            <RotateCw className={`w-4 h-4 ${evaluating ? 'animate-spin' : ''}`} />
            <span>{evaluating ? 'Evaluating...' : 'Evaluate All Requirements'}</span>
          </button>
        </div>

        {/* Summary Metric Counters */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-6 pt-5 border-t border-slate-800/80">
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-center">
            <div className="text-xs text-slate-400 font-medium mb-1">Total Reqs</div>
            <div className="text-lg font-black text-white">{summary.total_requirements}</div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800 text-center">
            <div className="text-xs text-slate-400 font-medium mb-1">Mandatory Reqs</div>
            <div className="text-lg font-black text-purple-400">{summary.mandatory_requirements}</div>
          </div>

          <div className="bg-emerald-950/30 p-3.5 rounded-xl border border-emerald-500/30 text-center">
            <div className="text-xs text-emerald-400 font-medium mb-1">Passed (PASS)</div>
            <div className="text-lg font-black text-emerald-300">{summary.pass_count}</div>
          </div>

          <div className="bg-rose-950/30 p-3.5 rounded-xl border border-rose-500/30 text-center">
            <div className="text-xs text-rose-400 font-medium mb-1">Failed (FAIL)</div>
            <div className="text-lg font-black text-rose-300">{summary.fail_count}</div>
          </div>

          <div className="bg-amber-950/30 p-3.5 rounded-xl border border-amber-500/30 text-center">
            <div className="text-xs text-amber-400 font-medium mb-1">Review Needed</div>
            <div className="text-lg font-black text-amber-300">{summary.review_count}</div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-300 text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          {error}
        </div>
      )}

      {/* Filter Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Scope:</span>
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <button
              onClick={() => setFilterScope('MANDATORY')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                filterScope === 'MANDATORY' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Mandatory ({summary.mandatory_requirements})
            </button>
            <button
              onClick={() => setFilterScope('OPTIONAL')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                filterScope === 'OPTIONAL' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Optional ({summary.optional_requirements})
            </button>
            <button
              onClick={() => setFilterScope('ALL')}
              className={`px-3 py-1 rounded-md font-medium transition ${
                filterScope === 'ALL' ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              All ({summary.total_requirements})
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Decision Filter:</span>
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            {(['ALL', 'PASS', 'FAIL', 'REVIEW'] as const).map(st => (
              <button
                key={st}
                onClick={() => setFilterState(st)}
                className={`px-3 py-1 rounded-md font-medium transition ${
                  filterState === st ? 'bg-purple-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Requirement Decisions List */}
      <div className="space-y-4">
        {filteredRequirements.length === 0 ? (
          <div className="text-center p-8 bg-slate-900 border border-slate-800 rounded-2xl text-slate-400 text-sm">
            No requirements match the selected filter criteria.
          </div>
        ) : (
          filteredRequirements.map(req => {
            const isExpanded = expandedReqId === req.requirement_id;
            return (
              <div
                key={req.requirement_id}
                className="bg-slate-900 border border-slate-800 rounded-2xl p-5 hover:border-slate-700/80 transition-all shadow-md space-y-4"
              >
                {/* Header Line */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-start gap-3">
                    <span className="px-2.5 py-1 rounded font-mono text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700 shrink-0">
                      {req.req_code}
                    </span>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">
                          {req.category}
                        </span>
                        {req.is_mandatory ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
                            MANDATORY
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                            OPTIONAL
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm font-bold text-white leading-snug">
                        {req.requirement_text}
                      </h4>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    {getReqBadge(req.decision)}
                    <button
                      onClick={() => toggleExpand(req.requirement_id)}
                      className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                {/* Deterministic Reason */}
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/90 text-xs text-slate-300 flex items-start gap-2">
                  <ShieldCheck className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <strong className="text-slate-200">System Decision Reason: </strong>
                    {req.reason}
                  </div>
                </div>

                {/* Expandable Traceability Details */}
                {isExpanded && (
                  <div className="pt-4 border-t border-slate-800/80 space-y-4 animate-fade-in">
                    
                    {/* Traceability Audit Trail */}
                    <div className="space-y-2">
                      <h5 className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5" /> Compliance Audit Traceability Chain:
                      </h5>

                      {/* Rule Evaluations */}
                      {req.rule_evaluations && req.rule_evaluations.length > 0 ? (
                        <div className="space-y-2">
                          {req.rule_evaluations.map((re: any, idx: number) => (
                            <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-xs space-y-1 font-mono">
                              <div className="flex justify-between items-center">
                                <span className="font-bold text-purple-300">Rule: {re.rule_code}</span>
                                <span className={`font-bold px-2 py-0.5 rounded text-[10px] ${
                                  re.evaluation_result === 'SATISFIED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                                }`}>
                                  {re.evaluation_result}
                                </span>
                              </div>
                              <div className="text-slate-400">
                                Detected: <strong className="text-white">{re.detected_value || 'N/A'}</strong> | Target: <strong className="text-white">{re.required_value || 'N/A'}</strong>
                              </div>
                              <div className="text-slate-400 italic">{re.explanation}</div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-xs text-slate-500 italic">No explicit rule evaluations recorded yet.</div>
                      )}

                      {/* Evidence Matches */}
                      {req.evidence_matches && req.evidence_matches.length > 0 && (
                        <div className="space-y-2 pt-2">
                          <h6 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                            Matched Document Evidence ({req.evidence_matches.length}):
                          </h6>
                          {req.evidence_matches.map((em: any, idx: number) => (
                            <div key={idx} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
                              <div className="space-y-1">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-slate-200">{em.document_name}</span>
                                  <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded text-[10px]">
                                    Page {em.page_number}
                                  </span>
                                  <span className="text-[10px] text-cyan-400">
                                    {(em.confidence_score * 100).toFixed(0)}% Match
                                  </span>
                                </div>
                                <p className="text-slate-400 italic line-clamp-2">"{em.evidence_text}"</p>
                              </div>

                              {onOpenDocumentPage && em.document_id && (
                                <button
                                  onClick={() => onOpenDocumentPage(em.document_id, em.page_number)}
                                  className="px-3 py-1.5 bg-purple-900/30 hover:bg-purple-900/50 text-purple-300 border border-purple-500/30 text-xs font-bold rounded-lg transition shrink-0 flex items-center gap-1.5"
                                >
                                  <ExternalLink className="w-3.5 h-3.5" /> View Page {em.page_number}
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Grounded AI Analysis Context */}
                    {req.ai_explanation && (
                      <div className="bg-slate-950/80 p-3.5 rounded-xl border border-purple-500/20 text-xs space-y-1">
                        <span className="font-bold text-purple-300 flex items-center gap-1.5">
                          <Brain className="w-3.5 h-3.5" /> Grounded AI Explanation (Phase 7):
                        </span>
                        <p className="text-slate-300 leading-relaxed font-sans">{req.ai_explanation}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
