import asyncio
import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from processor.tts_engine import TTSEngine

async def test_personas():
    engine = TTSEngine(output_dir=ROOT_DIR / "assets/audio")
    
    test_cases = [
        ("anchor", "This is the Cyber Insights anchor bringing you the latest data breach news."),
        ("expert", "Let's dive deep into the technical architecture of this zero-day exploit."),
        ("specialist", "In this tutorial, I'll show you how to secure your home network in three simple steps."),
        ("global_voice", "Welcome to a global perspective on artificial intelligence regulation.")
    ]
    
    print("🎙️ Testing New Voice Personas...")
    for persona, text in test_cases:
        filename = f"persona_test_{persona}.mp3"
        print(f"Generating for persona: {persona}...")
        path = await engine.generate_speech(text, persona=persona, filename=filename)
        if path and os.path.exists(path):
            print(f"✅ Created: {filename} ({os.path.getsize(path)} bytes)")
        else:
            print(f"❌ Failed: {persona}")

if __name__ == "__main__":
    asyncio.run(test_personas())
