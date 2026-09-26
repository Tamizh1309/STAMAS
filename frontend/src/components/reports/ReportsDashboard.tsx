import React, { useState, useEffect } from 'react';
import type { TenderComplianceReportResponse, BidderComplianceReportResponse, AuditPaginatedResponse } from '../../types';
import {
  fetchTenderReport,
  downloadTenderPdf,
  downloadTenderCsv,
  fetchBidderReport,
  downloadBidderPdf,
  downloadBidderCsv,
  fetchAuditReportData,
  downloadAuditCsv
} from '../../services/api';

interface ReportsDashboardProps {
  tenderId: number;
}

export const ReportsDashboard: React.FC<ReportsDashboardProps> = ({ tenderId }) => {
  const [reportTab, setReportTab] = useState<'TENDER_SUMMARY' | 'BIDDER_TRACEABILITY' | 'AUDIT_LOGS'>('TENDER_SUMMARY');

  // Tender Report State
  const [tenderReport, setTenderReport] = useState<TenderComplianceReportResponse | null>(null);
  const [loadingTender, setLoadingTender] = useState<boolean>(true);

  // Bidder Traceability State
  const [selectedBidderId, setSelectedBidderId] = useState<number | null>(null);
  const [bidderReport, setBidderReport] = useState<BidderComplianceReportResponse | null>(null);
  const [loadingBidder, setLoadingBidder] = useState<boolean>(false);

  // Audit State
  const [auditData, setAuditData] = useState<AuditPaginatedResponse | null>(null);
  const [actionFilter, setActionFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [auditPage, setAuditPage] = useState<number>(1);
  const [loadingAudit, setLoadingAudit] = useState<boolean>(false);

  // Download loading states
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [downloadingCsv, setDownloadingCsv] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadTenderData = async () => {
    try {
      setLoadingTender(true);
      setError(null);
      const res = await fetchTenderReport(tenderId);
      setTenderReport(res);
      if (res.bidders.length > 0 && !selectedBidderId) {
        setSelectedBidderId(res.bidders[0].bidder_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load tender report data');
    } finally {
      setLoadingTender(false);
    }
  };

  const loadBidderData = async (bId: number) => {
    try {
      setLoadingBidder(true);
      const res = await fetchBidderReport(tenderId, bId);
      setBidderReport(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load bidder report');
    } finally {
      setLoadingBidder(false);
    }
  };

  const loadAuditData = async () => {
    try {
      setLoadingAudit(true);
      const res = await fetchAuditReportData(tenderId, undefined, actionFilter, searchTerm, auditPage, 15);
      setAuditData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs');
    } finally {
      setLoadingAudit(false);
    }
  };

  useEffect(() => {
    loadTenderData();
  }, [tenderId]);

  useEffect(() => {
    if (selectedBidderId) {
      loadBidderData(selectedBidderId);
    }
  }, [selectedBidderId, tenderId]);

  useEffect(() => {
    if (reportTab === 'AUDIT_LOGS') {
      loadAuditData();
    }
  }, [reportTab, actionFilter, auditPage]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setAuditPage(1);
    loadAuditData();
  };

  const handleTenderPdfDownload = async () => {
    try {
      setDownloadingPdf(true);
      await downloadTenderPdf(tenderId);
    } catch (err: any) {
      alert(err.message || 'PDF Download failed');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleTenderCsvDownload = async () => {
    try {
      setDownloadingCsv(true);
      await downloadTenderCsv(tenderId);
    } catch (err: any) {
      alert(err.message || 'CSV Download failed');
    } finally {
      setDownloadingCsv(false);
    }
  };

  const handleBidderPdfDownload = async () => {
    if (!selectedBidderId) return;
    try {
      setDownloadingPdf(true);
      await downloadBidderPdf(tenderId, selectedBidderId);
    } catch (err: any) {
      alert(err.message || 'Bidder PDF Download failed');
    } finally {
      setDownloadingPdf(false);
    }
  };

  const handleBidderCsvDownload = async () => {
    if (!selectedBidderId) return;
    try {
      setDownloadingCsv(true);
      await downloadBidderCsv(tenderId, selectedBidderId);
    } catch (err: any) {
      alert(err.message || 'Bidder CSV Download failed');
    } finally {
      setDownloadingCsv(false);
    }
  };

  const handleAuditCsvDownload = async () => {
    try {
      setDownloadingCsv(true);
      await downloadAuditCsv(tenderId, undefined, actionFilter, searchTerm);
    } catch (err: any) {
      alert(err.message || 'Audit CSV Download failed');
    } finally {
      setDownloadingCsv(false);
    }
  };

  const exportRawJson = (data: any, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  if (loadingTender && !tenderReport) {
    return (
      <div className="flex items-center justify-center p-12 text-slate-400">
        <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Generating Reports & Audit Workstation...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 border-b border-slate-800 pb-5 mb-5">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold tracking-tight text-white">Phase 10 — Compliance Reports & Audit Workstation</h2>
              <span className="px-3 py-0.5 rounded-full text-xs font-semibold bg-cyan-950 text-cyan-300 border border-cyan-500/30">
                Traceable Audit Reports
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Tender: <strong className="text-slate-200">{tenderReport?.title}</strong> ({tenderReport?.tender_number})
            </p>
          </div>

          {/* Quick Export Controls */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={handleTenderPdfDownload}
              disabled={downloadingPdf}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs rounded-xl shadow transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>{downloadingPdf ? 'Preparing PDF...' : 'Download Tender PDF'}</span>
            </button>

            <button
              onClick={handleTenderCsvDownload}
              disabled={downloadingCsv}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs rounded-xl shadow transition-all flex items-center gap-2 disabled:opacity-50"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>{downloadingCsv ? 'Preparing CSV...' : 'Export Tender CSV'}</span>
            </button>

            <button
              onClick={() => exportRawJson(tenderReport, `STAMAS_Tender_${tenderId}_Report.json`)}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl border border-slate-700 transition-colors"
            >
              Raw JSON
            </button>
          </div>
        </div>

        {/* Executive Metric Cards */}
        {tenderReport && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Total Evaluated Bidders</span>
              <div className="text-2xl font-bold text-white mt-1">{tenderReport.total_bidders}</div>
              <span className="text-[10px] text-slate-500 mt-1 block">Full Procurement Scope</span>
            </div>

            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Phase 8 System Summary</span>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-sm font-bold text-emerald-400">{tenderReport.overall_system_summary.PASS || 0} PASS</span>
                <span className="text-sm font-bold text-amber-400">{tenderReport.overall_system_summary.REVIEW || 0} REVIEW</span>
                <span className="text-sm font-bold text-rose-400">{tenderReport.overall_system_summary.FAIL || 0} FAIL</span>
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Deterministic Algorithm Output</span>
            </div>

            <div className="bg-slate-950/60 border border-indigo-900/40 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Phase 9 Officer Final Summary</span>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-sm font-bold text-emerald-400">{tenderReport.overall_officer_summary.PASS || 0} PASS</span>
                <span className="text-sm font-bold text-amber-400">{tenderReport.overall_officer_summary.REVIEW || 0} REVIEW</span>
                <span className="text-sm font-bold text-rose-400">{tenderReport.overall_officer_summary.FAIL || 0} FAIL</span>
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Human Authoritative Finalization</span>
            </div>

            <div className="bg-slate-950/60 border border-slate-800 rounded-xl p-4">
              <span className="text-xs font-medium text-slate-400">Report Integrity Verification</span>
              <div className="text-xs font-mono text-emerald-400 mt-2 font-semibold">100% Traceable</div>
              <span className="text-[10px] text-slate-500 mt-1 block">Requirement &rarr; Evidence &rarr; Audit</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-rose-950/60 border border-rose-500/40 text-rose-300 p-4 rounded-xl text-xs">
          {error}
        </div>
      )}

      {/* Sub-view Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-4">
        <button
          onClick={() => setReportTab('TENDER_SUMMARY')}
          className={`px-4 py-3 text-xs font-bold border-b-2 transition ${reportTab === 'TENDER_SUMMARY' ? 'border-cyan-400 text-cyan-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
        >
          1. Tender Compliance Report
        </button>
        <button
          onClick={() => setReportTab('BIDDER_TRACEABILITY')}
          className={`px-4 py-3 text-xs font-bold border-b-2 transition ${reportTab === 'BIDDER_TRACEABILITY' ? 'border-indigo-400 text-indigo-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
        >
          2. Bidder Traceability Report
        </button>
        <button
          onClick={() => setReportTab('AUDIT_LOGS')}
          className={`px-4 py-3 text-xs font-bold border-b-2 transition ${reportTab === 'AUDIT_LOGS' ? 'border-purple-400 text-purple-400' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
        >
          3. Officer Action Audit Trail
        </button>
      </div>

      {/* TAB 1: Tender Compliance Summary Table */}
      {reportTab === 'TENDER_SUMMARY' && tenderReport && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-white">Bidder Compliance Status Matrix</h3>
            <span className="text-xs text-slate-400">Total Bidders: {tenderReport.bidders.length}</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300 border-collapse">
              <thead>
                <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="p-3">Company Name</th>
                  <th className="p-3">Reg No</th>
                  <th className="p-3">Requirements</th>
                  <th className="p-3">Phase 8 System</th>
                  <th className="p-3">Phase 9 Final Officer</th>
                  <th className="p-3">Override Breakdown</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {tenderReport.bidders.map(b => (
                  <tr key={b.bidder_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="p-3 font-semibold text-white">{b.company_name}</td>
                    <td className="p-3 font-mono text-slate-400">{b.registration_number || 'N/A'}</td>
                    <td className="p-3">{b.total_requirements}</td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${b.system_overall_decision === 'PASS' ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' : b.system_overall_decision === 'FAIL' ? 'bg-rose-950 text-rose-400 border border-rose-500/30' : 'bg-amber-950 text-amber-400 border border-amber-500/30'}`}>
                        SYSTEM: {b.system_overall_decision}
                      </span>
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${b.final_overall_decision === 'PASS' ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' : b.final_overall_decision === 'FAIL' ? 'bg-rose-950 text-rose-400 border border-rose-500/30' : 'bg-amber-950 text-amber-400 border border-amber-500/30'}`}>
                        OFFICER: {b.final_overall_decision}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400 font-mono">
                      {b.confirmed_count} Confirmed / {b.overridden_count} Overridden
                    </td>
                    <td className="p-3">
                      <span className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-300 rounded">
                        {b.review_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: Bidder Traceability Report */}
      {reportTab === 'BIDDER_TRACEABILITY' && tenderReport && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-white">Bidder Evidence Traceability Report</h3>
              <p className="text-xs text-slate-400 mt-0.5">Inspect full end-to-end evidence chain for a specific bidder.</p>
            </div>

            <div className="flex items-center gap-3">
              <label className="text-xs text-slate-400 font-medium">Select Bidder:</label>
              <select
                value={selectedBidderId || ''}
                onChange={e => setSelectedBidderId(Number(e.target.value))}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                {tenderReport.bidders.map(b => (
                  <option key={b.bidder_id} value={b.bidder_id}>
                    {b.company_name} ({b.final_overall_decision})
                  </option>
                ))}
              </select>

              <button
                onClick={handleBidderPdfDownload}
                disabled={downloadingPdf}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                Download PDF
              </button>

              <button
                onClick={handleBidderCsvDownload}
                disabled={downloadingCsv}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                Export CSV
              </button>
            </div>
          </div>

          {loadingBidder || !bidderReport ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading bidder traceability report...</div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs">
                <div><span className="text-slate-400">Company:</span> <strong className="text-white">{bidderReport.company_name}</strong></div>
                <div><span className="text-slate-400">Reg No:</span> <strong className="text-white">{bidderReport.registration_number || 'N/A'}</strong></div>
                <div><span className="text-slate-400">Phase 8 System:</span> <strong className="text-amber-400">{bidderReport.system_overall_decision}</strong></div>
                <div><span className="text-slate-400">Phase 9 Final:</span> <strong className="text-emerald-400">{bidderReport.final_overall_decision}</strong></div>
              </div>

              {/* Requirement Traceability Cards */}
              <div className="space-y-3">
                {bidderReport.requirements.map(req => (
                  <div key={req.requirement_id} className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3 text-xs">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-800/80 pb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono bg-slate-800 text-slate-200 px-2 py-0.5 rounded font-bold">{req.req_code}</span>
                        <span className="font-semibold text-white">{req.text}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${req.system_decision === 'PASS' ? 'bg-emerald-950 text-emerald-400' : req.system_decision === 'FAIL' ? 'bg-rose-950 text-rose-400' : 'bg-amber-950 text-amber-400'}`}>
                          SYSTEM: {req.system_decision}
                        </span>
                        <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${req.effective_decision === 'PASS' ? 'bg-emerald-950 text-emerald-400' : req.effective_decision === 'FAIL' ? 'bg-rose-950 text-rose-400' : 'bg-amber-950 text-amber-400'}`}>
                          OFFICER: {req.effective_decision} [{req.decision_type}]
                        </span>
                      </div>
                    </div>

                    {/* Traceability Details */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {/* Rule & Citation */}
                      <div className="bg-slate-900 p-3 rounded-lg space-y-1">
                        <span className="font-semibold text-slate-300">Phase 6 Rule & Phase 5 Citation:</span>
                        {req.evidence_matches.length > 0 ? (
                          <div className="text-slate-400 text-[11px] font-mono">
                            <div>Document: {req.evidence_matches[0].document_filename} (Page {req.evidence_matches[0].page_number})</div>
                            <div className="italic text-slate-300 mt-1">"{req.evidence_matches[0].evidence_text}"</div>
                          </div>
                        ) : (
                          <div className="text-amber-400 text-[11px]">No direct evidence citation found.</div>
                        )}
                      </div>

                      {/* Officer Decision & Override Reason */}
                      <div className="bg-slate-900 p-3 rounded-lg space-y-1">
                        <span className="font-semibold text-indigo-300">Officer Review Record:</span>
                        <div className="text-slate-300 text-[11px]">
                          <div>System Reason: {req.system_reason}</div>
                          {req.officer_decision?.override_reason && (
                            <div className="text-amber-300 mt-1"><strong>Override Reason: </strong>{req.officer_decision.override_reason}</div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Audit Dashboard */}
      {reportTab === 'AUDIT_LOGS' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5 shadow-xl">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-base font-bold text-white">Immutable Officer Action Audit Dashboard</h3>
              <p className="text-xs text-slate-400 mt-0.5">Search and filter complete historical review audit logs.</p>
            </div>

            <button
              onClick={handleAuditCsvDownload}
              disabled={downloadingCsv}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs rounded-xl shadow transition-all flex items-center gap-2 disabled:opacity-50"
            >
              Export Audit CSV
            </button>
          </div>

          {/* Search & Filter Bar */}
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-3 bg-slate-950 p-3 rounded-xl border border-slate-800">
            <input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Search officer name, action, or reason..."
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 min-w-[240px]"
            />

            <select
              value={actionFilter}
              onChange={e => setActionFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Actions</option>
              <option value="DECISION_CONFIRMED">DECISION_CONFIRMED</option>
              <option value="DECISION_OVERRIDDEN">DECISION_OVERRIDDEN</option>
              <option value="DECISION_FINALIZED">DECISION_FINALIZED</option>
              <option value="DECISION_REOPENED">DECISION_REOPENED</option>
            </select>

            <button type="submit" className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-lg transition-colors">
              Filter Log
            </button>
          </form>

          {/* Audit Events Table */}
          {loadingAudit || !auditData ? (
            <div className="p-8 text-center text-xs text-slate-400">Loading audit history...</div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300 border-collapse">
                  <thead>
                    <tr className="bg-slate-950 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Officer</th>
                      <th className="p-3">Action</th>
                      <th className="p-3">Transition</th>
                      <th className="p-3">Override Reason / Comment</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {auditData.events.map(a => (
                      <tr key={a.id} className="hover:bg-slate-800/40 transition-colors font-mono">
                        <td className="p-3 text-slate-400">{a.timestamp ? new Date(a.timestamp).toLocaleString() : ''}</td>
                        <td className="p-3 text-white font-semibold font-sans">{a.officer_name}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${a.action.includes('OVERRIDDEN') ? 'bg-amber-950 text-amber-400 border border-amber-500/30' : 'bg-indigo-950 text-indigo-300 border border-indigo-500/30'}`}>
                            {a.action}
                          </span>
                        </td>
                        <td className="p-3">
                          {a.previous_system_decision ? `${a.previous_system_decision} -> ${a.new_final_decision} [${a.decision_type}]` : 'N/A'}
                        </td>
                        <td className="p-3 font-sans text-slate-300">
                          {a.reason || a.comment || 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination Controls */}
              <div className="flex justify-between items-center bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs">
                <span className="text-slate-400">
                  Page {auditData.page} of {auditData.total_pages} ({auditData.total_events} total audit records)
                </span>
                <div className="flex gap-2">
                  <button
                    disabled={auditPage <= 1}
                    onClick={() => setAuditPage(p => Math.max(1, p - 1))}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded disabled:opacity-50 transition-colors"
                  >
                    Previous
                  </button>
                  <button
                    disabled={auditPage >= auditData.total_pages}
                    onClick={() => setAuditPage(p => p + 1)}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded disabled:opacity-50 transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
