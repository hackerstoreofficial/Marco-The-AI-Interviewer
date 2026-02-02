"""
Text-to-Speech Service for Marco AI Interview Simulator
Converts interview questions to speech using multiple TTS engines.
"""

import logging
from pathlib import Path
from typing import Optional, Literal
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSService:
    """
    Service for converting text to speech.
    Supports multiple TTS engines: pyttsx3 (offline), gTTS (online).
    """
    
    def __init__(self, engine: Literal['pyttsx3', 'gtts'] = 'pyttsx3'):
        """
        Initialize TTS Service.
        
        Args:
            engine: TTS engine to use ('pyttsx3' for offline, 'gtts' for online)
        """
        self.engine_type = engine
        self.has_pyttsx3 = False
        self.has_gtts = False
        self.tts_engine = None
        
        self._check_dependencies()
        self._initialize_engine()
    
    def _check_dependencies(self):
        """Check if required TTS libraries are available."""
        try:
            import pyttsx3
            self.has_pyttsx3 = True
        except ImportError:
            logger.warning("pyttsx3 not installed. Offline TTS disabled.")
        
        try:
            from gtts import gTTS
            self.has_gtts = True
        except ImportError:
            logger.warning("gTTS not installed. Online TTS disabled.")
    
    def _initialize_engine(self):
        """Initialize the selected TTS engine."""
        if self.engine_type == 'pyttsx3' and self.has_pyttsx3:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure voice properties
            self.tts_engine.setProperty('rate', 150)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            
            # Try to set a pleasant voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice if available (usually more pleasant)
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            logger.info("pyttsx3 TTS engine initialized")
            
        elif self.engine_type == 'gtts' and self.has_gtts:
            logger.info("gTTS engine selected (requires internet)")
        else:
            logger.error(f"TTS engine '{self.engine_type}' not available")
            raise RuntimeError(f"TTS engine '{self.engine_type}' not available. Install with: pip install {self.engine_type}")
    
    def speak(self, text: str, wait: bool = True) -> bool:
        """
        Speak the given text aloud.
        
        Args:
            text: Text to speak
            wait: Whether to wait for speech to complete (pyttsx3 only)
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return False
        
        try:
            if self.engine_type == 'pyttsx3' and self.tts_engine:
                self.tts_engine.say(text)
                if wait:
                    self.tts_engine.runAndWait()
                logger.info(f"Spoke text: {text[:50]}...")
                return True
            
            elif self.engine_type == 'gtts' and self.has_gtts:
                from gtts import gTTS
                import pygame
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                    temp_file = fp.name
                
                # Generate speech
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(temp_file)
                
                # Play audio
                pygame.mixer.init()
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                
                if wait:
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                
                # Cleanup
                pygame.mixer.quit()
                Path(temp_file).unlink()
                
                logger.info(f"Spoke text: {text[:50]}...")
                return True
            
            else:
                logger.error("No TTS engine available")
                return False
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False
    
    def save_to_file(self, text: str, output_path: str) -> bool:
        """
        Save speech to an audio file.
        
        Args:
            text: Text to convert to speech
            output_path: Path to save audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            output_path = Path(output_path)
            
            if self.engine_type == 'pyttsx3' and self.tts_engine:
                self.tts_engine.save_to_file(text, str(output_path))
                self.tts_engine.runAndWait()
                logger.info(f"Saved TTS to: {output_path}")
                return True
            
            elif self.engine_type == 'gtts' and self.has_gtts:
                from gtts import gTTS
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(str(output_path))
                logger.info(f"Saved TTS to: {output_path}")
                return True
            
            else:
                logger.error("No TTS engine available")
                return False
                
        except Exception as e:
            logger.error(f"Error saving TTS file: {e}")
            return False
    
    def set_rate(self, rate: int):
        """Set speech rate (pyttsx3 only)."""
        if self.engine_type == 'pyttsx3' and self.tts_engine:
            self.tts_engine.setProperty('rate', rate)
            logger.info(f"Speech rate set to: {rate}")
    
    def set_volume(self, volume: float):
        """Set speech volume 0.0 to 1.0 (pyttsx3 only)."""
        if self.engine_type == 'pyttsx3' and self.tts_engine:
            self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))
            logger.info(f"Speech volume set to: {volume}")
    
    def get_voices(self) -> list:
        """Get available voices (pyttsx3 only)."""
        if self.engine_type == 'pyttsx3' and self.tts_engine:
            voices = self.tts_engine.getProperty('voices')
            return [{'id': v.id, 'name': v.name, 'languages': v.languages} for v in voices]
        return []
    
    def set_voice(self, voice_id: str):
        """Set voice by ID (pyttsx3 only)."""
        if self.engine_type == 'pyttsx3' and self.tts_engine:
            self.tts_engine.setProperty('voice', voice_id)
            logger.info(f"Voice set to: {voice_id}")


# Standalone testing function
def test_tts_service():
    """Test the TTS service."""
    print("=" * 60)
    print("TTS Service Test")
    print("=" * 60)
    
    try:
        # Test pyttsx3 (offline)
        print("\nTesting pyttsx3 (offline TTS)...")
        service = TTSService(engine='pyttsx3')
        
        test_text = "Hello! This is Marco, your AI interview simulator. I will be asking you questions based on your resume."
        
        print(f"\nSpeaking: '{test_text}'")
        success = service.speak(test_text)
        
        if success:
            print("✓ TTS successful!")
        else:
            print("✗ TTS failed")
        
        # List available voices
        voices = service.get_voices()
        print(f"\nAvailable voices: {len(voices)}")
        for i, voice in enumerate(voices[:3], 1):
            print(f"  {i}. {voice['name']}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Install pyttsx3 with: pip install pyttsx3")


if __name__ == "__main__":
    test_tts_service()
