# STAMAS — Smart Tender Analysis & Management Assessment System

**AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement**  
**Problem Statement:** `SIH26100` — Government e-Marketplace (GeM) Procurement Intelligence Platform  

---

## Executive Overview

STAMAS is an end-to-end, AI-assisted compliance verification platform designed for GeM procurement officers. It automates tender requirement extraction, bidder document intelligence, evidence matching, deterministic rule evaluation, grounded RAG analysis, human-in-the-loop officer review, compliance reporting, and audit trail logging.

### Core Operating Principle
> **AI assists. Rules verify. Humans decide.**

### Live Production Deployment
- **Frontend Web UI (GitHub Pages):** [https://tamizh1309.github.io/STAMAS/](https://tamizh1309.github.io/STAMAS/)
- **Backend API Engine (FastAPI):** `https://twelve-badgers-punch.loca.lt/api/v1`
- **Swagger Interactive API Docs:** `https://twelve-badgers-punch.loca.lt/docs`
- **AI Intelligence Provider:** Groq Cloud LLM (`openai/gpt-oss-120b`) with server-side key management and deterministic fallbacks.

---

## Architecture Diagram

```
                 ┌───────────────────────────────────────┐
                 │       STAMAS Web UI Platform          │
                 │   React + Vite + TypeScript + Tailwind│
                 │   https://tamizh1309.github.io/STAMAS/│
                 └──────────────────┬────────────────────┘
                                    │ HTTPS / REST (VITE_API_BASE_URL)
                                    ▼
                 ┌───────────────────────────────────────┐
                 │       FastAPI Backend Engine          │
                 │      Python 3.11 + SQLAlchemy         │
                 │  https://twelve-badgers-punch.loca.lt │
                 └──────────┬─────────────────┬──────────┘
                            │                 │ Server-side API
                            ▼                 ▼
                 ┌──────────────────┐ ┌──────────────────┐
                 │ Document Parser  │ │ Groq Cloud LLM   │
                 │ PyMuPDF + Rules  │ │ openai/gpt-oss   │
                 └──────────────────┘ └──────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│ Requirement Extraction│ │  Document Processing  │ │   Evidence Matching   │
│   Category & Threshold│ │ PyMuPDF + Page Matrix │ │ Hybrid Semantic Match │
└───────────┬───────────┘ └───────────┬───────────┘ └───────────┬───────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │ Compliance Rule Engine  │
                         │ Numeric / Text / Date   │
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  System Decision Engine │
                         │   PASS / FAIL / REVIEW  │
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  Officer Workstation    │
                         │ Confirm / Override Audit│
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │ Reports & Audit Engine  │
                         │ PDF / CSV / JSON Audit  │
                         └─────────────────────────┘
```

---

## Complete System Feature Matrix

| Phase | Subsystem | Key Capabilities |
| :--- | :--- | :--- |
| **Phase 1** | Foundation | FastAPI backend, SQLite/PostgreSQL ORM, React UI, Health checks |
| **Phase 2** | Requirement Intelligence | Requirement identification, category detection, constraint parsing |
| **Phase 3** | Bidder Management | Bidder registration, document dossier tracking, status management |
| **Phase 4** | Document Intelligence | PyMuPDF text extraction, page numbering, OCR fallback layer |
| **Phase 5** | Evidence Matching | Keyword, semantic, and hybrid evidence retrieval with page traceability |
| **Phase 6** | Compliance Rule Engine | Deterministic numeric min/max/range, date, certification evaluation |
| **Phase 7** | AI + RAG Intelligence | Grounded RAG query generator, citation validator, AI fallback mode |
| **Phase 8** | System Decision Engine | Mandatory vs optional logic, PASS / FAIL / REVIEW decision matrix |
| **Phase 9** | Officer Review | Confirmation, manual override with justification, final review locking |
| **Phase 10** | Reports & Audit | Exportable PDF compliance reports, CSV structured data, audit logs |
| **Phase 11** | Benchmarking & Evaluation | Empirical Ground Truth benchmark suite, confusion matrix, latency stats |
| **Phase 12** | Deployment & Readiness | Production Docker containerization, 1-command startup, health probes |
| **Phase 13** | Integration & Hardening | Full end-to-end data flow validation, decision immutability integrity |
| **Phase 14** | Final System Validation | Master AC-01 to AC-18 validation, AI failure degradation mode |
| **Phase 15** | Submission Hardening | Repository audit, secret scan, local link cleanup, submission readiness |

---

## Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ or 20+

### 1-Command Startup (Windows)
```powershell
.\start.ps1
```

### Manual Local Startup

#### 1. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
source venv/bin/activate       # On Linux/macOS

pip install -r requirements.txt
python -m app.seed_demo        # Seed SIH demonstration data
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Access the application:
- **Frontend UI:** `http://localhost:3000`
- **Backend API Docs:** `http://localhost:8000/docs`
- **Health Check:** `http://localhost:8000/api/v1/health`
- **Readiness Probe:** `http://localhost:8000/api/v1/health/ready`

---

## Docker Containerized Setup

```bash
# Build and run containers
docker-compose up -d --build

# View logs
docker-compose logs -f
```

---

## SIH Demonstration Walkthrough (5-10 Minutes)

1. **Open Dashboard:** Navigate to `http://localhost:3000`.
2. **Select Tender:** Open demo tender `TND-SIH2026-GEM01` (*Procurement of Enterprise Cloud Compute*).
3. **View Requirements:** Inspect extracted financial turnover, experience, and ISO requirements.
4. **Open Bidder Dossier:** Select bidder `Param Tech Systems India Pvt Ltd`.
5. **Inspect Evidence:** View matched document snippets and exact page numbers.
6. **Review Rules:** Inspect deterministic rule evaluation outputs (`SATISFIED` vs `INDETERMINATE`).
7. **System Decision:** View overall system evaluation (`REVIEW`).
8. **Officer Review:** Confirm valid requirements and override ambiguous items with justification.
9. **Finalize Decision:** Lock final decision to `PASS`.
10. **Export Reports:** Download generated PDF / CSV compliance reports.
11. **Audit Trail:** Inspect complete timestamped audit event log.
12. **Evaluation Dashboard:** Switch to "Evaluation & Benchmarks" tab to view real-time accuracy metrics.

---

## Measured Benchmark Performance

Evaluated dynamically on ground truth dataset (`backend/benchmark/ground_truth.json`):
- **Requirement Extraction F1 Score:** `100.0%`
- **Evidence Top-1 Recall:** `80.0%` (Top-3 Recall: `100.0%`)
- **Decision Engine Accuracy:** `100.0%` (5/5 correct PASS/FAIL/REVIEW classifications)
- **Average Pipeline Latency:** `40.71 ms`
- **Automated Test Suite Pass Rate:** `55 / 55 Passed (100%)`

---

## Documentation Index

- [`ARCHITECTURE.md`](ARCHITECTURE.md): System architecture, core data flow, decision integrity, and security model
- [`DEMO_GUIDE.md`](DEMO_GUIDE.md): Step-by-step SIH demonstration guide (5–8 min walkthrough)
- [`TESTING.md`](TESTING.md): Testing pyramid, test module reference, and benchmark methodology
- [`DEPLOYMENT.md`](DEPLOYMENT.md): Detailed installation & production deployment guide
- [`DEPLOYMENT_CHECKLIST.md`](DEPLOYMENT_CHECKLIST.md): Readiness checklist
- [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md): Problem diagnosis & error resolution
- [`ENVIRONMENT.md`](ENVIRONMENT.md): Development, Demo, and Production configuration matrix
- [`LIMITATIONS.md`](LIMITATIONS.md): Factual system limitations and disclosures
- [`FINAL_SUBMISSION_READINESS.md`](FINAL_SUBMISSION_READINESS.md): Master submission readiness document
