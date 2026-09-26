import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.tender import Tender
from app.models.requirement import Requirement
from app.models.bidder import Bidder
from app.models.compliance_decision import ComplianceDecision
from app.models.officer_decision import (
    OfficerDecision, OfficerReviewAudit, FinalDecisionState,
    OfficerDecisionType, ReviewStatus, AuditAction
)
from app.models.evidence_match import EvidenceMatch
from app.models.rule_evaluation import RuleEvaluation
from app.models.rag import RAGQueryLog
from app.services.compliance.decision_engine import (
    evaluate_single_requirement_decision,
    evaluate_bidder_compliance_decisions
)


def _verify_scoping(db: Session, tender_id: int, bidder_id: int, requirement_id: Optional[int] = None):
    """
    Ensures tender_id, bidder_id, and requirement_id all belong to the same tender context.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender {tender_id} not found")

    bidder = db.query(Bidder).filter(Bidder.id == bidder_id, Bidder.tender_id == tender_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder {bidder_id} does not belong to Tender {tender_id}")

    if requirement_id:
        req = db.query(Requirement).filter(Requirement.id == requirement_id, Requirement.tender_id == tender_id).first()
        if not req:
            raise HTTPException(status_code=404, detail=f"Requirement {requirement_id} does not belong to Tender {tender_id}")
        return tender, bidder, req

    return tender, bidder, None


def _get_or_create_system_decision(db: Session, tender_id: int, bidder_id: int, requirement_id: int) -> ComplianceDecision:
    """
    Retrieves or generates Phase 8 System Compliance Decision for a requirement.
    """
    sys_dec = db.query(ComplianceDecision).filter(
        ComplianceDecision.tender_id == tender_id,
        ComplianceDecision.bidder_id == bidder_id,
        ComplianceDecision.requirement_id == requirement_id
    ).first()

    if not sys_dec:
        eval_dict = evaluate_single_requirement_decision(db, tender_id, bidder_id, requirement_id)
        sys_dec = db.query(ComplianceDecision).filter(
            ComplianceDecision.tender_id == tender_id,
            ComplianceDecision.bidder_id == bidder_id,
            ComplianceDecision.requirement_id == requirement_id
        ).first()

    return sys_dec


def confirm_requirement_decision(
    db: Session,
    tender_id: int,
    bidder_id: int,
    requirement_id: int,
    officer_comment: Optional[str] = None,
    officer_id: str = "OFFICER-001",
    officer_name: str = "Procurement Evaluation Officer",
    officer_role: str = "Senior Evaluation Officer"
) -> Dict[str, Any]:
    """
    Officer confirms the Phase 8 system decision without modification.
    """
    _verify_scoping(db, tender_id, bidder_id, requirement_id)
    sys_dec = _get_or_create_system_decision(db, tender_id, bidder_id, requirement_id)

    system_decision_val = sys_dec.decision if sys_dec else "REVIEW"

    # Check for existing officer decision
    off_dec = db.query(OfficerDecision).filter(
        OfficerDecision.tender_id == tender_id,
        OfficerDecision.bidder_id == bidder_id,
        OfficerDecision.requirement_id == requirement_id
    ).first()

    prev_final = off_dec.final_decision if off_dec else None

    if not off_dec:
        off_dec = OfficerDecision(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=requirement_id,
            system_decision_id=sys_dec.id if sys_dec else None,
            final_decision=system_decision_val,
            decision_type=OfficerDecisionType.CONFIRMED,
            officer_id=officer_id,
            officer_name=officer_name,
            officer_role=officer_role,
            officer_comment=officer_comment,
            override_reason=None,
            review_status=ReviewStatus.FINALIZED,
            finalized_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(off_dec)
    else:
        off_dec.final_decision = system_decision_val
        off_dec.decision_type = OfficerDecisionType.CONFIRMED
        off_dec.officer_id = officer_id
        off_dec.officer_name = officer_name
        off_dec.officer_role = officer_role
        off_dec.officer_comment = officer_comment
        off_dec.review_status = ReviewStatus.FINALIZED
        off_dec.finalized_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(off_dec)

    # Record Audit Log
    audit = OfficerReviewAudit(
        tender_id=tender_id,
        bidder_id=bidder_id,
        requirement_id=requirement_id,
        officer_decision_id=off_dec.id,
        officer_id=officer_id,
        officer_name=officer_name,
        officer_role=officer_role,
        action=AuditAction.DECISION_CONFIRMED,
        previous_system_decision=system_decision_val,
        previous_final_decision=prev_final,
        new_final_decision=system_decision_val,
        decision_type=OfficerDecisionType.CONFIRMED,
        comment=officer_comment
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": "Officer confirmed system decision",
        "officer_decision_id": off_dec.id,
        "requirement_id": requirement_id,
        "system_decision": system_decision_val,
        "final_decision": off_dec.final_decision,
        "decision_type": off_dec.decision_type,
        "review_status": off_dec.review_status
    }


def override_requirement_decision(
    db: Session,
    tender_id: int,
    bidder_id: int,
    requirement_id: int,
    final_decision: str,
    override_reason: str,
    officer_comment: Optional[str] = None,
    officer_id: str = "OFFICER-001",
    officer_name: str = "Procurement Evaluation Officer",
    officer_role: str = "Senior Evaluation Officer"
) -> Dict[str, Any]:
    """
    Officer overrides the system decision with an explicit reason.
    """
    _verify_scoping(db, tender_id, bidder_id, requirement_id)

    # Validate override_reason
    if not override_reason or not override_reason.strip():
        raise HTTPException(status_code=400, detail="Override reason is mandatory and cannot be empty.")
    if len(override_reason.strip()) < 10:
        raise HTTPException(status_code=400, detail="Override reason must be at least 10 characters long.")

    final_decision_upper = final_decision.upper().strip()
    if final_decision_upper not in ["PASS", "FAIL", "REVIEW"]:
        raise HTTPException(status_code=422, detail="Invalid final_decision. Must be PASS, FAIL, or REVIEW.")

    sys_dec = _get_or_create_system_decision(db, tender_id, bidder_id, requirement_id)
    system_decision_val = sys_dec.decision if sys_dec else "REVIEW"

    # Check for existing officer decision
    off_dec = db.query(OfficerDecision).filter(
        OfficerDecision.tender_id == tender_id,
        OfficerDecision.bidder_id == bidder_id,
        OfficerDecision.requirement_id == requirement_id
    ).first()

    prev_final = off_dec.final_decision if off_dec else None

    if not off_dec:
        off_dec = OfficerDecision(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=requirement_id,
            system_decision_id=sys_dec.id if sys_dec else None,
            final_decision=final_decision_upper,
            decision_type=OfficerDecisionType.OVERRIDDEN,
            officer_id=officer_id,
            officer_name=officer_name,
            officer_role=officer_role,
            officer_comment=officer_comment,
            override_reason=override_reason.strip(),
            review_status=ReviewStatus.FINALIZED,
            finalized_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(off_dec)
    else:
        off_dec.final_decision = final_decision_upper
        off_dec.decision_type = OfficerDecisionType.OVERRIDDEN
        off_dec.officer_id = officer_id
        off_dec.officer_name = officer_name
        off_dec.officer_role = officer_role
        off_dec.officer_comment = officer_comment
        off_dec.override_reason = override_reason.strip()
        off_dec.review_status = ReviewStatus.FINALIZED
        off_dec.finalized_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(off_dec)

    # Record Audit Log
    audit = OfficerReviewAudit(
        tender_id=tender_id,
        bidder_id=bidder_id,
        requirement_id=requirement_id,
        officer_decision_id=off_dec.id,
        officer_id=officer_id,
        officer_name=officer_name,
        officer_role=officer_role,
        action=AuditAction.DECISION_OVERRIDDEN,
        previous_system_decision=system_decision_val,
        previous_final_decision=prev_final,
        new_final_decision=final_decision_upper,
        decision_type=OfficerDecisionType.OVERRIDDEN,
        reason=override_reason.strip(),
        comment=officer_comment
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "message": f"Officer overridden decision to {final_decision_upper}",
        "officer_decision_id": off_dec.id,
        "requirement_id": requirement_id,
        "system_decision": system_decision_val,
        "final_decision": off_dec.final_decision,
        "decision_type": off_dec.decision_type,
        "override_reason": off_dec.override_reason,
        "review_status": off_dec.review_status
    }


def finalize_bidder_review(
    db: Session,
    tender_id: int,
    bidder_id: int,
    officer_id: str = "OFFICER-001",
    officer_name: str = "Procurement Evaluation Officer",
    officer_role: str = "Senior Evaluation Officer"
) -> Dict[str, Any]:
    """
    Finalizes all requirements for a bidder, creating overall bidder decision.
    """
    _verify_scoping(db, tender_id, bidder_id)

    # 1. Ensure Phase 8 evaluations exist
    sys_summary = evaluate_bidder_compliance_decisions(db, tender_id, bidder_id)
    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()

    # 2. Check each requirement for officer decision
    for req in requirements:
        off_dec = db.query(OfficerDecision).filter(
            OfficerDecision.tender_id == tender_id,
            OfficerDecision.bidder_id == bidder_id,
            OfficerDecision.requirement_id == req.id
        ).first()

        # If not reviewed, default confirm system decision
        if not off_dec:
            sys_dec = _get_or_create_system_decision(db, tender_id, bidder_id, req.id)
            confirm_requirement_decision(
                db=db,
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id,
                officer_comment="Auto-confirmed during final review submission.",
                officer_id=officer_id,
                officer_name=officer_name,
                officer_role=officer_role
            )

    # Record overall audit
    audit = OfficerReviewAudit(
        tender_id=tender_id,
        bidder_id=bidder_id,
        requirement_id=None,
        officer_id=officer_id,
        officer_name=officer_name,
        officer_role=officer_role,
        action=AuditAction.DECISION_FINALIZED,
        comment="All requirement reviews finalized by officer."
    )
    db.add(audit)
    db.commit()

    return get_bidder_review_summary(db, tender_id, bidder_id)


def reopen_bidder_review(
    db: Session,
    tender_id: int,
    bidder_id: int,
    reason: str,
    officer_id: str = "OFFICER-001",
    officer_name: str = "Procurement Evaluation Officer",
    officer_role: str = "Senior Evaluation Officer"
) -> Dict[str, Any]:
    """
    Reopens a finalized bidder review for further officer inspection.
    """
    _verify_scoping(db, tender_id, bidder_id)

    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Reopen reason is required.")

    off_decs = db.query(OfficerDecision).filter(
        OfficerDecision.tender_id == tender_id,
        OfficerDecision.bidder_id == bidder_id
    ).all()

    for d in off_decs:
        d.review_status = ReviewStatus.REOPENED
    db.commit()

    audit = OfficerReviewAudit(
        tender_id=tender_id,
        bidder_id=bidder_id,
        requirement_id=None,
        officer_id=officer_id,
        officer_name=officer_name,
        officer_role=officer_role,
        action=AuditAction.DECISION_REOPENED,
        reason=reason.strip(),
        comment="Officer reopened bidder compliance review."
    )
    db.add(audit)
    db.commit()

    return get_bidder_review_summary(db, tender_id, bidder_id)


def get_bidder_review_summary(db: Session, tender_id: int, bidder_id: int) -> Dict[str, Any]:
    """
    Compiles complete Officer Review Summary for a bidder.
    """
    _, bidder, _ = _verify_scoping(db, tender_id, bidder_id)

    # 1. Fetch Phase 8 System Decisions
    sys_res = evaluate_bidder_compliance_decisions(db, tender_id, bidder_id)
    sys_overall = sys_res.overall_decision if hasattr(sys_res, 'overall_decision') else sys_res.get('overall_decision', 'REVIEW')

    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()

    req_summaries = []
    confirmed_cnt = 0
    overridden_cnt = 0
    reviewed_cnt = 0
    pending_cnt = 0

    mandatory_final_decisions = []

    for req in requirements:
        sys_dec = db.query(ComplianceDecision).filter(
            ComplianceDecision.tender_id == tender_id,
            ComplianceDecision.bidder_id == bidder_id,
            ComplianceDecision.requirement_id == req.id
        ).first()

        sys_dec_val = sys_dec.decision if sys_dec else "REVIEW"
        sys_reason_val = sys_dec.reason if sys_dec else "System decision pending."

        off_dec = db.query(OfficerDecision).filter(
            OfficerDecision.tender_id == tender_id,
            OfficerDecision.bidder_id == bidder_id,
            OfficerDecision.requirement_id == req.id
        ).first()

        # Evidence & Rules
        ev_matches = db.query(EvidenceMatch).filter(
            EvidenceMatch.tender_id == tender_id,
            EvidenceMatch.bidder_id == bidder_id,
            EvidenceMatch.requirement_id == req.id
        ).all()

        rule_evals = db.query(RuleEvaluation).filter(
            RuleEvaluation.tender_id == tender_id,
            RuleEvaluation.bidder_id == bidder_id,
            RuleEvaluation.requirement_id == req.id
        ).all()

        # AI Grounded Explanation
        rag_log = db.query(RAGQueryLog).filter(
            RAGQueryLog.tender_id == tender_id,
            RAGQueryLog.bidder_id == bidder_id,
            RAGQueryLog.requirement_id == req.id
        ).order_by(RAGQueryLog.created_at.desc()).first()

        ai_exp = rag_log.ai_response if rag_log else None

        if off_dec:
            effective_dec = off_dec.final_decision
            dec_type = off_dec.decision_type
            rev_stat = off_dec.review_status
            reviewed_cnt += 1
            if off_dec.decision_type == OfficerDecisionType.CONFIRMED:
                confirmed_cnt += 1
            elif off_dec.decision_type == OfficerDecisionType.OVERRIDDEN:
                overridden_cnt += 1
            off_dec_dict = {
                "id": off_dec.id,
                "tender_id": off_dec.tender_id,
                "bidder_id": off_dec.bidder_id,
                "requirement_id": off_dec.requirement_id,
                "system_decision_id": off_dec.system_decision_id,
                "system_decision": sys_dec_val,
                "final_decision": off_dec.final_decision,
                "decision_type": off_dec.decision_type,
                "officer_id": off_dec.officer_id,
                "officer_name": off_dec.officer_name,
                "officer_role": off_dec.officer_role,
                "officer_comment": off_dec.officer_comment,
                "override_reason": off_dec.override_reason,
                "review_status": off_dec.review_status,
                "created_at": off_dec.created_at.isoformat() if off_dec.created_at else None,
                "finalized_at": off_dec.finalized_at.isoformat() if off_dec.finalized_at else None,
            }
        else:
            effective_dec = sys_dec_val
            dec_type = "SYSTEM_DECISION"
            rev_stat = "PENDING"
            pending_cnt += 1
            off_dec_dict = None

        if req.mandatory:
            mandatory_final_decisions.append((rev_stat, effective_dec))

        ev_matches_data = [
            {
                "id": ev.id,
                "document_id": ev.document_id,
                "page_id": ev.page_id,
                "evidence_text": ev.evidence_text,
                "match_status": ev.match_status,
                "confidence_score": ev.confidence_score,
                "matching_method": ev.matching_method,
                "matched_keywords": ev.matched_keywords,
                "document_filename": ev.document.filename if ev.document else f"Document #{ev.document_id}",
                "page_number": ev.page.page_number if ev.page else 1
            } for ev in ev_matches
        ]

        rule_evals_data = [
            {
                "id": rev.id,
                "rule_id": rev.rule_id,
                "rule_code": rev.rule.rule_code if rev.rule else f"RULE-{rev.rule_id}",
                "rule_type": rev.rule.rule_type if rev.rule else "GENERAL",
                "extracted_value": rev.extracted_value,
                "required_value": rev.required_value,
                "operator": rev.operator,
                "evaluation_status": rev.evaluation_status,
                "evaluation_result": rev.evaluation_result,
                "explanation": rev.explanation
            } for rev in rule_evals
        ]

        req_summaries.append({
            "requirement_id": req.id,
            "req_code": req.req_code,
            "text": req.text,
            "category": req.category,
            "is_mandatory": req.mandatory,
            "system_decision": sys_dec_val,
            "system_reason": sys_reason_val,
            "officer_decision": off_dec_dict,
            "effective_decision": effective_dec,
            "decision_type": dec_type,
            "review_status": rev_stat,
            "evidence_matches": ev_matches_data,
            "rule_evaluations": rule_evals_data,
            "ai_explanation": ai_exp
        })

    # Overall final bidder decision calculation
    if any(stat == "PENDING" for stat, _ in mandatory_final_decisions):
        final_overall = "PENDING"
        overall_review_status = "IN_PROGRESS" if reviewed_cnt > 0 else "PENDING"
    else:
        overall_review_status = "FINALIZED"
        m_decisions = [dec for _, dec in mandatory_final_decisions]
        if any(d == "FAIL" for d in m_decisions):
            final_overall = "FAIL"
        elif any(d == "REVIEW" for d in m_decisions):
            final_overall = "REVIEW"
        elif all(d == "PASS" for d in m_decisions):
            final_overall = "PASS"
        else:
            final_overall = "REVIEW"

    # Fetch audit logs
    audits = db.query(OfficerReviewAudit).filter(
        OfficerReviewAudit.tender_id == tender_id,
        OfficerReviewAudit.bidder_id == bidder_id
    ).order_by(OfficerReviewAudit.timestamp.desc()).all()

    audit_data = [
        {
            "id": a.id,
            "tender_id": a.tender_id,
            "bidder_id": a.bidder_id,
            "requirement_id": a.requirement_id,
            "officer_decision_id": a.officer_decision_id,
            "officer_id": a.officer_id,
            "officer_name": a.officer_name,
            "officer_role": a.officer_role,
            "action": a.action,
            "previous_system_decision": a.previous_system_decision,
            "previous_final_decision": a.previous_final_decision,
            "new_final_decision": a.new_final_decision,
            "decision_type": a.decision_type,
            "reason": a.reason,
            "comment": a.comment,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None
        } for a in audits
    ]

    return {
        "tender_id": tender_id,
        "bidder_id": bidder_id,
        "bidder_name": bidder.bidder_name,
        "company_name": bidder.company_name,
        "system_overall_decision": sys_overall,
        "final_overall_decision": final_overall,
        "review_status": overall_review_status,
        "total_requirements": len(requirements),
        "reviewed_count": reviewed_cnt,
        "pending_count": pending_cnt,
        "confirmed_count": confirmed_cnt,
        "overridden_count": overridden_cnt,
        "requirements": req_summaries,
        "audits": audit_data
    }


def get_requirement_review_detail(db: Session, tender_id: int, bidder_id: int, requirement_id: int) -> Dict[str, Any]:
    """
    Retrieves complete evidence traceability chain and decision details for a requirement.
    """
    summary = get_bidder_review_summary(db, tender_id, bidder_id)
    for req in summary["requirements"]:
        if req["requirement_id"] == requirement_id:
            return req
    raise HTTPException(status_code=404, detail=f"Requirement {requirement_id} not found for Bidder {bidder_id}")


def get_decision_audit_trail(db: Session, tender_id: int, bidder_id: int, requirement_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves chronological audit log entries for a bidder or specific requirement.
    """
    _verify_scoping(db, tender_id, bidder_id, requirement_id)
    query = db.query(OfficerReviewAudit).filter(
        OfficerReviewAudit.tender_id == tender_id,
        OfficerReviewAudit.bidder_id == bidder_id
    )
    if requirement_id:
        query = query.filter(OfficerReviewAudit.requirement_id == requirement_id)

    audits = query.order_by(OfficerReviewAudit.timestamp.asc()).all()

    return [
        {
            "id": a.id,
            "tender_id": a.tender_id,
            "bidder_id": a.bidder_id,
            "requirement_id": a.requirement_id,
            "officer_decision_id": a.officer_decision_id,
            "officer_id": a.officer_id,
            "officer_name": a.officer_name,
            "officer_role": a.officer_role,
            "action": a.action,
            "previous_system_decision": a.previous_system_decision,
            "previous_final_decision": a.previous_final_decision,
            "new_final_decision": a.new_final_decision,
            "decision_type": a.decision_type,
            "reason": a.reason,
            "comment": a.comment,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None
        } for a in audits
    ]
