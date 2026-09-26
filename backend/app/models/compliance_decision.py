from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class DecisionState:
    """
    Internal helper constants for Decision State.
    """
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    NOT_EVALUATED = "NOT_EVALUATED"


class DecisionType:
    """
    Helper constants for Decision Type.
    Always SYSTEM_DECISION in Phase 8.
    """
    SYSTEM_DECISION = "SYSTEM_DECISION"


class ComplianceDecision(Base):
    __tablename__ = "compliance_decisions"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=True, index=True) # Null for overall bidder decision record

    decision = Column(String(50), nullable=False, default="NOT_EVALUATED") # PASS, FAIL, REVIEW, NOT_EVALUATED
    decision_type = Column(String(50), nullable=False, default="SYSTEM_DECISION") # SYSTEM_DECISION
    is_mandatory = Column(Boolean, default=True)

    reason = Column(Text, nullable=False)
    rule_summary_json = Column(JSON, nullable=True) # Summary of rules evaluated
    evidence_summary_json = Column(JSON, nullable=True) # Summary of evidence matches & page references

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tender = relationship("Tender")
    bidder = relationship("Bidder")
    requirement = relationship("Requirement")
