import time
import pytest
from app.services.reporting.benchmark_evaluator import run_benchmark_evaluation
from app.services.reporting.report_service import generate_tender_report_data, export_report_pdf

def test_benchmark_evaluator_execution(db):
    """
    Executes live benchmark evaluator service and asserts calculated metrics.
    """
    t0 = time.perf_counter()
    metrics = run_benchmark_evaluation(db)
    t1 = time.perf_counter()

    assert metrics["total_cases_evaluated"] >= 3
    assert "precision" in metrics["requirement_extraction_metrics"]
    assert "top1_recall" in metrics["evidence_matching_metrics"]
    assert "accuracy" in metrics["decision_engine_metrics"]
    assert metrics["latency_metrics_ms"]["average_ms"] >= 0.0

    execution_time_ms = (t1 - t0) * 1000.0
    assert execution_time_ms < 5000.0 # Benchmark suite runs under 5 seconds


def test_pdf_rendering_latency(db):
    """
    Measures PDF generation performance.
    """
    from app.models.tender import Tender
    from app.models.bidder import Bidder
    
    tender = Tender(tender_id="TND-PERF-1", title="Perf Test Tender", department="QA")
    db.add(tender)
    db.commit()
    db.refresh(tender)

    bidder = Bidder(tender_id=tender.id, bidder_name="Perf Bidder", company_name="Perf Bidder")
    db.add(bidder)
    db.commit()

    tender_report = generate_tender_report_data(db, tender.id)
    t0 = time.perf_counter()
    pdf_bytes = export_report_pdf("TENDER", tender_report)
    t1 = time.perf_counter()

    render_time_ms = (t1 - t0) * 1000.0
    assert len(pdf_bytes) > 100
    assert render_time_ms < 2000.0 # PDF rendering under 2 seconds
