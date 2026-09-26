# STAMAS — SIH Demonstration Guide & Evaluator Walkthrough

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## 1. Demonstration Setup & Quick Start (2 Minutes)

### Step 1: Launch System
In PowerShell on Windows:
```powershell
.\start.ps1
```
This automatically boots:
- **Backend API:** `http://localhost:8000`
- **Frontend UI Platform:** `http://localhost:3000`

### Step 2: Seed Demonstration Dataset
In a second terminal window (if clean seed required):
```bash
cd backend
.\venv\Scripts\python -m app.seed_demo
```

---

## 2. 12-Step Live Demonstration Walkthrough (5–8 Minutes)

| Step # | User Action | System Demonstration | Key Evaluator Point |
| :---: | :--- | :--- | :--- |
| **1** | Open Dashboard | Navigate to `http://localhost:3000` | Displays active tenders, bidder statistics, system health status. |
| **2** | Open Tender | Select `TND-SIH2026-GEM01` (*Enterprise Cloud Compute RFP*) | Shows uploaded tender metadata, department (MeitY), and document page count (18 pages). |
| **3** | View Requirements | Inspect extracted requirements table | Shows mandatory flags, categories (Financial, Technical, ISO, Local Content), and numeric thresholds. |
| **4** | Open Bidder Dossier | Select bidder `Param Tech Systems India Pvt Ltd` | Shows uploaded bidder qualification documents and processing status. |
| **5** | Inspect Evidence | Click on Requirement `REQ-FIN-01` (Turnover) | Displays exact matched text snippet ("₹14.8 Cr"), document name, and page number (Page 5). |
| **6** | Rule Evaluation | Inspect Rule Engine tab | Displays deterministic rule result (`SATISFIED` for 14.8 Cr >= 10 Cr threshold). |
| **7** | View System Decision | Inspect Compliance Dashboard | System evaluates bidder as `REVIEW` due to ambiguous MAF signature layer. |
| **8** | Officer Workstation | Open Officer Review interface | Shows System Decision vs Final Officer Decision panel. |
| **9** | Confirm Valid Items | Click **Confirm** on Turnover & Experience rules | System logs officer confirmation events into audit history. |
| **10** | Apply Override | Select MAF rule, click **Override to PASS**, enter reason | Officer enters written justification (*"Original MAF verified on GeM portal under Appendix 4"*). |
| **11** | Finalize & Export | Click **Finalize Review**, then download PDF/CSV report | Downloads official compliance report containing complete evidence citations. |
| **12** | Audit & Benchmarks | Open Audit Trail & switch to **Evaluation & Benchmarks** tab | Shows timestamped audit history and live benchmark metrics (F1 100%, 0 failures). |

---

## 3. Demonstration Fallback Protocols

- **If External AI API Key is Offline:** The system automatically falls back to keyword retrieval and deterministic rule evaluation without interrupting the demonstration.
- **If Report Download is Blocked:** Use the live PDF/CSV preview API endpoints (`/api/v1/reports/bidders/28/pdf`).
