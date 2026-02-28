import asyncio
from main import YouTubeAmharicCreator

async def test_run():
    creator = YouTubeAmharicCreator()
    # Using a very short YouTube video for testing
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Rick Roll for testing (or any short clip)
    try:
        print("🚀 Starting Test Run...")
        # Since transcription and video generation can take time, we wrap it in a try-except
        video_path = await creator.process_video(test_url)
        print(f"🏁 Test Finished! Video at: {video_path}")
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    # Note: This requires ffmpeg installed on user system path
    # asyncio.run(test_run())
    print("Test script ready. Run manual verification.")
