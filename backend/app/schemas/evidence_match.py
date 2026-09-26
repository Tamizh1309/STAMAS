from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class EvidenceMatchBase(BaseModel):
    tender_id: int
    requirement_id: int
    bidder_id: int
    document_id: Optional[int] = None
    page_id: Optional[int] = None
    evidence_text: str
    match_status: str = "MATCHED"  # MATCHED, PARTIAL, LOW_CONFIDENCE, NOT_FOUND
    confidence_score: float = 0.0
    matching_method: str = "KEYWORD"  # KEYWORD, SEMANTIC, HYBRID
    matched_keywords: Optional[List[str]] = None
    reason: Optional[str] = None

class EvidenceMatchCreate(EvidenceMatchBase):
    pass

class EvidenceMatchResponse(EvidenceMatchBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # Extra helper fields for UI display
    document_name: Optional[str] = None
    page_number: Optional[int] = None
    req_code: Optional[str] = None
    requirement_text: Optional[str] = None
    bidder_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceSummaryResponse(BaseModel):
    bidder_id: int
    tender_id: int
    total_requirements: int
    matched_count: int
    partial_count: int
    low_confidence_count: int
    not_found_count: int

class MatchRunRequest(BaseModel):
    tender_id: int
    bidder_id: int
    requirement_id: Optional[int] = None
