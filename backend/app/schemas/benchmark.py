from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class ConfusionMatrixOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matrix: Dict[str, Dict[str, int]] # e.g. {"PASS": {"PASS": 3, "FAIL": 0}, ...}
    total_samples: int
    correct_samples: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float


class BenchmarkEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    benchmark_id: str
    timestamp: str
    environment: str
    total_cases_evaluated: int
    requirement_extraction_metrics: Dict[str, float] # precision, recall, f1
    evidence_matching_metrics: Dict[str, float] # top1_recall, top3_recall, top5_recall, precision
    rule_engine_metrics: Dict[str, float] # accuracy, satisfied_ratio
    decision_engine_metrics: ConfusionMatrixOut
    latency_metrics_ms: Dict[str, float] # avg, p50, p95, max
    error_taxonomy: Dict[str, int]
    limitations: List[str]
