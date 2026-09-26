# STAMAS API Documentation V1

Base URL: `http://localhost:8000/api/v1`

## Health Check
- `GET /health`
  - Returns backend status, database status, and PyMuPDF engine diagnostic information.

## Tender Management
- `POST /tenders/`
  - Create a new tender record.
- `GET /tenders/`
  - List all tenders with optional search parameter (`?search=...`).
- `GET /tenders/{id}`
  - Retrieve detailed tender record including pages.
- `POST /tenders/{id}/upload-pdf`
  - Upload tender PDF document, trigger PyMuPDF text & page parsing, store extracted text per page in DB.
- `GET /tenders/{id}/extracted-text`
  - Retrieve page-by-page extracted text with optional keyword search (`?query=...`).
