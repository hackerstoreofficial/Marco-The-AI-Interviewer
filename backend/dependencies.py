"""
Shared dependencies for FastAPI routes
"""

from typing import Optional
from fastapi import Depends, HTTPException, UploadFile
from pathlib import Path

from .database import db
from .config import settings
from services.ocr_service import OCRService
from services.tts_service import TTSService
from services.stt_service import STTService
from services.face_tracking_service import FaceTrackingService


# Service instances (singletons for stateless services)
_ocr_service: Optional[OCRService] = None
_tts_service: Optional[TTSService] = None
_stt_service: Optional[STTService] = None

# Per-session face tracking services (each session gets its own instance)
from typing import Dict
_session_face_services: Dict[int, FaceTrackingService] = {}


def get_ocr_service() -> OCRService:
    """Get OCR service instance"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service


def get_tts_service() -> TTSService:
    """Get TTS service instance"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService(engine=settings.TTS_ENGINE)
    return _tts_service


def get_stt_service() -> STTService:
    """Get STT service instance"""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService(model_size=settings.STT_MODEL)
    return _stt_service


def get_or_create_face_service(session_id: int) -> FaceTrackingService:
    """
    Get or create a face tracking service for a specific session.
    Each session gets its own instance to track violations independently.
    """
    global _session_face_services
    if session_id not in _session_face_services:
        _session_face_services[session_id] = FaceTrackingService(
            yaw_threshold=30.0,  # Degrees of yaw before considering "looking away"
            looking_away_duration=2.0  # Seconds before counting as violation
        )
    return _session_face_services[session_id]


def cleanup_face_service(session_id: int):
    """
    Cleanup face tracking service for a session when interview ends.
    """
    global _session_face_services
    if session_id in _session_face_services:
        del _session_face_services[session_id]


def get_face_tracking_service() -> FaceTrackingService:
    """
    DEPRECATED: Use get_or_create_face_service(session_id) instead.
    This function is kept for backward compatibility but should not be used.
    """
    # Return a temporary instance for testing/compatibility
    return FaceTrackingService(
        yaw_threshold=30.0,
        looking_away_duration=2.0
    )


async def get_db():
    """Get database connection"""
    return db


def validate_file_upload(file: UploadFile, allowed_extensions: set) -> Path:
    """Validate uploaded file"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    return file_ext
