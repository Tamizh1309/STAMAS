import pytest
from app.models.tender import Tender
from app.models.requirement import Requirement
from app.models.bidder import Bidder
from app.models.compliance_decision import ComplianceDecision
from app.models.officer_decision import OfficerDecision, OfficerReviewAudit

def create_sample_report_data(db, suffix="R1"):
    unique_tid = f"TENDER-REP-{suffix}"
    tender = Tender(
        tender_id=unique_tid,
        title="Reporting & Audit Test Tender",
        department="GeM Evaluation Dept"
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    req1 = Requirement(
        tender_id=tender.id, req_code="REQ-REP-1", category="Financial",
        text="Minimum turnover ₹10 Cr", mandatory=True
    )
    db.add(req1)
    db.commit()
    db.refresh(req1)

    bidder = Bidder(
        tender_id=tender.id, bidder_name=f"Report Bidder {suffix}",
        company_name=f"Report Company {suffix}"
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    sys_dec = ComplianceDecision(
        tender_id=tender.id, bidder_id=bidder.id, requirement_id=req1.id,
        decision="REVIEW", decision_type="SYSTEM_DECISION", reason="Validity indeterminate"
    )
    db.add(sys_dec)
    db.commit()

    off_dec = OfficerDecision(
        tender_id=tender.id, bidder_id=bidder.id, requirement_id=req1.id,
        system_decision_id=sys_dec.id, final_decision="PASS", decision_type="OVERRIDDEN",
        officer_id="OFFICER-001", officer_name="Senior Officer", officer_role="Evaluator",
        override_reason="Manually verified from supporting document annexure.",
        review_status="FINALIZED"
    )
    db.add(off_dec)
    db.commit()

    audit = OfficerReviewAudit(
        tender_id=tender.id, bidder_id=bidder.id, requirement_id=req1.id,
        officer_decision_id=off_dec.id, officer_id="OFFICER-001", officer_name="Senior Officer",
        officer_role="Evaluator", action="DECISION_OVERRIDDEN", previous_system_decision="REVIEW",
        new_final_decision="PASS", decision_type="OVERRIDDEN",
        reason="Manually verified from supporting document annexure."
    )
    db.add(audit)
    db.commit()

    return tender, bidder, req1


def test_get_tender_compliance_report(client, db):
    tender, bidder, _ = create_sample_report_data(db, "TENDER-REP")
    res = client.get(f"/api/v1/reports/tenders/{tender.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["tender_id"] == tender.id
    assert data["total_bidders"] == 1
    assert data["bidders"][0]["company_name"] == bidder.company_name
    assert data["bidders"][0]["system_overall_decision"] == "REVIEW"
    assert data["bidders"][0]["final_overall_decision"] == "PASS"
    assert data["bidders"][0]["overridden_count"] == 1


def test_get_bidder_compliance_report(client, db):
    tender, bidder, _ = create_sample_report_data(db, "BIDDER-REP")
    res = client.get(f"/api/v1/reports/bidders/{bidder.id}?tender_id={tender.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["bidder_id"] == bidder.id
    assert data["system_overall_decision"] == "REVIEW"
    assert data["final_overall_decision"] == "PASS"
    assert len(data["requirements"]) == 1
    assert data["requirements"][0]["decision_type"] == "OVERRIDDEN"


def test_tender_pdf_report_export(client, db):
    tender, _, _ = create_sample_report_data(db, "TENDER-PDF")
    res = client.get(f"/api/v1/reports/tenders/{tender.id}/pdf")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")


def test_bidder_pdf_report_export(client, db):
    tender, bidder, _ = create_sample_report_data(db, "BIDDER-PDF")
    res = client.get(f"/api/v1/reports/bidders/{bidder.id}/pdf?tender_id={tender.id}")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")


def test_tender_csv_export(client, db):
    tender, bidder, _ = create_sample_report_data(db, "TENDER-CSV")
    res = client.get(f"/api/v1/reports/tenders/{tender.id}/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert bidder.company_name in res.text


def test_audit_paginated_report(client, db):
    tender, bidder, _ = create_sample_report_data(db, "AUDIT-LOG")
    res = client.get(f"/api/v1/reports/audit?tender_id={tender.id}&page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total_events"] >= 1
    assert len(data["events"]) >= 1
    assert data["events"][0]["action"] == "DECISION_OVERRIDDEN"


def test_audit_csv_export(client, db):
    tender, _, _ = create_sample_report_data(db, "AUDIT-CSV")
    res = client.get(f"/api/v1/reports/audit/csv?tender_id={tender.id}")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "DECISION_OVERRIDDEN" in res.text


def test_reports_unknown_tender_404(client, db):
    res = client.get("/api/v1/reports/tenders/999999")
    assert res.status_code == 404
