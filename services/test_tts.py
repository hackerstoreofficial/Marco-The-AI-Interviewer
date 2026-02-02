"""
Test script for Text-to-Speech Service
Tests TTS functionality with different engines and configurations.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.tts_service import TTSService


def test_service_initialization():
    """Test TTS service initialization."""
    print("\n" + "=" * 70)
    print("TEST 1: Service Initialization")
    print("=" * 70)
    
    try:
        service = TTSService(engine='pyttsx3')
        print("✓ TTS Service initialized successfully")
        print(f"  - Engine: pyttsx3 (offline)")
        
        # Get available voices
        voices = service.get_voices()
        print(f"\n✓ Found {len(voices)} available voices:")
        for i, voice in enumerate(voices[:5], 1):
            print(f"  {i}. {voice['name']}")
            if i >= 5:
                print(f"  ... and {len(voices) - 5} more")
                break
        
        return service
        
    except Exception as e:
        print(f"✗ Failed to initialize service: {e}")
        print("\nMake sure pyttsx3 is installed:")
        print("  pip install pyttsx3")
        return None


def test_basic_speech(service):
    """Test basic text-to-speech."""
    print("\n" + "=" * 70)
    print("TEST 2: Basic Speech")
    print("=" * 70)
    
    test_sentences = [
        "Hello! Welcome to Marco, your AI interview simulator.",
        "Let's begin with your first question.",
        "Can you describe your experience with Python programming?"
    ]
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\nTest {i}: Speaking...")
        print(f"  Text: '{sentence}'")
        
        success = service.speak(sentence, wait=True)
        
        if success:
            print(f"  ✓ Speech completed successfully")
        else:
            print(f"  ✗ Speech failed")
        
        time.sleep(0.5)  # Brief pause between sentences


def test_voice_customization(service):
    """Test voice rate and volume customization."""
    print("\n" + "=" * 70)
    print("TEST 3: Voice Customization")
    print("=" * 70)
    
    test_text = "This is a test of voice customization."
    
    # Test different rates
    print("\nTesting different speech rates:")
    rates = [100, 150, 200]
    
    for rate in rates:
        print(f"\n  Rate: {rate} words per minute")
        service.set_rate(rate)
        service.speak(test_text, wait=True)
        time.sleep(0.3)
    
    # Reset to normal
    service.set_rate(150)
    
    # Test different volumes
    print("\nTesting different volumes:")
    volumes = [0.5, 0.7, 1.0]
    
    for volume in volumes:
        print(f"\n  Volume: {volume}")
        service.set_volume(volume)
        service.speak(test_text, wait=True)
        time.sleep(0.3)
    
    # Reset to normal
    service.set_volume(0.9)
    print("\n✓ Voice customization tests completed")


def test_save_to_file(service):
    """Test saving speech to audio file."""
    print("\n" + "=" * 70)
    print("TEST 4: Save to File")
    print("=" * 70)
    
    test_text = "This is Marco. Your interview will begin shortly. Please ensure your microphone and camera are working properly."
    output_file = Path(__file__).parent / "test_tts_output.wav"
    
    try:
        print(f"\nSaving speech to: {output_file.name}")
        print(f"Text: '{test_text}'")
        
        success = service.save_to_file(test_text, str(output_file))
        
        if success and output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✓ File saved successfully")
            print(f"  - Size: {file_size:,} bytes")
            print(f"  - Path: {output_file}")
            
            # Cleanup
            output_file.unlink()
            print(f"✓ Test file cleaned up")
        else:
            print("✗ Failed to save file")
            
    except Exception as e:
        print(f"✗ Error: {e}")


def test_interview_questions(service):
    """Test with realistic interview questions."""
    print("\n" + "=" * 70)
    print("TEST 5: Realistic Interview Questions")
    print("=" * 70)
    
    questions = [
        "Tell me about yourself and your background in software development.",
        "What programming languages are you most comfortable with?",
        "Describe a challenging project you worked on and how you overcame obstacles.",
        "How do you stay updated with the latest technology trends?",
        "Do you have any questions for me?"
    ]
    
    print("\nSpeaking interview questions:")
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}:")
        print(f"  '{question}'")
        
        success = service.speak(question, wait=True)
        
        if success:
            print(f"  ✓ Spoken successfully")
        else:
            print(f"  ✗ Failed")
        
        time.sleep(1)  # Pause between questions


def test_error_handling(service):
    """Test error handling."""
    print("\n" + "=" * 70)
    print("TEST 6: Error Handling")
    print("=" * 70)
    
    # Test empty text
    print("\nTest 1: Empty text")
    success = service.speak("", wait=True)
    if not success:
        print("  ✓ Correctly handled empty text")
    else:
        print("  ✗ Should have failed with empty text")
    
    # Test None
    print("\nTest 2: None value")
    success = service.speak(None, wait=True)
    if not success:
        print("  ✓ Correctly handled None value")
    else:
        print("  ✗ Should have failed with None")
    
    # Test very long text
    print("\nTest 3: Very long text")
    long_text = "This is a test. " * 100
    success = service.speak(long_text, wait=True)
    if success:
        print("  ✓ Successfully handled long text")
    else:
        print("  ✗ Failed with long text")


def run_all_tests():
    """Run all TTS tests."""
    print("\n" + "=" * 70)
    print(" TEXT-TO-SPEECH SERVICE TEST SUITE")
    print("=" * 70)
    
    # Test 1: Initialization
    service = test_service_initialization()
    if not service:
        print("\n✗ Cannot continue tests without successful initialization")
        return
    
    # Test 2: Basic speech
    test_basic_speech(service)
    
    # Test 3: Voice customization
    test_voice_customization(service)
    
    # Test 4: Save to file
    test_save_to_file(service)
    
    # Test 5: Interview questions
    test_interview_questions(service)
    
    # Test 6: Error handling
    test_error_handling(service)
    
    print("\n" + "=" * 70)
    print(" ALL TESTS COMPLETED")
    print("=" * 70)
    print("\nNote: If you encountered errors, install dependencies:")
    print("  pip install pyttsx3")
    print("\nFor online TTS (gTTS):")
    print("  pip install gTTS pygame")


if __name__ == "__main__":
    run_all_tests()
