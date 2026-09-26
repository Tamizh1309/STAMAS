import pytest
from app.models.tender import Tender, TenderStatus
from app.models.requirement import Requirement, RequirementCategory, RequirementStatus
from app.models.bidder import Bidder, BidderStatus
from app.models.bidder_document import BidderDocument, BidderDocumentPage, DocumentProcessingStatus, ExtractionStatus
from app.models.evidence_match import EvidenceMatch, MatchStatus
from app.services.evidence_matcher.matcher import EvidenceMatcherService


def setup_test_tender_data(db):
    """Helper to populate a test tender with requirements, bidders, documents, and document pages."""
    # 1. Tender
    tender = Tender(
        tender_id="TND-2026-001",
        title="Data Center Infrastructure Procurement",
        department="Ministry of Electronics & IT",
        status=TenderStatus.PROCESSED.value,
        page_count=10
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    # 2. Requirement
    req1 = Requirement(
        tender_id=tender.id,
        req_code="REQ-001",
        category=RequirementCategory.TECHNICAL.value,
        text="Bidder must have at least 5 years of experience in data center infrastructure projects.",
        mandatory=True,
        constraint_type="EXPERIENCE",
        threshold=5.0,
        unit="YEARS"
    )
    req2 = Requirement(
        tender_id=tender.id,
        req_code="REQ-002",
        category=RequirementCategory.ELIGIBILITY.value,
        text="Bidder must possess valid ISO 9001 quality certification.",
        mandatory=True,
        constraint_type="CERTIFICATION"
    )
    req3 = Requirement(
        tender_id=tender.id,
        req_code="REQ-003",
        category=RequirementCategory.FINANCIAL.value,
        text="Bidder must provide GSTIN registration certificate.",
        mandatory=True,
        constraint_type="REGISTRATION"
    )
    db.add_all([req1, req2, req3])
    db.commit()

    # 3. Bidder
    bidder = Bidder(
        tender_id=tender.id,
        bidder_id="BID-001",
        bidder_name="ABC Tech",
        company_name="ABC Technologies Pvt Ltd",
        status=BidderStatus.PROCESSED.value
    )
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    # 4. Bidder Documents & Pages
    doc1 = BidderDocument(
        bidder_id=bidder.id,
        tender_id=tender.id,
        filename="experience_certificate.pdf",
        stored_filename="doc_exp.pdf",
        file_path="/tmp/exp.pdf",
        category="EXPERIENCE",
        page_count=5,
        processing_status=DocumentProcessingStatus.PROCESSED.value,
        extraction_status=ExtractionStatus.TEXT_LAYER.value
    )
    doc2 = BidderDocument(
        bidder_id=bidder.id,
        tender_id=tender.id,
        filename="iso_certificate.pdf",
        stored_filename="doc_iso.pdf",
        file_path="/tmp/iso.pdf",
        category="CERTIFICATION",
        page_count=2,
        processing_status=DocumentProcessingStatus.PROCESSED.value,
        extraction_status=ExtractionStatus.TEXT_LAYER.value
    )
    doc3 = BidderDocument(
        bidder_id=bidder.id,
        tender_id=tender.id,
        filename="company_profile.pdf",
        stored_filename="doc_profile.pdf",
        file_path="/tmp/profile.pdf",
        category="OTHER",
        page_count=10,
        processing_status=DocumentProcessingStatus.PROCESSED.value,
        extraction_status=ExtractionStatus.TEXT_LAYER.value
    )
    db.add_all([doc1, doc2, doc3])
    db.commit()
    db.refresh(doc1)
    db.refresh(doc2)
    db.refresh(doc3)

    # Pages
    # Strong match for REQ-001 (5 years experience)
    p1 = BidderDocumentPage(
        document_id=doc1.id,
        page_number=4,
        extracted_text="ABC Technologies Pvt Ltd has successfully completed major data center infrastructure projects from 2018 to 2025 across India."
    )
    # Strong match for REQ-002 (ISO 9001)
    p2 = BidderDocumentPage(
        document_id=doc2.id,
        page_number=1,
        extracted_text="Certificate of Registration: ISO 9001:2015 Quality Management Systems. Certificate No: ISO-ABC-2025-001 valid till 2028."
    )
    # Partial match for REQ-001
    p3 = BidderDocumentPage(
        document_id=doc3.id,
        page_number=8,
        extracted_text="Company profile: ABC Technologies has extensive experience in data center infrastructure systems."
    )
    # Unrelated page
    p4 = BidderDocumentPage(
        document_id=doc3.id,
        page_number=2,
        extracted_text="Office seating arrangement, staff canteen menu, and internal directory list."
    )
    db.add_all([p1, p2, p3, p4])
    db.commit()

    return {
        "tender": tender,
        "req1": req1,
        "req2": req2,
        "req3": req3,
        "bidder": bidder,
        "doc1": doc1,
        "doc2": doc2,
        "doc3": doc3,
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4
    }


def test_evidence_matching_service_demo_workflow(db):
    """Test full matching workflow matching prompt demo requirements."""
    data = setup_test_tender_data(db)

    # Match REQ-001 (5 years data center experience)
    matches = EvidenceMatcherService.match_requirement_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req1"].id
    )

    assert len(matches) > 0
    best_match = matches[0]
    assert best_match.match_status == MatchStatus.MATCHED.value
    assert best_match.confidence_score >= 0.80
    assert best_match.document_id == data["doc1"].id
    assert best_match.page_id == data["p1"].id
    assert "2018 to 2025" in best_match.evidence_text
    assert len(best_match.reason) > 0


    # Second match should be partial
    if len(matches) > 1:
        second_match = matches[1]
        assert second_match.match_status in [MatchStatus.PARTIAL.value, MatchStatus.LOW_CONFIDENCE.value]
        assert second_match.document_id == data["doc3"].id


def test_iso_certificate_matching(db):
    """Test ISO 9001 requirement produces MATCHED result."""
    data = setup_test_tender_data(db)

    matches = EvidenceMatcherService.match_requirement_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req2"].id
    )

    assert len(matches) == 1
    m = matches[0]
    assert m.match_status == MatchStatus.MATCHED.value
    assert m.confidence_score >= 0.80
    assert m.document_id == data["doc2"].id
    assert m.page_id == data["p2"].id
    assert "ISO 9001" in m.evidence_text


def test_not_found_matching(db):
    """Test requirement with no matching evidence returns NOT_FOUND status."""
    data = setup_test_tender_data(db)

    # REQ-003 is GST registration, which is nowhere in document pages
    matches = EvidenceMatcherService.match_requirement_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id,
        requirement_id=data["req3"].id
    )

    assert len(matches) == 1
    m = matches[0]
    assert m.match_status == MatchStatus.NOT_FOUND.value
    assert m.confidence_score == 0.0


def test_cross_tender_matching_prevention(client, db):
    """Verify that cross-tender matching is strictly rejected."""
    data = setup_test_tender_data(db)

    # Create Tender B
    tender_b = Tender(
        tender_id="TND-2026-999",
        title="Other Tender",
        department="Railways",
        status=TenderStatus.PROCESSED.value
    )
    db.add(tender_b)
    db.commit()

    # Attempt matching Tender B requirement with Tender A bidder
    res = client.post(
        f"/api/v1/tenders/{tender_b.id}/bidders/{data['bidder'].id}/requirements/{data['req1'].id}/match"
    )
    assert res.status_code == 400
    assert "not found under tender" in res.json()["detail"].lower()


def test_batch_matching_and_rerun_safety(client, db):
    """Test batch matching endpoint and check rerun safety (no duplicates)."""
    data = setup_test_tender_data(db)

    # Run batch matching via API
    payload = {
        "tender_id": data["tender"].id,
        "bidder_id": data["bidder"].id
    }
    res = client.post("/api/v1/evidence-matches/run", json=payload)
    assert res.status_code == 200
    initial_count = len(res.json())
    assert initial_count >= 3

    # Run again (rerun)
    res2 = client.post("/api/v1/evidence-matches/run", json=payload)
    assert res2.status_code == 200
    rerun_count = len(res2.json())
    assert rerun_count == initial_count  # No duplicates created!

    # Check summary endpoint
    res_sum = client.get(f"/api/v1/bidders/{data['bidder'].id}/evidence-summary?tender_id={data['tender'].id}")
    assert res_sum.status_code == 200
    summary = res_sum.json()
    assert summary["total_requirements"] == 3
    assert summary["matched_count"] == 2
    assert summary["not_found_count"] == 1


def test_evidence_matches_retrieval_apis(client, db):
    """Test GET endpoints for evidence matches."""
    data = setup_test_tender_data(db)

    # Run matching first
    EvidenceMatcherService.match_all_requirements_for_bidder(
        db=db,
        tender_id=data["tender"].id,
        bidder_id=data["bidder"].id
    )

    # GET /api/v1/bidders/{bidder_id}/evidence-matches
    res1 = client.get(f"/api/v1/bidders/{data['bidder'].id}/evidence-matches")
    assert res1.status_code == 200
    items = res1.json()
    assert len(items) > 0
    # Ensure enriched UI fields exist
    assert "document_name" in items[0]
    assert "page_number" in items[0]
    assert "req_code" in items[0]

    # GET /api/v1/bidders/{bidder_id}/requirements/{requirement_id}/evidence
    res2 = client.get(f"/api/v1/bidders/{data['bidder'].id}/requirements/{data['req1'].id}/evidence")
    assert res2.status_code == 200
    req_items = res2.json()
    assert len(req_items) > 0

    # GET /api/v1/evidence-matches/{match_id}
    match_id = req_items[0]["id"]
    res3 = client.get(f"/api/v1/evidence-matches/{match_id}")
    assert res3.status_code == 200
    single_match = res3.json()
    assert single_match["id"] == match_id
