export interface Tender {
  id: number;
  tender_id: string;
  title: string;
  department: string;
  issue_date?: string;
  closing_date?: string;
  file_name?: string;
  file_size?: number;
  page_count: number;
  status: 'CREATED' | 'UPLOADED' | 'PROCESSING' | 'PROCESSED' | 'FAILED';
  created_at: string;
  updated_at: string;
}

export interface TenderPage {
  id: number;
  page_number: number;
  text_content: string;
  tables_data?: any;
}

export interface TenderDetail extends Tender {
  pages: TenderPage[];
  raw_text?: string;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  components: {
    database: string;
    pdf_parser: string;
  };
}

export interface PDFProcessingResult {
  tender_id: number;
  file_name: string;
  page_count: number;
  total_characters: number;
  status: string;
  message: string;
}

export interface Requirement {
  id: number;
  tender_id: number;
  req_code: string;
  category: 'ELIGIBILITY' | 'TECHNICAL' | 'FINANCIAL' | 'DOCUMENT' | 'OTHER';
  text: string;
  mandatory: boolean;
  constraint_type?: string;
  threshold?: number;
  unit?: string;
  currency?: string;
  source_document?: string;
  source_page?: number;
  evidence_text?: string;
  confidence: number;
  status: 'EXTRACTED' | 'CONFIRMED' | 'CORRECTED' | 'REVIEW';
  created_at: string;
  updated_at: string;
}

export interface ExtractionSummary {
  total_extracted: number;
  categories_breakdown: Record<string, number>;
  status: string;
  message: string;
}

/* Phase 3 Types */
export interface Bidder {
  id: number;
  tender_id: number;
  bidder_id: string;
  bidder_name: string;
  company_name: string;
  registration_number?: string;
  gstin?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  address?: string;
  status: 'ACTIVE' | 'INACTIVE' | 'UNDER_REVIEW' | 'SELECTED' | 'REJECTED';
  created_at: string;
  updated_at: string;
}

export interface BidderDocumentPage {
  id: number;
  document_id: number;
  page_number: number;
  extracted_text: string;
  tables_data?: any;
  extraction_method: string;
  extraction_status: string;
  extraction_quality: string;
}

export interface BidderDocument {
  id: number;
  bidder_id: number;
  tender_id: number;
  filename: string;
  category: string;
  file_size?: number;
  page_count: number;
  processing_status: 'UPLOADED' | 'PROCESSING' | 'PROCESSED' | 'FAILED';
  extraction_status: 'PENDING' | 'TEXT_LAYER' | 'OCR' | 'MIXED' | 'FAILED';
  error_message?: string;
  created_at: string;
  updated_at: string;
  pages?: BidderDocumentPage[];
}

/* Phase 5 Types */
export interface EvidenceMatch {
  id: number;
  tender_id: number;
  requirement_id: number;
  bidder_id: number;
  document_id?: number;
  page_id?: number;
  evidence_text: string;
  match_status: 'MATCHED' | 'PARTIAL' | 'LOW_CONFIDENCE' | 'NOT_FOUND';
  confidence_score: number;
  matching_method: 'KEYWORD' | 'SEMANTIC' | 'HYBRID';
  matched_keywords?: string[];
  reason?: string;
  created_at: string;
  updated_at: string;
  document_name?: string;
  page_number?: number;
  req_code?: string;
  requirement_text?: string;
  bidder_name?: string;
}

export interface EvidenceSummary {
  bidder_id: number;
  tender_id: number;
  total_requirements: number;
  matched_count: number;
  partial_count: number;
  low_confidence_count: number;
  not_found_count: number;
}

/* Phase 6 Types */
export interface ComplianceRule {
  id: number;
  requirement_id: number;
  rule_code: string;
  rule_type: string;
  field_name?: string;
  operator?: string;
  required_value?: string;
  required_value_max?: string;
  unit?: string;
  currency?: string;
  logical_operator: string;
  configuration_json?: any;
  created_at: string;
  updated_at: string;
}

export interface RuleEvaluation {
  id: number;
  rule_id?: number;
  requirement_id: number;
  bidder_id: number;
  tender_id: number;
  evidence_match_id?: number;
  extracted_value?: string;
  extracted_unit?: string;
  required_value?: string;
  operator?: string;
  evaluation_status: 'EVALUATED' | 'INSUFFICIENT_EVIDENCE' | 'NOT_EVALUABLE' | 'ERROR';
  evaluation_result: 'SATISFIED' | 'NOT_SATISFIED' | 'INDETERMINATE' | 'INSUFFICIENT_EVIDENCE' | 'CONFLICTING_EVIDENCE';
  explanation: string;
  created_at: string;
  updated_at: string;
  req_code?: string;
  requirement_text?: string;
  bidder_name?: string;
  document_id?: number;
  document_name?: string;
  page_number?: number;
  evidence_text?: string;
}

export interface RuleEvaluationSummary {
  bidder_id: number;
  tender_id: number;
  total_requirements: number;
  rules_evaluated: number;
  satisfied_count: number;
  not_satisfied_count: number;
  indeterminate_count: number;
  insufficient_evidence_count: number;
  conflicting_evidence_count: number;
}

/* Phase 7 RAG Intelligence Types */
export interface SourceCitation {
  source_id: string;
  document_id: number;
  document_name: string;
  page_id: number;
  page_number: number;
  chunk_id?: number;
  text_snippet: string;
  score?: number;
  retrieval_method?: string;
}

export interface RAGQueryRequest {
  tender_id: number;
  bidder_id: number;
  query: string;
  requirement_id?: number;
  document_id?: number;
  top_k?: number;
  retrieval_method?: 'KEYWORD' | 'SEMANTIC' | 'HYBRID';
}

export interface RAGQueryResponse {
  status: 'GROUNDED' | 'PARTIAL' | 'INSUFFICIENT_CONTEXT' | 'CONFLICTING_SOURCES' | 'AI_UNAVAILABLE' | 'ERROR';
  answer: string;
  sources: SourceCitation[];
  missing_information: string[];
  conflicts: string[];
  retrieval_score?: number;
  ai_provider_used: string;
  retrieval_method_used: string;
}

export interface RequirementRAGAnalysisResponse {
  requirement_id: number;
  requirement_text: string;
  bidder_id: number;
  bidder_name: string;
  status: 'GROUNDED' | 'PARTIAL' | 'INSUFFICIENT_CONTEXT' | 'CONFLICTING_SOURCES' | 'AI_UNAVAILABLE' | 'ERROR';
  answer: string;
  evidence_found: any[];
  rule_evaluation?: any;
  sources: SourceCitation[];
  ai_provider_used: string;
  retrieval_method_used: string;
}

export interface DocumentIndexResponse {
  document_id: number;
  chunks_created: number;
  status: string;
  message: string;
}

/* Phase 8: Compliance Decision Engine Types */
export interface RequirementDecisionSummary {
  requirement_id: number;
  req_code: string;
  requirement_text: string;
  category: string;
  is_mandatory: boolean;
  decision: 'PASS' | 'FAIL' | 'REVIEW';
  decision_type: string;
  reason: string;
  rule_count: number;
  passed_rules: number;
  failed_rules: number;
  review_rules: number;
  evidence_matches: any[];
  rule_evaluations: any[];
  ai_explanation?: string;
}

export interface OverallDecisionSummary {
  total_requirements: number;
  mandatory_requirements: number;
  optional_requirements: number;
  pass_count: number;
  fail_count: number;
  review_count: number;
  optional_pass_count: number;
  optional_fail_count: number;
  optional_review_count: number;
}

export interface ComplianceDecisionResponse {
  id?: number;
  tender_id: number;
  bidder_id: number;
  bidder_name: string;
  decision_type: string;
  overall_decision: 'PASS' | 'FAIL' | 'REVIEW';
  reason: string;
  summary: OverallDecisionSummary;
  requirements: RequirementDecisionSummary[];
  created_at?: string;
  updated_at?: string;
}

/* Phase 9 Officer Review & Human-in-the-Loop Types */
export interface OfficerConfirmRequest {
  officer_comment?: string;
  officer_id?: string;
  officer_name?: string;
  officer_role?: string;
}

export interface OfficerOverrideRequest {
  final_decision: 'PASS' | 'FAIL' | 'REVIEW';
  override_reason: string;
  officer_comment?: string;
  officer_id?: string;
  officer_name?: string;
  officer_role?: string;
}

export interface OfficerDecisionOut {
  id: number;
  tender_id: number;
  bidder_id: number;
  requirement_id?: number;
  system_decision_id?: number;
  system_decision?: string;
  final_decision: 'PASS' | 'FAIL' | 'REVIEW';
  decision_type: 'CONFIRMED' | 'OVERRIDDEN';
  officer_id: string;
  officer_name: string;
  officer_role: string;
  officer_comment?: string;
  override_reason?: string;
  review_status: string;
  created_at?: string;
  finalized_at?: string;
}

export interface OfficerReviewAuditOut {
  id: number;
  tender_id: number;
  bidder_id: number;
  requirement_id?: number;
  officer_decision_id?: number;
  officer_id: string;
  officer_name: string;
  officer_role: string;
  action: string;
  previous_system_decision?: string;
  previous_final_decision?: string;
  new_final_decision?: string;
  decision_type?: string;
  reason?: string;
  comment?: string;
  timestamp?: string;
}

export interface RequirementReviewSummary {
  requirement_id: number;
  req_code: string;
  text: string;
  category: string;
  is_mandatory: boolean;
  system_decision: 'PASS' | 'FAIL' | 'REVIEW';
  system_reason: string;
  officer_decision?: OfficerDecisionOut;
  effective_decision: 'PASS' | 'FAIL' | 'REVIEW';
  decision_type: 'SYSTEM_DECISION' | 'CONFIRMED' | 'OVERRIDDEN';
  review_status: 'PENDING' | 'CONFIRMED' | 'OVERRIDDEN' | 'FINALIZED';
  evidence_matches: any[];
  rule_evaluations: any[];
  ai_explanation?: string;
}

export interface BidderReviewSummaryResponse {
  tender_id: number;
  bidder_id: number;
  bidder_name: string;
  company_name: string;
  system_overall_decision: 'PASS' | 'FAIL' | 'REVIEW';
  final_overall_decision: 'PASS' | 'FAIL' | 'REVIEW' | 'PENDING';
  review_status: 'PENDING' | 'IN_PROGRESS' | 'FINALIZED' | 'REOPENED';
  total_requirements: number;
  reviewed_count: number;
  pending_count: number;
  confirmed_count: number;
  overridden_count: number;
  requirements: RequirementReviewSummary[];
  audits: OfficerReviewAuditOut[];
}

/* Phase 10 Reports & Audit Management Types */
export interface TenderBidderSummaryItem {
  bidder_id: number;
  bidder_name: string;
  company_name: string;
  registration_number?: string;
  system_overall_decision: string;
  final_overall_decision: string;
  review_status: string;
  total_requirements: number;
  passed_count?: number;
  failed_count?: number;
  review_count?: number;
  reviewed_count: number;
  pending_count: number;
  confirmed_count: number;
  overridden_count: number;
}

export interface TenderComplianceReportResponse {
  tender_id: number;
  tender_number: string;
  title: string;
  department: string;
  status: string;
  created_at?: string;
  generated_at: string;
  total_bidders: number;
  bidders: TenderBidderSummaryItem[];
  overall_system_summary: Record<string, number>;
  overall_officer_summary: Record<string, number>;
}

export interface BidderComplianceReportResponse {
  tender_id: number;
  tender_number?: string;
  tender_title: string;
  department: string;
  bidder_id: number;
  bidder_name: string;
  company_name: string;
  registration_number?: string;
  gstin?: string;
  email?: string;
  system_overall_decision: string;
  final_overall_decision: string;
  review_status: string;
  generated_at: string;
  summary_counts: Record<string, number>;
  requirements: RequirementReviewSummary[];
  audits: OfficerReviewAuditOut[];
}

export interface AuditPaginatedResponse {
  total_events: number;
  page: number;
  page_size: number;
  total_pages: number;
  override_stats: Record<string, number>;
  events: OfficerReviewAuditOut[];
}

/* Phase 11 Benchmark & Accuracy Evaluation Types */
export interface PrecisionRecallF1 {
  precision: number;
  recall: number;
  f1_score: number;
}

export interface TopKRecall {
  top1_recall: number;
  top3_recall: number;
  top5_recall: number;
  precision: number;
}

export interface RuleEngineMetrics {
  accuracy: number;
  satisfied_ratio: number;
}

export interface DecisionEngineMetrics {
  matrix: Record<string, Record<string, number>>;
  total_samples: number;
  correct_samples: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface LatencyMetricsMs {
  average_ms: number;
  p50_ms: number;
  p95_ms: number;
  max_ms: number;
}

export interface BenchmarkEvaluationResponse {
  benchmark_id: string;
  timestamp: string;
  environment: string;
  total_cases_evaluated: number;
  requirement_extraction_metrics: PrecisionRecallF1;
  evidence_matching_metrics: TopKRecall;
  rule_engine_metrics: RuleEngineMetrics;
  decision_engine_metrics: DecisionEngineMetrics;
  latency_metrics_ms: LatencyMetricsMs;
  error_taxonomy: Record<string, number>;
  limitations: string[];
}


