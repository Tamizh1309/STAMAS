# STAMAS — Troubleshooting & Issue Resolution Guide

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## 1. Common Runtime Issues & Solutions

### A. Backend Server Won't Start (`ModuleNotFoundError`)
* **Symptom:** `ModuleNotFoundError: No module named 'app'` or missing dependency.
* **Resolution:** Ensure the virtual environment is activated and dependencies are installed:
  ```bash
  cd backend
  .\venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  ```

### B. Frontend Cannot Connect to Backend (CORS / Connection Refused)
* **Symptom:** `Failed to fetch` or CORS error in browser developer console.
* **Resolution:**
  1. Confirm FastAPI backend is running on `http://localhost:8000`.
  2. Verify `CORS_ORIGINS` in `.env` includes your frontend URL (`http://localhost:3000` or `http://localhost:5173`).
  3. Ensure `VITE_API_BASE_URL` in `frontend/.env` points to `http://localhost:8000/api/v1`.

### C. External AI API Call Failures (`AI_UNAVAILABLE`)
* **Symptom:** RAG query returns `"AI_UNAVAILABLE"` or explanation is simplified.
* **Resolution:** STAMAS features **graceful AI degradation**. If `GEMINI_API_KEY` is invalid or offline, the platform automatically switches to deterministic keyword retrieval and rule engine evaluation without crashing.

### D. PDF File Upload Error (`File Too Large`)
* **Symptom:** HTTP 413 or upload fails for large tender dossiers.
* **Resolution:** Increase `MAX_UPLOAD_SIZE` in `.env` (default is `104857600` bytes / 100 MB).

### E. Database Locked Error (`sqlite3.OperationalError: database is locked`)
* **Symptom:** Concurrent SQLite access fails under high load.
* **Resolution:** SQLite is suitable for single-node development and demonstration. For high concurrency, configure PostgreSQL in `.env`:
  ```env
  DATABASE_URL=postgresql://stamas_user:stamas_pass@db:5432/stamas_db
  ```

---

## 2. Diagnostics Commands

```bash
# Check health probe
curl http://localhost:8000/api/v1/health

# Check readiness probe
curl http://localhost:8000/api/v1/health/ready

# Re-run automated unit, security, and benchmark test suites
cd backend
.\venv\Scripts\python -m pytest

# Run dynamic benchmark evaluator directly
.\venv\Scripts\python scratch/test_phase11_demo.py
```
