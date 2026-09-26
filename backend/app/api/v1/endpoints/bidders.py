from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.bidder import Bidder, BidderStatus
from app.models.tender import Tender
from app.schemas.bidder import (
    BidderCreate,
    BidderResponse,
    BidderUpdate,
)

router = APIRouter(
    tags=["Bidders"],
)


def generate_bidder_id(db: Session, tender_id: int) -> str:
    """Generate a bidder ID such as BID-001, BID-002, etc."""

    existing_count = (
        db.query(Bidder)
        .filter(Bidder.tender_id == tender_id)
        .count()
    )

    return f"BID-{existing_count + 1:03d}"


@router.post(
    "/tenders/{tender_id}/bidders",
    response_model=BidderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_bidder(
    tender_id: int,
    bidder_data: BidderCreate,
    db: Session = Depends(get_db),
):
    """Create a bidder under an existing tender."""
    # Enforce tender_id from path
    bidder_data.tender_id = tender_id
    tender = (
        db.query(Tender)
        .filter(Tender.id == bidder_data.tender_id)
        .first()
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found",
        )

    bidder = Bidder(
        tender_id=bidder_data.tender_id,
        bidder_id=generate_bidder_id(db, bidder_data.tender_id),
        bidder_name=bidder_data.bidder_name,
        company_name=bidder_data.company_name,
        registration_number=bidder_data.registration_number,
        gstin=bidder_data.gstin,
        contact_person=bidder_data.contact_person,
        email=bidder_data.email,
        phone=bidder_data.phone,
        address=bidder_data.address,
        status=BidderStatus.ACTIVE.value,
    )

    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    return bidder


@router.get(
    "/tenders/{tender_id}/bidders",
    response_model=list[BidderResponse],
)
def get_bidders_by_tender(
    tender_id: int,
    db: Session = Depends(get_db),
):
    """Get all bidders belonging to a tender."""

    tender = (
        db.query(Tender)
        .filter(Tender.id == tender_id)
        .first()
    )

    if not tender:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tender not found",
        )

    return (
        db.query(Bidder)
        .filter(Bidder.tender_id == tender_id)
        .order_by(Bidder.id.asc())
        .all()
    )


@router.get(
    "/bidders/{bidder_id}",
    response_model=BidderResponse,
)
def get_bidder(
    bidder_id: int,
    db: Session = Depends(get_db),
):
    """Get one bidder by database ID."""

    bidder = (
        db.query(Bidder)
        .filter(Bidder.id == bidder_id)
        .first()
    )

    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder not found",
        )

    return bidder


@router.patch(
    "/bidders/{bidder_id}",
    response_model=BidderResponse,
)
def update_bidder(
    bidder_id: int,
    bidder_data: BidderUpdate,
    db: Session = Depends(get_db),
):
    """Update bidder information."""

    bidder = (
        db.query(Bidder)
        .filter(Bidder.id == bidder_id)
        .first()
    )

    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder not found",
        )

    update_data = bidder_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(bidder, field, value)

    db.commit()
    db.refresh(bidder)

    return bidder


from app.models.evidence_match import EvidenceMatch

@router.delete(
    "/bidders/{bidder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_bidder(
    bidder_id: int,
    db: Session = Depends(get_db),
):
    """Delete a bidder, its documents, and its evidence matches."""

    bidder = (
        db.query(Bidder)
        .filter(Bidder.id == bidder_id)
        .first()
    )

    if not bidder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bidder not found",
        )

    db.query(EvidenceMatch).filter(EvidenceMatch.bidder_id == bidder_id).delete()
    db.delete(bidder)
    db.commit()

    return None