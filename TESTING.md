# STAMAS — Testing, Benchmarking & Accuracy Evaluation Framework

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## 1. Testing Framework Architecture

The STAMAS testing suite implements a 5-layer testing pyramid with 55 automated pytest tests:

```text
                  E2E Pipeline Test Suite (1 Test)
                                 ▲
               Security & Isolation Suite (3 Tests)
                                 ▲
              Performance Benchmark Suite (2 Tests)
                                 ▲
           Unit & Integration Test Suites (49 Tests)
```

---

## 2. Test Suites Reference

| Test Module | Path | Purpose |
| :--- | :--- | :--- |
| **Compliance Rules** | [`test_compliance_rules.py`](backend/tests/test_compliance_rules.py) | Unit tests for numeric min/max/range, date, certification rules. |
| **Decision Engine** | [`test_decision_engine.py`](backend/tests/test_decision_engine.py) | PASS/FAIL/REVIEW decision state matrix verification. |
| **Evidence Matching** | [`test_evidence_matching.py`](backend/tests/test_evidence_matching.py) | Keyword, semantic, and hybrid evidence retrieval matching. |
| **Health Probes** | [`test_health.py`](backend/tests/test_health.py) | Liveness and readiness endpoints. |
| **Officer Review** | [`test_officer_review.py`](backend/tests/test_officer_review.py) | Decision confirmation, manual override, finalization, audit. |
| **PDF Extraction** | [`test_pdf_extraction.py`](backend/tests/test_pdf_extraction.py) | Document text parsing, page extraction, OCR fallback. |
| **Performance Benchmark** | [`test_performance_benchmark.py`](backend/tests/test_performance_benchmark.py) | Live evaluator execution and PDF rendering latency checks. |
| **AI + RAG Intelligence** | [`test_rag_intelligence.py`](backend/tests/test_rag_intelligence.py) | Chunking, vector retrieval, grounded answers, fallback mode. |
| **Reports & Audit** | [`test_reports_audit.py`](backend/tests/test_reports_audit.py) | Report data aggregation, PDF/CSV rendering, audit history. |
| **Requirements** | [`test_requirements.py`](backend/tests/test_requirements.py) | Requirement extraction, threshold detection, mandatory flags. |
| **Security & Isolation** | [`test_security_isolation.py`](backend/tests/test_security_isolation.py) | Cross-tender data isolation, path traversal, prompt injection. |
| **Tenders** | [`test_tenders.py`](backend/tests/test_tenders.py) | Tender CRUD operations and page processing. |
| **E2E Pipeline** | [`test_e2e_pipeline.py`](backend/tests/test_e2e_pipeline.py) | Multi-phase end-to-end integration pipeline verification. |

---

## 3. How to Run Test Commands

```bash
# Execute entire pytest test suite (55 tests)
cd backend
.\venv\Scripts\python -m pytest

# Run specific test modules
.\venv\Scripts\python -m pytest tests/test_security_isolation.py
.\venv\Scripts\python -m pytest tests/test_e2e_pipeline.py

# Run Phase 13 Acceptance Test
.\venv\Scripts\python scratch/test_phase13_acceptance.py
```
