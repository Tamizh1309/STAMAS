import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class FinalDecisionState:
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"

class OfficerDecisionType:
    CONFIRMED = "CONFIRMED"
    OVERRIDDEN = "OVERRIDDEN"

class ReviewStatus:
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    FINALIZED = "FINALIZED"
    REOPENED = "REOPENED"

class AuditAction:
    REVIEW_STARTED = "REVIEW_STARTED"
    EVIDENCE_VIEWED = "EVIDENCE_VIEWED"
    DECISION_CONFIRMED = "DECISION_CONFIRMED"
    DECISION_OVERRIDDEN = "DECISION_OVERRIDDEN"
    DECISION_FINALIZED = "DECISION_FINALIZED"
    DECISION_REOPENED = "DECISION_REOPENED"


class OfficerDecision(Base):
    __tablename__ = "officer_decisions"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=True, index=True)
    system_decision_id = Column(Integer, ForeignKey("compliance_decisions.id", ondelete="SET NULL"), nullable=True, index=True)

    final_decision = Column(String(50), nullable=False) # PASS, FAIL, REVIEW
    decision_type = Column(String(50), nullable=False) # CONFIRMED, OVERRIDDEN

    officer_id = Column(String(100), nullable=False, default="OFFICER-001")
    officer_name = Column(String(255), nullable=False, default="Procurement Evaluation Officer")
    officer_role = Column(String(255), nullable=False, default="Senior Officer")

    officer_comment = Column(Text, nullable=True)
    override_reason = Column(Text, nullable=True)
    review_status = Column(String(50), nullable=False, default=ReviewStatus.PENDING)

    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    finalized_at = Column(DateTime, nullable=True)

    # Relationships
    tender = relationship("Tender")
    bidder = relationship("Bidder")
    requirement = relationship("Requirement")
    system_decision = relationship("ComplianceDecision")


class OfficerReviewAudit(Base):
    __tablename__ = "officer_review_audits"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id", ondelete="CASCADE"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id", ondelete="CASCADE"), nullable=True, index=True)
    officer_decision_id = Column(Integer, ForeignKey("officer_decisions.id", ondelete="SET NULL"), nullable=True, index=True)

    officer_id = Column(String(100), nullable=False, default="OFFICER-001")
    officer_name = Column(String(255), nullable=False, default="Procurement Evaluation Officer")
    officer_role = Column(String(255), nullable=False, default="Senior Officer")

    action = Column(String(100), nullable=False)
    previous_system_decision = Column(String(50), nullable=True)
    previous_final_decision = Column(String(50), nullable=True)
    new_final_decision = Column(String(50), nullable=True)
    decision_type = Column(String(50), nullable=True) # CONFIRMED / OVERRIDDEN

    reason = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationships
    tender = relationship("Tender")
    bidder = relationship("Bidder")
    requirement = relationship("Requirement")
