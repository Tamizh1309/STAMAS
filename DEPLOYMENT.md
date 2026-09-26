# STAMAS — Production Deployment & Setup Guide

**Smart Tender Analysis & Management Assessment System (STAMAS)**  
**Problem Statement:** SIH26100 — AI-Powered Integrated Bid Compliance Verification Platform for GeM Procurement  

---

## 1. Prerequisites & System Requirements

### Hardware Requirements
- **CPU:** 4 Cores (x86_64 or ARM64)
- **RAM:** Minimum 8 GB (16 GB Recommended for large PDF processing)
- **Disk:** 20 GB free SSD storage

### Software Requirements
- **OS:** Windows 10/11, Linux (Ubuntu 22.04 LTS), or macOS 13+
- **Python:** 3.11+
- **Node.js:** 18.x or 20.x
- **Docker:** Docker Desktop v4.20+ or Docker Engine with Docker Compose v2.x

---

## 2. Environment Configuration

1. Copy the master `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure environment variables in `.env`:
   ```env
   ENV=production
   PORT=8000
   DATABASE_URL=sqlite:///./stamas.db
   UPLOAD_DIR=./storage/uploads
   PROCESSED_DIR=./storage/processed
   REPORT_DIR=./storage/reports
   TEMP_DIR=./storage/temp
   MAX_UPLOAD_SIZE=104857600
   CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   AI_PROVIDER=GEMINI
   EMBEDDING_PROVIDER=KEYWORD
   GEMINI_API_KEY=your_gemini_api_key_here
   LOG_LEVEL=INFO
   ```

---

## 3. Local Deployment (Windows / Linux)

### Backend Setup
```bash
cd backend
python -m venv venv

# On Windows PowerShell:
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Run database setup & demo seeding
python -m app.seed_demo

# Start Backend FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run build
npm run dev
```

### 1-Command Startup (Windows)
```powershell
.\start.ps1
```

---

## 4. Containerized Deployment (Docker & Docker Compose)

```bash
# Build and start all services in detached mode
docker-compose up -d --build

# View container logs
docker-compose logs -f

# Check health status
docker-compose ps
```

Services exposed:
- **Frontend Web UI:** `http://localhost:3000`
- **Backend API:** `http://localhost:8000`
- **Health Check Endpoint:** `http://localhost:8000/api/v1/health`
- **Readiness Probe:** `http://localhost:8000/api/v1/health/ready`

---

## 5. Database Backup & Disaster Recovery

### SQLite Backup Procedure
```bash
# Backup SQLite database file and storage directory
cp backend/stamas.db storage/backups/stamas_backup_$(date +%Y%m%d_%H%M%S).db
tar -czvf storage/backups/storage_backup_$(date +%Y%m%d).tar.gz storage/
```

### SQLite Restore Procedure
```bash
# Restore database file
cp storage/backups/stamas_backup_TARGET.db backend/stamas.db
tar -xzvf storage/backups/storage_backup_TARGET.tar.gz -C ./
```

---

## 6. Observability & Health Probes

STAMAS provides production readiness endpoints:
- `GET /api/v1/health`: Checks database connectivity, PyMuPDF engine, version, and AI provider status.
- `GET /api/v1/health/ready`: Verifies database connection and write permissions across storage directories.
