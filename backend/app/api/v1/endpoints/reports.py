from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.schemas.report import TenderComplianceReportResponse, BidderComplianceReportResponse, AuditPaginatedResponse
from app.services.reporting.report_service import (
    generate_tender_report_data,
    generate_bidder_report_data,
    generate_audit_report_data,
    export_report_pdf,
    export_report_csv
)

router = APIRouter()


@router.get("/reports/tenders/{tender_id}", response_model=TenderComplianceReportResponse, summary="Get Tender Compliance Report Data")
def api_get_tender_report(tender_id: int, db: Session = Depends(get_db)):
    """
    Returns structured summary data for all bidders in a tender.
    """
    return generate_tender_report_data(db, tender_id)


@router.get("/reports/tenders/{tender_id}/pdf", summary="Download Tender Compliance Report PDF")
def api_download_tender_pdf(tender_id: int, db: Session = Depends(get_db)):
    """
    Generates and downloads a printable PDF report for a tender.
    """
    data = generate_tender_report_data(db, tender_id)
    pdf_bytes = export_report_pdf("TENDER", data)
    filename = f"STAMAS_Tender_{tender_id}_Compliance_Report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/tenders/{tender_id}/csv", summary="Download Tender Compliance CSV")
def api_download_tender_csv(tender_id: int, db: Session = Depends(get_db)):
    """
    Downloads tabular compliance summary in CSV format.
    """
    data = generate_tender_report_data(db, tender_id)
    csv_str = export_report_csv("TENDER", data)
    filename = f"STAMAS_Tender_{tender_id}_Compliance_Report.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/bidders/{bidder_id}", response_model=BidderComplianceReportResponse, summary="Get Bidder Compliance Report Data")
def api_get_bidder_report(
    bidder_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    db: Session = Depends(get_db)
):
    """
    Returns detailed compliance report data for a bidder, including system and officer decision breakdowns.
    """
    return generate_bidder_report_data(db, tender_id=tender_id, bidder_id=bidder_id)


@router.get("/reports/bidders/{bidder_id}/pdf", summary="Download Bidder Compliance Report PDF")
def api_download_bidder_pdf(
    bidder_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    db: Session = Depends(get_db)
):
    """
    Generates and downloads a printable PDF report for a single bidder.
    """
    data = generate_bidder_report_data(db, tender_id=tender_id, bidder_id=bidder_id)
    pdf_bytes = export_report_pdf("BIDDER", data)
    filename = f"STAMAS_Bidder_{bidder_id}_Compliance_Report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/bidders/{bidder_id}/csv", summary="Download Bidder Compliance CSV")
def api_download_bidder_csv(
    bidder_id: int,
    tender_id: int = Query(..., description="Tender ID scoping parameter"),
    db: Session = Depends(get_db)
):
    """
    Downloads detailed bidder requirement traceability breakdown in CSV format.
    """
    data = generate_bidder_report_data(db, tender_id=tender_id, bidder_id=bidder_id)
    csv_str = export_report_csv("BIDDER", data)
    filename = f"STAMAS_Bidder_{bidder_id}_Compliance_Report.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/reports/audit", response_model=AuditPaginatedResponse, summary="Get Paginated Audit Event Log")
def api_get_audit_report(
    tender_id: Optional[int] = Query(None, description="Tender ID filter"),
    bidder_id: Optional[int] = Query(None, description="Bidder ID filter"),
    action_filter: Optional[str] = Query(None, description="Action filter (e.g. DECISION_OVERRIDDEN)"),
    search: Optional[str] = Query(None, description="Search officer, action, or comment"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns paginated officer action audit log entries with filters.
    """
    return generate_audit_report_data(
        db,
        tender_id=tender_id,
        bidder_id=bidder_id,
        action_filter=action_filter,
        search=search,
        page=page,
        page_size=page_size
    )


@router.get("/reports/audit/csv", summary="Download Audit Trail CSV")
def api_download_audit_csv(
    tender_id: Optional[int] = Query(None),
    bidder_id: Optional[int] = Query(None),
    action_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Downloads full filtered audit event history in CSV format.
    """
    data = generate_audit_report_data(db, tender_id=tender_id, bidder_id=bidder_id, action_filter=action_filter, search=search, page=1, page_size=1000)
    csv_str = export_report_csv("AUDIT", data)
    filename = f"STAMAS_Audit_Trail.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
