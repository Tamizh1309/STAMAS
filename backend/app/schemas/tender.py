from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class TenderBase(BaseModel):
    tender_id: str = Field(..., description="Unique Tender Reference ID (e.g. GEM/2026/B/1001)")
    title: str = Field(..., description="Tender Title / Subject")
    department: str = Field(..., description="Procuring Entity / Department")
    issue_date: Optional[str] = Field(None, description="Issue date YYYY-MM-DD")
    closing_date: Optional[str] = Field(None, description="Closing date YYYY-MM-DD")

class TenderCreate(TenderBase):
    pass

class TenderPageResponse(BaseModel):
    id: int
    page_number: int
    text_content: str
    tables_data: Optional[List[List[List[str]]]] = None

    model_config = ConfigDict(from_attributes=True)

class TenderResponse(TenderBase):
    id: int
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    page_count: int = 0
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenderDetail(TenderResponse):
    pages: List[TenderPageResponse] = []
    raw_text: Optional[str] = None

class PDFProcessingResult(BaseModel):
    tender_id: int
    file_name: str
    page_count: int
    total_characters: int
    status: str
    message: str
