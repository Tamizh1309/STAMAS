from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.tender import Tender
from app.models.document import TenderPage
from app.models.requirement import Requirement, RequirementStatus, RequirementCategory
from app.models.evidence_match import EvidenceMatch

from app.schemas.requirement import (
    RequirementCreate, RequirementUpdate, RequirementResponse, ExtractionSummary
)
from app.services.requirement_extractor.rule_and_llm_extractor import RequirementExtractorService

router = APIRouter()

@router.post("/tenders/{tender_id}/extract-requirements", response_model=ExtractionSummary)
def extract_tender_requirements(tender_id: int, db: Session = Depends(get_db)):
    """
    Run Requirement Intelligence Module on extracted tender document pages.
    Structures requirements into ELIGIBILITY, TECHNICAL, FINANCIAL, DOCUMENT, and OTHER,
    retaining source page numbers and verbatim evidence text.
    """
    db_tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not db_tender:
        raise HTTPException(status_code=404, detail="Tender workspace not found.")

    pages = db.query(TenderPage).filter(TenderPage.tender_id == tender_id).order_by(TenderPage.page_number.asc()).all()
    if not pages:
        raise HTTPException(
            status_code=400,
            detail="No extracted document text found. Please upload and parse tender PDF first."
        )

    # Convert ORM pages to list of dicts for extraction service
    page_dicts = [
        {
            "page_number": p.page_number,
            "text_content": p.text_content,
            "tables_data": p.tables_data
        }
        for p in pages
    ]

    extracted = RequirementExtractorService.extract_requirements_from_pages(
        pages=page_dicts,
        document_name=db_tender.file_name or "Tender_Document.pdf"
    )

    # Delete existing evidence matches and requirements if re-running extraction
    db.query(EvidenceMatch).filter(EvidenceMatch.tender_id == tender_id).delete()
    db.query(Requirement).filter(Requirement.tender_id == tender_id).delete()


    breakdown = {"ELIGIBILITY": 0, "TECHNICAL": 0, "FINANCIAL": 0, "DOCUMENT": 0, "OTHER": 0}

    for item in extracted:
        db_req = Requirement(
            tender_id=tender_id,
            req_code=item["req_code"],
            category=item["category"],
            text=item["text"],
            mandatory=item["mandatory"],
            constraint_type=item["constraint_type"],
            threshold=item["threshold"],
            unit=item["unit"],
            currency=item["currency"],
            source_document=item["source_document"],
            source_page=item["source_page"],
            evidence_text=item["evidence_text"],
            confidence=item["confidence"],
            status=item["status"]
        )
        db.add(db_req)
        breakdown[item["category"]] = breakdown.get(item["category"], 0) + 1

    db.commit()

    return ExtractionSummary(
        total_extracted=len(extracted),
        categories_breakdown=breakdown,
        status="SUCCESS",
        message=f"Successfully extracted {len(extracted)} structured requirements across {len(pages)} pages."
    )

@router.get("/tenders/{tender_id}/requirements", response_model=List[RequirementResponse])
def get_tender_requirements(
    tender_id: int,
    category: Optional[str] = Query(None, description="Category filter: ELIGIBILITY, TECHNICAL, FINANCIAL, DOCUMENT, OTHER"),
    db: Session = Depends(get_db)
):
    """
    Get extracted requirements for a tender with optional category filtering.
    """
    db_tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not db_tender:
        raise HTTPException(status_code=404, detail="Tender workspace not found.")

    query = db.query(Requirement).filter(Requirement.tender_id == tender_id)
    if category and category.upper() != "ALL":
        query = query.filter(Requirement.category == category.upper())

    return query.order_by(Requirement.id.asc()).all()

@router.post("/tenders/{tender_id}/requirements", response_model=RequirementResponse, status_code=status.HTTP_201_CREATED)
def create_manual_requirement(
    tender_id: int,
    req_in: RequirementCreate,
    db: Session = Depends(get_db)
):
    """
    Allow procurement officer to manually add a missing requirement.
    """
    db_tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not db_tender:
        raise HTTPException(status_code=404, detail="Tender workspace not found.")

    # Generate next REQ code
    existing_count = db.query(Requirement).filter(Requirement.tender_id == tender_id).count()
    req_code = req_in.req_code or f"REQ-{(existing_count + 1):03d}"

    db_req = Requirement(
        tender_id=tender_id,
        req_code=req_code,
        category=req_in.category.upper(),
        text=req_in.text,
        mandatory=req_in.mandatory,
        constraint_type=req_in.constraint_type or "TEXT_MATCH",
        threshold=req_in.threshold,
        unit=req_in.unit,
        currency=req_in.currency,
        source_document=req_in.source_document or (db_tender.file_name or "Manual_Entry"),
        source_page=req_in.source_page or 1,
        evidence_text=req_in.evidence_text or req_in.text,
        confidence=1.0,
        status=RequirementStatus.CONFIRMED.value
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)
    return db_req

@router.put("/requirements/{id}", response_model=RequirementResponse)
def update_requirement(
    id: int,
    req_update: RequirementUpdate,
    db: Session = Depends(get_db)
):
    """
    Allow procurement officer to edit requirement fields, category, mandatory toggle, and status.
    """
    db_req = db.query(Requirement).filter(Requirement.id == id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    update_data = req_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "category":
                setattr(db_req, field, value.upper())
            else:
                setattr(db_req, field, value)

    # Set status to CORRECTED if officer edited text or category
    if "text" in update_data or "category" in update_data or "mandatory" in update_data:
        if req_update.status:
            db_req.status = req_update.status
        else:
            db_req.status = RequirementStatus.CORRECTED.value

    db.commit()
    db.refresh(db_req)
    return db_req

@router.delete("/requirements/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_requirement(id: int, db: Session = Depends(get_db)):
    """
    Allow procurement officer to delete an incorrect or duplicate requirement.
    """
    db_req = db.query(Requirement).filter(Requirement.id == id).first()
    if not db_req:
        raise HTTPException(status_code=404, detail="Requirement not found.")

    db.query(EvidenceMatch).filter(EvidenceMatch.requirement_id == id).delete()
    db.delete(db_req)
    db.commit()
    return None

