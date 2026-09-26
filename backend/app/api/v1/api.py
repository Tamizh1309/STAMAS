from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    tenders,
    requirements,
    bidders,
    bidder_documents,
    evidence_matches,
    compliance_rules,
    rag,
    compliance_decisions,
    officer_review,
    reports,
    benchmark,
)

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"],
)

api_router.include_router(
    tenders.router,
    prefix="/tenders",
    tags=["Tenders"],
)

api_router.include_router(
    requirements.router,
    tags=["Requirements"],
)

api_router.include_router(
    bidders.router,
)

api_router.include_router(
    bidder_documents.router,
)

api_router.include_router(
    evidence_matches.router,
)

api_router.include_router(
    compliance_rules.router,
)

api_router.include_router(
    rag.router,
    prefix="/rag",
    tags=["AI + RAG Intelligence"],
)

api_router.include_router(
    compliance_decisions.router,
    prefix="/compliance",
    tags=["Compliance Decision Engine"],
)

api_router.include_router(
    officer_review.router,
    prefix="/compliance",
    tags=["Officer Review & Human Decision Management"],
)

api_router.include_router(
    reports.router,
    tags=["Reports & Compliance Audit"],
)

api_router.include_router(
    benchmark.router,
    prefix="/benchmark",
    tags=["Testing & Benchmarking Evaluation"],
)