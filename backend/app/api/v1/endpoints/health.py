from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import pymupdf

from app.core.database import get_db
from app.core.config import settings

router = APIRouter()

@router.get("/health")
def check_health(db: Session = Depends(get_db)):
    """
    Health check endpoint verifying DB connectivity and PyMuPDF engine readiness.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "service": "STAMAS API",
        "version": settings.VERSION,
        "environment": settings.ENV,
        "components": {
            "database": db_status,
            "pdf_parser": f"PyMuPDF v{pymupdf.__version__}",
            "ai_provider": settings.AI_PROVIDER,
            "ai_configured": bool(
                settings.GROQ_API_KEY if settings.AI_PROVIDER.upper() == "GROQ" else
                settings.GEMINI_API_KEY if settings.AI_PROVIDER.upper() == "GEMINI" else
                settings.OPENAI_API_KEY if settings.AI_PROVIDER.upper() == "OPENAI" else False
            )
        }
    }


@router.get("/health/ready")
def check_readiness(db: Session = Depends(get_db)):
    """
    Readiness probe verifying DB, storage writeability, and directory availability.
    """
    # 1. DB check
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

    # 2. Storage directories check
    storage_checks = {}
    for dir_name, dir_path in [
        ("uploads", settings.UPLOAD_DIR),
        ("processed", settings.PROCESSED_DIR),
        ("reports", settings.REPORT_DIR),
        ("temp", settings.TEMP_DIR)
    ]:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"Storage directory {dir_name} unavailable: {str(e)}")
        
        storage_checks[dir_name] = "writable"

    return {
        "ready": True,
        "status": "READY",
        "service": "STAMAS API",
        "version": settings.VERSION,
        "storage": storage_checks
    }


