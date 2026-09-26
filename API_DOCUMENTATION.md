# STAMAS — API Endpoint Documentation Reference

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## API Overview

STAMAS backend is built with FastAPI and exposes RESTful JSON endpoints under `/api/v1`.

Interactive OpenAPI Swagger UI is available at `http://localhost:8000/docs`.

---

## Core Endpoint Reference

### 1. Health & Readiness Probes
- `GET /api/v1/health`: Returns system health, database connection, PyMuPDF engine, and version status.
- `GET /api/v1/health/ready`: Readiness probe checking database connectivity and storage directory writeability.

### 2. Tender Management
- `POST /api/v1/tenders/`: Upload and register a new Tender PDF.
- `GET /api/v1/tenders/`: List tenders with status filtering and search.
- `GET /api/v1/tenders/{id}`: Retrieve detailed tender metadata and extracted pages.
- `POST /api/v1/tenders/{id}/process`: Process tender PDF into pages and extract requirements.

### 3. Requirement Intelligence
- `GET /api/v1/requirements/tender/{tender_id}`: List extracted requirements for a tender.
- `POST /api/v1/requirements/tender/{tender_id}/extract`: Trigger AI/heuristic requirement extraction.
- `PATCH /api/v1/requirements/{id}`: Update or confirm requirement details.

### 4. Bidder & Qualification Dossier Management
- `POST /api/v1/bidders/`: Register a new bidder for a tender.
- `GET /api/v1/bidders/tender/{tender_id}`: List bidders for a specific tender.
- `POST /api/v1/bidders/{bidder_id}/documents`: Upload bidder qualification documents.
- `POST /api/v1/bidders/{bidder_id}/documents/{doc_id}/process`: Process bidder document into page text.

### 5. Evidence Retrieval & Matching
- `POST /api/v1/evidence/match`: Match bidder document evidence against tender requirements.
- `GET /api/v1/evidence/bidder/{bidder_id}`: Retrieve evidence matches for a bidder.

### 6. Compliance Rule Engine
- `POST /api/v1/compliance/rules/evaluate`: Evaluate deterministic rules for a bidder.
- `GET /api/v1/bidders/{bidder_id}/rule-evaluations`: List rule evaluation results.

### 7. AI + RAG Intelligence
- `POST /api/v1/rag/query`: Execute grounded RAG query over document context with citations.
- `POST /api/v1/rag/analyze-requirement`: Generate grounded AI explanation for a requirement.

### 8. Compliance Decision Engine
- `POST /api/v1/compliance/evaluate-bidder`: Generate overall System Decision (`PASS` / `FAIL` / `REVIEW`).
- `GET /api/v1/compliance/bidders/{bidder_id}/summary`: Retrieve compliance decision summary.

### 9. Officer Review & Human Decision Management
- `POST /api/v1/compliance/bidders/{bidder_id}/requirements/{req_id}/confirm`: Officer confirms system decision.
- `POST /api/v1/compliance/bidders/{bidder_id}/requirements/{req_id}/override`: Officer applies manual override with justification.
- `POST /api/v1/compliance/bidders/{bidder_id}/finalize`: Finalize bidder compliance review.

### 10. Reports & Audit Subsystem
- `GET /api/v1/reports/tenders/{tender_id}`: Retrieve Tender Compliance Summary Report.
- `GET /api/v1/reports/tenders/{tender_id}/pdf`: Download Tender Compliance Report PDF.
- `GET /api/v1/reports/tenders/{tender_id}/csv`: Download Tender Compliance Data CSV.
- `GET /api/v1/reports/bidders/{bidder_id}`: Retrieve Bidder Compliance Summary Report.
- `GET /api/v1/reports/bidders/{bidder_id}/pdf`: Download Bidder Compliance Report PDF.
- `GET /api/v1/reports/bidders/{bidder_id}/csv`: Download Bidder Compliance Data CSV.
- `GET /api/v1/audit/`: Query officer action audit events with pagination and filtering.

### 11. Testing & Benchmarking Evaluation
- `GET /api/v1/benchmark/run`: Execute Ground Truth benchmark suite and return live metrics.
- `GET /api/v1/benchmark/report`: Get latest benchmark evaluation report.
