from sqlalchemy import Column, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class TenderPage(Base):
    __tablename__ = "tender_pages"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    tables_data = Column(JSON, nullable=True) # JSON representation of extracted tables
    
    tender = relationship("Tender", back_populates="pages")
