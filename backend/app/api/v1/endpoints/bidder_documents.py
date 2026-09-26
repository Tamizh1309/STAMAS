import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.models.bidder import Bidder, BidderStatus
from app.models.bidder_document import BidderDocument, BidderDocumentPage, DocumentProcessingStatus, ExtractionStatus
from app.schemas.bidder_document import BidderDocumentResponse, BidderDocumentDetailResponse, BidderDocumentPageResponse
from app.services.document_processor.pdf_extractor import PDFExtractorService

router = APIRouter(
    tags=["Bidder Documents"],
)

def update_bidder_status(bidder: Bidder, db: Session, target_status: str):
    if bidder.status != target_status:
        bidder.status = target_status
        db.commit()

@router.post("/bidders/{bidder_id}/documents", response_model=BidderDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_bidder_document(
    bidder_id: int,
    category: str = Form("OTHER"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    upload_dir = os.path.join(settings.UPLOAD_DIR, "bidders", str(bidder.tender_id), str(bidder_id))
    os.makedirs(upload_dir, exist_ok=True)

    save_filename = f"doc_{file.filename}"
    save_path = os.path.join(upload_dir, save_filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(save_path)

    db_doc = BidderDocument(
        bidder_id=bidder_id,
        tender_id=bidder.tender_id,
        filename=file.filename,
        stored_filename=save_filename,
        file_path=save_path,
        category=category,
        file_size=file_size,
        mime_type="application/pdf",
        processing_status=DocumentProcessingStatus.UPLOADED.value,
        extraction_status=ExtractionStatus.PENDING.value
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    if bidder.status in [BidderStatus.CREATED.value, BidderStatus.ACTIVE.value]:
        update_bidder_status(bidder, db, BidderStatus.DOCUMENTS_UPLOADED.value)

    return db_doc

@router.post("/bidders/{bidder_id}/documents/{document_id}/process", response_model=BidderDocumentResponse)
def process_bidder_document(
    bidder_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id, BidderDocument.bidder_id == bidder_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    bidder = doc.bidder
    doc.processing_status = DocumentProcessingStatus.PROCESSING.value
    db.commit()
    update_bidder_status(bidder, db, BidderStatus.PROCESSING.value)

    try:
        extraction_data = PDFExtractorService.extract_pdf_data(doc.file_path)
        
        db.query(BidderDocumentPage).filter(BidderDocumentPage.document_id == doc.id).delete()
        
        for p in extraction_data["pages"]:
            db_page = BidderDocumentPage(
                document_id=doc.id,
                page_number=p["page_number"],
                extracted_text=p["text_content"],
                tables_data=p["tables_data"],
                extraction_method=p.get("extraction_method", "TEXT_LAYER"),
                extraction_status="SUCCESS",
                extraction_quality=p.get("extraction_quality", "MEDIUM")
            )
            db.add(db_page)
            
        doc.page_count = extraction_data["page_count"]
        doc.processing_status = DocumentProcessingStatus.PROCESSED.value
        doc.extraction_status = extraction_data.get("extraction_method", ExtractionStatus.TEXT_LAYER.value)
        doc.error_message = None
        db.commit()
        db.refresh(doc)
        
        # Check if all uploaded docs for this bidder are processed
        all_docs = db.query(BidderDocument).filter(BidderDocument.bidder_id == bidder_id).all()
        if all(d.processing_status == DocumentProcessingStatus.PROCESSED.value for d in all_docs):
            update_bidder_status(bidder, db, BidderStatus.PROCESSED.value)
        
        return doc
    except Exception as e:
        doc.processing_status = DocumentProcessingStatus.FAILED.value
        doc.extraction_status = ExtractionStatus.FAILED.value
        doc.error_message = str(e)
        db.commit()
        
        update_bidder_status(bidder, db, BidderStatus.FAILED.value)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.get("/bidders/{bidder_id}/documents", response_model=List[BidderDocumentResponse])
def get_bidder_documents(
    bidder_id: int,
    db: Session = Depends(get_db)
):
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")
        
    return db.query(BidderDocument).filter(BidderDocument.bidder_id == bidder_id).order_by(BidderDocument.created_at.desc()).all()

@router.get("/bidders/{bidder_id}/documents/{document_id}", response_model=BidderDocumentDetailResponse)
def get_bidder_document_detail(
    bidder_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id, BidderDocument.bidder_id == bidder_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/bidders/{bidder_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bidder_document(
    bidder_id: int,
    document_id: int,
    db: Session = Depends(get_db)
):
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id, BidderDocument.bidder_id == bidder_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    db.delete(doc)
    db.commit()
    
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except:
            pass
            
    return None

@router.get("/bidder-documents/{document_id}", response_model=BidderDocumentResponse)
def get_bidder_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/bidder-documents/{document_id}/pages", response_model=List[BidderDocumentPageResponse])
def get_bidder_document_pages(document_id: int, db: Session = Depends(get_db)):
    pages = db.query(BidderDocumentPage).filter(BidderDocumentPage.document_id == document_id).order_by(BidderDocumentPage.page_number.asc()).all()
    return pages

@router.get("/bidder-documents/{document_id}/pages/{page_number}", response_model=BidderDocumentPageResponse)
def get_bidder_document_page(document_id: int, page_number: int, db: Session = Depends(get_db)):
    page = db.query(BidderDocumentPage).filter(BidderDocumentPage.document_id == document_id, BidderDocumentPage.page_number == page_number).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.delete("/bidder-documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bidder_document_direct(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    db.delete(doc)
    db.commit()
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except:
            pass
    return None
