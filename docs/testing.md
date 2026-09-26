# STAMAS Test Suite & Benchmarking

## Backend Unit & Integration Tests

To run all backend tests:

```bash
cd backend
.\venv\Scripts\pytest -o pythonpath=. -v
```

### Test Coverage Included in Phase 1:
1. `test_health.py`: Health check diagnostic endpoint & root API availability.
2. `test_tenders.py`: Tender creation, duplicate prevention, pagination, and detail retrieval.
3. `test_pdf_extraction.py`: PDF document upload, PyMuPDF page parsing, text storage, and keyword search.

## Frontend Production Build Test

To run frontend TypeScript validation & Vite bundle build:

```bash
cd frontend
npm run build
```
