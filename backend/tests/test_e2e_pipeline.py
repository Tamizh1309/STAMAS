import pytest

from app.models.tender import Tender
from app.models.requirement import Requirement
from app.models.bidder import Bidder
from app.models.bidder_document import BidderDocument, BidderDocumentPage
from app.models.evidence_match import EvidenceMatch
from app.models.compliance_rule import ComplianceRule
from app.models.rule_evaluation import RuleEvaluation
from app.services.compliance.decision_engine import evaluate_bidder_compliance_decisions
from app.services.compliance.officer_review import confirm_requirement_decision, override_requirement_decision, finalize_bidder_review
from app.services.reporting.report_service import generate_bidder_report_data, export_report_pdf, export_report_csv

def test_complete_stamas_end_to_end_pipeline(client, db):
    """
    Verifies the complete 11-phase workflow:
    Tender -> Requirement -> Bidder -> Document -> Evidence -> Rules -> System Decision -> Officer Review -> Report -> Audit.
    """
    # 1. Tender
    tender = Tender(tender_id="TND-E2E-1001", title="GeM Data Center Expansion RFP", department="MeitY")
    db.add(tender)
    db.commit()
    db.refresh(tender)

    # 2. Requirements
    req1 = Requirement(tender_id=tender.id, req_code="REQ-01", text="Minimum turnover ₹10 Crore", mandatory=True)
    req2 = Requirement(tender_id=tender.id, req_code="REQ-02", text="Valid ISO 9001 certificate", mandatory=True)
    db.add_all([req1, req2])
    db.commit()
    db.refresh(req1)
    db.refresh(req2)

    # 3. Bidder
    bidder = Bidder(tender_id=tender.id, bidder_name="E2E Corp Pvt Ltd", company_name="E2E Corp Pvt Ltd")
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    # 4. Document & Page
    doc = BidderDocument(bidder_id=bidder.id, tender_id=tender.id, filename="e2e_dossier.pdf", stored_filename="e2e.pdf", file_path="/docs/e2e.pdf")
    db.add(doc)
    db.commit()

    page = BidderDocumentPage(document_id=doc.id, page_number=10, extracted_text="Turnover is 15 crore INR. ISO 9001 reference included.")
    db.add(page)
    db.commit()

    # 5. Evidence & Rules
    ev1 = EvidenceMatch(tender_id=tender.id, bidder_id=bidder.id, requirement_id=req1.id, document_id=doc.id, page_id=page.id, evidence_text="Turnover is 15 crore", match_status="MATCHED", confidence_score=0.95)
    ev2 = EvidenceMatch(tender_id=tender.id, bidder_id=bidder.id, requirement_id=req2.id, document_id=doc.id, page_id=page.id, evidence_text="ISO reference", match_status="LOW_CONFIDENCE", confidence_score=0.45)
    db.add_all([ev1, ev2])
    db.commit()

    r1 = ComplianceRule(requirement_id=req1.id, rule_code="R1", rule_type="NUMERIC_MIN", operator=">=", required_value="10.0")
    r2 = ComplianceRule(requirement_id=req2.id, rule_code="R2", rule_type="CERTIFICATION_REQUIRED", operator="EQUALS", required_value="VALID")
    db.add_all([r1, r2])
    db.commit()

    eval1 = RuleEvaluation(rule_id=r1.id, requirement_id=req1.id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=ev1.id, extracted_value="15 Cr", required_value="10 Cr", operator=">=", evaluation_status="EVALUATED", evaluation_result="SATISFIED", explanation="Satisfied")
    eval2 = RuleEvaluation(rule_id=r2.id, requirement_id=req2.id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=ev2.id, extracted_value="ISO reference", required_value="Valid ISO", operator="EQUALS", evaluation_status="EVALUATED", evaluation_result="INDETERMINATE", explanation="Indeterminate")
    db.add_all([eval1, eval2])
    db.commit()

    # 6. System Decision Engine (Phase 8)
    sys_res = evaluate_bidder_compliance_decisions(db, tender.id, bidder.id)
    assert sys_res.overall_decision == "REVIEW"

    # 7. Officer Review Workstation (Phase 9)
    confirm_requirement_decision(db, tender.id, bidder.id, req1.id, officer_comment="Turnover confirmed")
    override_requirement_decision(db, tender.id, bidder.id, req2.id, final_decision="PASS", override_reason="ISO certificate manually verified from page 10.", officer_comment="Approved")
    final_summary = finalize_bidder_review(db, tender.id, bidder.id)

    assert final_summary["final_overall_decision"] == "PASS"

    # 8. Reports & Audit (Phase 10)
    b_report = generate_bidder_report_data(db, tender.id, bidder.id)
    pdf_bytes = export_report_pdf("BIDDER", b_report)
    csv_str = export_report_csv("BIDDER", b_report)

    assert len(pdf_bytes) > 500
    assert len(csv_str) > 200

    # 9. API Verification
    api_res = client.get(f"/api/v1/reports/bidders/{bidder.id}?tender_id={tender.id}")
    assert api_res.status_code == 200
    assert api_res.json()["final_overall_decision"] == "PASS"

    # 10. Benchmark Endpoint Verification (Phase 11)
    bench_res = client.get("/api/v1/benchmark/run")
    assert bench_res.status_code == 200
    assert bench_res.json()["total_cases_evaluated"] >= 1
