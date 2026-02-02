"""
Speech Router - Handle TTS and STT operations
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import tempfile
from pathlib import Path
import shutil

from ..dependencies import get_tts_service, get_stt_service
from services.tts_service import TTSService
from services.stt_service import STTService


router = APIRouter(prefix="/api/speech", tags=["speech"])


class TTSRequest(BaseModel):
    """Text-to-speech request"""
    text: str


class TTSResponse(BaseModel):
    """Text-to-speech response"""
    audio_file: str
    message: str


class STTResponse(BaseModel):
    """Speech-to-text response"""
    transcribed_text: str
    confidence: float = 0.0


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
    tts_service: TTSService = Depends(get_tts_service)
):
    """Convert text to speech"""
    try:
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_path = temp_file.name
        temp_file.close()
        
        # Generate speech
        success = tts_service.save_to_file(request.text, temp_path)
        
        if not success:
            raise HTTPException(status_code=500, detail="TTS generation failed")
        
        return TTSResponse(
            audio_file=temp_path,
            message="Speech generated successfully"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.get("/tts/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve generated audio file"""
    file_path = Path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=file_path.name
    )


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    stt_service: STTService = Depends(get_stt_service)
):
    """Convert speech to text"""
    try:
        # Save uploaded audio to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, 'wb') as buffer:
            shutil.copyfileobj(audio.file, buffer)
        
        # Transcribe
        transcribed_text = stt_service.transcribe_audio_file(temp_path)
        
        if not transcribed_text:
            raise HTTPException(status_code=500, detail="Transcription failed")
        
        # Get confidence score
        confidence = stt_service.get_confidence_score(temp_path) or 0.0
        
        # Cleanup
        Path(temp_path).unlink()
        
        return STTResponse(
            transcribed_text=transcribed_text,
            confidence=confidence
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT failed: {str(e)}")
