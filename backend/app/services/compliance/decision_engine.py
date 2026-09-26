from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.requirement import Requirement
from app.models.evidence_match import EvidenceMatch
from app.models.compliance_rule import ComplianceRule, RuleType
from app.models.rule_evaluation import RuleEvaluation, EvaluationResult
from app.models.compliance_decision import ComplianceDecision, DecisionState, DecisionType
from app.schemas.compliance_decision import (
    RequirementDecisionSummary,
    OverallDecisionSummary,
    ComplianceDecisionResponse,
)
from app.services.rule_engine import RuleEngineService
from app.services.rag.generator import generate_grounded_response
from app.services.rag.retriever import retrieve_chunks


def evaluate_single_requirement_decision(
    db: Session,
    requirement: Requirement,
    bidder_id: int
) -> RequirementDecisionSummary:
    """
    Evaluates a single requirement for a bidder, producing a deterministic
    PASS / FAIL / REVIEW decision based on Phase 5 Evidence & Phase 6 Rule Evaluations.
    """
    tender_id = requirement.tender_id
    requirement_id = requirement.id
    is_mandatory = getattr(requirement, 'mandatory', True)

    # Fetch existing Phase 6 Rule Evaluations for this requirement & bidder
    rule_evals = db.query(RuleEvaluation).filter(
        RuleEvaluation.requirement_id == requirement_id,
        RuleEvaluation.bidder_id == bidder_id
    ).all()

    # If no rule evaluations exist, run rule engine on demand
    if not rule_evals:
        rule_evals = RuleEngineService.evaluate_requirement_rules_for_bidder(
            db=db,
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=requirement_id
        )

    # Fetch Phase 5 Evidence Matches
    evidence_matches = db.query(EvidenceMatch).filter(
        EvidenceMatch.requirement_id == requirement_id,
        EvidenceMatch.bidder_id == bidder_id
    ).all()

    # Serialized evidence list
    evidence_list = []
    for em in evidence_matches:
        doc_name = em.bidder_document.original_filename if em.bidder_document else "Document"
        evidence_list.append({
            "match_id": em.id,
            "document_id": em.document_id,
            "document_name": doc_name,
            "page_number": em.page_number,
            "evidence_text": em.evidence_text,
            "match_status": str(em.match_status),
            "confidence_score": em.confidence_score
        })

    # Serialized rule evaluation list
    eval_list = []
    passed_rules = 0
    failed_rules = 0
    review_rules = 0

    for rev in rule_evals:
        result_str = str(rev.evaluation_result.value if hasattr(rev.evaluation_result, 'value') else rev.evaluation_result)
        eval_list.append({
            "evaluation_id": rev.id,
            "rule_id": rev.rule_id,
            "rule_code": rev.rule.rule_code if rev.rule else "RULE",
            "evaluation_result": result_str,
            "detected_value": rev.extracted_value,
            "required_value": rev.required_value,
            "explanation": rev.explanation
        })

        if result_str == "SATISFIED":
            passed_rules += 1
        elif result_str == "NOT_SATISFIED":
            failed_rules += 1
        else: # INDETERMINATE, INSUFFICIENT_EVIDENCE, CONFLICTING_EVIDENCE
            review_rules += 1

    rule_count = len(rule_evals)

    # Multi-rule logical operator check (default ALL)
    first_rule = rule_evals[0].rule if rule_evals and rule_evals[0].rule else None
    logical_operator = first_rule.logical_operator if first_rule and hasattr(first_rule, 'logical_operator') else "ALL"

    # Deterministic Decision Matrix
    decision = DecisionState.REVIEW
    reason = ""

    if rule_count == 0 or not evidence_matches:
        decision = DecisionState.REVIEW
        reason = "Requirement could not be evaluated due to missing or insufficient bidder evidence."
    elif logical_operator == "ANY":
        if passed_rules > 0:
            decision = DecisionState.PASS
            reason = f"At least one compliance rule was satisfied ({passed_rules}/{rule_count} rules passed)."
        elif failed_rules == rule_count:
            decision = DecisionState.FAIL
            reason = f"All compliance rules failed evaluation ({failed_rules}/{rule_count} rules failed)."
        else:
            decision = DecisionState.REVIEW
            reason = "No compliance rule was satisfied, and available evidence requires officer review."
    else: # Default: ALL logic
        if failed_rules > 0:
            decision = DecisionState.FAIL
            failed_explanations = [e['explanation'] for e in eval_list if e['evaluation_result'] == 'NOT_SATISFIED']
            reason = f"Deterministic rule failure: {'; '.join(failed_explanations[:2])}"
        elif passed_rules == rule_count and rule_count > 0:
            decision = DecisionState.PASS
            reason = f"All mandatory compliance rules for this requirement were evaluated and satisfied ({passed_rules}/{rule_count} passed)."
        else:
            decision = DecisionState.REVIEW
            reason = "Evidence was identified but contains unverified, indeterminate, or conflicting values requiring officer review."

    # Grounded AI explanation (Phase 7 RAG integration)
    ai_explanation = None
    try:
        chunks = retrieve_chunks(
            db=db,
            tender_id=tender_id,
            bidder_id=bidder_id,
            query=requirement.requirement_text,
            requirement_id=requirement_id,
            top_k=2,
            method="HYBRID"
        )
        if chunks:
            rag_res = generate_grounded_response(
                query=f"Explain evidence for requirement: {requirement.requirement_text}",
                retrieved_chunks=chunks,
                requirement_text=requirement.requirement_text
            )
            ai_explanation = rag_res.get("answer")
    except Exception:
        ai_explanation = None

    # Upsert requirement-level ComplianceDecision record
    existing = db.query(ComplianceDecision).filter(
        ComplianceDecision.tender_id == tender_id,
        ComplianceDecision.bidder_id == bidder_id,
        ComplianceDecision.requirement_id == requirement_id
    ).first()

    if existing:
        existing.decision = decision
        existing.reason = reason
        existing.is_mandatory = is_mandatory
        existing.rule_summary_json = eval_list
        existing.evidence_summary_json = evidence_list
    else:
        new_dec = ComplianceDecision(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=requirement_id,
            decision=decision,
            decision_type=DecisionType.SYSTEM_DECISION,
            is_mandatory=is_mandatory,
            reason=reason,
            rule_summary_json=eval_list,
            evidence_summary_json=evidence_list
        )
        db.add(new_dec)

    db.commit()

    return RequirementDecisionSummary(
        requirement_id=requirement_id,
        req_code=requirement.requirement_code,
        requirement_text=requirement.requirement_text,
        category=requirement.category.value if hasattr(requirement.category, 'value') else str(requirement.category),
        is_mandatory=is_mandatory,
        decision=decision,
        decision_type=DecisionType.SYSTEM_DECISION,
        reason=reason,
        rule_count=rule_count,
        passed_rules=passed_rules,
        failed_rules=failed_rules,
        review_rules=review_rules,
        evidence_matches=evidence_list,
        rule_evaluations=eval_list,
        ai_explanation=ai_explanation
    )


def evaluate_bidder_compliance_decisions(
    db: Session,
    tender_id: int,
    bidder_id: int
) -> ComplianceDecisionResponse:
    """
    Evaluates all requirements for a bidder in a tender, aggregates mandatory & optional
    requirements, and determines the overall bidder SYSTEM_DECISION.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise ValueError("Tender not found")

    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise ValueError("Bidder not found")

    requirements = db.query(Requirement).filter(Requirement.tender_id == tender_id).all()

    req_summaries: List[RequirementDecisionSummary] = []

    for req in requirements:
        req_dec = evaluate_single_requirement_decision(db, req, bidder_id)
        req_summaries.append(req_dec)

    # Aggregation Counters
    mandatory_reqs = [r for r in req_summaries if r.is_mandatory]
    optional_reqs = [r for r in req_summaries if not r.is_mandatory]

    mandatory_pass = sum(1 for r in mandatory_reqs if r.decision == DecisionState.PASS)
    mandatory_fail = sum(1 for r in mandatory_reqs if r.decision == DecisionState.FAIL)
    mandatory_review = sum(1 for r in mandatory_reqs if r.decision == DecisionState.REVIEW)

    optional_pass = sum(1 for r in optional_reqs if r.decision == DecisionState.PASS)
    optional_fail = sum(1 for r in optional_reqs if r.decision == DecisionState.FAIL)
    optional_review = sum(1 for r in optional_reqs if r.decision == DecisionState.REVIEW)

    # Deterministic Overall Bidder Decision Priority Logic (for Mandatory Requirements)
    if mandatory_fail > 0:
        overall_decision = DecisionState.FAIL
        overall_reason = f"{mandatory_fail} mandatory tender requirement(s) failed deterministic compliance rule evaluation."
    elif mandatory_review > 0 or (len(mandatory_reqs) == 0 and len(req_summaries) > 0 and sum(1 for r in req_summaries if r.decision == DecisionState.REVIEW) > 0):
        overall_decision = DecisionState.REVIEW
        overall_reason = f"{mandatory_review} mandatory tender requirement(s) require officer review due to unverified or insufficient evidence."
    elif len(mandatory_reqs) > 0 and mandatory_pass == len(mandatory_reqs):
        overall_decision = DecisionState.PASS
        overall_reason = f"All {mandatory_pass} mandatory tender requirements passed deterministic compliance rule evaluations."
    elif len(req_summaries) > 0 and sum(1 for r in req_summaries if r.decision == DecisionState.PASS) == len(req_summaries):
        overall_decision = DecisionState.PASS
        overall_reason = "All tender requirements passed deterministic compliance rule evaluations."
    else:
        overall_decision = DecisionState.REVIEW
        overall_reason = "Requirement evidence requires officer verification."

    summary = OverallDecisionSummary(
        total_requirements=len(req_summaries),
        mandatory_requirements=len(mandatory_reqs),
        optional_requirements=len(optional_reqs),
        pass_count=mandatory_pass,
        fail_count=mandatory_fail,
        review_count=mandatory_review,
        optional_pass_count=optional_pass,
        optional_fail_count=optional_fail,
        optional_review_count=optional_review
    )

    # Upsert Overall Bidder ComplianceDecision record (requirement_id is None)
    existing_overall = db.query(ComplianceDecision).filter(
        ComplianceDecision.tender_id == tender_id,
        ComplianceDecision.bidder_id == bidder_id,
        ComplianceDecision.requirement_id.is_(None)
    ).first()

    if existing_overall:
        existing_overall.decision = overall_decision
        existing_overall.reason = overall_reason
        existing_overall.rule_summary_json = {
            "pass_count": mandatory_pass,
            "fail_count": mandatory_fail,
            "review_count": mandatory_review
        }
        existing_overall.evidence_summary_json = {
            "total_requirements": len(req_summaries)
        }
        db.commit()
        db.refresh(existing_overall)
        overall_id = existing_overall.id
        created_at_str = str(existing_overall.created_at)
        updated_at_str = str(existing_overall.updated_at)
    else:
        new_overall = ComplianceDecision(
            tender_id=tender_id,
            bidder_id=bidder_id,
            requirement_id=None,
            decision=overall_decision,
            decision_type=DecisionType.SYSTEM_DECISION,
            is_mandatory=True,
            reason=overall_reason,
            rule_summary_json={
                "pass_count": mandatory_pass,
                "fail_count": mandatory_fail,
                "review_count": mandatory_review
            },
            evidence_summary_json={
                "total_requirements": len(req_summaries)
            }
        )
        db.add(new_overall)
        db.commit()
        db.refresh(new_overall)
        overall_id = new_overall.id
        created_at_str = str(new_overall.created_at)
        updated_at_str = str(new_overall.updated_at)

    return ComplianceDecisionResponse(
        id=overall_id,
        tender_id=tender_id,
        bidder_id=bidder_id,
        bidder_name=bidder.company_name,
        decision_type=DecisionType.SYSTEM_DECISION,
        overall_decision=overall_decision,
        reason=overall_reason,
        summary=summary,
        requirements=req_summaries,
        created_at=created_at_str,
        updated_at=updated_at_str
    )
