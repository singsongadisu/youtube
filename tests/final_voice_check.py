import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

from processor.tts_engine import TTSEngine
from processor.creative_engine import CreativeEngine

async def final_verification():
    print("🚀 Starting Final Voice & Content Verification...")
    
    # 1. Test Creative Script Generation for 'Cyber'
    engine = CreativeEngine()
    print("Generating 'Cyber' script...")
    result = await engine.generate_script("cyber attacks in 2026", duration_mins=1)
    script = result["script"]
    print(f"✅ Script Generated (Partial): {script[:200]}...")
    
    # 2. Test Humanized Voice Generation with 'cyber_news' tone
    tts = TTSEngine(output_dir=ROOT_DIR / "assets/audio")
    print("Generating 'Cyber News' style voice...")
    audio_path = await tts.generate_speech(
        script, 
        lang='en', 
        gender='male', 
        tone='cyber_news', 
        filename="final_cyber_news_test.mp3"
    )
    
    if audio_path and os.path.exists(audio_path):
        print(f"✅ Voice Generation Success: {audio_path}")
        print(f"File Size: {os.path.getsize(audio_path)} bytes")
    else:
        print("❌ Voice Generation Failed!")

if __name__ == "__main__":
    asyncio.run(final_verification())
