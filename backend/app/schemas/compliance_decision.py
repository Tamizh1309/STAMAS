from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class RequirementDecisionSummary(BaseModel):
    requirement_id: int
    req_code: str
    requirement_text: str
    category: str = "GENERAL"
    is_mandatory: bool = True
    decision: str = Field(..., description="PASS, FAIL, or REVIEW")
    decision_type: str = "SYSTEM_DECISION"
    reason: str
    rule_count: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    review_rules: int = 0
    evidence_matches: List[Dict[str, Any]] = []
    rule_evaluations: List[Dict[str, Any]] = []
    ai_explanation: Optional[str] = None


class OverallDecisionSummary(BaseModel):
    total_requirements: int = 0
    mandatory_requirements: int = 0
    optional_requirements: int = 0
    pass_count: int = 0
    fail_count: int = 0
    review_count: int = 0
    optional_pass_count: int = 0
    optional_fail_count: int = 0
    optional_review_count: int = 0


class DecisionEvaluateRequest(BaseModel):
    tender_id: int
    bidder_id: int
    requirement_id: Optional[int] = None


class ComplianceDecisionResponse(BaseModel):
    id: Optional[int] = None
    tender_id: int
    bidder_id: int
    bidder_name: str
    decision_type: str = "SYSTEM_DECISION"
    overall_decision: str = Field(..., description="PASS, FAIL, or REVIEW")
    reason: str
    summary: OverallDecisionSummary
    requirements: List[RequirementDecisionSummary] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
