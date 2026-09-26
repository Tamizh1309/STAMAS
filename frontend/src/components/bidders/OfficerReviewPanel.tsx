import React, { useState, useEffect } from 'react';
import type { BidderReviewSummaryResponse, RequirementReviewSummary, OfficerReviewAuditOut } from '../../types';
import {
  fetchBidderReviewSummary,
  confirmRequirementDecision,
  overrideRequirementDecision,
  finalizeBidderReview,
  reopenBidderReview,
  fetchDecisionAuditTrail
} from '../../services/api';

interface OfficerReviewPanelProps {
  tenderId: number;
  bidderId: number;
}

export const OfficerReviewPanel: React.FC<OfficerReviewPanelProps> = ({ tenderId, bidderId }) => {
  const [summary, setSummary] = useState<BidderReviewSummaryResponse | null>(null);
  const [audits, setAudits] = useState<OfficerReviewAuditOut[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Modal / Override State
  const [activeReq, setActiveReq] = useState<RequirementReviewSummary | null>(null);
  const [modalMode, setModalMode] = useState<'CONFIRM' | 'OVERRIDE' | 'REOPEN' | null>(null);
  
  // Form inputs
  const [officerComment, setOfficerComment] = useState<string>('');
  const [overrideDecision, setOverrideDecision] = useState<'PASS' | 'FAIL' | 'REVIEW'>('PASS');
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [reopenReason, setReopenReason] = useState<string>('');
  const [validationError, setValidationError] = useState<string | null>(null);

  // Expanded requirement IDs
  const [expandedReqs, setExpandedReqs] = useState<number[]>([]);

  const loadReviewData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchBidderReviewSummary(tenderId, bidderId);
      setSummary(res);

      const auditData = await fetchDecisionAuditTrail(tenderId, bidderId);
      setAudits(auditData);
    } catch (err: any) {
      setError(err.message || 'Failed to load officer review data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviewData();
  }, [tenderId, bidderId]);

  const toggleExpand = (id: number) => {
    setExpandedReqs(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleOpenConfirmModal = (req: RequirementReviewSummary) => {
    setActiveReq(req);
    setOfficerComment('');
    setValidationError(null);
    setModalMode('CONFIRM');
  };

  const handleOpenOverrideModal = (req: RequirementReviewSummary) => {
    setActiveReq(req);
    setOfficerComment('');
    // Default override choice to something different from system decision
    setOverrideDecision(req.system_decision === 'PASS' ? 'FAIL' : 'PASS');
    setOverrideReason('');
    setValidationError(null);
    setModalMode('OVERRIDE');
  };

  const handleOpenReopenModal = () => {
    setReopenReason('');
    setValidationError(null);
    setModalMode('REOPEN');
  };

  const handleConfirmSubmit = async () => {
    if (!activeReq) return;
    try {
      setLoading(true);
      await confirmRequirementDecision(tenderId, bidderId, activeReq.requirement_id, officerComment);
      setActionSuccess(`Successfully confirmed decision for ${activeReq.req_code}`);
      setModalMode(null);
      await loadReviewData();
    } catch (err: any) {
      setValidationError(err.message || 'Failed to confirm decision');
    } finally {
      setLoading(false);
    }
  };

  const handleOverrideSubmit = async () => {
    if (!activeReq) return;
    if (!overrideReason || overrideReason.trim().length < 10) {
      setValidationError('Override reason is mandatory and must be at least 10 characters long.');
      return;
    }

    try {
      setLoading(true);
      await overrideRequirementDecision(
        tenderId,
        bidderId,
        activeReq.requirement_id,
        overrideDecision,
        overrideReason,
        officerComment
      );
      setActionSuccess(`Successfully overridden decision for ${activeReq.req_code} to ${overrideDecision}`);
      setModalMode(null);
      await loadReviewData();
    } catch (err: any) {
      setValidationError(err.message || 'Failed to override decision');
    } finally {
      setLoading(false);
    }
  };

  const handleFinalizeAll = async () => {
    if (!window.confirm('Are you sure you want to finalize the entire officer compliance review for this bidder?')) return;
    try {
      setLoading(true);
      await finalizeBidderReview(tenderId, bidderId);
      setActionSuccess('All requirement reviews successfully finalized!');
      await loadReviewData();
    } catch (err: any) {
      setError(err.message || 'Failed to finalize review');
    } finally {
      setLoading(false);
    }
  };

  const handleReopenSubmit = async () => {
    if (!reopenReason || !reopenReason.trim()) {
      setValidationError('Reopen reason is required.');
      return;
    }
    try {
      setLoading(true);
      await reopenBidderReview(tenderId, bidderId, reopenReason);
      setActionSuccess('Review reopened successfully!');
      setModalMode(null);
      await loadReviewData();
    } catch (err: any) {
      setValidationError(err.message || 'Failed to reopen review');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400">
        <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Loading Officer Review & Human Decision Manager...</span>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="bg-rose-900/20 border border-rose-500/40 text-rose-300 p-6 rounded-xl my-4">
        <h3 className="text-lg font-semibold mb-2">Error Loading Review Workstation</h3>
        <p className="text-sm">{error || 'Review summary not available'}</p>
        <button onClick={loadReviewData} className="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-sm font-medium transition-colors">
          Retry Loading
        </button>
      </div>
    );
  }

  const filteredRequirements = summary.requirements.filter(req => {
    if (statusFilter === 'ALL') return true;
    if (statusFilter === 'CONFIRMED') return req.decision_type === 'CONFIRMED';
    if (statusFilter === 'OVERRIDDEN') return req.decision_type === 'OVERRIDDEN';
    if (statusFilter === 'PENDING') return req.review_status === 'PENDING';
    return true;
  });

  const getDecisionBadge = (decision: string, isOfficer: boolean = false) => {
    let bg = 'bg-slate-700/50 text-slate-300 border-slate-600';
    if (decision === 'PASS') bg = 'bg-emerald-950/60 text-emerald-400 border-emerald-500/40';
    if (decision === 'FAIL') bg = 'bg-rose-950/60 text-rose-400 border-rose-500/40';
    if (decision === 'REVIEW') bg = 'bg-amber-950/60 text-amber-400 border-amber-500/40';
    if (decision === 'PENDING') bg = 'bg-sky-950/60 text-sky-400 border-sky-500/40';

    return (
      <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${bg} flex items-center gap-1.5`}>
        <span className={`w-1.5 h-1.5 rounded-full ${decision === 'PASS' ? 'bg-emerald-400' : decision === 'FAIL' ? 'bg-rose-400' : decision === 'REVIEW' ? 'bg-amber-400' : 'bg-sky-400'}`} />
        {isOfficer ? `OFFICER: ${decision}` : `SYSTEM: ${decision}`}
      </span>
    );
  };

  return (
    <div className="space-y-6 text-slate-100">
      {/* Officer Identity & Notice Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-5 mb-5">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold tracking-tight text-white">Phase 9 — Officer Review & Human Decision Manager</h2>
              <span className="px-3 py-0.5 rounded-full text-xs font-semibold bg-indigo-950 text-indigo-300 border border-indigo-500/30">
                Human-in-the-Loop
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Evaluator: <strong className="text-slate-200">Procurement Evaluation Officer (OFFICER-001)</strong> | Senior Evaluation Officer
            </p>
          </div>

          <div className="flex items-center gap-3">
            {summary.review_status === 'FINALIZED' ? (
              <button
                onClick={handleOpenReopenModal}
                className="px-4 py-2 bg-amber-600/20 hover:bg-amber-600/30 text-amber-300 border border-amber-500/40 text-xs font-semibold rounded-xl transition-all"
              >
                Reopen Review
              </button>
            ) : (
              <button
                onClick={handleFinalizeAll}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs rounded-xl shadow-lg shadow-emerald-950/40 transition-all flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                Finalize Officer Assessment
              </button>
            )}
          </div>
        </div>

        {/* Dual Decision Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Phase 8 System Decision</span>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-lg font-bold text-white">{summary.system_overall_decision}</span>
              {getDecisionBadge(summary.system_overall_decision, false)}
            </div>
            <span className="text-[10px] text-slate-500 mt-1 block">Deterministic Compliance Output</span>
          </div>

          <div className="bg-slate-950/60 border border-indigo-900/40 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Final Officer Determination</span>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-lg font-bold text-indigo-300">{summary.final_overall_decision}</span>
              {getDecisionBadge(summary.final_overall_decision, true)}
            </div>
            <span className="text-[10px] text-slate-500 mt-1 block">Human Officer Authoritative Status</span>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Review Workstation Progress</span>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-lg font-bold text-white">{summary.reviewed_count} / {summary.total_requirements}</span>
              <span className="text-xs font-semibold text-slate-300 bg-slate-800 px-2 py-0.5 rounded">
                {Math.round((summary.reviewed_count / (summary.total_requirements || 1)) * 100)}% Complete
              </span>
            </div>
            <span className="text-[10px] text-slate-500 mt-1 block">{summary.pending_count} Pending Officer Confirmation</span>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-medium">Override Breakdown</span>
            <div className="mt-2 flex items-center gap-3">
              <div className="text-emerald-400 font-bold text-sm">{summary.confirmed_count} Confirmed</div>
              <div className="text-amber-400 font-bold text-sm">{summary.overridden_count} Overridden</div>
            </div>
            <span className="text-[10px] text-slate-500 mt-1 block">Audit trail preserves all actions</span>
          </div>
        </div>

        {/* Human-in-the-Loop Principle Banner */}
        <div className="bg-gradient-to-r from-indigo-950/50 via-slate-900 to-slate-950 border border-indigo-800/30 rounded-xl p-3.5 flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400 shrink-0">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457-.39-2.823-1.07-4" />
            </svg>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            <strong className="text-indigo-300 font-semibold">STAMAS Principle: </strong>
            "AI finds evidence $\rightarrow$ Rules evaluate $\rightarrow$ System proposes $\rightarrow$ Human Officer decides."
            Original Phase 8 system decisions are immutably preserved for audit accountability.
          </p>
        </div>
      </div>

      {actionSuccess && (
        <div className="bg-emerald-950/60 border border-emerald-500/40 text-emerald-300 px-4 py-3 rounded-xl text-xs flex justify-between items-center">
          <span>{actionSuccess}</span>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-white font-bold">&times;</button>
        </div>
      )}

      {/* Requirement List Header & Filter Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <span>Requirement Compliance Reviews</span>
          <span className="text-xs font-normal text-slate-400">({filteredRequirements.length} shown)</span>
        </h3>

        <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
          {['ALL', 'PENDING', 'CONFIRMED', 'OVERRIDDEN'].map(filter => (
            <button
              key={filter}
              onClick={() => setStatusFilter(filter)}
              className={`px-3 py-1.5 rounded-md font-medium transition-all ${statusFilter === filter ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'}`}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      {/* Requirement Cards Accordion */}
      <div className="space-y-4">
        {filteredRequirements.map(req => {
          const isExpanded = expandedReqs.includes(req.requirement_id);
          return (
            <div key={req.requirement_id} className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-all shadow-md">
              <div
                onClick={() => toggleExpand(req.requirement_id)}
                className="p-4 cursor-pointer flex flex-col md:flex-row items-start md:items-center justify-between gap-4 hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="px-2.5 py-1 bg-slate-800 text-slate-300 text-xs font-mono font-semibold rounded-md border border-slate-700 shrink-0">
                    {req.req_code}
                  </span>
                  <div>
                    <h4 className="text-sm font-semibold text-white leading-snug">{req.text}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${req.is_mandatory ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30' : 'bg-slate-800 text-slate-400'}`}>
                        {req.is_mandatory ? 'MANDATORY' : 'OPTIONAL'}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">• Category: {req.category}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end md:self-auto">
                  {getDecisionBadge(req.system_decision, false)}
                  {getDecisionBadge(req.effective_decision, true)}

                  {req.decision_type === 'CONFIRMED' && (
                    <span className="text-[10px] bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30 font-semibold">CONFIRMED</span>
                  )}
                  {req.decision_type === 'OVERRIDDEN' && (
                    <span className="text-[10px] bg-amber-950 text-amber-400 px-2 py-0.5 rounded border border-amber-500/30 font-semibold">OVERRIDDEN</span>
                  )}

                  <svg className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {/* Expanded Detail Workspace */}
              {isExpanded && (
                <div className="border-t border-slate-800 p-5 bg-slate-950/50 space-y-5">
                  {/* Action Controls Header */}
                  <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-xs text-slate-300">
                      <strong className="text-white">Officer Action Station:</strong> Review evidence chain and select authoritative decision.
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleOpenConfirmModal(req)}
                        className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                        </svg>
                        Confirm System ({req.system_decision})
                      </button>

                      <button
                        onClick={() => handleOpenOverrideModal(req)}
                        className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                        Override System Decision
                      </button>
                    </div>
                  </div>

                  {/* System Decision vs Officer Override Card */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl">
                      <span className="text-xs font-semibold text-slate-400 block mb-1">Phase 8 System Decision & Reason</span>
                      <div className="flex items-center gap-2 mb-2">
                        {getDecisionBadge(req.system_decision, false)}
                      </div>
                      <p className="text-xs text-slate-300 bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 font-mono">
                        {req.system_reason}
                      </p>
                    </div>

                    <div className="bg-slate-900 border border-indigo-900/40 p-3.5 rounded-xl">
                      <span className="text-xs font-semibold text-indigo-300 block mb-1">Officer Review Record</span>
                      {req.officer_decision ? (
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            {getDecisionBadge(req.officer_decision.final_decision, true)}
                            <span className="text-[10px] text-slate-400 font-mono">
                              By {req.officer_decision.officer_name} ({req.officer_decision.officer_role})
                            </span>
                          </div>
                          {req.officer_decision.override_reason && (
                            <div className="text-xs text-amber-300 bg-amber-950/30 p-2 rounded border border-amber-500/30">
                              <strong>Override Reason: </strong>{req.officer_decision.override_reason}
                            </div>
                          )}
                          {req.officer_decision.officer_comment && (
                            <div className="text-xs text-slate-300 bg-slate-950 p-2 rounded border border-slate-800">
                              <strong>Comment: </strong>{req.officer_decision.officer_comment}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-xs text-slate-400 italic bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                          Pending officer confirmation or override.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Evidence Traceability & Rule Chain */}
                  <div className="space-y-3">
                    <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">Full Evidence & Rule Traceability</h5>

                    {/* Rules */}
                    {req.rule_evaluations.length > 0 && (
                      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2">
                        <span className="text-xs font-semibold text-slate-400">Phase 6 Rule Evaluation</span>
                        {req.rule_evaluations.map((rev: any, idx: number) => (
                          <div key={idx} className="bg-slate-950 p-2.5 rounded-lg text-xs space-y-1 font-mono">
                            <div className="flex justify-between text-slate-300">
                              <span>Rule Code: {rev.rule_code} [{rev.rule_type}]</span>
                              <span className={`font-bold ${rev.evaluation_result === 'SATISFIED' ? 'text-emerald-400' : 'text-amber-400'}`}>{rev.evaluation_result}</span>
                            </div>
                            <div className="text-slate-400">Comparison: Extracted '{rev.extracted_value}' {rev.operator} Required '{rev.required_value}'</div>
                            <div className="text-slate-500">{rev.explanation}</div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Evidence Source */}
                    {req.evidence_matches.length > 0 ? (
                      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 space-y-2">
                        <span className="text-xs font-semibold text-slate-400">Phase 5 Document Evidence Citation</span>
                        {req.evidence_matches.map((ev: any, idx: number) => (
                          <div key={idx} className="bg-slate-950 p-2.5 rounded-lg text-xs space-y-1">
                            <div className="flex justify-between items-center text-blue-400 font-semibold">
                              <span className="flex items-center gap-1.5">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                </svg>
                                {ev.document_filename} (Page {ev.page_number})
                              </span>
                              <span className="text-[10px] text-slate-400">Confidence: {Math.round(ev.confidence_score * 100)}% ({ev.matching_method})</span>
                            </div>
                            <p className="text-slate-300 italic bg-slate-900/80 p-2 rounded border border-slate-800/80">"{ev.evidence_text}"</p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-amber-400/90 bg-amber-950/30 p-3 rounded-xl border border-amber-500/30">
                        No direct Phase 5 evidence match found for this requirement.
                      </div>
                    )}

                    {/* Grounded AI Explanation */}
                    {req.ai_explanation && (
                      <div className="bg-indigo-950/30 border border-indigo-800/40 rounded-xl p-3.5 space-y-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-indigo-300">Phase 7 Grounded AI Evidence Explanation</span>
                          <span className="text-[10px] bg-indigo-900 text-indigo-200 px-2 py-0.5 rounded font-mono">ADVISORY ONLY</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
                          {req.ai_explanation}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Immutable Audit Trail Timeline */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <svg className="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Immutable Officer Action Audit Trail
        </h3>

        {audits.length === 0 ? (
          <p className="text-xs text-slate-500 italic">No audit records logged yet.</p>
        ) : (
          <div className="relative border-l border-slate-800 ml-4 space-y-4">
            {audits.map(audit => (
              <div key={audit.id} className="ml-6 relative group">
                <div className="absolute -left-[31px] top-1 w-2.5 h-2.5 rounded-full bg-indigo-500 border-2 border-slate-900" />
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-300">{audit.action}</span>
                    <span className="text-[10px] text-slate-500 font-mono">{audit.timestamp ? new Date(audit.timestamp).toLocaleString() : ''}</span>
                  </div>
                  <div className="text-slate-400">
                    By <strong className="text-slate-200">{audit.officer_name}</strong> ({audit.officer_role})
                  </div>
                  {audit.previous_final_decision && (
                    <div className="text-slate-300 font-mono">
                      Transition: {audit.previous_final_decision} &rarr; <strong className="text-emerald-400">{audit.new_final_decision}</strong> [{audit.decision_type}]
                    </div>
                  )}
                  {audit.reason && (
                    <div className="text-amber-300 bg-amber-950/20 p-2 rounded border border-amber-500/20 mt-1">
                      <strong>Reason: </strong>{audit.reason}
                    </div>
                  )}
                  {audit.comment && (
                    <div className="text-slate-400 italic">"{audit.comment}"</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirmation & Override Modals */}
      {modalMode && activeReq && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white">
                {modalMode === 'CONFIRM' ? 'Confirm System Decision' : 'Override System Decision'}
              </h3>
              <button onClick={() => setModalMode(null)} className="text-slate-400 hover:text-white font-bold">&times;</button>
            </div>

            <div className="text-xs space-y-2 bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div><strong className="text-slate-300">Requirement:</strong> {activeReq.req_code} — {activeReq.text}</div>
              <div><strong className="text-slate-300">Phase 8 System Decision:</strong> <span className="font-bold text-amber-400">{activeReq.system_decision}</span></div>
            </div>

            {validationError && (
              <div className="text-xs text-rose-300 bg-rose-950/50 p-3 rounded-lg border border-rose-500/40">
                {validationError}
              </div>
            )}

            {modalMode === 'CONFIRM' && (
              <div className="space-y-3">
                <p className="text-xs text-slate-300">
                  You are confirming the system-generated <strong className="text-emerald-400">{activeReq.system_decision}</strong> decision as your final officer determination.
                </p>
                <div>
                  <label className="text-xs font-medium text-slate-400 block mb-1">Optional Officer Comment</label>
                  <textarea
                    value={officerComment}
                    onChange={e => setOfficerComment(e.target.value)}
                    placeholder="Enter review notes or supporting remarks..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                    rows={3}
                  />
                </div>
              </div>
            )}

            {modalMode === 'OVERRIDE' && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-medium text-slate-400 block mb-1">New Authoritative Final Decision</label>
                  <select
                    value={overrideDecision}
                    onChange={e => setOverrideDecision(e.target.value as any)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="PASS">PASS</option>
                    <option value="FAIL">FAIL</option>
                    <option value="REVIEW">REVIEW</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-medium text-amber-400 block mb-1">Mandatory Override Reason * (min 10 chars)</label>
                  <textarea
                    value={overrideReason}
                    onChange={e => setOverrideReason(e.target.value)}
                    placeholder="Provide explicit, verifiable justification for overriding system decision..."
                    className="w-full bg-slate-950 border border-amber-500/40 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-amber-500"
                    rows={3}
                  />
                </div>

                <div>
                  <label className="text-xs font-medium text-slate-400 block mb-1">Optional Officer Comment</label>
                  <input
                    type="text"
                    value={officerComment}
                    onChange={e => setOfficerComment(e.target.value)}
                    placeholder="Additional comments..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button onClick={() => setModalMode(null)} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 rounded-lg transition-colors">
                Cancel
              </button>
              {modalMode === 'CONFIRM' ? (
                <button onClick={handleConfirmSubmit} className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-xs font-semibold text-white rounded-lg transition-colors">
                  Submit Confirmation
                </button>
              ) : (
                <button onClick={handleOverrideSubmit} className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white rounded-lg transition-colors">
                  Submit Override & Record Audit
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {modalMode === 'REOPEN' && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">Reopen Finalized Assessment</h3>
            {validationError && (
              <div className="text-xs text-rose-300 bg-rose-950/50 p-2.5 rounded-lg border border-rose-500/40">
                {validationError}
              </div>
            )}
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1">Reason for Reopening *</label>
              <textarea
                value={reopenReason}
                onChange={e => setReopenReason(e.target.value)}
                placeholder="Enter justification for reopening finalized review..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                rows={3}
              />
            </div>
            <div className="flex justify-end gap-3 pt-2">
              <button onClick={() => setModalMode(null)} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 rounded-lg transition-colors">
                Cancel
              </button>
              <button onClick={handleReopenSubmit} className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white rounded-lg transition-colors">
                Confirm Reopen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
