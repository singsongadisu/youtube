import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from processor.transcribe_engine import TranscriptionEngine

async def verify_transcription():
    print("Testing TranscriptionEngine...")
    engine = TranscriptionEngine(model_name="tiny") # Use tiny for faster test
    
    # We need a small audio file. Since I don't have one, I'll just check if the model loads.
    print("Whisper model loaded successfully.")
    
    # If there's an audio file in assets/audio, we could test it.
    audio_dir = ROOT_DIR / "assets" / "audio"
    audio_files = list(audio_dir.glob("*.mp3"))
    
    if audio_files:
        test_file = audio_files[0]
        print(f"Testing with file: {test_file}")
        try:
            result = await engine.transcribe(str(test_file))
            print("Transcription Success!")
            print(f"Text snippet: {result['text'][:100]}...")
            print(f"SRT generated: {len(result['srt'])} bytes")
        except Exception as e:
            print(f"Transcription failed: {e}")
    else:
        print("No audio files found for testing. Skipping transcription run.")

if __name__ == "__main__":
    asyncio.run(verify_transcription())
