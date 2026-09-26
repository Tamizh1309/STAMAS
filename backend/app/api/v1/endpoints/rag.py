from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.tender import Tender
from app.models.bidder import Bidder
from app.models.bidder_document import BidderDocument
from app.models.requirement import Requirement
from app.models.evidence_match import EvidenceMatch
from app.models.rule_evaluation import RuleEvaluation
from app.models.rag import RAGQueryLog
from app.schemas.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RequirementRAGAnalysisRequest,
    RequirementRAGAnalysisResponse,
    DocumentIndexResponse,
    SourceCitation,
)
from app.services.rag import (
    index_document,
    index_all_bidder_documents,
    retrieve_chunks,
    generate_grounded_response,
)

router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse)
def run_rag_query(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Performs grounded RAG document Q&A for a bidder in a tender.
    Scoped strictly to (tender_id, bidder_id).
    """
    tender = db.query(Tender).filter(Tender.id == request.tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    bidder = db.query(Bidder).filter(Bidder.id == request.bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    # Optional requirement text context
    req_text = None
    if request.requirement_id:
        req = db.query(Requirement).filter(Requirement.id == request.requirement_id).first()
        if req:
            req_text = req.requirement_text

    # Retrieve chunks
    chunks = retrieve_chunks(
        db=db,
        tender_id=request.tender_id,
        bidder_id=request.bidder_id,
        query=request.query,
        requirement_id=request.requirement_id,
        document_id=request.document_id,
        top_k=request.top_k or 5,
        method=request.retrieval_method or "HYBRID"
    )

    # Generate response
    rag_result = generate_grounded_response(
        query=request.query,
        retrieved_chunks=chunks,
        requirement_text=req_text
    )

    # Log query
    log = RAGQueryLog(
        tender_id=request.tender_id,
        bidder_id=request.bidder_id,
        requirement_id=request.requirement_id,
        query=request.query,
        response_status=rag_result["status"],
        answer=rag_result["answer"],
        cited_sources_json=rag_result["sources"]
    )
    db.add(log)
    db.commit()

    citations = [SourceCitation(**s) for s in rag_result["sources"]]
    avg_score = round(sum(s.score or 0 for s in citations) / len(citations), 4) if citations else 0.0

    return RAGQueryResponse(
        status=rag_result["status"],
        answer=rag_result["answer"],
        sources=citations,
        missing_information=rag_result.get("missing_information", []),
        conflicts=rag_result.get("conflicts", []),
        retrieval_score=avg_score,
        ai_provider_used=rag_result.get("ai_provider_used", "NONE"),
        retrieval_method_used=request.retrieval_method or "HYBRID"
    )


@router.post("/requirements/{requirement_id}/analyze", response_model=RequirementRAGAnalysisResponse)
def analyze_requirement_with_rag(
    requirement_id: int,
    request: RequirementRAGAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Performs AI grounded analysis for a specific tender requirement and bidder context.
    Integrates retrieved evidence, Phase 5 matches, and Phase 6 rule evaluations.
    """
    req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    bidder = db.query(Bidder).filter(Bidder.id == request.bidder_id).first()
    if not bidder:
        raise HTTPException(status_code=404, detail="Bidder not found")

    # Fetch Phase 5 evidence matches
    evidence_matches = db.query(EvidenceMatch).filter(
        EvidenceMatch.requirement_id == requirement_id,
        EvidenceMatch.bidder_id == request.bidder_id
    ).all()

    evidence_found = []
    for m in evidence_matches:
        evidence_found.append({
            "match_id": m.id,
            "document_id": m.document_id,
            "document_name": m.bidder_document.original_filename if m.bidder_document else "Doc",
            "page_number": m.page_number,
            "evidence_text": m.evidence_text,
            "confidence_score": m.confidence_score,
            "match_status": m.match_status.value if hasattr(m.match_status, 'value') else str(m.match_status)
        })

    # Fetch Phase 6 compliance rule evaluation
    rule_eval = db.query(RuleEvaluation).filter(
        RuleEvaluation.requirement_id == requirement_id,
        RuleEvaluation.bidder_id == request.bidder_id
    ).first()

    rule_eval_dict = None
    if rule_eval:
        rule_eval_dict = {
            "evaluation_id": rule_eval.id,
            "rule_code": rule_eval.rule.rule_code if rule_eval.rule else "N/A",
            "result": rule_eval.evaluation_result.value if hasattr(rule_eval.evaluation_result, 'value') else str(rule_eval.evaluation_result),
            "detected_value": rule_eval.detected_value,
            "explanation": rule_eval.explanation
        }

    # Retrieve chunks using requirement text as query
    chunks = retrieve_chunks(
        db=db,
        tender_id=req.tender_id,
        bidder_id=request.bidder_id,
        query=req.requirement_text,
        requirement_id=requirement_id,
        top_k=request.top_k or 5,
        method="HYBRID"
    )

    rag_result = generate_grounded_response(
        query=f"Explain how the retrieved bidder evidence supports or fails the requirement: '{req.requirement_text}'",
        retrieved_chunks=chunks,
        requirement_text=req.requirement_text,
        rule_evaluation=rule_eval_dict
    )

    citations = [SourceCitation(**s) for s in rag_result["sources"]]

    return RequirementRAGAnalysisResponse(
        requirement_id=req.id,
        requirement_text=req.requirement_text,
        bidder_id=bidder.id,
        bidder_name=bidder.company_name,
        status=rag_result["status"],
        answer=rag_result["answer"],
        evidence_found=evidence_found,
        rule_evaluation=rule_eval_dict,
        sources=citations,
        ai_provider_used=rag_result.get("ai_provider_used", "NONE"),
        retrieval_method_used="HYBRID"
    )


@router.post("/documents/{document_id}/index", response_model=DocumentIndexResponse)
def index_document_endpoint(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Triggers indexing or re-indexing of a BidderDocument into RAG chunks.
    """
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Bidder document not found")

    count = index_document(db, document_id)
    return DocumentIndexResponse(
        document_id=document_id,
        chunks_created=count,
        status="INDEXED",
        message=f"Successfully indexed document '{doc.original_filename}' into {count} chunks."
    )


@router.post("/bidders/{bidder_id}/query", response_model=RAGQueryResponse)
def bidder_qa_query(
    bidder_id: int,
    tender_id: int,
    query: str,
    top_k: int = 5,
    retrieval_method: str = "HYBRID",
    db: Session = Depends(get_db)
):
    """
    Convenience endpoint for Bidder Document Q&A.
    """
    req = RAGQueryRequest(
        tender_id=tender_id,
        bidder_id=bidder_id,
        query=query,
        top_k=top_k,
        retrieval_method=retrieval_method
    )
    return run_rag_query(request=req, db=db)


@router.post("/documents/{document_id}/query", response_model=RAGQueryResponse)
def document_qa_query(
    document_id: int,
    query: str,
    top_k: int = 5,
    retrieval_method: str = "HYBRID",
    db: Session = Depends(get_db)
):
    """
    Convenience endpoint for Document-specific Q&A.
    """
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Bidder document not found")

    req = RAGQueryRequest(
        tender_id=doc.tender_id,
        bidder_id=doc.bidder_id,
        document_id=document_id,
        query=query,
        top_k=top_k,
        retrieval_method=retrieval_method
    )
    return run_rag_query(request=req, db=db)
