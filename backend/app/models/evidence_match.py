import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class MatchStatus(str, enum.Enum):
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    NOT_FOUND = "NOT_FOUND"

class MatchingMethod(str, enum.Enum):
    KEYWORD = "KEYWORD"
    SEMANTIC = "SEMANTIC"
    HYBRID = "HYBRID"

class EvidenceMatch(Base):
    __tablename__ = "evidence_matches"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False, index=True)
    document_id = Column(Integer, ForeignKey("bidder_documents.id"), nullable=True, index=True)
    page_id = Column(Integer, ForeignKey("bidder_document_pages.id"), nullable=True, index=True)
    
    evidence_text = Column(Text, nullable=False)
    match_status = Column(String(50), nullable=False, default=MatchStatus.NOT_FOUND.value)
    confidence_score = Column(Float, nullable=False, default=0.0)
    matching_method = Column(String(50), nullable=False, default=MatchingMethod.KEYWORD.value)
    matched_keywords = Column(JSON, nullable=True)
    reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    tender = relationship("Tender")
    requirement = relationship("Requirement")
    bidder = relationship("Bidder")
    document = relationship("BidderDocument")
    page = relationship("BidderDocumentPage")

    @property
    def page_number(self) -> int:
        return self.page.page_number if self.page else 1

    @property
    def bidder_document(self):
        return self.document
