"""
Configuration and settings for Marco AI Interview Simulator Backend
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Marco AI Interview Simulator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_PATH: Path = Path(__file__).parent.parent / "database" / "marco_interviews.db"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",  # Live Server
        "http://127.0.0.1:5500",
        "file://",  # Allow file:// protocol for local HTML
    ]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_DIR: Path = Path(__file__).parent / "uploads"
    ALLOWED_RESUME_EXTENSIONS: set = {".pdf", ".docx", ".doc"}
    
    # Services
    TTS_ENGINE: str = "pyttsx3"  # or "gtts"
    STT_MODEL: str = "base"  # Whisper model size
    FACE_TRACKING_MAX_VIOLATIONS: int = 7
    FACE_TRACKING_THRESHOLD: float = 30.0
    
    # Interview
    INTERVIEW_DURATION_MINUTES: int = 30
    MAX_QUESTIONS: int = 10
    
    # LLM API Keys (loaded from environment)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(exist_ok=True)
