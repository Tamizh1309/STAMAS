from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.benchmark import BenchmarkEvaluationResponse
from app.services.reporting.benchmark_evaluator import run_benchmark_evaluation

router = APIRouter()


@router.get("/run", response_model=BenchmarkEvaluationResponse, summary="Execute Live Benchmark Evaluation")
def api_run_benchmark_evaluation(db: Session = Depends(get_db)):
    """
    Runs live evaluation of STAMAS engine components against benchmark ground truth and returns calculated metrics.
    """
    return run_benchmark_evaluation(db)


@router.get("/report", response_model=BenchmarkEvaluationResponse, summary="Get Latest Benchmark Evaluation Report")
def api_get_benchmark_report(db: Session = Depends(get_db)):
    """
    Returns the latest benchmark evaluation report.
    """
    return run_benchmark_evaluation(db)
