import type { Tender, TenderDetail, TenderPage, SystemHealth, PDFProcessingResult, Requirement, ExtractionSummary, Bidder, BidderDocument, EvidenceMatch, EvidenceSummary, ComplianceRule, RuleEvaluation, RuleEvaluationSummary, RAGQueryRequest, RAGQueryResponse, RequirementRAGAnalysisResponse, DocumentIndexResponse, RequirementDecisionSummary, ComplianceDecisionResponse, OfficerReviewAuditOut, BidderReviewSummaryResponse, TenderComplianceReportResponse, BidderComplianceReportResponse, AuditPaginatedResponse, BenchmarkEvaluationResponse } from '../types';

/* Phase 10: Reports & Compliance Audit APIs */
export async function fetchTenderReport(tenderId: number): Promise<TenderComplianceReportResponse> {
  const res = await fetch(`${API_BASE}/reports/tenders/${tenderId}`);
  if (!res.ok) throw new Error('Failed to fetch tender compliance report');
  return res.json();
}

export async function downloadTenderPdf(tenderId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/reports/tenders/${tenderId}/pdf`);
  if (!res.ok) throw new Error('Failed to download tender PDF report');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `STAMAS_Tender_${tenderId}_Compliance_Report.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function downloadTenderCsv(tenderId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/reports/tenders/${tenderId}/csv`);
  if (!res.ok) throw new Error('Failed to download tender CSV report');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `STAMAS_Tender_${tenderId}_Compliance_Report.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function fetchBidderReport(tenderId: number, bidderId: number): Promise<BidderComplianceReportResponse> {
  const res = await fetch(`${API_BASE}/reports/bidders/${bidderId}?tender_id=${tenderId}`);
  if (!res.ok) throw new Error('Failed to fetch bidder compliance report');
  return res.json();
}

export async function downloadBidderPdf(tenderId: number, bidderId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/reports/bidders/${bidderId}/pdf?tender_id=${tenderId}`);
  if (!res.ok) throw new Error('Failed to download bidder PDF report');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `STAMAS_Bidder_${bidderId}_Compliance_Report.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function downloadBidderCsv(tenderId: number, bidderId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/reports/bidders/${bidderId}/csv?tender_id=${tenderId}`);
  if (!res.ok) throw new Error('Failed to download bidder CSV report');
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `STAMAS_Bidder_${bidderId}_Compliance_Report.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function fetchAuditReportData(
  tenderId?: number,
  bidderId?: number,
  actionFilter?: string,
  search?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<AuditPaginatedResponse> {
  let url = `${API_BASE}/reports/audit?page=${page}&page_size=${pageSize}`;
  if (tenderId) url += `&tender_id=${tenderId}`;
  if (bidderId) url += `&bidder_id=${bidderId}`;
  if (actionFilter && actionFilter !== 'ALL') url += `&action_filter=${encodeURIComponent(actionFilter)}`;
  if (search && search.trim()) url += `&search=${encodeURIComponent(search.trim())}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch audit log report data');
  return res.json();
}

export async function downloadAuditCsv(
  tenderId?: number,
  bidderId?: number,
  actionFilter?: string,
  search?: string
): Promise<void> {
  let url = `${API_BASE}/reports/audit/csv?`;
  if (tenderId) url += `&tender_id=${tenderId}`;
  if (bidderId) url += `&bidder_id=${bidderId}`;
  if (actionFilter && actionFilter !== 'ALL') url += `&action_filter=${encodeURIComponent(actionFilter)}`;
  if (search && search.trim()) url += `&search=${encodeURIComponent(search.trim())}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to download audit CSV');
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = `STAMAS_Audit_Trail.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

/* Phase 9: Officer Review & Human-in-the-Loop APIs */
export async function fetchBidderReviewSummary(
  tenderId: number,
  bidderId: number
): Promise<BidderReviewSummaryResponse> {
  const res = await fetch(`${API_BASE}/compliance/review/bidders/${bidderId}?tender_id=${tenderId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to fetch bidder review summary');
  }
  return res.json();
}

export async function confirmRequirementDecision(
  tenderId: number,
  bidderId: number,
  requirementId: number,
  officerComment?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/compliance/review/bidders/${bidderId}/requirements/${requirementId}/confirm?tender_id=${tenderId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ officer_comment: officerComment }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to confirm system decision');
  }
  return res.json();
}

export async function overrideRequirementDecision(
  tenderId: number,
  bidderId: number,
  requirementId: number,
  finalDecision: 'PASS' | 'FAIL' | 'REVIEW',
  overrideReason: string,
  officerComment?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/compliance/review/bidders/${bidderId}/requirements/${requirementId}/override?tender_id=${tenderId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      final_decision: finalDecision,
      override_reason: overrideReason,
      officer_comment: officerComment,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to override system decision');
  }
  return res.json();
}

export async function finalizeBidderReview(
  tenderId: number,
  bidderId: number
): Promise<BidderReviewSummaryResponse> {
  const res = await fetch(`${API_BASE}/compliance/review/bidders/${bidderId}/finalize?tender_id=${tenderId}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to finalize bidder review');
  }
  return res.json();
}

export async function reopenBidderReview(
  tenderId: number,
  bidderId: number,
  reason: string
): Promise<BidderReviewSummaryResponse> {
  const res = await fetch(`${API_BASE}/compliance/review/bidders/${bidderId}/reopen?tender_id=${tenderId}&reason=${encodeURIComponent(reason)}`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to reopen bidder review');
  }
  return res.json();
}

export async function fetchDecisionAuditTrail(
  tenderId: number,
  bidderId: number,
  requirementId?: number
): Promise<OfficerReviewAuditOut[]> {
  let url = `${API_BASE}/compliance/review/bidders/${bidderId}/audit?tender_id=${tenderId}`;
  if (requirementId) {
    url += `&requirement_id=${requirementId}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch decision audit trail');
  return res.json();
}

/* Phase 8: Compliance Decision Engine APIs */
export async function evaluateComplianceDecisions(
  tenderId: number,
  bidderId: number
): Promise<ComplianceDecisionResponse> {
  const res = await fetch(`${API_BASE}/compliance/decisions/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tender_id: tenderId, bidder_id: bidderId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to evaluate compliance decisions');
  }
  return res.json();
}

export async function fetchBidderComplianceSummary(
  bidderId: number,
  tenderId: number
): Promise<ComplianceDecisionResponse> {
  const res = await fetch(`${API_BASE}/compliance/bidders/${bidderId}/compliance-summary?tender_id=${tenderId}`);
  if (!res.ok) throw new Error('Failed to fetch bidder compliance summary');
  return res.json();
}

export async function fetchRequirementDecision(
  bidderId: number,
  requirementId: number
): Promise<RequirementDecisionSummary> {
  const res = await fetch(`${API_BASE}/compliance/bidders/${bidderId}/requirements/${requirementId}/decision`);
  if (!res.ok) throw new Error('Failed to fetch requirement decision');
  return res.json();
}

export async function reevaluateDecision(decisionId: number): Promise<ComplianceDecisionResponse> {
  const res = await fetch(`${API_BASE}/compliance/decisions/${decisionId}/re-evaluate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to re-evaluate decision');
  return res.json();
}

/* Phase 7: AI + RAG Intelligence APIs */
export async function queryRAG(reqData: RAGQueryRequest): Promise<RAGQueryResponse> {
  const res = await fetch(`${API_BASE}/rag/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reqData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to query RAG intelligence engine');
  }
  return res.json();
}

export async function analyzeRequirementRAG(
  requirementId: number,
  bidderId: number
): Promise<RequirementRAGAnalysisResponse> {
  const res = await fetch(`${API_BASE}/rag/requirements/${requirementId}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ bidder_id: bidderId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to analyze requirement with RAG AI');
  }
  return res.json();
}

export async function indexDocumentRAG(documentId: number): Promise<DocumentIndexResponse> {
  const res = await fetch(`${API_BASE}/rag/documents/${documentId}/index`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to index bidder document');
  }
  return res.json();
}



const API_BASE = '/api/v1';

export async function fetchHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchTenders(search?: string): Promise<Tender[]> {
  const url = search ? `${API_BASE}/tenders/?search=${encodeURIComponent(search)}` : `${API_BASE}/tenders/`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch tenders');
  return res.json();
}

export async function fetchTenderDetail(id: number): Promise<TenderDetail> {
  const res = await fetch(`${API_BASE}/tenders/${id}`);
  if (!res.ok) throw new Error('Failed to fetch tender details');
  return res.json();
}

export async function createTender(data: {
  tender_id: string;
  title: string;
  department: string;
  issue_date?: string;
  closing_date?: string;
}): Promise<Tender> {
  const res = await fetch(`${API_BASE}/tenders/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create tender');
  }
  return res.json();
}

export async function uploadTenderPDF(id: number, file: File): Promise<PDFProcessingResult> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/tenders/${id}/upload-pdf`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload and process PDF');
  }
  return res.json();
}

export async function searchExtractedText(id: number, query?: string): Promise<TenderPage[]> {
  const url = query 
    ? `${API_BASE}/tenders/${id}/extracted-text?query=${encodeURIComponent(query)}`
    : `${API_BASE}/tenders/${id}/extracted-text`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to search extracted text');
  return res.json();
}

/* Phase 2: Requirement Intelligence APIs */

export async function extractRequirements(tenderId: number): Promise<ExtractionSummary> {
  const res = await fetch(`${API_BASE}/tenders/${tenderId}/extract-requirements`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to extract requirements');
  }
  return res.json();
}

export async function fetchRequirements(tenderId: number, category?: string): Promise<Requirement[]> {
  const url = category && category !== 'ALL'
    ? `${API_BASE}/tenders/${tenderId}/requirements?category=${encodeURIComponent(category)}`
    : `${API_BASE}/tenders/${tenderId}/requirements`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch requirements');
  return res.json();
}

export async function createManualRequirement(tenderId: number, data: Partial<Requirement>): Promise<Requirement> {
  const res = await fetch(`${API_BASE}/tenders/${tenderId}/requirements`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create manual requirement');
  }
  return res.json();
}

export async function updateRequirement(reqId: number, data: Partial<Requirement>): Promise<Requirement> {
  const res = await fetch(`${API_BASE}/requirements/${reqId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update requirement');
  }
  return res.json();
}

export async function deleteRequirement(reqId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/requirements/${reqId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete requirement');
  }
}

/* Phase 3: Bidder Management APIs */
export async function fetchBidders(tenderId: number): Promise<Bidder[]> {
  const res = await fetch(`${API_BASE}/tenders/${tenderId}/bidders`);
  if (!res.ok) throw new Error('Failed to fetch bidders');
  return res.json();
}

export async function createBidder(tenderId: number, data: Partial<Bidder>): Promise<Bidder> {
  const res = await fetch(`${API_BASE}/tenders/${tenderId}/bidders`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to create bidder');
  }
  return res.json();
}

export async function fetchBidder(bidderId: number): Promise<Bidder> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}`);
  if (!res.ok) throw new Error('Failed to fetch bidder');
  return res.json();
}

export async function updateBidder(bidderId: number, data: Partial<Bidder>): Promise<Bidder> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to update bidder');
  }
  return res.json();
}

export async function deleteBidder(bidderId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete bidder');
  }
}

export async function fetchBidderDocuments(bidderId: number): Promise<BidderDocument[]> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/documents`);
  if (!res.ok) throw new Error('Failed to fetch bidder documents');
  return res.json();
}

export async function uploadBidderDocument(bidderId: number, category: string, file: File): Promise<BidderDocument> {
  const formData = new FormData();
  formData.append('category', category);
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/bidders/${bidderId}/documents`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to upload bidder document');
  }
  return res.json();
}

export async function processBidderDocument(bidderId: number, documentId: number): Promise<BidderDocument> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/documents/${documentId}/process`, {
    method: 'POST',
  });
  
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to process document');
  }
  return res.json();
}

export async function deleteBidderDocument(bidderId: number, documentId: number): Promise<void> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/documents/${documentId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to delete document');
  }
}

export async function fetchBidderDocumentDetail(bidderId: number, documentId: number): Promise<BidderDocument> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/documents/${documentId}`);
  if (!res.ok) throw new Error('Failed to fetch document details');
  return res.json();
}

/* Phase 5: Evidence Matching Engine APIs */

export async function matchRequirement(
  tenderId: number,
  bidderId: number,
  requirementId: number
): Promise<EvidenceMatch[]> {
  const res = await fetch(
    `${API_BASE}/tenders/${tenderId}/bidders/${bidderId}/requirements/${requirementId}/match`,
    { method: 'POST' }
  );
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to match requirement evidence');
  }
  return res.json();
}

export async function runBatchEvidenceMatching(
  tenderId: number,
  bidderId: number
): Promise<EvidenceMatch[]> {
  const res = await fetch(`${API_BASE}/evidence-matches/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tender_id: tenderId, bidder_id: bidderId }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to run batch evidence matching');
  }
  return res.json();
}

export async function fetchBidderEvidenceMatches(
  bidderId: number,
  tenderId?: number,
  requirementId?: number
): Promise<EvidenceMatch[]> {
  const params = new URLSearchParams();
  if (tenderId) params.append('tender_id', tenderId.toString());
  if (requirementId) params.append('requirement_id', requirementId.toString());

  const url = `${API_BASE}/bidders/${bidderId}/evidence-matches?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch bidder evidence matches');
  return res.json();
}

export async function fetchRequirementEvidenceForBidder(
  bidderId: number,
  requirementId: number
): Promise<EvidenceMatch[]> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/requirements/${requirementId}/evidence`);
  if (!res.ok) throw new Error('Failed to fetch requirement evidence');
  return res.json();
}

export async function fetchBidderEvidenceSummary(
  bidderId: number,
  tenderId: number
): Promise<EvidenceSummary> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/evidence-summary?tender_id=${tenderId}`);
  if (!res.ok) throw new Error('Failed to fetch evidence summary');
  return res.json();
}

export async function fetchEvidenceMatchDetail(matchId: number): Promise<EvidenceMatch> {
  const res = await fetch(`${API_BASE}/evidence-matches/${matchId}`);
  if (!res.ok) throw new Error('Failed to fetch evidence match details');
  return res.json();
}

/* Phase 6: Compliance Rule Engine APIs */

export async function evaluateComplianceRules(
  tenderId: number,
  bidderId: number,
  requirementId?: number
): Promise<RuleEvaluation[]> {
  const res = await fetch(`${API_BASE}/compliance/rules/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tender_id: tenderId,
      bidder_id: bidderId,
      requirement_id: requirementId,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to evaluate compliance rules');
  }
  return res.json();
}

export async function fetchBidderRuleEvaluations(
  bidderId: number,
  tenderId?: number,
  resultFilter?: string
): Promise<RuleEvaluation[]> {
  const params = new URLSearchParams();
  if (tenderId) params.append('tender_id', tenderId.toString());
  if (resultFilter && resultFilter !== 'ALL') params.append('evaluation_result', resultFilter);

  const url = `${API_BASE}/bidders/${bidderId}/rule-evaluations?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch bidder rule evaluations');
  return res.json();
}

export async function fetchRequirementRuleEvaluations(
  bidderId: number,
  requirementId: number
): Promise<RuleEvaluation[]> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/requirements/${requirementId}/rule-evaluations`);
  if (!res.ok) throw new Error('Failed to fetch requirement rule evaluations');
  return res.json();
}

export async function fetchBidderRuleSummary(
  bidderId: number,
  tenderId: number
): Promise<RuleEvaluationSummary> {
  const res = await fetch(`${API_BASE}/bidders/${bidderId}/rule-summary?tender_id=${tenderId}`);
  if (!res.ok) throw new Error('Failed to fetch rule summary');
  return res.json();
}

export async function createCustomRule(
  requirementId: number,
  ruleData: Partial<ComplianceRule>
): Promise<ComplianceRule> {
  const res = await fetch(`${API_BASE}/requirements/${requirementId}/rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ruleData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create custom rule');
  }
  return res.json();
}

/* Phase 11 API Helpers */
export async function runBenchmarkEvaluation(): Promise<BenchmarkEvaluationResponse> {
  const res = await fetch(`${API_BASE}/benchmark/run`);
  if (!res.ok) throw new Error('Failed to execute benchmark evaluation');
  return res.json();
}


