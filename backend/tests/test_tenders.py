from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_list_tenders():
    # 1. Create Tender
    payload = {
        "tender_id": "TEST/GEM/2026/001",
        "title": "Supply of Enterprise IT Hardware & Networking Equipment",
        "department": "Ministry of Electronics & IT (MeitY)",
        "issue_date": "2026-09-01",
        "closing_date": "2026-10-15"
    }
    response = client.post("/api/v1/tenders/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["tender_id"] == payload["tender_id"]
    assert data["status"] == "CREATED"
    tender_id = data["id"]

    # 2. List Tenders
    list_res = client.get("/api/v1/tenders/")
    assert list_res.status_code == 200
    tenders = list_res.json()
    assert len(tenders) > 0
    assert any(t["id"] == tender_id for t in tenders)

    # 3. Get Detail
    detail_res = client.get(f"/api/v1/tenders/{tender_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["title"] == payload["title"]

def test_duplicate_tender_id_fails():
    payload = {
        "tender_id": "DUP/GEM/2026/999",
        "title": "Duplicate Test Tender",
        "department": "Department of Science"
    }
    res1 = client.post("/api/v1/tenders/", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/tenders/", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]
