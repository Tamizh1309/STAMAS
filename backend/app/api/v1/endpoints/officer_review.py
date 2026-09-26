from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.schemas.officer_decision import (
    OfficerConfirmRequest,
    OfficerOverrideRequest,
    OfficerDecisionOut,
    OfficerReviewAuditOut,
    RequirementReviewSummary,
    BidderReviewSummaryResponse
)
from app.services.compliance.officer_review import (
    confirm_requirement_decision,
    override_requirement_decision,
    finalize_bidder_review,
    reopen_bidder_review,
    get_bidder_review_summary,
    get_requirement_review_detail,
    get_decision_audit_trail
)

router = APIRouter()


@router.get("/review/bidders/{bidder_id}", response_model=BidderReviewSummaryResponse, summary="Get Bidder Review Summary")
def api_get_bidder_review_summary(
    bidder_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    db: Session = Depends(get_db)
):
    """
    Returns full officer review summary for a bidder, including system decisions, officer decisions, and requirement breakdowns.
    """
    return get_bidder_review_summary(db, tender_id=tender_id, bidder_id=bidder_id)


@router.get("/review/bidders/{bidder_id}/requirements/{requirement_id}", response_model=RequirementReviewSummary, summary="Get Requirement Review Detail")
def api_get_requirement_review_detail(
    bidder_id: int,
    requirement_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    db: Session = Depends(get_db)
):
    """
    Returns evidence traceability chain, system decision, rule evaluations, and officer review state for a single requirement.
    """
    return get_requirement_review_detail(db, tender_id=tender_id, bidder_id=bidder_id, requirement_id=requirement_id)


@router.post("/review/bidders/{bidder_id}/requirements/{requirement_id}/confirm", summary="Confirm System Decision")
def api_confirm_requirement_decision(
    bidder_id: int,
    requirement_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    req_body: OfficerConfirmRequest = OfficerConfirmRequest(),
    db: Session = Depends(get_db)
):
    """
    Officer confirms the Phase 8 system decision for a requirement.
    """
    return confirm_requirement_decision(
        db=db,
        tender_id=tender_id,
        bidder_id=bidder_id,
        requirement_id=requirement_id,
        officer_comment=req_body.officer_comment,
        officer_id=req_body.officer_id,
        officer_name=req_body.officer_name,
        officer_role=req_body.officer_role
    )


@router.post("/review/bidders/{bidder_id}/requirements/{requirement_id}/override", summary="Override System Decision")
def api_override_requirement_decision(
    bidder_id: int,
    requirement_id: int,
    req_body: OfficerOverrideRequest,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    db: Session = Depends(get_db)
):
    """
    Officer overrides the system decision for a requirement with a mandatory override reason.
    """
    return override_requirement_decision(
        db=db,
        tender_id=tender_id,
        bidder_id=bidder_id,
        requirement_id=requirement_id,
        final_decision=req_body.final_decision,
        override_reason=req_body.override_reason,
        officer_comment=req_body.officer_comment,
        officer_id=req_body.officer_id,
        officer_name=req_body.officer_name,
        officer_role=req_body.officer_role
    )


@router.post("/review/bidders/{bidder_id}/finalize", response_model=BidderReviewSummaryResponse, summary="Finalize Bidder Review")
def api_finalize_bidder_review(
    bidder_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    officer_id: str = Query("OFFICER-001"),
    db: Session = Depends(get_db)
):
    """
    Finalizes the entire compliance review for a bidder.
    """
    return finalize_bidder_review(db, tender_id=tender_id, bidder_id=bidder_id, officer_id=officer_id)


@router.post("/review/bidders/{bidder_id}/reopen", response_model=BidderReviewSummaryResponse, summary="Reopen Finalized Review")
def api_reopen_bidder_review(
    bidder_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    reason: str = Query(..., description="Mandatory reason for reopening finalized review"),
    officer_id: str = Query("OFFICER-001"),
    db: Session = Depends(get_db)
):
    """
    Reopens a finalized bidder compliance review for further officer inspection.
    """
    return reopen_bidder_review(db, tender_id=tender_id, bidder_id=bidder_id, reason=reason, officer_id=officer_id)


@router.get("/review/bidders/{bidder_id}/audit", response_model=List[OfficerReviewAuditOut], summary="Get Decision Audit Trail")
def api_get_decision_audit_trail(
    bidder_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    requirement_id: Optional[int] = Query(None, description="Optional requirement ID filter"),
    db: Session = Depends(get_db)
):
    """
    Returns complete chronological audit log entries for a bidder or requirement.
    """
    return get_decision_audit_trail(db, tender_id=tender_id, bidder_id=bidder_id, requirement_id=requirement_id)
