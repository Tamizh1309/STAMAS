import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class RequirementCategory(str, enum.Enum):
    ELIGIBILITY = "ELIGIBILITY"
    TECHNICAL = "TECHNICAL"
    FINANCIAL = "FINANCIAL"
    DOCUMENT = "DOCUMENT"
    OTHER = "OTHER"

class RequirementStatus(str, enum.Enum):
    EXTRACTED = "EXTRACTED"
    CONFIRMED = "CONFIRMED"
    CORRECTED = "CORRECTED"
    REVIEW = "REVIEW"

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    req_code = Column(String(50), nullable=False) # e.g. REQ-001
    
    category = Column(String(50), nullable=False, default=RequirementCategory.OTHER.value)
    text = Column(Text, nullable=False)
    mandatory = Column(Boolean, default=True)
    
    constraint_type = Column(String(100), nullable=True) # NUMERIC_THRESHOLD, DOCUMENT_PRESENCE, CERTIFICATION, etc.
    threshold = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    currency = Column(String(50), nullable=True)
    
    source_document = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    evidence_text = Column(Text, nullable=True)
    confidence = Column(Float, default=0.9)
    status = Column(String(50), default=RequirementStatus.EXTRACTED.value)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationship
    tender = relationship("Tender", back_populates="requirements")

    @property
    def requirement_text(self) -> str:
        return self.text

    @property
    def requirement_code(self) -> str:
        return self.req_code
