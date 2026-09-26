from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BidderBase(BaseModel):
    bidder_name: str
    company_name: str
    registration_number: Optional[str] = None
    gstin: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class BidderCreate(BidderBase):
    tender_id: int


class BidderUpdate(BaseModel):
    bidder_name: Optional[str] = None
    company_name: Optional[str] = None
    registration_number: Optional[str] = None
    gstin: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None


class BidderResponse(BidderBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    bidder_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class BidderListResponse(BidderResponse):
    document_count: int = 0