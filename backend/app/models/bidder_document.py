import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class DocumentCategory(str, enum.Enum):
    FINANCIAL = "FINANCIAL"
    TECHNICAL = "TECHNICAL"
    ELIGIBILITY = "ELIGIBILITY"
    CERTIFICATION = "CERTIFICATION"
    EXPERIENCE = "EXPERIENCE"
    REGISTRATION = "REGISTRATION"
    TAX = "TAX"
    ANNEXURE = "ANNEXURE"
    OTHER = "OTHER"

class DocumentProcessingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    
class ExtractionStatus(str, enum.Enum):
    PENDING = "PENDING"
    TEXT_LAYER = "TEXT_LAYER"
    OCR = "OCR"
    MIXED = "MIXED"
    FAILED = "FAILED"

class BidderDocument(Base):
    __tablename__ = "bidder_documents"

    id = Column(Integer, primary_key=True, index=True) # acts as document_id
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    
    filename = Column(String(255), nullable=False) # replaced original_filename
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    category = Column(String(50), default=DocumentCategory.OTHER.value)
    
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    page_count = Column(Integer, default=0)
    
    processing_status = Column(String(50), default=DocumentProcessingStatus.UPLOADED.value)
    extraction_status = Column(String(50), default=ExtractionStatus.PENDING.value)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    bidder = relationship("Bidder", back_populates="documents")
    tender = relationship("Tender")
    pages = relationship("BidderDocumentPage", back_populates="document", cascade="all, delete-orphan")

    @property
    def original_filename(self) -> str:
        return self.filename

    @property
    def file_name(self) -> str:
        return self.filename

class BidderDocumentPage(Base):
    __tablename__ = "bidder_document_pages"

    id = Column(Integer, primary_key=True, index=True) # acts as page_id
    document_id = Column(Integer, ForeignKey("bidder_documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=False) # replaced text_content
    tables_data = Column(JSON, nullable=True)
    extraction_method = Column(String(50), default="TEXT_LAYER")
    extraction_status = Column(String(50), default="SUCCESS")
    extraction_quality = Column(String(50), default="HIGH")
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationship
    document = relationship("BidderDocument", back_populates="pages")
