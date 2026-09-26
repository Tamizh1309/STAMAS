from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class RequirementBase(BaseModel):
    req_code: Optional[str] = Field(None, description="Requirement code, e.g. REQ-001")
    category: str = Field(..., description="Category: ELIGIBILITY, TECHNICAL, FINANCIAL, DOCUMENT, OTHER")
    text: str = Field(..., description="Human readable requirement text")
    mandatory: bool = Field(True, description="Whether the requirement is mandatory")
    
    constraint_type: Optional[str] = Field(None, description="e.g. NUMERIC_THRESHOLD, DOCUMENT_PRESENCE, CERTIFICATION, EXPERIENCE")
    threshold: Optional[float] = Field(None, description="Numeric threshold value if applicable")
    unit: Optional[str] = Field(None, description="Unit e.g. CRORE, YEARS, PROJECTS")
    currency: Optional[str] = Field(None, description="Currency e.g. INR")
    
    source_document: Optional[str] = Field(None, description="Source PDF filename")
    source_page: Optional[int] = Field(None, description="Source PDF page number")
    evidence_text: Optional[str] = Field(None, description="Verbatim evidence snippet from source document")
    confidence: float = Field(0.9, description="Extraction confidence score between 0.0 and 1.0")
    status: str = Field("EXTRACTED", description="Status: EXTRACTED, CONFIRMED, CORRECTED, REVIEW")

class RequirementCreate(RequirementBase):
    pass

class RequirementUpdate(BaseModel):
    category: Optional[str] = None
    text: Optional[str] = None
    mandatory: Optional[bool] = None
    constraint_type: Optional[str] = None
    threshold: Optional[float] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None

class RequirementResponse(RequirementBase):
    id: int
    tender_id: int
    req_code: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExtractionSummary(BaseModel):
    total_extracted: int
    categories_breakdown: dict
    status: str
    message: str
