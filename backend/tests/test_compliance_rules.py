import pytest
from app.models.tender import Tender, TenderStatus
from app.models.requirement import Requirement, RequirementCategory
from app.models.bidder import Bidder, BidderStatus
from app.models.bidder_document import BidderDocument, BidderDocumentPage, DocumentProcessingStatus
from app.models.evidence_match import EvidenceMatch, MatchStatus
from app.models.compliance_rule import ComplianceRule, RuleType
from app.models.rule_evaluation import RuleEvaluation, EvaluationResult, EvaluationStatus
from app.services.evidence_matcher.matcher import EvidenceMatcherService
from app.services.rule_engine.evaluator import RuleEngineService


def setup_rule_test_data(db):
    """Helper to populate test data for rule evaluations."""
    tender = Tender(
        tender_id="TND-RULE-2026",
        title="Compliance Rule Test Tender",
        department="Ministry of Finance",
        status=TenderStatus.PROCESSED.value
    )
    db.add(tender)
    db.commit()

    req1 = Requirement(
        tender_id=tender.id,
        req_code="REQ-001",
        category=RequirementCategory.FINANCIAL.value,
        text="Average annual turnover must be at least ₹10 crore.",
        mandatory=True,
        constraint_type="FINANCIAL",
        threshold=10.0,
        unit="CRORE",
        currency="INR"
    )
    req2 = Requirement(
        tender_id=tender.id,
        req_code="REQ-002",
        category=RequirementCategory.TECHNICAL.value,
        text="Bidder must have minimum 5 years experience in data center infrastructure.",
        mandatory=True,
        constraint_type="EXPERIENCE",
        threshold=5.0,
        unit="YEARS"
    )
    req3 = Requirement(
        tender_id=tender.id,
        req_code="REQ-003",
        category=RequirementCategory.ELIGIBILITY.value,
        text="Bidder must provide valid ISO 9001 quality certification.",
        mandatory=True,
        constraint_type="CERTIFICATION"
    )
    req4 = Requirement(
        tender_id=tender.id,
        req_code="REQ-004",
        category=RequirementCategory.ELIGIBILITY.value,
        text="Bidder must have active GST registration.",
        mandatory=True,
        constraint_type="REGISTRATION"
    )
    db.add_all([req1, req2, req3, req4])
    db.commit()

    bidder = Bidder(
        tender_id=tender.id,
        bidder_id="BID-RULE-01",
        bidder_name="ABC Tech",
        company_name="ABC Technologies Pvt Ltd",
        status=BidderStatus.PROCESSED.value
    )
    db.add(bidder)
    db.commit()

    doc = BidderDocument(
        bidder_id=bidder.id,
        tender_id=tender.id,
        filename="compliance_doc.pdf",
        stored_filename="doc_comp.pdf",
        file_path="/tmp/comp.pdf",
        category="TECHNICAL",
        page_count=5,
        processing_status=DocumentProcessingStatus.PROCESSED.value
    )
    db.add(doc)
    db.commit()

    p1 = BidderDocumentPage(
        document_id=doc.id,
        page_number=1,
        extracted_text="Audited Financial Report: Average annual turnover of ABC Technologies is ₹12.5 crore for FY 2024-25."
    )
    p2 = BidderDocumentPage(
        document_id=doc.id,
        page_number=2,
        extracted_text="ABC Technologies completed major data center projects from 2018 to 2025 across India."
    )
    p3 = BidderDocumentPage(
        document_id=doc.id,
        page_number=3,
        extracted_text="Certificate of Registration: ISO 9001:2015 Quality Management Systems. Certificate No: ISO-ABC-2025."
    )
    db.add_all([p1, p2, p3])
    db.commit()

    # Run evidence matching first
    EvidenceMatcherService.match_all_requirements_for_bidder(
        db=db,
        tender_id=tender.id,
        bidder_id=bidder.id
    )

    return {
        "tender": tender,
        "req1": req1,
        "req2": req2,
        "req3": req3,
        "req4": req4,
        "bidder": bidder,
        "doc": doc
    }


def test_turnover_min_satisfied(db):
    """TEST 1: Turnover ₹12.5 crore >= ₹10 crore requirement -> SATISFIED."""
    data = setup_rule_test_data(db)

    evals = RuleEngineService.evaluate_requirement_rules_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req1"].id
    )

    assert len(evals) == 1
    e = evals[0]
    assert e.evaluation_result == EvaluationResult.SATISFIED.value
    assert e.extracted_value == "12.5"
    assert "exceeds" in e.explanation.lower() or "satisfies" in e.explanation.lower() or "meets" in e.explanation.lower()


def test_years_experience_satisfied(db):
    """TEST 3: Experience 2018-2025 (7 years) >= 5 years -> SATISFIED."""
    data = setup_rule_test_data(db)

    evals = RuleEngineService.evaluate_requirement_rules_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req2"].id
    )

    assert len(evals) == 1
    e = evals[0]
    assert e.evaluation_result == EvaluationResult.SATISFIED.value
    assert e.extracted_value == "7"
    assert "7 years" in e.explanation


def test_iso_certification_satisfied(db):
    """TEST 5: ISO 9001 certification required & found -> SATISFIED."""
    data = setup_rule_test_data(db)

    evals = RuleEngineService.evaluate_requirement_rules_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req3"].id
    )

    assert len(evals) == 1
    e = evals[0]
    assert e.evaluation_result == EvaluationResult.SATISFIED.value
    assert "ISO 9001" in e.extracted_value


def test_missing_evidence_insufficient_evidence(db):
    """TEST 6: Requirement with no evidence -> INSUFFICIENT_EVIDENCE."""
    data = setup_rule_test_data(db)

    # REQ-004 is GST registration, which was NOT in any page
    evals = RuleEngineService.evaluate_requirement_rules_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req4"].id
    )

    assert len(evals) == 1
    e = evals[0]
    assert e.evaluation_result == EvaluationResult.INSUFFICIENT_EVIDENCE.value
    assert "No relevant evidence" in e.explanation


def test_conflicting_evidence_handling(db):
    """TEST 7: Conflicting turnover evidence -> CONFLICTING_EVIDENCE."""
    data = setup_rule_test_data(db)

    # Add a second document page with a conflicting turnover value of 7 crore
    p_conflict = BidderDocumentPage(
        document_id=data["doc"].id,
        page_number=4,
        extracted_text="Financial summary: Average annual turnover of ABC Tech is ₹7 crore for previous term."
    )
    db.add(p_conflict)
    db.commit()

    # Re-run evidence matching
    EvidenceMatcherService.match_requirement_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req1"].id
    )

    evals = RuleEngineService.evaluate_requirement_rules_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req1"].id
    )

    assert len(evals) == 1
    e = evals[0]
    assert e.evaluation_result == EvaluationResult.CONFLICTING_EVIDENCE.value
    assert "conflicting" in e.explanation.lower()


def test_batch_rule_evaluation_and_summary_apis(client, db):
    """Test POST /compliance/rules/evaluate batch mode and GET summary API."""
    data = setup_rule_test_data(db)

    # Trigger batch rule evaluation via API
    payload = {
        "tender_id": data["tender"].id,
        "bidder_id": data["bidder"].id
    }
    res = client.post("/api/v1/compliance/rules/evaluate", json=payload)
    assert res.status_code == 200
    evals = res.json()
    assert len(evals) == 4

    # Ensure UI enriched traceability fields exist
    assert "req_code" in evals[0]
    assert "requirement_text" in evals[0]
    assert "explanation" in evals[0]

    # Re-run (rerun safety check - no duplicate records)
    res2 = client.post("/api/v1/compliance/rules/evaluate", json=payload)
    assert res2.status_code == 200
    assert len(res2.json()) == 4

    # GET summary
    res_sum = client.get(f"/api/v1/bidders/{data['bidder'].id}/rule-summary?tender_id={data['tender'].id}")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["total_requirements"] == 4
    assert summary["rules_evaluated"] == 4
    assert summary["satisfied_count"] == 3
    assert summary["insufficient_evidence_count"] == 1
