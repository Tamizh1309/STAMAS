# STAMAS — System Architecture & Data Flow Reference

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## 1. System Architecture Overview

STAMAS is built around a decoupled, evidence-driven architecture. The frontend UI operates asynchronously against a RESTful FastAPI backend. The core decision engine separates deterministic rule evaluation from human officer review actions, preserving full auditability.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            STAMAS FRONTEND UI                               │
│                   React 18 + TypeScript + Vite + Tailwind                   │
│                                                                             │
│  [Dashboard] ──> [Tenders] ──> [Bidders] ──> [Compliance] ──> [Reports/Audit]│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST API (Port 8000)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI API GATEWAY                              │
│                Router / Middleware / CORS / Security Validation             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
      ┌────────────────────────────────┼────────────────────────────────┐
      ▼                                ▼                                ▼
┌─────────────┐                ┌─────────────┐                ┌─────────────┐
│ Tender &    │                │ Document    │                │ Evidence &  │
│ Requirement │                │ Processing  │                │ Rule Engine │
│ Services    │                │ Service     │                │ Service     │
└──────┬──────┘                └──────┬──────┘                └──────┬──────┘
       │                              │                              │
       └──────────────────────────────┼──────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CORE ASSESSMENT PIPELINE                          │
│                                                                             │
│  Tender PDF ──> Requirement Extraction ──> Document Intelligence            │
│         │                                          │                        │
│         ▼                                          ▼                        │
│  Ground Truth ─────────> Evidence Matching <────── Page Matrix              │
│                                   │                                         │
│                                   ▼                                         │
│                       Deterministic Rule Engine                             │
│                                   │                                         │
│                                   ▼                                         │
│                      AI / RAG Explanation Layer                             │
│                                   │                                         │
│                                   ▼                                         │
│                       System Decision Engine                                │
│                     (PASS / FAIL / REVIEW State)                            │
│                                   │                                         │
│                                   ▼                                         │
│                  Officer Workstation & Human Review                         │
│                    (Confirm / Override Action)                              │
│                                   │                                         │
│                                   ▼                                         │
│                       Final Officer Decision                                │
│                                   │                                         │
│                                   ▼                                         │
│                       Reports & Audit Subsystem                             │
│                    (PDF / CSV / JSON Audit Log)                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Data Flow & Entity Relationships

The STAMAS data model enforces complete end-to-end traceability across all 12 system phases:

```text
Tender (TND-SIH2026-GEM01)
├── TenderPage (Page 1 .. N)
└── Requirement (REQ-01 .. REQ-05)
      ├── ComplianceRule (RULE-01 .. RULE-05)
      │     └── RuleEvaluation (EVAL-01 .. EVAL-05)
      └── EvidenceMatch (EV-01 .. EV-05)
            ├── BidderDocument (DOC-01 .. DOC-02)
            │     └── BidderDocumentPage (Page 1 .. N)
            └── Bidder (BIDDER-PARAM-99)
                  ├── System ComplianceDecision (PASS / FAIL / REVIEW)
                  ├── Human OfficerDecision (Confirmed / Overridden)
                  ├── OfficerReviewAudit (Audit Event Log)
                  └── Final Compliance Report (PDF / CSV)
```

---

## 3. Decision Integrity Engine

STAMAS strictly decouples **System Decisions** from **Human Officer Decisions**:

1. **System Decision Engine (Phase 8):** Generates an unalterable system decision (`PASS`, `FAIL`, or `REVIEW`) derived deterministically from evidence completeness and rule satisfaction.
2. **Officer Review Workstation (Phase 9):** Procurement officers review evidence, citations, and rule explanations. Officers may **CONFIRM** the system decision or apply a **MANUAL OVERRIDE** with mandatory written justification.
3. **Immutability Principle:** The underlying system decision remains untouched in audit history when an officer applies an override, ensuring full transparency.

---

## 4. Security & Isolation Architecture

- **Cross-Tender Isolation:** Database queries enforce combined `(tender_id, bidder_id)` constraints to prevent cross-dossier data leakage.
- **Prompt Injection Defense:** Malicious text within submitted bidder documents is treated strictly as raw text data without influencing LLM prompt execution.
- **Path Sanitization:** File operations sanitize paths to prevent directory escape vulnerabilities during export.
