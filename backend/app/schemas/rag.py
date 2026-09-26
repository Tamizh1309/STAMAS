from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class SourceCitation(BaseModel):
    source_id: str = Field(..., description="Unique source identifier like SOURCE-1")
    document_id: int
    document_name: str
    page_id: int
    page_number: int
    chunk_id: Optional[int] = None
    text_snippet: str
    score: Optional[float] = None
    retrieval_method: Optional[str] = None


class RAGQueryRequest(BaseModel):
    tender_id: int
    bidder_id: int
    query: str
    requirement_id: Optional[int] = None
    document_id: Optional[int] = None
    top_k: Optional[int] = 5
    retrieval_method: Optional[str] = "HYBRID" # KEYWORD, SEMANTIC, HYBRID


class RAGQueryResponse(BaseModel):
    status: str # GROUNDED, PARTIAL, INSUFFICIENT_CONTEXT, CONFLICTING_SOURCES, AI_UNAVAILABLE, ERROR
    answer: str
    sources: List[SourceCitation] = []
    missing_information: List[str] = []
    conflicts: List[str] = []
    retrieval_score: Optional[float] = None
    ai_provider_used: str = "NONE"
    retrieval_method_used: str = "KEYWORD"


class RequirementRAGAnalysisRequest(BaseModel):
    bidder_id: int
    top_k: Optional[int] = 5


class RequirementRAGAnalysisResponse(BaseModel):
    requirement_id: int
    requirement_text: str
    bidder_id: int
    bidder_name: str
    status: str # GROUNDED, PARTIAL, INSUFFICIENT_CONTEXT, CONFLICTING_SOURCES, AI_UNAVAILABLE, ERROR
    answer: str
    evidence_found: List[Dict[str, Any]] = []
    rule_evaluation: Optional[Dict[str, Any]] = None
    sources: List[SourceCitation] = []
    ai_provider_used: str = "NONE"
    retrieval_method_used: str = "KEYWORD"


class DocumentIndexResponse(BaseModel):
    document_id: int
    chunks_created: int
    status: str
    message: str
