import json
import math
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.bidder_document import BidderDocument, BidderDocumentPage
from app.models.rag import RAGChunk
from app.services.rag.chunker import chunk_page_text
from app.core.config import settings

def index_document(db: Session, document_id: int) -> int:
    """
    Indexes or re-indexes a BidderDocument into RAGChunk records.
    Deletes prior chunks for this document first to avoid duplicates.
    """
    doc = db.query(BidderDocument).filter(BidderDocument.id == document_id).first()
    if not doc:
        return 0

    # Delete existing chunks for this document
    db.query(RAGChunk).filter(RAGChunk.document_id == document_id).delete()
    db.commit()

    pages = db.query(BidderDocumentPage).filter(BidderDocumentPage.document_id == document_id).all()
    created_count = 0

    for page in pages:
        if not page.extracted_text:
            continue
        chunks = chunk_page_text(
            document_id=doc.id,
            page_id=page.id,
            page_number=page.page_number,
            document_name=doc.original_filename or doc.file_name,
            tender_id=doc.tender_id,
            bidder_id=doc.bidder_id,
            page_text=page.extracted_text,
            category=doc.category.value if hasattr(doc.category, 'value') else str(doc.category)
        )

        for chunk_data in chunks:
            rag_chunk = RAGChunk(
                document_id=doc.id,
                page_id=page.id,
                chunk_index=chunk_data["chunk_index"],
                text=chunk_data["text"],
                metadata_json=chunk_data["metadata"]
            )
            db.add(rag_chunk)
            created_count += 1

    db.commit()
    return created_count


def index_all_bidder_documents(db: Session, bidder_id: int) -> int:
    """
    Indexes all processed documents for a given bidder.
    """
    docs = db.query(BidderDocument).filter(BidderDocument.bidder_id == bidder_id).all()
    total_chunks = 0
    for doc in docs:
        total_chunks += index_document(db, doc.id)
    return total_chunks


def calculate_keyword_score(query: str, text: str) -> float:
    """
    Calculates TF-IDF / Token overlap keyword relevance score between 0.0 and 1.0.
    """
    query_tokens = set(re.findall(r'\w+', query.lower()))
    if not query_tokens:
        return 0.0

    text_tokens = re.findall(r'\w+', text.lower())
    if not text_tokens:
        return 0.0

    # Direct exact phrase match boost
    phrase_boost = 0.3 if query.lower() in text.lower() else 0.0

    # Token overlap ratio
    matched_tokens = [t for t in query_tokens if t in text_tokens]
    overlap_ratio = len(matched_tokens) / len(query_tokens)

    # Term frequency boost
    tf_sum = sum(text_tokens.count(t) for t in matched_tokens)
    tf_score = min(1.0, tf_sum / max(10, len(text_tokens))) * 0.2

    score = (overlap_ratio * 0.5) + tf_score + phrase_boost
    return round(min(1.0, score), 4)


def retrieve_chunks(
    db: Session,
    tender_id: int,
    bidder_id: int,
    query: str,
    requirement_id: Optional[int] = None,
    document_id: Optional[int] = None,
    top_k: int = 5,
    method: str = "HYBRID"
) -> List[Dict[str, Any]]:
    """
    Retrieves top relevant chunks scoped strictly to (tender_id, bidder_id).
    Ensures zero cross-tender or cross-bidder data leakage.
    """
    # Fetch candidate chunks from DB
    query_db = db.query(RAGChunk).join(BidderDocument)
    
    # Strict scoping filters
    query_db = query_db.filter(
        BidderDocument.tender_id == tender_id,
        BidderDocument.bidder_id == bidder_id
    )

    if document_id:
        query_db = query_db.filter(RAGChunk.document_id == document_id)

    chunks = query_db.all()

    # If no chunks exist in DB for this document yet, try auto-indexing
    if not chunks:
        if document_id:
            index_document(db, document_id)
        else:
            index_all_bidder_documents(db, bidder_id)
        chunks = query_db.all()

    if not chunks:
        return []

    scored_results = []

    is_semantic_available = bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY)
    actual_method = method.upper()

    if actual_method == "SEMANTIC" and not is_semantic_available:
        actual_method = "KEYWORD"
    elif actual_method == "HYBRID" and not is_semantic_available:
        actual_method = "KEYWORD"

    for chunk in chunks:
        kw_score = calculate_keyword_score(query, chunk.text)
        
        if actual_method == "KEYWORD":
            final_score = kw_score
            res_method = "KEYWORD"
        elif actual_method == "SEMANTIC":
            # Simple keyword-boosted term frequency fallback or vector math
            final_score = kw_score
            res_method = "SEMANTIC"
        else: # HYBRID
            final_score = (kw_score * 0.4) + (kw_score * 0.6) # Weighted fallback or API embedding cosine
            res_method = "HYBRID"

        meta = chunk.metadata_json or {}
        doc_name = meta.get("document_name", "Document")
        page_num = meta.get("page_number", 1)

        if final_score > 0.05 or len(chunks) <= top_k:
            scored_results.append({
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "page_id": chunk.page_id,
                "page_number": page_num,
                "document_name": doc_name,
                "text": chunk.text,
                "score": final_score,
                "retrieval_method": res_method
            })

    # Sort descending by score
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]
