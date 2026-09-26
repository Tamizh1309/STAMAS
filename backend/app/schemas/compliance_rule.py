from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ComplianceRuleBase(BaseModel):
    requirement_id: int
    rule_code: Optional[str] = None
    rule_type: str  # EXISTENCE, NUMERIC_MIN, CERTIFICATION_REQUIRED, etc.
    field_name: Optional[str] = None
    operator: Optional[str] = None
    required_value: Optional[str] = None
    required_value_max: Optional[str] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    logical_operator: str = "ALL"
    configuration_json: Optional[Any] = None

class ComplianceRuleCreate(ComplianceRuleBase):
    pass

class ComplianceRuleResponse(ComplianceRuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RuleEvaluationResponse(BaseModel):
    id: int
    rule_id: Optional[int] = None
    requirement_id: int
    bidder_id: int
    tender_id: int
    evidence_match_id: Optional[int] = None

    extracted_value: Optional[str] = None
    extracted_unit: Optional[str] = None
    required_value: Optional[str] = None
    operator: Optional[str] = None

    evaluation_status: str  # EVALUATED, INSUFFICIENT_EVIDENCE, NOT_EVALUABLE, ERROR
    evaluation_result: str  # SATISFIED, NOT_SATISFIED, INDETERMINATE, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE
    explanation: str

    created_at: datetime
    updated_at: datetime

    # Enriched UI Traceability Fields
    req_code: Optional[str] = None
    requirement_text: Optional[str] = None
    bidder_name: Optional[str] = None
    document_id: Optional[int] = None
    document_name: Optional[str] = None
    page_number: Optional[int] = None
    evidence_text: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RuleEvaluationSummaryResponse(BaseModel):
    bidder_id: int
    tender_id: int
    total_requirements: int
    rules_evaluated: int
    satisfied_count: int
    not_satisfied_count: int
    indeterminate_count: int
    insufficient_evidence_count: int
    conflicting_evidence_count: int

class RuleEvaluateRequest(BaseModel):
    tender_id: int
    bidder_id: int
    requirement_id: Optional[int] = None
