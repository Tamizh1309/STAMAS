import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.models.tender import Tender, TenderStatus
from app.models.document import TenderPage
from app.schemas.tender import TenderCreate, TenderResponse, TenderDetail, PDFProcessingResult, TenderPageResponse
from app.services.document_processor.pdf_extractor import PDFExtractorService

router = APIRouter()

@router.post("/", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
def create_tender(tender_in: TenderCreate, db: Session = Depends(get_db)):
    """
    Create a new Tender record.
    """
    existing = db.query(Tender).filter(Tender.tender_id == tender_in.tender_id).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Tender with ID '{tender_in.tender_id}' already exists."
        )

    db_tender = Tender(
        tender_id=tender_in.tender_id,
        title=tender_in.title,
        department=tender_in.department,
        issue_date=tender_in.issue_date,
        closing_date=tender_in.closing_date,
        status=TenderStatus.CREATED.value
    )
    db.add(db_tender)
    db.commit()
    db.refresh(db_tender)
    return db_tender

@router.get("/", response_model=List[TenderResponse])
def list_tenders(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all created tenders with pagination and optional search filter.
    """
    query = db.query(Tender)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Tender.title.ilike(search_filter)) |
            (Tender.tender_id.ilike(search_filter)) |
            (Tender.department.ilike(search_filter))
        )
    return query.order_by(Tender.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=TenderDetail)
def get_tender(id: int, db: Session = Depends(get_db)):
    """
    Get detailed tender information including extracted pages and raw text.
    """
    db_tender = db.query(Tender).filter(Tender.id == id).first()
    if not db_tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    return db_tender

@router.post("/{id}/upload-pdf", response_model=PDFProcessingResult)
def upload_tender_pdf(
    id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload tender PDF document, parse pages, extract raw text, and persist to DB.
    """
    db_tender = db.query(Tender).filter(Tender.id == id).first()
    if not db_tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Create destination file path
    save_filename = f"tender_{db_tender.id}_{file.filename}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(save_path)
    db_tender.file_name = file.filename
    db_tender.file_path = save_path
    db_tender.file_size = file_size
    db_tender.status = TenderStatus.PROCESSING.value
    db.commit()

    try:
        # Extract pages and text using PDFExtractorService
        extraction_data = PDFExtractorService.extract_pdf_data(save_path)

        # Clear existing pages if re-uploading
        db.query(TenderPage).filter(TenderPage.tender_id == db_tender.id).delete()

        # Add page records
        for p in extraction_data["pages"]:
            db_page = TenderPage(
                tender_id=db_tender.id,
                page_number=p["page_number"],
                text_content=p["text_content"],
                tables_data=p["tables_data"]
            )
            db.add(db_page)

        db_tender.page_count = extraction_data["page_count"]
        db_tender.raw_text = extraction_data["full_text"]
        db_tender.status = TenderStatus.PROCESSED.value
        db.commit()

        return PDFProcessingResult(
            tender_id=db_tender.id,
            file_name=file.filename,
            page_count=extraction_data["page_count"],
            total_characters=extraction_data["total_characters"],
            status="SUCCESS",
            message=f"Successfully extracted {extraction_data['page_count']} pages ({extraction_data['total_characters']} chars)."
        )

    except Exception as e:
        db_tender.status = TenderStatus.FAILED.value
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.get("/{id}/extracted-text", response_model=List[TenderPageResponse])
def get_extracted_text(
    id: int, 
    query: Optional[str] = Query(None, description="Search term within document text"),
    db: Session = Depends(get_db)
):
    """
    Retrieve extracted pages with optional text keyword search filtering.
    """
    db_tender = db.query(Tender).filter(Tender.id == id).first()
    if not db_tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    pages_query = db.query(TenderPage).filter(TenderPage.tender_id == id)
    if query:
        pages_query = pages_query.filter(TenderPage.text_content.ilike(f"%{query}%"))
    
    return pages_query.order_by(TenderPage.page_number.asc()).all()
