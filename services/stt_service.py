"""
Speech-to-Text Service for Marco AI Interview Simulator
Converts candidate speech to text using multiple STT engines.
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Literal
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class STTService:
    """
    Service for converting speech to text.
    Uses OpenAI Whisper for high-accuracy transcription.
    """
    
    def __init__(self, model_size: Literal['tiny', 'base', 'small', 'medium', 'large'] = 'base'):
        """
        Initialize STT Service with Whisper.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
                       - tiny: Fastest, least accurate (~39M params)
                       - base: Good balance (~74M params) - RECOMMENDED
                       - small: Better accuracy (~244M params)
                       - medium: High accuracy (~769M params)
                       - large: Best accuracy (~1550M params)
        """
        self.model_size = model_size
        self.has_whisper = False
        self.has_speech_recognition = False
        self.whisper_model = None
        self.recognizer = None
        
        self._check_dependencies()
        self._initialize_engine()
    
    def _check_dependencies(self):
        """Check if required STT libraries are available."""
        try:
            import whisper
            self.has_whisper = True
        except ImportError:
            logger.warning("whisper not installed. Install with: pip install openai-whisper")
        
        try:
            import speech_recognition as sr
            self.has_speech_recognition = True
        except ImportError:
            logger.warning("speech_recognition not installed. Microphone support limited.")
    
    def _initialize_engine(self):
        """Initialize Whisper model."""
        if not self.has_whisper:
            raise RuntimeError("OpenAI Whisper is required. Install with: pip install openai-whisper")
        
        try:
            import whisper
            logger.info(f"Loading Whisper model '{self.model_size}'... (this may take a moment)")
            self.whisper_model = whisper.load_model(self.model_size)
            logger.info(f"Whisper model '{self.model_size}' loaded successfully")
            
            # Initialize speech recognition for microphone if available
            if self.has_speech_recognition:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = 300
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                logger.info("Microphone support enabled")
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            raise RuntimeError(f"Whisper initialization failed: {e}")
    
    def listen_from_microphone(self, duration: int = 5) -> Optional[str]:
        """
        Listen to microphone and convert speech to text using Whisper.
        
        Args:
            duration: Seconds to record audio
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.has_speech_recognition:
            logger.error("speech_recognition not available for microphone input")
            return None
        
        import speech_recognition as sr
        import tempfile
        from pathlib import Path
        
        try:
            with sr.Microphone() as source:
                logger.info(f"Listening... (recording for {duration} seconds)")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Record audio for specified duration
                audio = self.recognizer.record(source, duration=duration)
                
                logger.info("Processing speech with Whisper...")
                
                # Save audio to temporary WAV file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                    temp_path = temp_file.name
                    with open(temp_path, 'wb') as f:
                        f.write(audio.get_wav_data())
                
                # Transcribe with Whisper
                text = self.transcribe_audio_file(temp_path)
                
                # Cleanup
                Path(temp_path).unlink()
                
                if text:
                    logger.info(f"Recognized: {text}")
                return text
                
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            return None
    
    def transcribe_audio_file(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio from a file using Whisper.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
            
        Returns:
            Transcribed text or None if failed
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            logger.error(f"Audio file not found: {audio_path}")
            return None
        
        if not self.whisper_model:
            logger.error("Whisper model not initialized")
            return None
        
        try:
            result = self.whisper_model.transcribe(str(audio_path))
            text = result['text'].strip()
            logger.info(f"Transcribed from file: {text[:100]}...")
            return text
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None
    
    def get_confidence_score(self, audio_path: str) -> Optional[float]:
        """
        Get confidence score for transcription (Whisper).
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Confidence score (0.0 to 1.0) or None
        """
        if not self.whisper_model:
            logger.warning("Whisper model not available")
            return None
        
        try:
            result = self.whisper_model.transcribe(str(audio_path))
            # Whisper provides avg_logprob as confidence indicator
            avg_logprob = result.get('avg_logprob', -1.0)
            # Convert log probability to approximate confidence (0-1)
            # Higher (closer to 0) is better
            confidence = min(1.0, max(0.0, (avg_logprob + 1.0)))
            return confidence
        except Exception as e:
            logger.error(f"Error getting confidence: {e}")
            return None
    
    def set_energy_threshold(self, threshold: int):
        """Set energy threshold for speech detection."""
        if self.recognizer:
            self.recognizer.energy_threshold = threshold
            logger.info(f"Energy threshold set to: {threshold}")
    
    def set_pause_threshold(self, threshold: float):
        """Set pause threshold (seconds of silence to end phrase)."""
        if self.recognizer:
            self.recognizer.pause_threshold = threshold
            logger.info(f"Pause threshold set to: {threshold}s")


# Standalone testing function
def test_stt_service():
    """Test the STT service."""
    print("=" * 60)
    print("STT Service Test")
    print("=" * 60)
    
    try:
        # Test Whisper STT
        print("\nTesting Whisper STT (offline, high accuracy)...")
        service = STTService(model_size='base')
        
        print("\nTest 1: Microphone Input")
        print("Please speak a sentence when prompted...")
        print("(Recording for 5 seconds)")
        
        text = service.listen_from_microphone(duration=5)
        
        if text:
            print(f"✓ Recognized: '{text}'")
        else:
            print("✗ No speech recognized or error occurred")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Install dependencies with:")
        print("  pip install openai-whisper SpeechRecognition pyaudio")


if __name__ == "__main__":
    test_stt_service()
