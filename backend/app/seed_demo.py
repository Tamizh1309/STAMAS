import os
import sys
import datetime
from sqlalchemy.orm import Session

# Ensure module path resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal, engine, Base
from app.models.tender import Tender
from app.models.requirement import Requirement
from app.models.bidder import Bidder
from app.models.bidder_document import BidderDocument, BidderDocumentPage
from app.models.evidence_match import EvidenceMatch
from app.models.compliance_rule import ComplianceRule
from app.models.rule_evaluation import RuleEvaluation
from app.services.compliance.decision_engine import evaluate_bidder_compliance_decisions
from app.services.compliance.officer_review import confirm_requirement_decision, override_requirement_decision, finalize_bidder_review

def seed_demo_dataset():
    """
    Populates the database with an official SIH26100 GeM Procurement Bid Compliance Verification demonstration scenario.
    """
    print("=" * 70)
    print("STAMAS DEMO SEEDER — SIH26100 GeM Procurement Platform")
    print("=" * 70)

    # Initialize tables
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if demo tender already exists
        existing_tender = db.query(Tender).filter(Tender.tender_id == "TND-SIH2026-GEM01").first()
        if existing_tender:
            print("[!] Demo tender 'TND-SIH2026-GEM01' already exists in database. Skipping duplicate creation.")
            return existing_tender.id

        print("[+] Creating SIH Demonstration Tender: TND-SIH2026-GEM01...")
        tender = Tender(
            tender_id="TND-SIH2026-GEM01",
            title="Procurement of Enterprise Cloud Compute & AI Storage Cluster",
            department="Ministry of Electronics and Information Technology (MeitY)",
            issue_date=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=15),
            closing_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=15),
            status="PROCESSED",
            page_count=18,
            file_name="GeM_Cloud_Compute_RFP_2026.pdf"
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)

        print("[+] Seeding Tender Compliance Requirements...")
        reqs = [
            Requirement(
                tender_id=tender.id, req_code="REQ-FIN-01", category="FINANCIAL",
                text="Bidder must have a minimum average annual financial turnover of ₹10 Crore in the last 3 financial years.",
                mandatory=True, threshold=10.0, unit="Cr", currency="INR", constraint_type="MINIMUM", source_page=4, confidence=0.98
            ),
            Requirement(
                tender_id=tender.id, req_code="REQ-TECH-02", category="TECHNICAL",
                text="Bidder must possess at least 5 years of experience in deploying Government Cloud Data Center Infrastructure.",
                mandatory=True, threshold=5.0, unit="Years", constraint_type="MINIMUM", source_page=6, confidence=0.95
            ),
            Requirement(
                tender_id=tender.id, req_code="REQ-CERT-03", category="COMPLIANCE",
                text="Bidder must possess a valid ISO 9001:2015 Quality Management System Certificate.",
                mandatory=True, constraint_type="CERTIFICATION", source_page=9, confidence=0.92
            ),
            Requirement(
                tender_id=tender.id, req_code="REQ-LOC-04", category="ELIGIBILITY",
                text="Local Content percentage under Make in India policy must be equal to or greater than 50%.",
                mandatory=True, threshold=50.0, unit="Percent", constraint_type="MINIMUM", source_page=12, confidence=0.96
            ),
            Requirement(
                tender_id=tender.id, req_code="REQ-DOC-05", category="DOCUMENT",
                text="Submission of Manufacturer Authorization Form (MAF) from OEM.",
                mandatory=False, constraint_type="DOCUMENT_REQUIRED", source_page=14, confidence=0.90
            )
        ]
        db.add_all(reqs)
        db.commit()
        for r in reqs:
            db.refresh(r)

        print("[+] Creating Demonstration Bidder: Param Tech Systems India Pvt Ltd...")
        bidder = Bidder(
            tender_id=tender.id,
            bidder_id="BIDDER-PARAM-99",
            bidder_name="Param Tech Systems India Pvt Ltd",
            company_name="Param Tech Systems India Pvt Ltd",
            registration_number="REG-MH-2018-9921",
            gstin="27AAACP9981K1Z5",
            contact_person="Rajesh Sharma",
            email="contact@paramtechsystems.in",
            phone="+91-9876543210",
            status="UNDER_REVIEW"
        )
        db.add(bidder)
        db.commit()
        db.refresh(bidder)

        print("[+] Uploading Bidder Qualification Dossier Documents...")
        doc1 = BidderDocument(
            bidder_id=bidder.id, tender_id=tender.id, filename="financial_audited_turnover.pdf",
            stored_filename="doc_fin_audited.pdf", category="FINANCIAL", page_count=12,
            processing_status="PROCESSED", extraction_status="TEXT_LAYER", file_path="/storage/uploads/doc_fin_audited.pdf"
        )
        doc2 = BidderDocument(
            bidder_id=bidder.id, tender_id=tender.id, filename="iso_quality_credentials.pdf",
            stored_filename="doc_iso_cert.pdf", category="COMPLIANCE", page_count=5,
            processing_status="PROCESSED", extraction_status="TEXT_LAYER", file_path="/storage/uploads/doc_iso_cert.pdf"
        )
        db.add_all([doc1, doc2])
        db.commit()
        db.refresh(doc1)
        db.refresh(doc2)

        page1 = BidderDocumentPage(
            document_id=doc1.id, page_number=5,
            extracted_text="Audited Financial Statement FY 2024-25: Average Annual Turnover for the preceding three financial years is ₹14.8 Crore INR. Local content declared at 65% under Class-I Local Supplier category."
        )
        page2 = BidderDocumentPage(
            document_id=doc2.id, page_number=2,
            extracted_text="Certification: ISO 9001:2015 Quality Management System valid until December 2027. Experience Certificate: 7 Years in NIC Cloud Services."
        )
        db.add_all([page1, page2])
        db.commit()
        db.refresh(page1)
        db.refresh(page2)

        print("[+] Seeding Evidence Matching Records...")
        evidences = [
            EvidenceMatch(
                tender_id=tender.id, bidder_id=bidder.id, requirement_id=reqs[0].id, document_id=doc1.id, page_id=page1.id,
                evidence_text="Average Annual Turnover for the preceding three financial years is ₹14.8 Crore INR.", match_status="MATCHED", confidence_score=0.96, matching_method="HYBRID"
            ),
            EvidenceMatch(
                tender_id=tender.id, bidder_id=bidder.id, requirement_id=reqs[1].id, document_id=doc2.id, page_id=page2.id,
                evidence_text="Experience Certificate: 7 Years in NIC Cloud Services.", match_status="MATCHED", confidence_score=0.94, matching_method="HYBRID"
            ),
            EvidenceMatch(
                tender_id=tender.id, bidder_id=bidder.id, requirement_id=reqs[2].id, document_id=doc2.id, page_id=page2.id,
                evidence_text="ISO 9001:2015 Quality Management System valid until December 2027.", match_status="MATCHED", confidence_score=0.92, matching_method="SEMANTIC"
            ),
            EvidenceMatch(
                tender_id=tender.id, bidder_id=bidder.id, requirement_id=reqs[3].id, document_id=doc1.id, page_id=page1.id,
                evidence_text="Local content declared at 65% under Class-I Local Supplier category.", match_status="MATCHED", confidence_score=0.95, matching_method="KEYWORD"
            ),
            EvidenceMatch(
                tender_id=tender.id, bidder_id=bidder.id, requirement_id=reqs[4].id, document_id=doc2.id, page_id=page2.id,
                evidence_text="Manufacturer Authorization Form reference cited without formal attachment signature.", match_status="LOW_CONFIDENCE", confidence_score=0.48, matching_method="KEYWORD"
            )
        ]
        db.add_all(evidences)
        db.commit()

        print("[+] Evaluating Compliance Rules...")
        c_rules = [
            ComplianceRule(requirement_id=reqs[0].id, rule_code="RULE-FIN-01", rule_type="NUMERIC_MIN", operator=">=", required_value="10.0"),
            ComplianceRule(requirement_id=reqs[1].id, rule_code="RULE-EXP-02", rule_type="NUMERIC_MIN", operator=">=", required_value="5.0"),
            ComplianceRule(requirement_id=reqs[2].id, rule_code="RULE-ISO-03", rule_type="CERTIFICATION_REQUIRED", operator="EQUALS", required_value="VALID"),
            ComplianceRule(requirement_id=reqs[3].id, rule_code="RULE-LOC-04", rule_type="NUMERIC_MIN", operator=">=", required_value="50.0"),
            ComplianceRule(requirement_id=reqs[4].id, rule_code="RULE-DOC-05", rule_type="DOCUMENT_REQUIRED", operator="EQUALS", required_value="ATTACHED")
        ]
        db.add_all(c_rules)
        db.commit()

        evals = [
            RuleEvaluation(rule_id=c_rules[0].id, requirement_id=reqs[0].id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=evidences[0].id, extracted_value="14.8 Cr", required_value="10.0 Cr", operator=">=", evaluation_status="EVALUATED", evaluation_result="SATISFIED", explanation="Extracted turnover 14.8 Cr exceeds minimum threshold 10.0 Cr."),
            RuleEvaluation(rule_id=c_rules[1].id, requirement_id=reqs[1].id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=evidences[1].id, extracted_value="7 Years", required_value="5.0 Years", operator=">=", evaluation_status="EVALUATED", evaluation_result="SATISFIED", explanation="Extracted experience 7 Years exceeds threshold 5 Years."),
            RuleEvaluation(rule_id=c_rules[2].id, requirement_id=reqs[2].id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=evidences[2].id, extracted_value="Valid ISO 9001:2015", required_value="VALID ISO", operator="EQUALS", evaluation_status="EVALUATED", evaluation_result="SATISFIED", explanation="Valid ISO 9001:2015 certificate confirmed."),
            RuleEvaluation(rule_id=c_rules[3].id, requirement_id=reqs[3].id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=evidences[3].id, extracted_value="65%", required_value="50%", operator=">=", evaluation_status="EVALUATED", evaluation_result="SATISFIED", explanation="Extracted local content 65% meets Class-I local supplier rule."),
            RuleEvaluation(rule_id=c_rules[4].id, requirement_id=reqs[4].id, bidder_id=bidder.id, tender_id=tender.id, evidence_match_id=evidences[4].id, extracted_value="Cited without signature", required_value="ATTACHED", operator="EQUALS", evaluation_status="EVALUATED", evaluation_result="INDETERMINATE", explanation="MAF cited in text but physical signature layer requires procurement officer verification.")
        ]
        db.add_all(evals)
        db.commit()

        print("[+] Running System Decision Engine (Phase 8)...")
        sys_decision = evaluate_bidder_compliance_decisions(db, tender.id, bidder.id)
        print(f"    -> Overall System Decision: {sys_decision.overall_decision}")

        print("[+] Simulating Procurement Officer Review (Phase 9)...")
        confirm_requirement_decision(db, tender.id, bidder.id, reqs[0].id, officer_comment="Turnover verified against audited balance sheet.")
        confirm_requirement_decision(db, tender.id, bidder.id, reqs[1].id, officer_comment=" NIC Cloud experience verified.")
        confirm_requirement_decision(db, tender.id, bidder.id, reqs[2].id, officer_comment="ISO certificate verified with accreditation board.")
        confirm_requirement_decision(db, tender.id, bidder.id, reqs[3].id, officer_comment="Class-I local supplier self-declaration verified.")
        override_requirement_decision(db, tender.id, bidder.id, reqs[4].id, final_decision="PASS", override_reason="Original MAF document uploaded on GeM Portal verified under Appendix 4.", officer_comment="Manual override approved by Procurement Committee.")

        print("[+] Finalizing Procurement Review & Audit Log...")
        final_summary = finalize_bidder_review(db, tender.id, bidder.id)
        print(f"    -> Final Overall Officer Decision: {final_summary['final_overall_decision']}")

        print("\n[SUCCESS] DEMO SEED DATA CREATED SUCCESSFULLY!")
        print(f"  - Tender ID: {tender.id} ({tender.tender_id})")
        print(f"  - Bidder ID: {bidder.id} ({bidder.company_name})")
        print(f"  - Final Decision: {final_summary['final_overall_decision']}")
        return tender.id

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error seeding demo dataset: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_demo_dataset()
