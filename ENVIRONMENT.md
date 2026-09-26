# STAMAS — Environment Configuration Matrix

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## Environment Matrix Comparison

| Configuration Parameter | DEVELOPMENT | DEMO (SIH Evaluation) | PRODUCTION (GitHub Pages + FastAPI) |
| :--- | :--- | :--- | :--- |
| **`ENV`** | `development` | `demo` | `production` |
| **`PORT`** | `8000` | `8000` | `8000` |
| **`DATABASE_URL`** | `sqlite:///./stamas.db` | `sqlite:///./stamas.db` | `sqlite:///./stamas.db` / `postgresql://...` |
| **`CORS_ORIGINS`** | `["http://localhost:3000"]` | `["http://localhost:3000"]` | `["https://tamizh1309.github.io"]` |
| **`VITE_API_BASE_URL`** | `http://localhost:8000/api/v1` | `http://localhost:8000/api/v1` | `https://YOUR-BACKEND-DOMAIN/api/v1` |
| **`Frontend Host`** | `http://localhost:3000` | `http://localhost:3000` | `https://tamizh1309.github.io/STAMAS/` |
| **`UPLOAD_DIR`** | `./storage/uploads` | `./storage/uploads` | `/var/stamas/uploads` |
| **`REPORT_DIR`** | `./storage/reports` | `./storage/reports` | `/var/stamas/reports` |
| **`AI_PROVIDER`** | `GEMINI` / `LOCAL` | `GEMINI` (with fallback) | `GEMINI` / `OPENAI` |
| **`EMBEDDING_PROVIDER`** | `KEYWORD` | `KEYWORD` | `GEMINI` / `LOCAL` |
| **`LOG_LEVEL`** | `DEBUG` | `INFO` | `WARNING` |
| **`MAX_UPLOAD_SIZE`** | `104857600` (100MB) | `104857600` (100MB) | `524288000` (500MB) |

