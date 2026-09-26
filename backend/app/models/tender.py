import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class TenderStatus(str, enum.Enum):
    CREATED = "CREATED"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    issue_date = Column(String(50), nullable=True)
    closing_date = Column(String(50), nullable=True)
    
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True) # Bytes
    
    page_count = Column(Integer, default=0)
    raw_text = Column(Text, nullable=True)
    status = Column(String(50), default=TenderStatus.CREATED.value)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    pages = relationship("TenderPage", back_populates="tender", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="tender", cascade="all, delete-orphan")
    bidders = relationship("Bidder", back_populates="tender", cascade="all, delete-orphan")
