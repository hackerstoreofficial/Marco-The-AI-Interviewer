import os
from pathlib import Path
from typing import Optional, List, Set
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Marco AI Interview Simulator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_PATH: Path = Path(__file__).parent.parent / "database" / "marco_interviews.db"
    # Added this so it doesn't crash reading your .env
    DATABASE_URL: Optional[str] = None 
    
    # Security (Crucial missing field)
    ENCRYPTION_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "file://",
    ]
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    UPLOAD_DIR: Path = Path(__file__).parent / "uploads"
    ALLOWED_RESUME_EXTENSIONS: Set[str] = {".pdf", ".docx", ".doc"}
    
    # Services
    TTS_ENGINE: str = "pyttsx3"
    STT_MODEL: str = "base"
    FACE_TRACKING_MAX_VIOLATIONS: int = 7
    FACE_TRACKING_THRESHOLD: float = 30.0
    
    # Face Proctoring (These were causing errors!)
    FACE_YAW_THRESHOLD: float = 30.0
    FACE_LOOKING_AWAY_DURATION: float = 2.0
    
    # Interview
    INTERVIEW_DURATION_MINUTES: int = 30
    MAX_QUESTIONS: int = 10
    
    # LLM API Keys
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # <--- This is the magic fix. It ignores unexpected vars.

# Global settings instance
settings = Settings()

# Ensure upload directory exists
settings.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)