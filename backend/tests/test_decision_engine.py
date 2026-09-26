import pytest
from app.models.tender import Tender
from app.models.requirement import Requirement, RequirementCategory
from app.models.bidder import Bidder
from app.models.bidder_document import BidderDocument, BidderDocumentPage, DocumentCategory, DocumentProcessingStatus
from app.models.evidence_match import EvidenceMatch, MatchStatus, MatchingMethod
from app.models.compliance_rule import ComplianceRule, RuleType
from app.models.rule_evaluation import RuleEvaluation, EvaluationResult, EvaluationStatus
from app.models.compliance_decision import ComplianceDecision, DecisionState, DecisionType
from app.services.compliance.decision_engine import (
    evaluate_single_requirement_decision,
    evaluate_bidder_compliance_decisions,
)


def test_single_requirement_decision_pass(db):
    tender = Tender(tender_id="T-PASS", title="Pass Tender", department="GeM", status="PROCESSED")
    db.add(tender)
    db.commit()

    req = Requirement(tender_id=tender.id, req_code="REQ-01", text="Minimum turnover ₹10 Cr", mandatory=True, category=RequirementCategory.FINANCIAL)
    db.add(req)
    db.commit()

    bidder = Bidder(bidder_name="Pass Bidder", company_name="Pass Bidder", email="pass@test.com", tender_id=tender.id)
    db.add(bidder)
    db.commit()

    doc = BidderDocument(bidder_id=bidder.id, tender_id=tender.id, filename="financials.pdf", stored_filename="fin.pdf", file_path="/data/fin.pdf", category=DocumentCategory.FINANCIAL, processing_status=DocumentProcessingStatus.PROCESSED)
    db.add(doc)
    db.commit()

    page = BidderDocumentPage(document_id=doc.id, page_number=12, extracted_text="Average annual turnover for preceding 3 years is ₹12.5 crore.")
    db.add(page)
    db.commit()

    match = EvidenceMatch(tender_id=tender.id, requirement_id=req.id, bidder_id=bidder.id, document_id=doc.id, page_id=page.id, evidence_text="Average annual turnover for preceding 3 years is ₹12.5 crore.", confidence_score=0.95, match_status=MatchStatus.MATCHED, matching_method=MatchingMethod.SEMANTIC)
    db.add(match)

    rule = ComplianceRule(requirement_id=req.id, rule_code="RULE_TURNOVER", rule_type=RuleType.NUMERIC_MIN, field_name="turnover", required_value="10")
    db.add(rule)
    db.commit()

    rule_eval = RuleEvaluation(rule_id=rule.id, requirement_id=req.id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=match.id, evaluation_status=EvaluationStatus.EVALUATED, evaluation_result=EvaluationResult.SATISFIED, extracted_value="12.5", required_value="10", explanation="₹12.5 crore meets or exceeds required minimum of ₹10 crore.")
    db.add(rule_eval)
    db.commit()

    res = evaluate_single_requirement_decision(db, req, bidder.id)
    assert res.decision == "PASS"
    assert res.decision_type == "SYSTEM_DECISION"
    assert "satisfied" in res.reason.lower()


def test_single_requirement_decision_fail(db):
    tender = Tender(tender_id="T-FAIL", title="Fail Tender", department="GeM", status="PROCESSED")
    db.add(tender)
    db.commit()

    req = Requirement(tender_id=tender.id, req_code="REQ-02", text="Minimum turnover ₹10 Cr", mandatory=True, category=RequirementCategory.FINANCIAL)
    db.add(req)
    db.commit()

    bidder = Bidder(bidder_name="Fail Bidder", company_name="Fail Bidder", email="fail@test.com", tender_id=tender.id)
    db.add(bidder)
    db.commit()

    doc = BidderDocument(bidder_id=bidder.id, tender_id=tender.id, filename="financials.pdf", stored_filename="fin.pdf", file_path="/data/fin.pdf", category=DocumentCategory.FINANCIAL, processing_status=DocumentProcessingStatus.PROCESSED)
    db.add(doc)
    db.commit()

    page = BidderDocumentPage(document_id=doc.id, page_number=12, extracted_text="Average annual turnover is ₹7 crore.")
    db.add(page)
    db.commit()

    match = EvidenceMatch(tender_id=tender.id, requirement_id=req.id, bidder_id=bidder.id, document_id=doc.id, page_id=page.id, evidence_text="Average annual turnover is ₹7 crore.", confidence_score=0.95, match_status=MatchStatus.MATCHED, matching_method=MatchingMethod.SEMANTIC)
    db.add(match)

    rule = ComplianceRule(requirement_id=req.id, rule_code="RULE_TURNOVER", rule_type=RuleType.NUMERIC_MIN, field_name="turnover", required_value="10")
    db.add(rule)
    db.commit()

    rule_eval = RuleEvaluation(rule_id=rule.id, requirement_id=req.id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=match.id, evaluation_status=EvaluationStatus.EVALUATED, evaluation_result=EvaluationResult.NOT_SATISFIED, extracted_value="7", required_value="10", explanation="Detected turnover of ₹7 crore is below required minimum threshold of ₹10 crore.")
    db.add(rule_eval)
    db.commit()

    res = evaluate_single_requirement_decision(db, req, bidder.id)
    assert res.decision == "FAIL"
    assert "below required minimum" in res.reason.lower()


def test_missing_evidence_produces_review(db):
    tender = Tender(tender_id="T-MISS", title="Missing Tender", department="GeM", status="PROCESSED")
    db.add(tender)
    db.commit()

    req = Requirement(tender_id=tender.id, req_code="REQ-03", text="ISO 9001 certification required", mandatory=True, category=RequirementCategory.TECHNICAL)
    db.add(req)
    db.commit()

    bidder = Bidder(bidder_name="No Evidence Bidder", company_name="No Evidence Bidder", email="none@test.com", tender_id=tender.id)
    db.add(bidder)
    db.commit()

    rule = ComplianceRule(requirement_id=req.id, rule_code="RULE_ISO", rule_type=RuleType.CERTIFICATION_REQUIRED, required_value="ISO 9001")
    db.add(rule)
    db.commit()

    rule_eval = RuleEvaluation(rule_id=rule.id, requirement_id=req.id, bidder_id=bidder.id, tender_id=tender.id, evaluation_status=EvaluationStatus.INSUFFICIENT_EVIDENCE, evaluation_result=EvaluationResult.INSUFFICIENT_EVIDENCE, explanation="No bidder document evidence found for ISO 9001.")
    db.add(rule_eval)
    db.commit()

    res = evaluate_single_requirement_decision(db, req, bidder.id)
    assert res.decision == "REVIEW"
    assert res.decision != "FAIL" # Must NOT auto-fail on missing evidence


def test_overall_bidder_decision_priority(db):
    tender = Tender(tender_id="T-OVERALL", title="Overall Tender", department="GeM", status="PROCESSED")
    db.add(tender)
    db.commit()

    r1 = Requirement(tender_id=tender.id, req_code="R1", text="Turnover >= 10", mandatory=True, category=RequirementCategory.FINANCIAL)
    r2 = Requirement(tender_id=tender.id, req_code="R2", text="Experience >= 5", mandatory=True, category=RequirementCategory.TECHNICAL)
    r3 = Requirement(tender_id=tender.id, req_code="R3", text="Optional ISO", mandatory=False, category=RequirementCategory.TECHNICAL)
    db.add_all([r1, r2, r3])
    db.commit()

    bidder = Bidder(bidder_name="Priority Bidder", company_name="Priority Bidder", email="priority@test.com", tender_id=tender.id)
    db.add(bidder)
    db.commit()

    doc = BidderDocument(bidder_id=bidder.id, tender_id=tender.id, filename="doc.pdf", stored_filename="doc.pdf", file_path="/data/doc.pdf", category=DocumentCategory.FINANCIAL, processing_status=DocumentProcessingStatus.PROCESSED)
    db.add(doc)
    db.commit()

    page = BidderDocumentPage(document_id=doc.id, page_number=1, extracted_text="Turnover 12 Cr. Experience 7 years.")
    db.add(page)
    db.commit()

    rule1 = ComplianceRule(requirement_id=r1.id, rule_code="RULE-1", rule_type=RuleType.NUMERIC_MIN, required_value="10")
    rule2 = ComplianceRule(requirement_id=r2.id, rule_code="RULE-2", rule_type=RuleType.NUMERIC_MIN, required_value="5")
    rule3 = ComplianceRule(requirement_id=r3.id, rule_code="RULE-3", rule_type=RuleType.CERTIFICATION_REQUIRED, required_value="ISO")
    db.add_all([rule1, rule2, rule3])
    db.commit()

    eval1 = RuleEvaluation(rule_id=rule1.id, requirement_id=r1.id, bidder_id=bidder.id, tender_id=tender.id, evaluation_status=EvaluationStatus.EVALUATED, evaluation_result=EvaluationResult.SATISFIED, extracted_value="12", explanation="Passed")
    eval2 = RuleEvaluation(rule_id=rule2.id, requirement_id=r2.id, bidder_id=bidder.id, tender_id=tender.id, evaluation_status=EvaluationStatus.EVALUATED, evaluation_result=EvaluationResult.SATISFIED, extracted_value="7", explanation="Passed")
    eval3 = RuleEvaluation(rule_id=rule3.id, requirement_id=r3.id, bidder_id=bidder.id, tender_id=tender.id, evaluation_status=EvaluationStatus.EVALUATED, evaluation_result=EvaluationResult.NOT_SATISFIED, explanation="Optional failed")
    db.add_all([eval1, eval2, eval3])
    db.commit()

    # Add evidence match records so decision engine sees evidence matched
    em1 = EvidenceMatch(tender_id=tender.id, requirement_id=r1.id, bidder_id=bidder.id, document_id=doc.id, page_id=page.id, evidence_text="Turnover 12 Cr", confidence_score=0.9, match_status=MatchStatus.MATCHED)
    em2 = EvidenceMatch(tender_id=tender.id, requirement_id=r2.id, bidder_id=bidder.id, document_id=doc.id, page_id=page.id, evidence_text="Experience 7 years", confidence_score=0.9, match_status=MatchStatus.MATCHED)
    em3 = EvidenceMatch(tender_id=tender.id, requirement_id=r3.id, bidder_id=bidder.id, document_id=doc.id, page_id=page.id, evidence_text="ISO missing", confidence_score=0.9, match_status=MatchStatus.MATCHED)
    db.add_all([em1, em2, em3])
    db.commit()

    res = evaluate_bidder_compliance_decisions(db, tender.id, bidder.id)
    # Optional requirement failed, but all mandatory requirements passed -> Overall PASS!
    assert res.overall_decision == "PASS"
    assert res.summary.mandatory_requirements == 2
    assert res.summary.optional_requirements == 1
    assert res.summary.pass_count == 2
    assert res.summary.optional_fail_count == 1


def test_api_compliance_decisions_flow(db, client):
    tender = Tender(tender_id="T-API-DEC", title="API Decision Tender", department="GeM", status="PROCESSED")
    db.add(tender)
    db.commit()

    req = Requirement(tender_id=tender.id, req_code="REQ-API", text="Minimum turnover ₹10 Cr", mandatory=True, category=RequirementCategory.FINANCIAL)
    db.add(req)
    db.commit()

    bidder = Bidder(bidder_name="API Bidder", company_name="API Bidder", email="api@test.com", tender_id=tender.id)
    db.add(bidder)
    db.commit()

    doc = BidderDocument(bidder_id=bidder.id, tender_id=tender.id, filename="fin.pdf", stored_filename="fin.pdf", file_path="/data/fin.pdf", category=DocumentCategory.FINANCIAL, processing_status=DocumentProcessingStatus.PROCESSED)
    db.add(doc)
    db.commit()

    page = BidderDocumentPage(document_id=doc.id, page_number=1, extracted_text="Turnover ₹12.5 crore.")
    db.add(page)
    db.commit()

    match = EvidenceMatch(tender_id=tender.id, requirement_id=req.id, bidder_id=bidder.id, document_id=doc.id, page_id=page.id, evidence_text="Turnover ₹12.5 crore.", confidence_score=0.9, match_status=MatchStatus.MATCHED)
    db.add(match)

    rule = ComplianceRule(requirement_id=req.id, rule_code="RULE_API", rule_type=RuleType.NUMERIC_MIN, required_value="10")
    db.add(rule)
    db.commit()

    rule_eval = RuleEvaluation(rule_id=rule.id, requirement_id=req.id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=match.id, evaluation_status=EvaluationStatus.EVALUATED, evaluation_result=EvaluationResult.SATISFIED, extracted_value="12.5", required_value="10", explanation="Satisfied")
    db.add(rule_eval)
    db.commit()

    tender_id = tender.id
    bidder_id = bidder.id
    req_id = req.id

    # 1. API evaluate decisions
    res_eval = client.post("/api/v1/compliance/decisions/evaluate", json={"tender_id": tender_id, "bidder_id": bidder_id})
    assert res_eval.status_code == 200
    data = res_eval.json()
    assert data["overall_decision"] == "PASS"
    assert data["decision_type"] == "SYSTEM_DECISION"
    assert len(data["requirements"]) == 1
    assert data["requirements"][0]["decision"] == "PASS"

    # 2. API get compliance summary
    res_sum = client.get(f"/api/v1/compliance/bidders/{bidder_id}/compliance-summary?tender_id={tender_id}")
    assert res_sum.status_code == 200
    assert res_sum.json()["overall_decision"] == "PASS"

    # 3. API get requirement-level decision
    res_req = client.get(f"/api/v1/compliance/bidders/{bidder_id}/requirements/{req_id}/decision")
    assert res_req.status_code == 200
    assert res_req.json()["decision"] == "PASS"
