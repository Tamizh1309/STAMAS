import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_requirement_extraction_flow():
    # 1. Create tender
    create_res = client.post("/api/v1/tenders/", json={
        "tender_id": "REQ/TEST/GEM/2026/101",
        "title": "Requirement Intelligence System Verification",
        "department": "Ministry of Defense"
    })
    assert create_res.status_code == 201
    tender_id = create_res.json()["id"]

    # 2. Upload sample PDF
    sample_pdf = "./data/sample_tenders/sample_gem_tender.pdf"
    assert os.path.exists(sample_pdf), "Sample PDF should exist for test execution"

    with open(sample_pdf, "rb") as f:
        client.post(
            f"/api/v1/tenders/{tender_id}/upload-pdf",
            files={"file": ("sample_gem_tender.pdf", f, "application/pdf")}
        )

    # 3. Trigger Requirement Extraction
    extract_res = client.post(f"/api/v1/tenders/{tender_id}/extract-requirements")
    assert extract_res.status_code == 200
    extract_data = extract_res.json()
    assert extract_data["status"] == "SUCCESS"
    assert extract_data["total_extracted"] > 0
    assert "FINANCIAL" in extract_data["categories_breakdown"]

    # 4. Fetch Extracted Requirements
    reqs_res = client.get(f"/api/v1/tenders/{tender_id}/requirements")
    assert reqs_res.status_code == 200
    reqs = reqs_res.json()
    assert len(reqs) == extract_data["total_extracted"]

    # Verify source page preservation and evidence text linking
    financial_req = next((r for r in reqs if r["category"] == "FINANCIAL"), None)
    assert financial_req is not None
    assert financial_req["source_page"] in [1, 2, 3]
    assert len(financial_req["evidence_text"]) > 0
    assert financial_req["mandatory"] is True

def get_or_create_test_tender():
    tenders_res = client.get("/api/v1/tenders/")
    if len(tenders_res.json()) > 0:
        return tenders_res.json()[0]["id"]
    create_res = client.post("/api/v1/tenders/", json={
        "tender_id": "REQ/TEST/HELPER/001",
        "title": "Test Tender Helper",
        "department": "IT Dept"
    })
    return create_res.json()["id"]

def test_category_filtering():
    tender_id = get_or_create_test_tender()
    financial_res = client.get(f"/api/v1/tenders/{tender_id}/requirements?category=FINANCIAL")
    assert financial_res.status_code == 200
    financial_reqs = financial_res.json()
    assert all(r["category"] == "FINANCIAL" for r in financial_reqs)

def test_manual_requirement_creation_and_edit_delete():
    tender_id = get_or_create_test_tender()


    # 2. Add manual requirement
    new_req_payload = {
        "category": "TECHNICAL",
        "text": "Vendor must provide 24/7 on-site technical maintenance support",
        "mandatory": True,
        "constraint_type": "TEXT_MATCH",
        "source_page": 2,
        "evidence_text": "Vendor must provide 24/7 on-site technical maintenance support"
    }
    create_req_res = client.post(f"/api/v1/tenders/{tender_id}/requirements", json=new_req_payload)
    assert create_req_res.status_code == 201
    created_req = create_req_res.json()
    req_id = created_req["id"]
    assert created_req["category"] == "TECHNICAL"
    assert created_req["status"] == "CONFIRMED"

    # 3. Edit requirement (change category & text)
    edit_payload = {
        "category": "ELIGIBILITY",
        "text": "Vendor must provide 24/7 on-site SLA technical support",
        "mandatory": True,
        "status": "CORRECTED"
    }
    edit_res = client.put(f"/api/v1/requirements/{req_id}", json=edit_payload)
    assert edit_res.status_code == 200
    updated = edit_res.json()
    assert updated["category"] == "ELIGIBILITY"
    assert updated["status"] == "CORRECTED"
    assert "SLA" in updated["text"]

    # 4. Verify Persistence via GET
    get_res = client.get(f"/api/v1/tenders/{tender_id}/requirements")
    all_reqs = get_res.json()
    matched = next((r for r in all_reqs if r["id"] == req_id), None)
    assert matched is not None
    assert matched["category"] == "ELIGIBILITY"

    # 5. Delete Requirement
    del_res = client.delete(f"/api/v1/requirements/{req_id}")
    assert del_res.status_code == 204

    # Verify deleted
    get_after_del = client.get(f"/api/v1/tenders/{tender_id}/requirements")
    assert not any(r["id"] == req_id for r in get_after_del.json())

def test_extract_requirements_without_pdf_fails():
    # Create empty tender without PDF upload
    create_res = client.post("/api/v1/tenders/", json={
        "tender_id": "EMPTY/NO/PDF/001",
        "title": "Empty Tender Without Upload",
        "department": "Department of Commerce"
    })
    tender_id = create_res.json()["id"]

    extract_res = client.post(f"/api/v1/tenders/{tender_id}/extract-requirements")
    assert extract_res.status_code == 400
    assert "No extracted document text found" in extract_res.json()["detail"]
