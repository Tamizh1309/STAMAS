from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.requirement import Requirement
from app.models.bidder_document import BidderDocument, BidderDocumentPage
from app.models.evidence_match import EvidenceMatch, MatchStatus
from app.schemas.evidence_match import (
    EvidenceMatchResponse,
    EvidenceSummaryResponse,
    MatchRunRequest,
)
from app.services.evidence_matcher.matcher import EvidenceMatcherService

router = APIRouter(
    tags=["Evidence Matching Engine"],
)


def _enrich_evidence_match(match: EvidenceMatch, db: Session) -> EvidenceMatchResponse:
    """Helper to attach document_name, page_number, req_code, requirement_text, bidder_name for UI display."""
    doc_name = None
    page_num = None
    req_code = None
    req_text = None
    bidder_name = None

    if match.document_id:
        doc = db.query(BidderDocument).filter(BidderDocument.id == match.document_id).first()
        if doc:
            doc_name = doc.filename
    
    if match.page_id:
        page = db.query(BidderDocumentPage).filter(BidderDocumentPage.id == match.page_id).first()
        if page:
            page_num = page.page_number

    if match.requirement_id:
        req = db.query(Requirement).filter(Requirement.id == match.requirement_id).first()
        if req:
            req_code = req.req_code
            req_text = req.text

    if match.bidder_id:
        bdr = db.query(Bidder).filter(Bidder.id == match.bidder_id).first()
        if bdr:
            bidder_name = bdr.company_name or bdr.bidder_name

    resp = EvidenceMatchResponse.model_validate(match)
    resp.document_name = doc_name
    resp.page_number = page_num
    resp.req_code = req_code
    resp.requirement_text = req_text
    resp.bidder_name = bidder_name

    return resp


@router.post(
    "/tenders/{tender_id}/bidders/{bidder_id}/requirements/{requirement_id}/match",
    response_model=List[EvidenceMatchResponse],
    status_code=status.HTTP_200_OK,
)
def match_single_requirement(
    tender_id: int,
    bidder_id: int,
    requirement_id: int,
    db: Session = Depends(get_db),
):
    """Run evidence matching for a single tender requirement and bidder."""
    try:
        matches = EvidenceMatcherService.match_requirement_for_bidder(
            db=db,
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=requirement_id,
        )
        return [_enrich_evidence_match(m, db) for m in matches]
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post(
    "/evidence-matches/run",
    response_model=List[EvidenceMatchResponse],
    status_code=status.HTTP_200_OK,
)
def run_evidence_matching(
    payload: MatchRunRequest,
    db: Session = Depends(get_db),
):
    """Batch or single evidence matching endpoint."""
    if payload.requirement_id:
        try:
            matches = EvidenceMatcherService.match_requirement_for_bidder(
                db=db,
                tender_id=payload.tender_id,
                bidder_id=payload.bidder_id,
                requirement_id=payload.requirement_id,
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    else:
        try:
            matches = EvidenceMatcherService.match_all_requirements_for_bidder(
                db=db,
                tender_id=payload.tender_id,
                bidder_id=payload.bidder_id,
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    return [_enrich_evidence_match(m, db) for m in matches]


@router.get(
    "/bidders/{bidder_id}/evidence-matches",
    response_model=List[EvidenceMatchResponse],
)
def get_bidder_evidence_matches(
    bidder_id: int,
    tender_id: Optional[int] = Query(None),
    requirement_id: Optional[int] = Query(None),
    match_status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all evidence matches for a bidder."""
    query = db.query(EvidenceMatch).filter(EvidenceMatch.bidder_id == bidder_id)

    if tender_id:
        query = query.filter(EvidenceMatch.tender_id == tender_id)
    if requirement_id:
        query = query.filter(EvidenceMatch.requirement_id == requirement_id)
    if match_status:
        query = query.filter(EvidenceMatch.match_status == match_status)

    matches = query.order_by(EvidenceMatch.confidence_score.desc()).all()
    return [_enrich_evidence_match(m, db) for m in matches]


@router.get(
    "/bidders/{bidder_id}/requirements/{requirement_id}/evidence",
    response_model=List[EvidenceMatchResponse],
)
def get_requirement_evidence_for_bidder(
    bidder_id: int,
    requirement_id: int,
    db: Session = Depends(get_db),
):
    """Get evidence matches for a specific bidder and requirement."""
    matches = (
        db.query(EvidenceMatch)
        .filter(
            EvidenceMatch.bidder_id == bidder_id,
            EvidenceMatch.requirement_id == requirement_id,
        )
        .order_by(EvidenceMatch.confidence_score.desc())
        .all()
    )
    return [_enrich_evidence_match(m, db) for m in matches]


@router.get(
    "/bidders/{bidder_id}/evidence-summary",
    response_model=EvidenceSummaryResponse,
)
def get_bidder_evidence_summary(
    bidder_id: int,
    tender_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Get evidence retrieval statistics for a bidder under a tender."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id, Bidder.tender_id == tender_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found for this tender")

    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()
    total_reqs = len(requirements)

    matches = db.query(EvidenceMatch).filter(
        EvidenceMatch.bidder_id == bidder_id,
        EvidenceMatch.tender_id == tender_id
    ).all()

    # Group by requirement to find highest status match per requirement
    req_status_map = {}
    for req in requirements:
        req_matches = [m for m in matches if m.requirement_id == req.id]
        if not req_matches:
            req_status_map[req.id] = MatchStatus.NOT_FOUND.value
        else:
            # Highest confidence match determines requirement evidence status
            best_match = max(req_matches, key=lambda x: x.confidence_score)
            req_status_map[req.id] = best_match.match_status

    matched_cnt = sum(1 for s in req_status_map.values() if s == MatchStatus.MATCHED.value)
    partial_cnt = sum(1 for s in req_status_map.values() if s == MatchStatus.PARTIAL.value)
    low_conf_cnt = sum(1 for s in req_status_map.values() if s == MatchStatus.LOW_CONFIDENCE.value)
    not_found_cnt = sum(1 for s in req_status_map.values() if s == MatchStatus.NOT_FOUND.value)

    return EvidenceSummaryResponse(
        bidder_id=bidder_id,
        tender_id=tender_id,
        total_requirements=total_reqs,
        matched_count=matched_cnt,
        partial_count=partial_cnt,
        low_confidence_count=low_conf_cnt,
        not_found_count=not_found_cnt,
    )


@router.get(
    "/evidence-matches/{match_id}",
    response_model=EvidenceMatchResponse,
)
def get_evidence_match_detail(
    match_id: int,
    db: Session = Depends(get_db),
):
    """Get details of a single evidence match record."""
    match = db.query(EvidenceMatch).filter(EvidenceMatch.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Evidence match not found")
    return _enrich_evidence_match(match, db)
