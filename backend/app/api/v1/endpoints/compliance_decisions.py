from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.requirement import Requirement
from app.models.compliance_decision import ComplianceDecision
from app.schemas.compliance_decision import (
    DecisionEvaluateRequest,
    ComplianceDecisionResponse,
    RequirementDecisionSummary,
)
from app.services.compliance.decision_engine import (
    evaluate_single_requirement_decision,
    evaluate_bidder_compliance_decisions,
)

router = APIRouter()


@router.post("/evaluate", response_model=ComplianceDecisionResponse)
@router.post("/decisions/evaluate", response_model=ComplianceDecisionResponse)
def evaluate_compliance_decisions_endpoint(
    request: DecisionEvaluateRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluates all requirements for a bidder in a tender, converting evidence and rule evaluations
    into PASS / FAIL / REVIEW SYSTEM_DECISIONS.
    """
    tender = db.query(Tender).filter(Tender.id == request.tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    bidder = db.query(Bidder).filter(Bidder.id == request.bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    try:
        response = evaluate_bidder_compliance_decisions(
            db=db,
            tender_id=request.tender_id,
            bidder_id=request.bidder_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance decision evaluation failed: {str(e)}")


@router.get("/bidders/{bidder_id}/compliance-summary", response_model=ComplianceDecisionResponse)
def get_bidder_compliance_summary(
    bidder_id: int,
    tender_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns the overall compliance summary and requirement decisions for a bidder.
    If no decision exists yet, auto-evaluates.
    """
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    return evaluate_bidder_compliance_decisions(
        db=db,
        tender_id=tender_id,
        bidder_id=bidder_id
    )


@router.get("/bidders/{bidder_id}/requirements/{requirement_id}/decision", response_model=RequirementDecisionSummary)
def get_requirement_decision_endpoint(
    bidder_id: int,
    requirement_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns the requirement-level system decision with full traceability down to rule evaluations
    and evidence matches.
    """
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    return evaluate_single_requirement_decision(
        db=db,
        requirement=req,
        bidder_id=bidder_id
    )


@router.get("/decisions/{decision_id}")
def get_decision_detail(
    decision_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns full detail of a ComplianceDecision record by ID.
    """
    decision = db.query(ComplianceDecision).filter(ComplianceDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Compliance decision not found")

    return {
        "id": decision.id,
        "tender_id": decision.tender_id,
        "bidder_id": decision.bidder_id,
        "requirement_id": decision.requirement_id,
        "decision": decision.decision,
        "decision_type": decision.decision_type,
        "is_mandatory": decision.is_mandatory,
        "reason": decision.reason,
        "rule_summary": decision.rule_summary_json,
        "evidence_summary": decision.evidence_summary_json,
        "created_at": str(decision.created_at),
        "updated_at": str(decision.updated_at)
    }


@router.post("/decisions/{decision_id}/re-evaluate", response_model=ComplianceDecisionResponse)
def reevaluate_decision(
    decision_id: int,
    db: Session = Depends(get_db)
):
    """
    Recalculates system decision for the target decision's bidder and tender.
    """
    decision = db.query(ComplianceDecision).filter(ComplianceDecision.id == decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Compliance decision not found")

    return evaluate_bidder_compliance_decisions(
        db=db,
        tender_id=decision.tender_id,
        bidder_id=decision.bidder_id
    )
