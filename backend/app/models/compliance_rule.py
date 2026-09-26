import datetime
import enum
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class RuleType(str, enum.Enum):
    EXISTENCE = "EXISTENCE"
    BOOLEAN = "BOOLEAN"
    NUMERIC_MIN = "NUMERIC_MIN"
    NUMERIC_MAX = "NUMERIC_MAX"
    NUMERIC_RANGE = "NUMERIC_RANGE"
    TEXT_EQUALS = "TEXT_EQUALS"
    TEXT_CONTAINS = "TEXT_CONTAINS"
    TEXT_MATCH = "TEXT_MATCH"
    DATE_BEFORE = "DATE_BEFORE"
    DATE_AFTER = "DATE_AFTER"
    DATE_RANGE = "DATE_RANGE"
    YEARS_EXPERIENCE = "YEARS_EXPERIENCE"
    CERTIFICATION_REQUIRED = "CERTIFICATION_REQUIRED"
    REGISTRATION_REQUIRED = "REGISTRATION_REQUIRED"
    TURNOVER_MIN = "TURNOVER_MIN"
    DOCUMENT_REQUIRED = "DOCUMENT_REQUIRED"

class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False, index=True)
    rule_code = Column(String(50), nullable=False) # e.g. RULE-001
    
    rule_type = Column(String(50), nullable=False, default=RuleType.TEXT_MATCH.value)
    field_name = Column(String(100), nullable=True)
    operator = Column(String(50), nullable=True) # GREATER_THAN_OR_EQUAL, EQUALS, etc.
    required_value = Column(String(255), nullable=True)
    required_value_max = Column(String(255), nullable=True)
    unit = Column(String(50), nullable=True)
    currency = Column(String(50), nullable=True)
    
    logical_operator = Column(String(10), default="ALL") # ALL, ANY, NOT
    configuration_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationship
    requirement = relationship("Requirement")

    @property
    def target_value(self) -> str:
        return self.required_value
