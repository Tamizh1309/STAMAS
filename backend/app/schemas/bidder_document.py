from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict

class BidderDocumentBase(BaseModel):
    category: str
    
class BidderDocumentResponse(BidderDocumentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    bidder_id: int
    tender_id: int
    filename: str
    file_size: Optional[int] = None
    page_count: int
    processing_status: str
    extraction_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BidderDocumentPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    document_id: int
    page_number: int
    extracted_text: str
    tables_data: Optional[Any] = None
    extraction_method: str
    extraction_status: str
    extraction_quality: str

class BidderDocumentDetailResponse(BidderDocumentResponse):
    pages: List[BidderDocumentPageResponse] = []
