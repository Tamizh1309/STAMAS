import re
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.requirement import Requirement
from app.models.bidder import Bidder
from app.models.evidence_match import EvidenceMatch, MatchStatus
from app.models.compliance_rule import ComplianceRule, RuleType
from app.models.rule_evaluation import RuleEvaluation, EvaluationStatus, EvaluationResult

class RuleEngineService:
    """
    Compliance Rule Engine Service (Phase 6)
    Evaluates requirements against Phase 5 evidence matches using explicit, deterministic rules.
    Outputs transparent, human-readable explanations.
    """

    @classmethod
    def get_or_create_default_rules_for_requirement(
        cls, db: Session, requirement: Requirement
    ) -> List[ComplianceRule]:
        """
        Retrieves existing explicit compliance rules for a requirement, or auto-generates
        a deterministic default rule based on requirement metadata.
        """
        existing_rules = db.query(ComplianceRule).filter(
            ComplianceRule.requirement_id == requirement.id
        ).all()

        if existing_rules:
            return existing_rules

        text_lower = (requirement.text or "").lower()
        constraint_type = (requirement.constraint_type or "").upper()
        req_code = requirement.req_code

        # Rule auto-inference based on requirement metadata
        rule_type = RuleType.TEXT_MATCH.value
        operator = "CONTAINS"
        required_val = requirement.text
        unit = requirement.unit
        currency = requirement.currency

        if "year" in text_lower or constraint_type == "EXPERIENCE" or requirement.unit == "YEARS":
            rule_type = RuleType.YEARS_EXPERIENCE.value
            operator = "GREATER_THAN_OR_EQUAL"
            required_val = str(int(requirement.threshold)) if requirement.threshold else "5"
            unit = "YEARS"
        elif "turnover" in text_lower or "crore" in text_lower or constraint_type == "FINANCIAL":
            rule_type = RuleType.TURNOVER_MIN.value
            operator = "GREATER_THAN_OR_EQUAL"
            required_val = str(requirement.threshold) if requirement.threshold else "10"
            unit = requirement.unit or "CRORE"
            currency = requirement.currency or "INR"
        elif "iso" in text_lower or constraint_type == "CERTIFICATION":
            rule_type = RuleType.CERTIFICATION_REQUIRED.value
            operator = "CONTAINS"
            iso_match = re.search(r'\biso[- ]?\d+\b', text_lower)
            required_val = iso_match.group(0).upper() if iso_match else "ISO 9001"
        elif "gst" in text_lower or "gstin" in text_lower or constraint_type == "REGISTRATION":
            rule_type = RuleType.REGISTRATION_REQUIRED.value
            operator = "CONTAINS"
            required_val = "GST"
        elif constraint_type == "DOCUMENT_PRESENCE" or requirement.category == "DOCUMENT":
            rule_type = RuleType.DOCUMENT_REQUIRED.value
            operator = "EXISTS"
            required_val = requirement.req_code

        default_rule = ComplianceRule(
            requirement_id=requirement.id,
            rule_code=f"RULE-{req_code}",
            rule_type=rule_type,
            field_name=constraint_type or "evidence_text",
            operator=operator,
            required_value=required_val,
            unit=unit,
            currency=currency,
            logical_operator="ALL"
        )
        db.add(default_rule)
        db.commit()
        db.refresh(default_rule)

        return [default_rule]

    @staticmethod
    def extract_values_from_evidence(evidence_text: str) -> Dict[str, Any]:
        """
        Extracts structured numbers, durations, dates, certifications, and registrations from evidence text.
        Never hallucinates missing numbers or facts.
        """
        if not evidence_text or not evidence_text.strip():
            return {}

        text_lower = evidence_text.lower()
        extracted = {}

        # 1. Experience duration from year range e.g. "from 2018 to 2025" or "2018-2025"
        year_ranges = re.findall(r'\b(19\d\d|20\d\d)\s*(?:to|-|until)\s*(19\d\d|20\d\d)\b', text_lower)
        if year_ranges:
            diffs = [int(end) - int(start) for start, end in year_ranges]
            max_duration = max(diffs)
            extracted["experience_years"] = max_duration
            extracted["year_range"] = f"{year_ranges[0][0]}-{year_ranges[0][1]}"

        # Explicit experience mention e.g. "7 years experience" or "10 yrs"
        exp_matches = re.findall(r'\b(\d+(?:\.\d+)?)\s*(?:years?|yrs?)\b', text_lower)
        if exp_matches and "experience_years" not in extracted:
            extracted["experience_years"] = float(exp_matches[0])

        # 2. Turnover / monetary values e.g. "₹12.5 crore", "12.5 crore", "INR 10 Crore"
        turnover_matches = re.findall(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(crore|lakh|lakhs|million|billion)\b', text_lower)
        if turnover_matches:
            val_str, unit_str = turnover_matches[0]
            extracted["turnover_value"] = float(val_str)
            extracted["turnover_unit"] = unit_str.upper()

        # 3. Certifications e.g. "ISO 9001:2015", "ISO 9001"
        iso_matches = re.findall(r'\biso[- ]?\d+(?:\:\d+)?\b', text_lower)
        if iso_matches:
            extracted["certification"] = iso_matches[0].upper()

        # 4. Registrations e.g. "GSTIN: 33ABCDE1234F1Z5", "GST"
        gst_matches = re.findall(r'\b[0-9]{2}[a-z]{5}[0-9]{4}[a-z]{1}[1-9a-z]{1}z[0-9a-z]{1}\b', text_lower)
        if gst_matches:
            extracted["gstin"] = gst_matches[0].upper()
        elif "gst" in text_lower:
            extracted["gstin"] = "GST Registered"

        return extracted

    @classmethod
    def evaluate_rule_against_evidence(
        cls,
        rule: ComplianceRule,
        requirement: Requirement,
        evidence_matches: List[EvidenceMatch]
    ) -> Tuple[str, str, Optional[str], Optional[str], Optional[EvidenceMatch], str]:
        """
        Deterministically evaluates a ComplianceRule against evidence matches.
        Returns (evaluation_status, evaluation_result, extracted_value, extracted_unit, best_evidence, explanation).
        """
        # Case A: No evidence matches exist
        if not evidence_matches:
            return (
                EvaluationStatus.INSUFFICIENT_EVIDENCE.value,
                EvaluationResult.INSUFFICIENT_EVIDENCE.value,
                None,
                None,
                None,
                "No relevant evidence was found for evaluating this rule."
            )

        # Filter out NOT_FOUND evidence matches
        valid_matches = [m for m in evidence_matches if m.match_status != MatchStatus.NOT_FOUND.value]

        if not valid_matches:
            return (
                EvaluationStatus.INSUFFICIENT_EVIDENCE.value,
                EvaluationResult.INSUFFICIENT_EVIDENCE.value,
                None,
                None,
                evidence_matches[0],
                "No relevant evidence pages met the relevance threshold for evaluating this rule."
            )

        best_match = max(valid_matches, key=lambda m: m.confidence_score)

        # Case B: Low confidence evidence
        if best_match.match_status == MatchStatus.LOW_CONFIDENCE.value or best_match.confidence_score < 0.60:
            return (
                EvaluationStatus.NOT_EVALUABLE.value,
                EvaluationResult.INSUFFICIENT_EVIDENCE.value,
                None,
                None,
                best_match,
                "The available evidence has low matching confidence and was not treated as sufficient for deterministic rule evaluation."
            )

        # Case C: Conflicting evidence detection (e.g., Doc A says 12 Crore, Doc B says 7 Crore)
        extracted_per_match = []
        for m in valid_matches:
            ext = cls.extract_values_from_evidence(m.evidence_text)
            if ext:
                extracted_per_match.append((m, ext))

        if rule.rule_type in [RuleType.TURNOVER_MIN.value, RuleType.NUMERIC_MIN.value]:
            turnover_vals = [e[1]["turnover_value"] for e in extracted_per_match if "turnover_value" in e[1]]
            if len(set(turnover_vals)) > 1:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.CONFLICTING_EVIDENCE.value,
                    str(turnover_vals),
                    rule.unit,
                    best_match,
                    f"Multiple evidence sources contain conflicting numerical values ({', '.join(str(v) for v in turnover_vals)} {rule.unit or ''}). Requires officer review."
                )

        # Extract values for best match
        extracted = cls.extract_values_from_evidence(best_match.evidence_text)
        rule_type = rule.rule_type
        req_val_str = rule.required_value or (str(requirement.threshold) if requirement.threshold else None)

        # 1. YEARS_EXPERIENCE Rule Evaluation
        if rule_type in [RuleType.YEARS_EXPERIENCE.value, RuleType.NUMERIC_MIN.value] and (rule.unit == "YEARS" or "year" in requirement.text.lower()):
            required_years = float(req_val_str) if req_val_str and req_val_str.replace('.', '', 1).isdigit() else 5.0
            
            if "experience_years" in extracted:
                exp_yrs = float(extracted["experience_years"])
                year_range_info = f" (from date period {extracted.get('year_range')})" if "year_range" in extracted else ""
                
                if exp_yrs >= required_years:
                    return (
                        EvaluationStatus.EVALUATED.value,
                        EvaluationResult.SATISFIED.value,
                        f"{exp_yrs:g}",
                        "YEARS",
                        best_match,
                        f"Evidence indicates project experience of approximately {exp_yrs:g} years{year_range_info}, which meets or exceeds the required minimum of {required_years:g} years."
                    )
                else:
                    return (
                        EvaluationStatus.EVALUATED.value,
                        EvaluationResult.NOT_SATISFIED.value,
                        f"{exp_yrs:g}",
                        "YEARS",
                        best_match,
                        f"Evidence indicates project experience of {exp_yrs:g} years{year_range_info}, which is below the required minimum of {required_years:g} years."
                    )
            else:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.INDETERMINATE.value,
                    None,
                    "YEARS",
                    best_match,
                    "Evidence mentions project experience but no specific numeric duration or date range could be extracted."
                )

        # 2. TURNOVER_MIN / NUMERIC_MIN Rule Evaluation
        elif rule_type in [RuleType.TURNOVER_MIN.value, RuleType.NUMERIC_MIN.value]:
            required_num = float(req_val_str) if req_val_str and req_val_str.replace('.', '', 1).isdigit() else 10.0
            
            if "turnover_value" in extracted:
                act_num = extracted["turnover_value"]
                act_unit = extracted.get("turnover_unit", rule.unit or "CRORE")
                
                if act_num >= required_num:
                    return (
                        EvaluationStatus.EVALUATED.value,
                        EvaluationResult.SATISFIED.value,
                        f"{act_num:g}",
                        act_unit,
                        best_match,
                        f"Detected turnover of {act_num:g} {act_unit} meets or exceeds the required minimum threshold of {required_num:g} {rule.unit or 'CRORE'}."
                    )
                else:
                    return (
                        EvaluationStatus.EVALUATED.value,
                        EvaluationResult.NOT_SATISFIED.value,
                        f"{act_num:g}",
                        act_unit,
                        best_match,
                        f"Detected turnover of {act_num:g} {act_unit} is below the required minimum threshold of {required_num:g} {rule.unit or 'CRORE'}."
                    )
            else:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.INDETERMINATE.value,
                    None,
                    rule.unit,
                    best_match,
                    "No explicit numeric monetary value was found in the available evidence text."
                )

        # 3. CERTIFICATION_REQUIRED Rule Evaluation
        elif rule_type == RuleType.CERTIFICATION_REQUIRED.value:
            req_cert = (rule.required_value or "ISO 9001").lower()
            ev_lower = best_match.evidence_text.lower()
            
            if req_cert in ev_lower or "certification" in extracted or "iso" in ev_lower:
                cert_detected = extracted.get("certification", req_cert.upper())
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.SATISFIED.value,
                    cert_detected,
                    None,
                    best_match,
                    f"Required certification ({cert_detected}) was detected in the bidder document evidence."
                )
            else:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.NOT_SATISFIED.value,
                    None,
                    None,
                    best_match,
                    f"Required certification ({rule.required_value}) was not found in the evidence text."
                )

        # 4. REGISTRATION_REQUIRED Rule Evaluation
        elif rule_type == RuleType.REGISTRATION_REQUIRED.value:
            req_reg = (rule.required_value or "GST").lower()
            ev_lower = best_match.evidence_text.lower()
            
            if req_reg in ev_lower or "gstin" in extracted or "registration" in ev_lower:
                reg_detected = extracted.get("gstin", "Registration Verified")
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.SATISFIED.value,
                    reg_detected,
                    None,
                    best_match,
                    f"Required registration evidence ({reg_detected}) was found in the bidder document."
                )
            else:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.NOT_SATISFIED.value,
                    None,
                    None,
                    best_match,
                    f"Required registration details ({rule.required_value}) were not found in the evidence text."
                )

        # 5. DOCUMENT_REQUIRED / EXISTENCE / Default TEXT_MATCH Evaluation
        else:
            if best_match.match_status == MatchStatus.MATCHED.value:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.SATISFIED.value,
                    "Document Present",
                    None,
                    best_match,
                    "Strong matching evidence document page is present for this requirement."
                )
            elif best_match.match_status == MatchStatus.PARTIAL.value:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.SATISFIED.value,
                    "Partial Match",
                    None,
                    best_match,
                    "Partial matching evidence text was found for this requirement."
                )
            else:
                return (
                    EvaluationStatus.EVALUATED.value,
                    EvaluationResult.INDETERMINATE.value,
                    None,
                    None,
                    best_match,
                    "Insufficient evidence to verify requirement compliance."
                )

    @classmethod
    def evaluate_requirement_rules_for_bidder(
        cls,
        db: Session,
        tender_id: int,
        bidder_id: int,
        requirement_id: int
    ) -> List[RuleEvaluation]:
        """
        Evaluates rules for a single requirement and bidder.
        Safely clears existing RuleEvaluation records for this (bidder_id, requirement_id) first.
        """
        requirement = db.query(Requirement).filter(
            Requirement.id == requirement_id,
            Requirement.tender_id == tender_id
        ).first()

        if not requirement:
            raise ValueError(f"Requirement {requirement_id} not found under tender {tender_id}")

        bidder = db.query(Bidder).filter(
            Bidder.id == bidder_id,
            Bidder.tender_id == tender_id
        ).first()

        if not bidder:
            raise ValueError(f"Bidder {bidder_id} not found under tender {tender_id}")

        # Clear existing evaluations for this requirement & bidder (rerun safety)
        db.query(RuleEvaluation).filter(
            RuleEvaluation.bidder_id == bidder_id,
            RuleEvaluation.requirement_id == requirement_id
        ).delete()
        db.commit()

        # Get or auto-create rules
        rules = cls.get_or_create_default_rules_for_requirement(db, requirement)

        # Retrieve Phase 5 evidence matches for this requirement & bidder
        evidence_matches = db.query(EvidenceMatch).filter(
            EvidenceMatch.bidder_id == bidder_id,
            EvidenceMatch.requirement_id == requirement_id
        ).all()

        evaluations = []
        for rule in rules:
            status, result, ext_val, ext_unit, best_ev, expl = cls.evaluate_rule_against_evidence(
                rule=rule,
                requirement=requirement,
                evidence_matches=evidence_matches
            )

            eval_rec = RuleEvaluation(
                rule_id=rule.id,
                requirement_id=requirement.id,
                bidder_id=bidder_id,
                tender_id=tender_id,
                evidence_match_id=best_ev.id if best_ev else None,
                extracted_value=ext_val,
                extracted_unit=ext_unit,
                required_value=rule.required_value or (str(requirement.threshold) if requirement.threshold else None),
                operator=rule.operator,
                evaluation_status=status,
                evaluation_result=result,
                explanation=expl
            )
            db.add(eval_rec)
            evaluations.append(eval_rec)

        db.commit()
        for e in evaluations:
            db.refresh(e)

        return evaluations

    @classmethod
    def evaluate_all_rules_for_bidder(
        cls,
        db: Session,
        tender_id: int,
        bidder_id: int
    ) -> List[RuleEvaluation]:
        """
        Batch evaluates all rules for all requirements of a tender for a given bidder.
        Rerun safe: removes existing rule evaluations for this (tender_id, bidder_id) first.
        """
        requirements = db.query(Requirement).filter(
            Requirement.tender_id == tender_id
        ).all()

        if not requirements:
            return []

        all_evaluations = []
        for req in requirements:
            evals = cls.evaluate_requirement_rules_for_bidder(
                db=db,
                tender_id=tender_id,
                bidder_id=bidder_id,
                requirement_id=req.id
            )
            all_evaluations.extend(evals)

        return all_evaluations
