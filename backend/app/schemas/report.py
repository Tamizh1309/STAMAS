from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

class TenderBidderSummaryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bidder_id: int
    bidder_name: str
    company_name: str
    registration_number: Optional[str] = None
    system_overall_decision: str
    final_overall_decision: str
    review_status: str
    total_requirements: int = 0
    passed_count: int = 0
    failed_count: int = 0
    review_count: int = 0
    reviewed_count: int = 0
    pending_count: int = 0
    confirmed_count: int = 0
    overridden_count: int = 0


class TenderComplianceReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tender_id: int
    tender_number: str
    title: str
    department: str
    status: str
    created_at: Optional[str] = None
    generated_at: str
    total_bidders: int
    bidders: List[TenderBidderSummaryItem] = []
    overall_system_summary: Dict[str, int] = {}
    overall_officer_summary: Dict[str, int] = {}


class BidderComplianceReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tender_id: int
    tender_title: str
    bidder_id: int
    bidder_name: str
    company_name: str
    registration_number: Optional[str] = None
    gstin: Optional[str] = None
    email: Optional[str] = None
    system_overall_decision: str
    final_overall_decision: str
    review_status: str
    generated_at: str
    summary_counts: Dict[str, int] = {}
    requirements: List[Dict[str, Any]] = []
    audits: List[Dict[str, Any]] = []


class AuditPaginatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_events: int
    page: int
    page_size: int
    total_pages: int
    override_stats: Dict[str, int] = {}
    events: List[Dict[str, Any]] = []
