from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class RAGChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("bidder_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(Integer, ForeignKey("bidder_document_pages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding_reference = Column(Text, nullable=True) # JSON serialized embedding array or ref if present
    metadata_json = Column(JSON, nullable=True) # metadata containing tender_id, bidder_id, document_name, page_number, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("BidderDocument", backref="rag_chunks")
    page = relationship("BidderDocumentPage", backref="rag_chunks")


class RAGQueryLog(Base):
    __tablename__ = "rag_query_logs"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id", ondelete="SET NULL"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    response_status = Column(String(50), nullable=False) # GROUNDED, PARTIAL, INSUFFICIENT_CONTEXT, CONFLICTING_SOURCES, AI_UNAVAILABLE, ERROR
    answer = Column(Text, nullable=False)
    cited_sources_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
