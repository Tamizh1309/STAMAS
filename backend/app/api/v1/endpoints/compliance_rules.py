from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.requirement import Requirement
from app.models.bidder_document import BidderDocument, BidderDocumentPage
from app.models.evidence_match import EvidenceMatch
from app.models.compliance_rule import ComplianceRule
from app.models.rule_evaluation import RuleEvaluation, EvaluationResult
from app.schemas.compliance_rule import (
    ComplianceRuleCreate,
    ComplianceRuleResponse,
    RuleEvaluationResponse,
    RuleEvaluationSummaryResponse,
    RuleEvaluateRequest,
)
from app.services.rule_engine.evaluator import RuleEngineService

router = APIRouter(
    tags=["Compliance Rule Engine"],
)


def _enrich_rule_evaluation(ev: RuleEvaluation, db: Session) -> RuleEvaluationResponse:
    """Helper to attach req_code, requirement_text, bidder_name, document_id, document_name, page_number, evidence_text for UI display."""
    req_code = None
    req_text = None
    bidder_name = None
    doc_id = None
    doc_name = None
    page_num = None
    ev_text = None

    if ev.requirement_id:
        req = db.query(Requirement).filter(Requirement.id == ev.requirement_id).first()
        if req:
            req_code = req.req_code
            req_text = req.text

    if ev.bidder_id:
        bdr = db.query(Bidder).filter(Bidder.id == ev.bidder_id).first()
        if bdr:
            bidder_name = bdr.company_name or bdr.bidder_name

    if ev.evidence_match_id:
        em = db.query(EvidenceMatch).filter(EvidenceMatch.id == ev.evidence_match_id).first()
        if em:
            ev_text = em.evidence_text
            doc_id = em.document_id
            if em.document_id:
                doc = db.query(BidderDocument).filter(BidderDocument.id == em.document_id).first()
                if doc:
                    doc_name = doc.filename
            if em.page_id:
                page = db.query(BidderDocumentPage).filter(BidderDocumentPage.id == em.page_id).first()
                if page:
                    page_num = page.page_number

    resp = RuleEvaluationResponse.model_validate(ev)
    resp.req_code = req_code
    resp.requirement_text = req_text
    resp.bidder_name = bidder_name
    resp.document_id = doc_id
    resp.document_name = doc_name
    resp.page_number = page_num
    resp.evidence_text = ev_text

    return resp


@router.post(
    "/compliance/rules/evaluate",
    response_model=List[RuleEvaluationResponse],
    status_code=status.HTTP_200_OK,
)
def evaluate_compliance_rules(
    payload: RuleEvaluateRequest,
    db: Session = Depends(get_db),
):
    """Run compliance rule engine for a single requirement or batch all requirements for a bidder."""
    if payload.requirement_id:
        try:
            evaluations = RuleEngineService.evaluate_requirement_rules_for_bidder(
                db=db,
                tender_id=payload.tender_id,
                bidder_id=payload.bidder_id,
                requirement_id=payload.requirement_id,
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    else:
        try:
            evaluations = RuleEngineService.evaluate_all_rules_for_bidder(
                db=db,
                tender_id=payload.tender_id,
                bidder_id=payload.bidder_id,
            )
        except ValueError as ve:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))

    return [_enrich_rule_evaluation(e, db) for e in evaluations]


@router.get(
    "/bidders/{bidder_id}/rule-evaluations",
    response_model=List[RuleEvaluationResponse],
)
def get_bidder_rule_evaluations(
    bidder_id: int,
    tender_id: Optional[int] = Query(None),
    evaluation_result: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all rule evaluation records for a bidder."""
    query = db.query(RuleEvaluation).filter(RuleEvaluation.bidder_id == bidder_id)

    if tender_id:
        query = query.filter(RuleEvaluation.tender_id == tender_id)
    if evaluation_result:
        query = query.filter(RuleEvaluation.evaluation_result == evaluation_result)

    evaluations = query.order_by(RuleEvaluation.id.asc()).all()
    return [_enrich_rule_evaluation(e, db) for e in evaluations]


@router.get(
    "/bidders/{bidder_id}/requirements/{requirement_id}/rule-evaluations",
    response_model=List[RuleEvaluationResponse],
)
def get_requirement_rule_evaluations(
    bidder_id: int,
    requirement_id: int,
    db: Session = Depends(get_db),
):
    """Get rule evaluations for a specific requirement and bidder."""
    evaluations = (
        db.query(RuleEvaluation)
        .filter(
            RuleEvaluation.bidder_id == bidder_id,
            RuleEvaluation.requirement_id == requirement_id,
        )
        .all()
    )
    return [_enrich_rule_evaluation(e, db) for e in evaluations]


@router.get(
    "/bidders/{bidder_id}/rule-summary",
    response_model=RuleEvaluationSummaryResponse,
)
def get_bidder_rule_summary(
    bidder_id: int,
    tender_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Get rule evaluation statistics for a bidder under a tender."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id, Bidder.tender_id == tender_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found for this tender")

    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()
    total_reqs = len(requirements)

    evaluations = (
        db.query(RuleEvaluation)
        .filter(
            RuleEvaluation.bidder_id == bidder_id,
            RuleEvaluation.tender_id == tender_id,
        )
        .all()
    )

    rules_eval_count = len(evaluations)
    satisfied_cnt = sum(1 for e in evaluations if e.evaluation_result == EvaluationResult.SATISFIED.value)
    not_satisfied_cnt = sum(1 for e in evaluations if e.evaluation_result == EvaluationResult.NOT_SATISFIED.value)
    indeterminate_cnt = sum(1 for e in evaluations if e.evaluation_result == EvaluationResult.INDETERMINATE.value)
    insufficient_ev_cnt = sum(1 for e in evaluations if e.evaluation_result == EvaluationResult.INSUFFICIENT_EVIDENCE.value)
    conflicting_ev_cnt = sum(1 for e in evaluations if e.evaluation_result == EvaluationResult.CONFLICTING_EVIDENCE.value)

    return RuleEvaluationSummaryResponse(
        bidder_id=bidder_id,
        tender_id=tender_id,
        total_requirements=total_reqs,
        rules_evaluated=rules_eval_count,
        satisfied_count=satisfied_cnt,
        not_satisfied_count=not_satisfied_cnt,
        indeterminate_count=indeterminate_cnt,
        insufficient_evidence_count=insufficient_ev_cnt,
        conflicting_evidence_count=conflicting_ev_cnt,
    )


@router.get(
    "/rules/{rule_id}",
    response_model=ComplianceRuleResponse,
)
def get_rule_detail(
    rule_id: int,
    db: Session = Depends(get_db),
):
    """Get details of a single compliance rule."""
    rule = db.query(ComplianceRule).filter(ComplianceRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Compliance rule not found")
    return rule


@router.post(
    "/requirements/{requirement_id}/rules",
    response_model=ComplianceRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_custom_rule_for_requirement(
    requirement_id: int,
    rule_in: ComplianceRuleCreate,
    db: Session = Depends(get_db),
):
    """Add a custom rule to a requirement."""
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    existing_count = db.query(ComplianceRule).filter(ComplianceRule.requirement_id == requirement_id).count()
    rule_code = rule_in.rule_code or f"RULE-{req.req_code}-{(existing_count + 1)}"

    rule = ComplianceRule(
        requirement_id=requirement_id,
        rule_code=rule_code,
        rule_type=rule_in.rule_type,
        field_name=rule_in.field_name,
        operator=rule_in.operator,
        required_value=rule_in.required_value,
        required_value_max=rule_in.required_value_max,
        unit=rule_in.unit,
        currency=rule_in.currency,
        logical_operator=rule_in.logical_operator or "ALL",
        configuration_json=rule_in.configuration_json,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
