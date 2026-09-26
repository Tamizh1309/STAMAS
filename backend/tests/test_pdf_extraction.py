import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_pdf_upload_and_text_extraction():
    # 1. Create tender
    create_res = client.post("/api/v1/tenders/", json={
        "tender_id": "PDF/EXTRACT/TEST/001",
        "title": "Data Center PDF Extraction Verification",
        "department": "Defense R&D Organization (DRDO)"
    })
    assert create_res.status_code == 201
    tender_id = create_res.json()["id"]

    # 2. Upload sample PDF
    sample_pdf_path = "./data/sample_tenders/sample_gem_tender.pdf"
    assert os.path.exists(sample_pdf_path), "Sample PDF should be generated first"

    with open(sample_pdf_path, "rb") as f:
        upload_res = client.post(
            f"/api/v1/tenders/{tender_id}/upload-pdf",
            files={"file": ("sample_gem_tender.pdf", f, "application/pdf")}
        )

    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "SUCCESS"
    assert upload_data["page_count"] == 3
    assert upload_data["total_characters"] > 500

    # 3. Retrieve Extracted Pages
    pages_res = client.get(f"/api/v1/tenders/{tender_id}/extracted-text")
    assert pages_res.status_code == 200
    pages = pages_res.json()
    assert len(pages) == 3
    assert "GOVERNMENT E-MARKETPLACE" in pages[0]["text_content"]
    assert "FINANCIAL CAPACITY & TURNOVER" in pages[1]["text_content"]
    assert "MANDATORY DOCUMENTS CHECKLIST" in pages[2]["text_content"]

    # 4. Search within PDF pages
    search_res = client.get(f"/api/v1/tenders/{tender_id}/extracted-text?query=Turnover")
    assert search_res.status_code == 200
    matching_pages = search_res.json()
    assert len(matching_pages) > 0
    assert any("Turnover" in p["text_content"] for p in matching_pages)
