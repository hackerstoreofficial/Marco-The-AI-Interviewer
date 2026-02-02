"""
Test script for Speech-to-Text Service
Tests STT functionality with microphone input and audio files.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.stt_service import STTService


def test_service_initialization():
    """Test STT service initialization."""
    print("\n" + "=" * 70)
    print("TEST 1: Service Initialization")
    print("=" * 70)
    
    try:
        service = STTService(model_size='base')
        print("✓ STT Service initialized successfully")
        print(f"  - Engine: OpenAI Whisper (offline)")
        print(f"  - Model: base (~74M parameters)")
        
        if service.recognizer:
            print(f"  - Microphone support: Enabled")
            print(f"  - Energy threshold: {service.recognizer.energy_threshold}")
            print(f"  - Pause threshold: {service.recognizer.pause_threshold}s")
        else:
            print(f"  - Microphone support: Disabled (SpeechRecognition not installed)")
        
        return service
        
    except Exception as e:
        print(f"✗ Failed to initialize service: {e}")
        print("\nMake sure Whisper is installed:")
        print("  pip install openai-whisper SpeechRecognition pyaudio")
        return None


def test_microphone_access():
    """Test microphone access."""
    print("\n" + "=" * 70)
    print("TEST 2: Microphone Access")
    print("=" * 70)
    
    try:
        import speech_recognition as sr
        
        # List available microphones
        mic_list = sr.Microphone.list_microphone_names()
        print(f"\n✓ Found {len(mic_list)} microphone(s):")
        for i, mic in enumerate(mic_list[:5], 1):
            print(f"  {i}. {mic}")
            if i >= 5 and len(mic_list) > 5:
                print(f"  ... and {len(mic_list) - 5} more")
                break
        
        # Test microphone access
        with sr.Microphone() as source:
            print(f"\n✓ Microphone accessed successfully")
            print(f"  - Sample rate: {source.SAMPLE_RATE} Hz")
            print(f"  - Chunk size: {source.CHUNK}")
        
        return True
        
    except Exception as e:
        print(f"✗ Microphone access failed: {e}")
        print("\nNote: This is normal if no microphone is available")
        return False


def test_live_transcription(service):
    """Test live microphone transcription."""
    print("\n" + "=" * 70)
    print("TEST 3: Live Microphone Transcription (Whisper)")
    print("=" * 70)
    
    print("\nThis test will record from your microphone using Whisper.")
    print("You will have 3 attempts to speak different sentences.")
    print("\nExample sentences to try:")
    print("  - 'My name is John and I am a software engineer'")
    print("  - 'I have five years of experience in Python development'")
    print("  - 'I am interested in machine learning and artificial intelligence'")
    
    input("\nPress Enter when ready to start...")
    
    for i in range(3):
        print(f"\n--- Attempt {i+1}/3 ---")
        print("Recording for 5 seconds... (speak now)")
        
        text = service.listen_from_microphone(duration=5)
        
        if text:
            print(f"✓ Recognized: '{text}'")
            print(f"  - Length: {len(text)} characters")
            print(f"  - Word count: {len(text.split())}")
        else:
            print("✗ No speech recognized")
        
        if i < 2:
            time.sleep(1)


def test_configuration(service):
    """Test STT configuration options."""
    print("\n" + "=" * 70)
    print("TEST 4: Configuration Options")
    print("=" * 70)
    
    # Test different energy thresholds
    print("\nTesting energy threshold adjustment:")
    thresholds = [100, 300, 500]
    
    for threshold in thresholds:
        service.set_energy_threshold(threshold)
        print(f"  ✓ Energy threshold set to: {threshold}")
    
    # Test different pause thresholds
    print("\nTesting pause threshold adjustment:")
    pauses = [0.5, 0.8, 1.2]
    
    for pause in pauses:
        service.set_pause_threshold(pause)
        print(f"  ✓ Pause threshold set to: {pause}s")
    
    # Reset to defaults
    service.set_energy_threshold(300)
    service.set_pause_threshold(0.8)
    print("\n✓ Configuration tests completed")


def test_interview_simulation(service):
    """Test with interview-like interaction."""
    print("\n" + "=" * 70)
    print("TEST 5: Interview Simulation (Whisper)")
    print("=" * 70)
    
    questions = [
        "Tell me about yourself",
        "What are your technical skills?",
        "Describe a challenging project"
    ]
    
    print("\nThis simulates an interview scenario.")
    print("You will be asked 3 questions. Answer each one.")
    print("Each answer will be recorded for 10 seconds.")
    
    user_input = input("\nDo you want to run this test? (y/n): ").strip().lower()
    
    if user_input != 'y':
        print("⚠ Skipped interview simulation test")
        return
    
    answers = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Question {i}/3 ---")
        print(f"Q: {question}")
        print("\nRecording your answer for 10 seconds... (speak now)")
        
        answer = service.listen_from_microphone(duration=10)
        
        if answer:
            print(f"A: '{answer}'")
            answers.append(answer)
        else:
            print("A: [No response detected]")
            answers.append(None)
        
        time.sleep(1)
    
    # Summary
    print("\n" + "-" * 70)
    print("Interview Summary:")
    print("-" * 70)
    
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\nQ{i}: {q}")
        print(f"A{i}: {a if a else '[No response]'}")
    
    successful = sum(1 for a in answers if a)
    print(f"\n✓ Successfully captured {successful}/{len(questions)} answers")


def test_error_handling(service):
    """Test error handling."""
    print("\n" + "=" * 70)
    print("TEST 6: Error Handling")
    print("=" * 70)
    
    # Test with non-existent audio file
    print("\nTest 1: Non-existent audio file")
    text = service.transcribe_audio_file("nonexistent_file.wav")
    if text is None:
        print("  ✓ Correctly handled missing file")
    else:
        print(f"  ✗ Unexpected result: {text}")


def run_all_tests():
    """Run all STT tests."""
    print("\n" + "=" * 70)
    print(" SPEECH-TO-TEXT SERVICE TEST SUITE")
    print("=" * 70)
    
    # Test 1: Initialization
    service = test_service_initialization()
    if not service:
        print("\n✗ Cannot continue tests without successful initialization")
        return
    
    # Test 2: Microphone access
    has_microphone = test_microphone_access()
    
    if not has_microphone:
        print("\n⚠ Skipping microphone tests (no microphone available)")
        print("\nNote: The STT service is still functional for audio file transcription")
        return
    
    # Test 3: Live transcription
    test_live_transcription(service)
    
    # Test 4: Configuration
    test_configuration(service)
    
    # Test 5: Interview simulation
    test_interview_simulation(service)
    
    # Test 6: Error handling
    test_error_handling(service)
    
    print("\n" + "=" * 70)
    print(" ALL TESTS COMPLETED")
    print("=" * 70)
    print("\nNote: Install dependencies if needed:")
    print("  pip install openai-whisper SpeechRecognition pyaudio")
    print("\nWhisper Model Sizes:")
    print("  - tiny: Fastest (~39M params)")
    print("  - base: Recommended (~74M params)")
    print("  - small: Better accuracy (~244M params)")
    print("  - medium/large: Best accuracy (requires more resources)")


if __name__ == "__main__":
    run_all_tests()
