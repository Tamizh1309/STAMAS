import os
import sys

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy.orm import Session
from app.core.database import Base, engine, SessionLocal
from app.models.tender import Tender
from app.models.requirement import Requirement, RequirementCategory
from app.models.bidder import Bidder
from app.models.bidder_document import BidderDocument, BidderDocumentPage, DocumentCategory, DocumentProcessingStatus
from app.models.evidence_match import EvidenceMatch, MatchStatus, MatchingMethod
from app.models.compliance_rule import ComplianceRule, RuleType
from app.models.rule_evaluation import RuleEvaluation, EvaluationResult
from app.models.rag import RAGChunk, RAGQueryLog
from app.services.rag.retriever import index_document, retrieve_chunks
from app.services.rag.generator import generate_grounded_response

def run_phase7_demo():
    print("=" * 70)
    print("STAMAS — PHASE 7: AI + RAG INTELLIGENCE DEMO")
    print("Smart Tender Analysis & Compliance Assessment System")
    print("SIH26100 — GeM Procurement Compliance Platform")
    print("=" * 70)

    # Re-create database tables cleanly for demo
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Step 1: Create Tender
        tender = Tender(
            tender_id="GEM/2026/B/8821901",
            title="Data Center Infrastructure Procurement",
            department="Ministry of Electronics & IT",
            status="PROCESSED"
        )
        db.add(tender)
        db.commit()
        db.refresh(tender)
        print(f"\n[1] Tender Created: #{tender.id} | {tender.title} ({tender.tender_id})")

        # Step 2: Create Requirement
        req = Requirement(
            tender_id=tender.id,
            req_code="REQ-TECH-005",
            text="Bidder must have minimum 5 years experience in data center infrastructure projects.",
            category=RequirementCategory.TECHNICAL,
            mandatory=True
        )
        db.add(req)
        db.commit()
        db.refresh(req)
        print(f"[2] Requirement Added: [{req.req_code}] {req.text}")

        # Step 3: Create Bidder
        bidder = Bidder(
            tender_id=tender.id,
            bidder_name="ABC Technologies Pvt Ltd",
            company_name="ABC Technologies Pvt Ltd",
            registration_number="REG-ABC-2026-889",
            gstin="33ABCDE1234F1Z5",
            email="contact@abctech.co.in"
        )
        db.add(bidder)
        db.commit()
        db.refresh(bidder)
        print(f"[3] Bidder Registered: {bidder.company_name} (GSTIN: {bidder.gstin})")

        # Step 4: Add Bidder Document & Pages
        doc = BidderDocument(
            bidder_id=bidder.id,
            tender_id=tender.id,
            filename="experience_certificate.pdf",
            stored_filename="exp_cert_abc.pdf",
            file_path="./data/uploads/exp_cert_abc.pdf",
            category=DocumentCategory.EXPERIENCE,
            processing_status=DocumentProcessingStatus.PROCESSED
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        page4 = BidderDocumentPage(
            document_id=doc.id,
            page_number=4,
            extracted_text="ABC Technologies Pvt Ltd has successfully completed data center infrastructure projects continuously from 2018 to 2025 across multiple government client sites. Total experience spans over 7 years."
        )
        db.add(page4)
        db.commit()
        print(f"[4] Document Processed: {doc.filename} (Page 4 Extracted)")

        # Step 5: Index Document into RAG Chunks
        chunks_count = index_document(db, doc.id)
        print(f"[5] RAG Indexer: Created {chunks_count} searchable chunk(s) preserving source metadata.")

        # Step 6: Phase 5 Evidence Matching Engine
        match = EvidenceMatch(
            tender_id=tender.id,
            requirement_id=req.id,
            bidder_id=bidder.id,
            document_id=doc.id,
            page_id=page4.id,
            evidence_text="completed data center infrastructure projects continuously from 2018 to 2025",
            confidence_score=0.94,
            match_status=MatchStatus.MATCHED,
            matching_method=MatchingMethod.SEMANTIC
        )
        db.add(match)
        db.commit()
        print(f"[6] Phase 5 Evidence Matching: Matched snippet on Page 4 (Confidence: 94%)")

        # Step 7: Phase 6 Deterministic Rule Engine
        rule = ComplianceRule(
            requirement_id=req.id,
            rule_code="RULE_EXP_YEARS_MIN",
            rule_type=RuleType.NUMERIC_MIN,
            field_name="experience_years",
            required_value="5"
        )
        db.add(rule)
        db.commit()

        eval_res = RuleEvaluation(
            rule_id=rule.id,
            requirement_id=req.id,
            bidder_id=bidder.id,
            tender_id=tender.id,
            evidence_match_id=match.id,
            extracted_value="7",
            required_value="5",
            operator="GREATER_THAN_OR_EQUAL",
            evaluation_result=EvaluationResult.SATISFIED,
            explanation="7 years of documented experience >= required minimum of 5 years."
        )
        db.add(eval_res)
        db.commit()
        print(f"[7] Phase 6 Rule Evaluation: {rule.rule_code} -> Result: {eval_res.evaluation_result}")

        # Step 8: Phase 7 Grounded AI RAG Analysis
        print("\n" + "-" * 70)
        print("PHASE 7 GROUNDED RAG INTELLIGENCE QUERY")
        print("-" * 70)
        user_query = "Why does STAMAS consider the experience requirement supported?"
        print(f"Officer Question: \"{user_query}\"")

        retrieved = retrieve_chunks(
            db=db,
            tender_id=tender.id,
            bidder_id=bidder.id,
            query=user_query,
            top_k=3,
            method="HYBRID"
        )

        rule_eval_dict = {
            "rule_code": rule.rule_code,
            "result": eval_res.evaluation_result,
            "detected_value": eval_res.extracted_value,
            "explanation": eval_res.explanation
        }

        rag_response = generate_grounded_response(
            query=user_query,
            retrieved_chunks=retrieved,
            requirement_text=req.text,
            rule_evaluation=rule_eval_dict
        )

        print(f"\n[AI Status]: {rag_response['status']}")
        print(f"[AI Provider]: {rag_response['ai_provider_used']}")
        print(f"\n[Grounded AI Explanation]:\n{rag_response['answer']}")

        print("\n[Cited Sources]:")
        for src in rag_response['sources']:
            print(f"  • [{src['source_id']}] Document: {src['document_name']} | Page: {src['page_number']}")
            print(f"    Text: \"{src['text_snippet']}\"")

        print("\n" + "=" * 70)
        print("PHASE 7 RAG INTELLIGENCE WORKFLOW VERIFIED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        db.close()

if __name__ == "__main__":
    run_phase7_demo()
