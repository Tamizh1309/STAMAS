import io
import csv
import json
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.requirement import Requirement
from app.models.compliance_decision import ComplianceDecision
from app.models.officer_decision import OfficerDecision, OfficerReviewAudit, OfficerDecisionType, ReviewStatus
from app.models.evidence_match import EvidenceMatch
from app.models.rule_evaluation import RuleEvaluation
from app.services.compliance.officer_review import get_bidder_review_summary, get_decision_audit_trail, _verify_scoping

# ReportLab Imports for PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable


def generate_tender_report_data(db: Session, tender_id: int) -> Dict[str, Any]:
    """
    Aggregates complete Tender Compliance Report data across all bidders.
    """
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail=f"Tender {tender_id} not found")

    bidders = db.query(Bidder).filter(Bidder.tender_id == tender_id).all()

    bidder_summaries = []
    sys_counts = {"PASS": 0, "FAIL": 0, "REVIEW": 0}
    off_counts = {"PASS": 0, "FAIL": 0, "REVIEW": 0, "PENDING": 0}

    for b in bidders:
        b_summary = get_bidder_review_summary(db, tender_id, b.id)

        sys_dec = b_summary["system_overall_decision"]
        final_dec = b_summary["final_overall_decision"]

        sys_counts[sys_dec] = sys_counts.get(sys_dec, 0) + 1
        off_counts[final_dec] = off_counts.get(final_dec, 0) + 1

        bidder_summaries.append({
            "bidder_id": b.id,
            "bidder_name": b.bidder_name,
            "company_name": b.company_name,
            "registration_number": b.registration_number,
            "system_overall_decision": sys_dec,
            "final_overall_decision": final_dec,
            "review_status": b_summary["review_status"],
            "total_requirements": b_summary["total_requirements"],
            "reviewed_count": b_summary["reviewed_count"],
            "pending_count": b_summary["pending_count"],
            "confirmed_count": b_summary["confirmed_count"],
            "overridden_count": b_summary["overridden_count"]
        })

    return {
        "tender_id": tender.id,
        "tender_number": tender.tender_id,
        "title": tender.title,
        "department": tender.department,
        "status": tender.status,
        "created_at": tender.created_at.isoformat() if tender.created_at else None,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_bidders": len(bidders),
        "bidders": bidder_summaries,
        "overall_system_summary": sys_counts,
        "overall_officer_summary": off_counts
    }


def generate_bidder_report_data(db: Session, tender_id: int, bidder_id: int) -> Dict[str, Any]:
    """
    Aggregates detailed Bidder Compliance Report data.
    """
    tender, bidder, _ = _verify_scoping(db, tender_id, bidder_id)
    summary = get_bidder_review_summary(db, tender_id, bidder_id)

    summary_counts = {
        "total": summary["total_requirements"],
        "reviewed": summary["reviewed_count"],
        "pending": summary["pending_count"],
        "confirmed": summary["confirmed_count"],
        "overridden": summary["overridden_count"]
    }

    return {
        "tender_id": tender.id,
        "tender_number": tender.tender_id,
        "tender_title": tender.title,
        "department": tender.department,
        "bidder_id": bidder.id,
        "bidder_name": bidder.bidder_name,
        "company_name": bidder.company_name,
        "registration_number": bidder.registration_number,
        "gstin": bidder.gstin,
        "email": bidder.email,
        "system_overall_decision": summary["system_overall_decision"],
        "final_overall_decision": summary["final_overall_decision"],
        "review_status": summary["review_status"],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "summary_counts": summary_counts,
        "requirements": summary["requirements"],
        "audits": summary["audits"]
    }


def generate_audit_report_data(
    db: Session,
    tender_id: Optional[int] = None,
    bidder_id: Optional[int] = None,
    action_filter: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Returns filtered and paginated audit event history with metrics.
    """
    query = db.query(OfficerReviewAudit)

    if tender_id:
        query = query.filter(OfficerReviewAudit.tender_id == tender_id)
    if bidder_id:
        query = query.filter(OfficerReviewAudit.bidder_id == bidder_id)
    if action_filter and action_filter != "ALL":
        query = query.filter(OfficerReviewAudit.action == action_filter)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (OfficerReviewAudit.officer_name.ilike(search_term)) |
            (OfficerReviewAudit.action.ilike(search_term)) |
            (OfficerReviewAudit.reason.ilike(search_term)) |
            (OfficerReviewAudit.comment.ilike(search_term))
        )

    total_events = query.count()
    total_pages = (total_events + page_size - 1) // page_size if page_size > 0 else 1

    events = query.order_by(OfficerReviewAudit.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # Calculate global stats
    confirmed_cnt = db.query(OfficerReviewAudit).filter(OfficerReviewAudit.action == "DECISION_CONFIRMED").count()
    overridden_cnt = db.query(OfficerReviewAudit).filter(OfficerReviewAudit.action == "DECISION_OVERRIDDEN").count()
    reopened_cnt = db.query(OfficerReviewAudit).filter(OfficerReviewAudit.action == "DECISION_REOPENED").count()

    event_data = [
        {
            "id": a.id,
            "tender_id": a.tender_id,
            "bidder_id": a.bidder_id,
            "requirement_id": a.requirement_id,
            "officer_decision_id": a.officer_decision_id,
            "officer_id": a.officer_id,
            "officer_name": a.officer_name,
            "officer_role": a.officer_role,
            "action": a.action,
            "previous_system_decision": a.previous_system_decision,
            "previous_final_decision": a.previous_final_decision,
            "new_final_decision": a.new_final_decision,
            "decision_type": a.decision_type,
            "reason": a.reason,
            "comment": a.comment,
            "timestamp": a.timestamp.isoformat() if a.timestamp else None
        } for a in events
    ]

    return {
        "total_events": total_events,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "override_stats": {
            "confirmed": confirmed_cnt,
            "overridden": overridden_cnt,
            "reopened": reopened_cnt
        },
        "events": event_data
    }


def export_report_pdf(report_type: str, data: Dict[str, Any]) -> bytes:
    """
    Generates a professional PDF document using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#1E293B'))
    subtitle_style = ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#64748B'))
    heading_style = ParagraphStyle('SectionHeading', parent=styles['Heading2'], fontSize=13, leading=16, textColor=colors.HexColor('#0F172A'), spaceBefore=12, spaceAfter=6)
    cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#334155'))
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#0F172A'), fontName='Helvetica-Bold')

    story = []

    # Header Banner
    story.append(Paragraph("<b>STAMAS — Smart Tender Compliance Platform</b>", title_style))
    story.append(Paragraph(f"Official Compliance & Audit Verification Report | Generated: {data.get('generated_at', 'N/A')}", subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=12))

    if report_type == "TENDER":
        story.append(Paragraph(f"<b>Tender Compliance Summary Report</b>", heading_style))
        story.append(Paragraph(f"<b>Tender ID:</b> {data.get('tender_number')} | <b>Title:</b> {data.get('title')}", cell_style))
        story.append(Paragraph(f"<b>Department:</b> {data.get('department')} | <b>Total Bidders:</b> {data.get('total_bidders')}", cell_style))
        story.append(Spacer(1, 12))

        # Bidder summary table
        table_data = [[
            Paragraph("Bidder Company", cell_bold),
            Paragraph("Req Count", cell_bold),
            Paragraph("System Decision", cell_bold),
            Paragraph("Final Officer Decision", cell_bold),
            Paragraph("Review Status", cell_bold)
        ]]

        for b in data.get("bidders", []):
            table_data.append([
                Paragraph(b["company_name"], cell_style),
                Paragraph(str(b["total_requirements"]), cell_style),
                Paragraph(f"<b>{b['system_overall_decision']}</b>", cell_style),
                Paragraph(f"<b>{b['final_overall_decision']}</b> ({b['confirmed_count']} Conf / {b['overridden_count']} Over)", cell_style),
                Paragraph(b["review_status"], cell_style)
            ])

        t = Table(table_data, colWidths=[160, 60, 100, 140, 80])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)

    elif report_type == "BIDDER":
        story.append(Paragraph(f"<b>Bidder Detailed Compliance Report</b>", heading_style))
        story.append(Paragraph(f"<b>Bidder:</b> {data.get('company_name')} (ID: {data.get('bidder_id')})", cell_style))
        story.append(Paragraph(f"<b>Tender:</b> {data.get('tender_title')} ({data.get('tender_number')})", cell_style))
        story.append(Paragraph(f"<b>System Overall Decision:</b> {data.get('system_overall_decision')} | <b>Final Officer Decision:</b> {data.get('final_overall_decision')}", cell_style))
        story.append(Spacer(1, 12))

        story.append(Paragraph("<b>Requirement-wise Compliance & Traceability Breakdown</b>", heading_style))

        table_data = [[
            Paragraph("Code", cell_bold),
            Paragraph("Requirement", cell_bold),
            Paragraph("System", cell_bold),
            Paragraph("Final Officer", cell_bold),
            Paragraph("Override / Comment", cell_bold)
        ]]

        for req in data.get("requirements", []):
            off_str = f"{req['effective_decision']} [{req['decision_type']}]"
            comment_str = req.get("officer_decision", {}).get("override_reason") or req.get("system_reason") or "N/A"

            table_data.append([
                Paragraph(req["req_code"], cell_style),
                Paragraph(req["text"], cell_style),
                Paragraph(f"<b>{req['system_decision']}</b>", cell_style),
                Paragraph(f"<b>{off_str}</b>", cell_style),
                Paragraph(comment_str[:120], cell_style)
            ])

        t = Table(table_data, colWidths=[60, 180, 70, 90, 140])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t)

    # Footer Disclaimer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceAfter=8))
    story.append(Paragraph(
        "<b>STAMAS Disclaimer:</b> System decisions are produced by deterministic rule engine algorithms. "
        "Final procurement decisions reflect authoritative officer review. Both layers are preserved separately for complete auditability.",
        ParagraphStyle('FooterText', parent=styles['Normal'], fontSize=7, leading=9, textColor=colors.HexColor('#94A3B8'))
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def export_report_csv(report_type: str, data: Dict[str, Any]) -> str:
    """
    Exports structured tabular report data into CSV string format.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "TENDER":
        writer.writerow(["Tender ID", "Tender Title", "Department", "Bidder ID", "Company Name", "System Decision", "Final Officer Decision", "Review Status", "Total Reqs", "Confirmed", "Overridden"])
        for b in data.get("bidders", []):
            writer.writerow([
                data.get("tender_number"), data.get("title"), data.get("department"),
                b["bidder_id"], b["company_name"], b["system_overall_decision"],
                b["final_overall_decision"], b["review_status"], b["total_requirements"],
                b["confirmed_count"], b["overridden_count"]
            ])

    elif report_type == "BIDDER":
        writer.writerow([
            "Tender ID", "Bidder ID", "Company Name", "Req Code", "Requirement Text", "Category",
            "Mandatory", "System Decision", "Final Officer Decision", "Decision Type", "Rule Result",
            "Evidence Text", "Document Filename", "Page Number", "Override Reason", "Officer Comment"
        ])
        for req in data.get("requirements", []):
            doc_name = req["evidence_matches"][0]["document_filename"] if req.get("evidence_matches") else "N/A"
            page_num = req["evidence_matches"][0]["page_number"] if req.get("evidence_matches") else "N/A"
            ev_text = req["evidence_matches"][0]["evidence_text"] if req.get("evidence_matches") else "N/A"
            rule_res = req["rule_evaluations"][0]["evaluation_result"] if req.get("rule_evaluations") else "N/A"
            off_dec = req.get("officer_decision") or {}

            writer.writerow([
                data.get("tender_number"), data.get("bidder_id"), data.get("company_name"),
                req["req_code"], req["text"], req["category"], req["is_mandatory"],
                req["system_decision"], req["effective_decision"], req["decision_type"],
                rule_res, ev_text, doc_name, page_num,
                off_dec.get("override_reason", ""), off_dec.get("officer_comment", "")
            ])

    elif report_type == "AUDIT":
        writer.writerow(["Timestamp", "Tender ID", "Bidder ID", "Requirement ID", "Officer Name", "Officer Role", "Action", "Previous Decision", "New Decision", "Decision Type", "Reason", "Comment"])
        for a in data.get("events", []):
            writer.writerow([
                a.get("timestamp"), a.get("tender_id"), a.get("bidder_id"), a.get("requirement_id"),
                a.get("officer_name"), a.get("officer_role"), a.get("action"),
                a.get("previous_system_decision"), a.get("new_final_decision"), a.get("decision_type"),
                a.get("reason"), a.get("comment")
            ])

    return output.getvalue()
