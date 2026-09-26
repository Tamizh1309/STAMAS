import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class EvaluationStatus(str, enum.Enum):
    EVALUATED = "EVALUATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_EVALUABLE = "NOT_EVALUABLE"
    ERROR = "ERROR"

class EvaluationResult(str, enum.Enum):
    SATISFIED = "SATISFIED"
    NOT_SATISFIED = "NOT_SATISFIED"
    INDETERMINATE = "INDETERMINATE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"

class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("compliance_rules.id"), nullable=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False, index=True)
    evidence_match_id = Column(Integer, ForeignKey("evidence_matches.id"), nullable=True, index=True)
    
    extracted_value = Column(String(255), nullable=True)
    extracted_unit = Column(String(50), nullable=True)
    required_value = Column(String(255), nullable=True)
    operator = Column(String(50), nullable=True)
    
    evaluation_status = Column(String(50), nullable=False, default=EvaluationStatus.EVALUATED.value)
    evaluation_result = Column(String(50), nullable=False, default=EvaluationResult.INDETERMINATE.value)
    explanation = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    rule = relationship("ComplianceRule")
    requirement = relationship("Requirement")
    bidder = relationship("Bidder")
    tender = relationship("Tender")
    evidence_match = relationship("EvidenceMatch")

    @property
    def detected_value(self) -> str:
        return self.extracted_value
