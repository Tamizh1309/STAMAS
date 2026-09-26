import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "STAMAS - Smart Tender Analysis & Management Assessment System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment & Database
    ENV: str = os.getenv("ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./stamas.db")
    
    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./storage/uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR", "./storage/processed")
    REPORT_DIR: str = os.getenv("REPORT_DIR", "./storage/reports")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./storage/temp")
    SAMPLE_DATA_DIR: str = os.getenv("SAMPLE_DATA_DIR", "./data/sample_tenders")
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", 104857600)) # 100 MB
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://tamizh1309.github.io"
    ]

    # AI & RAG Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "GEMINI") # GEMINI, OPENAI, LOCAL, NONE
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "KEYWORD") # GEMINI, OPENAI, LOCAL, KEYWORD


settings = Settings()

# Ensure required storage and sample directories exist
for path in [settings.UPLOAD_DIR, settings.PROCESSED_DIR, settings.REPORT_DIR, settings.TEMP_DIR, settings.SAMPLE_DATA_DIR]:
    os.makedirs(path, exist_ok=True)

