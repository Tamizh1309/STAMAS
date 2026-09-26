from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any

class OfficerConfirmRequest(BaseModel):
    officer_comment: Optional[str] = None
    officer_id: str = "OFFICER-001"
    officer_name: str = "Procurement Evaluation Officer"
    officer_role: str = "Senior Evaluation Officer"


class OfficerOverrideRequest(BaseModel):
    final_decision: str = Field(..., description="PASS, FAIL, or REVIEW")
    override_reason: str = Field(..., description="Mandatory reason for overriding system decision")
    officer_comment: Optional[str] = None
    officer_id: str = "OFFICER-001"
    officer_name: str = "Procurement Evaluation Officer"
    officer_role: str = "Senior Evaluation Officer"

    @field_validator("final_decision")
    @classmethod
    def validate_final_decision(cls, v: str) -> str:
        v_upper = v.upper().strip()
        if v_upper not in ["PASS", "FAIL", "REVIEW"]:
            raise ValueError("final_decision must be one of: PASS, FAIL, REVIEW")
        return v_upper

    @field_validator("override_reason")
    @classmethod
    def validate_override_reason(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("override_reason cannot be empty or whitespace")
        if len(v.strip()) < 10:
            raise ValueError("override_reason must be at least 10 characters long")
        return v.strip()


class OfficerDecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    bidder_id: int
    requirement_id: Optional[int] = None
    system_decision_id: Optional[int] = None
    system_decision: Optional[str] = "REVIEW"
    final_decision: str
    decision_type: str # CONFIRMED or OVERRIDDEN
    officer_id: str
    officer_name: str
    officer_role: str
    officer_comment: Optional[str] = None
    override_reason: Optional[str] = None
    review_status: str
    created_at: Optional[str] = None
    finalized_at: Optional[str] = None


class OfficerReviewAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    bidder_id: int
    requirement_id: Optional[int] = None
    officer_decision_id: Optional[int] = None
    officer_id: str
    officer_name: str
    officer_role: str
    action: str
    previous_system_decision: Optional[str] = None
    previous_final_decision: Optional[str] = None
    new_final_decision: Optional[str] = None
    decision_type: Optional[str] = None
    reason: Optional[str] = None
    comment: Optional[str] = None
    timestamp: Optional[str] = None


class RequirementReviewSummary(BaseModel):
    requirement_id: int
    req_code: str
    text: str
    category: str = "GENERAL"
    is_mandatory: bool = True
    system_decision: str = "REVIEW"
    system_reason: str = ""
    officer_decision: Optional[OfficerDecisionOut] = None
    effective_decision: str = "REVIEW"
    decision_type: str = "SYSTEM_DECISION" # SYSTEM_DECISION, CONFIRMED, OVERRIDDEN
    review_status: str = "PENDING" # PENDING, CONFIRMED, OVERRIDDEN, FINALIZED
    evidence_matches: List[Dict[str, Any]] = []
    rule_evaluations: List[Dict[str, Any]] = []
    ai_explanation: Optional[str] = None


class BidderReviewSummaryResponse(BaseModel):
    tender_id: int
    bidder_id: int
    bidder_name: str
    company_name: str
    system_overall_decision: str
    final_overall_decision: str
    review_status: str
    total_requirements: int = 0
    reviewed_count: int = 0
    pending_count: int = 0
    confirmed_count: int = 0
    overridden_count: int = 0
    requirements: List[RequirementReviewSummary] = []
    audits: List[OfficerReviewAuditOut] = []
