"""
STT Router for Marco AI Interview Simulator
Handles speech-to-text transcription using Whisper
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging
import tempfile
from pathlib import Path
import sys

# Add services to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from services.stt_service import STTService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stt", tags=["stt"])

# Initialize STT service (lazy loading)
stt_service = None

def get_stt_service():
    """Get or initialize STT service"""
    global stt_service
    if stt_service is None:
        try:
            logger.info("Initializing Whisper STT service...")
            stt_service = STTService(model_size='base')
            logger.info("Whisper STT service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize STT service: {e}")
            raise HTTPException(status_code=500, detail=f"STT service initialization failed: {str(e)}")
    return stt_service


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio file using Whisper
    
    Args:
        audio: Audio file (webm, wav, mp3, etc.)
        
    Returns:
        JSON with transcribed text
    """
    try:
        logger.info(f"Received audio file: {audio.filename}, type: {audio.content_type}")
        
        # Get STT service
        service = get_stt_service()
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename).suffix) as temp_file:
            temp_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)
            logger.info(f"Saved audio to temp file: {temp_path} ({len(content)} bytes)")
        
        # Transcribe with Whisper
        logger.info("Transcribing with Whisper...")
        text = service.transcribe_audio_file(temp_path)
        
        # Cleanup
        Path(temp_path).unlink()
        
        if text:
            logger.info(f"Transcription successful: {text[:100]}...")
            return JSONResponse({
                "success": True,
                "text": text,
                "transcript": text,  # Alias for compatibility
                "length": len(text)
            })
        else:
            logger.warning("No text transcribed from audio")
            return JSONResponse({
                "success": False,
                "text": "",
                "transcript": "",
                "error": "No speech detected in audio"
            })
            
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if STT service is available"""
    try:
        service = get_stt_service()
        return JSONResponse({
            "status": "healthy",
            "model": service.model_size if service else None,
            "whisper_available": service.has_whisper if service else False
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=500)
