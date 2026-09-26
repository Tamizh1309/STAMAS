import React, { useState, useEffect } from 'react';
import {
  CheckCircle, XCircle, AlertTriangle, HelpCircle, Layers,
  RefreshCw, Eye, Sparkles, Filter, ChevronRight, FileText, Info
} from 'lucide-react';
import type { Bidder, Requirement, RuleEvaluation, RuleEvaluationSummary } from '../../types';
import {
  fetchRequirements,
  fetchBidderRuleSummary,
  fetchBidderRuleEvaluations,
  evaluateComplianceRules
} from '../../services/api';

interface RuleEnginePanelProps {
  tenderId: number;
  bidder: Bidder;
  onOpenDocumentPage: (documentId: number, pageNumber: number) => void;
}

export const RuleEnginePanel: React.FC<RuleEnginePanelProps> = ({
  tenderId,
  bidder,
  onOpenDocumentPage
}) => {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [evaluations, setEvaluations] = useState<RuleEvaluation[]>([]);
  const [summary, setSummary] = useState<RuleEvaluationSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluatingLoading, setEvaluatingLoading] = useState(false);
  const [evaluatingReqId, setEvaluatingReqId] = useState<number | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('ALL');

  const loadData = async () => {
    try {
      setLoading(true);
      const [reqs, evals] = await Promise.all([
        fetchRequirements(tenderId),
        fetchBidderRuleEvaluations(bidder.id, tenderId)
      ]);
      setRequirements(reqs);
      setEvaluations(evals);

      try {
        const sumData = await fetchBidderRuleSummary(bidder.id, tenderId);
        setSummary(sumData);
      } catch {
        setSummary(null);
      }
    } catch (err) {
      console.error('Failed to load compliance rule data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [tenderId, bidder.id]);

  const handleRunBatchEvaluation = async () => {
    try {
      setEvaluatingLoading(true);
      await evaluateComplianceRules(tenderId, bidder.id);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to evaluate compliance rules');
    } finally {
      setEvaluatingLoading(false);
    }
  };

  const handleEvaluateSingle = async (reqId: number) => {
    try {
      setEvaluatingReqId(reqId);
      await evaluateComplianceRules(tenderId, bidder.id, reqId);
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to evaluate rules for requirement');
    } finally {
      setEvaluatingReqId(null);
    }
  };

  const getResultBadge = (result: RuleEvaluation['evaluation_result']) => {
    switch (result) {
      case 'SATISFIED':
        return {
          bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
          icon: <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />,
          label: 'SATISFIED'
        };
      case 'NOT_SATISFIED':
        return {
          bg: 'bg-red-500/10 text-red-400 border-red-500/30',
          icon: <XCircle className="w-3.5 h-3.5 text-red-400" />,
          label: 'NOT SATISFIED'
        };
      case 'CONFLICTING_EVIDENCE':
        return {
          bg: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-purple-400" />,
          label: 'CONFLICTING EVIDENCE'
        };
      case 'INDETERMINATE':
        return {
          bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
          icon: <HelpCircle className="w-3.5 h-3.5 text-amber-400" />,
          label: 'INDETERMINATE'
        };
      case 'INSUFFICIENT_EVIDENCE':
      default:
        return {
          bg: 'bg-slate-800 text-slate-400 border-slate-700',
          icon: <HelpCircle className="w-3.5 h-3.5 text-slate-400" />,
          label: 'INSUFFICIENT EVIDENCE'
        };
    }
  };

  const filteredRequirements = requirements.filter(req => {
    if (activeFilter === 'ALL') return true;
    const reqEvals = evaluations.filter(e => e.requirement_id === req.id);
    if (activeFilter === 'INSUFFICIENT_EVIDENCE') {
      return reqEvals.length === 0 || reqEvals.every(e => e.evaluation_result === 'INSUFFICIENT_EVIDENCE');
    }
    return reqEvals.some(e => e.evaluation_result === activeFilter);
  });

  return (
    <div className="space-y-6 animate-fade-in">
      
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-lg font-extrabold text-white">Compliance Rule Engine</h3>
            <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
              PHASE 6 — DETERMINISTIC RULES
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Evaluates requirement constraints against Phase 5 evidence matches using explicit deterministic rule logic. Outputs transparent, audit-ready explanations.
          </p>
        </div>

        <button
          onClick={handleRunBatchEvaluation}
          disabled={evaluatingLoading || requirements.length === 0}
          className="flex items-center space-x-2 px-5 py-3 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 shadow-lg shadow-purple-500/25 transition disabled:opacity-50 shrink-0"
        >
          {evaluatingLoading ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin text-purple-200" />
              <span>Evaluating Rules...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4 text-purple-200" />
              <span>Evaluate All Rules</span>
            </>
          )}
        </button>
      </div>

      {/* Summary Statistics Dashboard */}
      {summary && (
        <div className="space-y-2">
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-3">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Rules Evaluated</div>
              <div className="text-2xl font-extrabold text-white mt-1">{summary.rules_evaluated}</div>
            </div>
            <div className="bg-slate-900 border border-emerald-900/40 rounded-xl p-4">
              <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">Satisfied</div>
              <div className="text-2xl font-extrabold text-emerald-400 mt-1">{summary.satisfied_count}</div>
            </div>
            <div className="bg-slate-900 border border-red-900/40 rounded-xl p-4">
              <div className="text-[10px] font-bold text-red-400 uppercase tracking-wider">Not Satisfied</div>
              <div className="text-2xl font-extrabold text-red-400 mt-1">{summary.not_satisfied_count}</div>
            </div>
            <div className="bg-slate-900 border border-amber-900/40 rounded-xl p-4">
              <div className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Indeterminate</div>
              <div className="text-2xl font-extrabold text-amber-400 mt-1">{summary.indeterminate_count}</div>
            </div>
            <div className="bg-slate-900 border border-purple-900/40 rounded-xl p-4">
              <div className="text-[10px] font-bold text-purple-400 uppercase tracking-wider">Conflicting</div>
              <div className="text-2xl font-extrabold text-purple-400 mt-1">{summary.conflicting_evidence_count}</div>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Insufficient Evidence</div>
              <div className="text-2xl font-extrabold text-slate-400 mt-1">{summary.insufficient_evidence_count}</div>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-[11px] text-slate-400 italic bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
            <Info className="w-3.5 h-3.5 text-purple-400 shrink-0" />
            <span>
              Note: Rule evaluation results reflect requirement constraint checks. Final procurement PASS / FAIL / REVIEW decisions belong to Phase 8.
            </span>
          </div>
        </div>
      )}

      {/* Status Filters */}
      <div className="flex items-center justify-between bg-slate-900/60 p-2 rounded-xl border border-slate-800">
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          <Filter className="w-4 h-4 text-purple-400 ml-2" />
          <span>Filter Rule Result:</span>
          {['ALL', 'SATISFIED', 'NOT_SATISFIED', 'INDETERMINATE', 'CONFLICTING_EVIDENCE', 'INSUFFICIENT_EVIDENCE'].map(st => (
            <button
              key={st}
              onClick={() => setActiveFilter(st)}
              className={`px-3 py-1 rounded-lg text-[11px] font-semibold transition ${
                activeFilter === st
                  ? 'bg-purple-600 text-white font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Requirements Rule Evaluations List */}
      {loading ? (
        <div className="text-center py-12 text-slate-400 text-sm">Loading rule evaluations...</div>
      ) : requirements.length === 0 ? (
        <div className="text-center py-12 bg-slate-900 border border-slate-800 rounded-2xl text-slate-400 text-sm">
          No requirements found for this tender.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredRequirements.map(req => {
            const evalsForReq = evaluations.filter(e => e.requirement_id === req.id);
            const isSingleEvaluating = evaluatingReqId === req.id;

            return (
              <div key={req.id} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-md">
                
                {/* Requirement Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-purple-400 bg-purple-950/80 px-2.5 py-1 rounded border border-purple-800/40">
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
                    onClick={() => handleEvaluateSingle(req.id)}
                    disabled={isSingleEvaluating}
                    className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-purple-300 bg-purple-950/60 hover:bg-purple-900/80 border border-purple-800/50 transition self-start md:self-auto shrink-0"
                  >
                    {isSingleEvaluating ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Layers className="w-3.5 h-3.5" />
                    )}
                    <span>{isSingleEvaluating ? 'Evaluating...' : 'Evaluate Rule'}</span>
                  </button>
                </div>

                {/* Rule Evaluation Results for Requirement */}
                {evalsForReq.length === 0 ? (
                  <div className="text-xs text-slate-400 italic bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
                    No rules evaluated yet for this requirement. Click "Evaluate Rule" to run deterministic rule checks.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {evalsForReq.map(ev => {
                      const badge = getResultBadge(ev.evaluation_result as any);

                      return (
                        <div
                          key={ev.id}
                          className="bg-slate-950 border border-slate-800/90 rounded-xl p-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:border-slate-700 transition"
                        >
                          <div className="space-y-2 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[10px] font-bold border ${badge.bg}`}>
                                {badge.icon}
                                <span>{badge.label}</span>
                              </span>

                              {ev.extracted_value && (
                                <span className="text-xs font-mono font-bold text-purple-300 bg-slate-900 px-2.5 py-0.5 rounded border border-slate-800">
                                  Detected: {ev.extracted_value} {ev.extracted_unit || ''}
                                </span>
                              )}

                              {ev.required_value && (
                                <span className="text-xs font-mono text-slate-400 bg-slate-900 px-2.5 py-0.5 rounded border border-slate-800">
                                  Required: {ev.operator || '='} {ev.required_value}
                                </span>
                              )}

                              {ev.document_name && (
                                <span className="text-xs font-semibold text-slate-300 flex items-center space-x-1">
                                  <FileText className="w-3.5 h-3.5 text-blue-400 inline" />
                                  <span>{ev.document_name} — Page {ev.page_number || 1}</span>
                                </span>
                              )}
                            </div>

                            {/* Human Readable Explanation */}
                            <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 leading-relaxed">
                              <strong className="text-purple-400 font-bold">Rule Explanation:</strong> {ev.explanation}
                            </div>

                            {/* Evidence Citation Snippet */}
                            {ev.evidence_text && (
                              <div className="text-[11px] font-mono text-slate-400 bg-slate-950/60 p-2 rounded border border-slate-900 truncate max-w-2xl">
                                Source Evidence: "{ev.evidence_text}"
                              </div>
                            )}
                          </div>

                          {/* View Source Page Action */}
                          {ev.document_id && ev.page_number && (
                            <button
                              onClick={() => onOpenDocumentPage(ev.document_id!, ev.page_number!)}
                              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-bold text-white bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 transition shrink-0 self-end md:self-center"
                            >
                              <Eye className="w-3.5 h-3.5 text-blue-400" />
                              <span>View Evidence</span>
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
    </div>
  );
};
