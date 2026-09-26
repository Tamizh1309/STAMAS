import pytest

from app.models.tender import Tender
from app.models.requirement import Requirement
from app.models.bidder import Bidder
from app.models.compliance_decision import ComplianceDecision


def create_sample_tender_and_bidder(db, suffix="1"):
    unique_tid = f"TENDER-OFF-{suffix}"
    tender = Tender(
        tender_id=unique_tid,
        title="Officer Review Test Tender",
        department="IT Dept"
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    req1 = Requirement(
        tender_id=tender.id,
        req_code=f"REQ-M1-{suffix}",
        category="Financial",
        text="Minimum turnover 10 Cr",
        mandatory=True
    )
    req2 = Requirement(
        tender_id=tender.id,
        req_code=f"REQ-M2-{suffix}",
        category="Technical",
        text="5 years experience",
        mandatory=True
    )
    db.add_all([req1, req2])
    db.commit()
    db.refresh(req1)
    db.refresh(req2)

    bidder = Bidder(
        tender_id=tender.id,
        bidder_name=f"Bidder {suffix}",
        company_name=f"Company {suffix}"
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    # System decisions
    sys1 = ComplianceDecision(
        tender_id=tender.id, bidder_id=bidder.id, requirement_id=req1.id,
        decision="PASS", decision_type="SYSTEM_DECISION", reason="System satisfied"
    )
    sys2 = ComplianceDecision(
        tender_id=tender.id, bidder_id=bidder.id, requirement_id=req2.id,
        decision="REVIEW", decision_type="SYSTEM_DECISION", reason="System indeterminate"
    )
    db.add_all([sys1, sys2])
    db.commit()

    return tender, bidder, req1, req2


def test_officer_confirm_pass(client, db):
    tender, bidder, req1, _ = create_sample_tender_and_bidder(db, "CONFIRM-PASS")
    response = client.post(
        f"/api/v1/compliance/review/bidders/{bidder.id}/requirements/{req1.id}/confirm?tender_id={tender.id}",
        json={"officer_comment": "Verified manually"}
    )
    assert response.status_code == 200, f"Got status {response.status_code}: {response.text}"
    data = response.json()
    assert data["system_decision"] == "PASS"
    assert data["final_decision"] == "PASS"
    assert data["decision_type"] == "CONFIRMED"
    assert data["review_status"] == "FINALIZED"


def test_officer_override_review_to_pass(client, db):
    tender, bidder, _, req2 = create_sample_tender_and_bidder(db, "OVERRIDE-PASS")
    response = client.post(
        f"/api/v1/compliance/review/bidders/{bidder.id}/requirements/{req2.id}/override?tender_id={tender.id}",
        json={
            "final_decision": "PASS",
            "override_reason": "Experience certificate verified from supporting annexures.",
            "officer_comment": "Valid document found"
        }
    )
    assert response.status_code == 200, f"Got status {response.status_code}: {response.text}"
    data = response.json()
    assert data["system_decision"] == "REVIEW"
    assert data["final_decision"] == "PASS"
    assert data["decision_type"] == "OVERRIDDEN"
    assert data["override_reason"] == "Experience certificate verified from supporting annexures."


def test_officer_override_pass_to_fail(client, db):
    tender, bidder, req1, _ = create_sample_tender_and_bidder(db, "OVERRIDE-FAIL")
    response = client.post(
        f"/api/v1/compliance/review/bidders/{bidder.id}/requirements/{req1.id}/override?tender_id={tender.id}",
        json={
            "final_decision": "FAIL",
            "override_reason": "Audit detected invalid turnover documentation.",
            "officer_comment": "Rejected upon deep audit"
        }
    )
    assert response.status_code == 200, f"Got status {response.status_code}: {response.text}"
    data = response.json()
    assert data["system_decision"] == "PASS"
    assert data["final_decision"] == "FAIL"
    assert data["decision_type"] == "OVERRIDDEN"


def test_override_missing_reason_validation(client, db):
    tender, bidder, req1, _ = create_sample_tender_and_bidder(db, "VALIDATION-FAIL")
    response = client.post(
        f"/api/v1/compliance/review/bidders/{bidder.id}/requirements/{req1.id}/override?tender_id={tender.id}",
        json={
            "final_decision": "FAIL",
            "override_reason": "   short   ", # too short (<10 chars)
        }
    )
    assert response.status_code == 422 # Validation error


def test_audit_log_creation_and_history(client, db):
    tender, bidder, req1, _ = create_sample_tender_and_bidder(db, "AUDIT-HISTORY")
    
    # 1. Confirm
    client.post(
        f"/api/v1/compliance/review/bidders/{bidder.id}/requirements/{req1.id}/confirm?tender_id={tender.id}",
        json={"officer_comment": "First step confirm"}
    )

    # 2. Override
    client.post(
        f"/api/v1/compliance/review/bidders/{bidder.id}/requirements/{req1.id}/override?tender_id={tender.id}",
        json={
            "final_decision": "FAIL",
            "override_reason": "New information received showing turnover failure.",
        }
    )

    # 3. Check audit history
    audit_res = client.get(
        f"/api/v1/compliance/review/bidders/{bidder.id}/audit?tender_id={tender.id}"
    )
    assert audit_res.status_code == 200, f"Got status {audit_res.status_code}: {audit_res.text}"
    audits = audit_res.json()
    assert len(audits) >= 2
    actions = [a["action"] for a in audits]
    assert "DECISION_CONFIRMED" in actions
    assert "DECISION_OVERRIDDEN" in actions


def test_reopen_finalized_review(client, db):
    tender, bidder, _, _ = create_sample_tender_and_bidder(db, "REOPEN")

    # Finalize
    client.post(f"/api/v1/compliance/review/bidders/{bidder.id}/finalize?tender_id={tender.id}")

    # Reopen
    reopen_res = client.post(
        f"/api/v1/compliance/review/bidders/{bidder.id}/reopen?tender_id={tender.id}&reason=New%20bidder%20document%20submitted"
    )
    assert reopen_res.status_code == 200, f"Got status {reopen_res.status_code}: {reopen_res.text}"
    summary = reopen_res.json()

    audits = summary["audits"]
    actions = [a["action"] for a in audits]
    assert "DECISION_REOPENED" in actions


def test_cross_tender_isolation(client, db):
    tender1, bidder1, req1, _ = create_sample_tender_and_bidder(db, "T1")
    tender2, bidder2, req2, _ = create_sample_tender_and_bidder(db, "T2")

    # Try to confirm bidder1 with tender2 ID
    res = client.post(
        f"/api/v1/compliance/review/bidders/{bidder1.id}/requirements/{req1.id}/confirm?tender_id={tender2.id}",
        json={"officer_comment": "Illegal cross-tender call"}
    )
    assert res.status_code == 404 # Scoping rejection
