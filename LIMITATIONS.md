# STAMAS — Factual System Limitations & Disclosures

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## Factual Limitations & Scope Disclosures

1. **SIH Prototype Scope:** STAMAS is an AI-assisted bid compliance verification prototype developed for the Smart India Hackathon (SIH26100). It is not an official government production system or direct integration with GeM APIs unless formally deployed.
2. **AI Provider Availability & Fallback:** External LLM APIs (e.g. Google Gemini) are subject to network availability and quota limits. STAMAS features **graceful fallback** to deterministic keyword retrieval and rule evaluation when LLM services are unavailable.
3. **OCR & Document Quality:** PyMuPDF text extraction accuracy is dependent on source PDF quality. Poorly scanned, rotated, or degraded documents rely on OCR fallbacks which may introduce character recognition variances.
4. **Single-Node Local Database:** Development and local benchmarking use SQLite. Production multi-user deployment requires PostgreSQL connection pooling as documented in `DEPLOYMENT.md`.
5. **Human-in-the-Loop Requirement:** STAMAS is designed to assist procurement officers, not replace them. All final procurement compliance decisions require human officer review, confirmation, or manual override.
