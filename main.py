import os
import asyncio
import json
from processor.downloader import VideoDownloader
from processor.transcriber import Transcriber
from processor.english_recreator import EnglishVideoRecreator
from audio.generator import AudioEngine
from visual.editor import VisualEngine
from pathlib import Path

class YouTubeAmharicCreator:
    def __init__(self):
        self.base_dir = Path(__file__).parent.absolute()
        self.downloader = VideoDownloader(download_path=self.base_dir / "assets/downloads")
        self.transcriber = Transcriber(model_size="base")
        self.audio_engine = AudioEngine(output_path=self.base_dir / "assets/audio")
        self.visual_engine = VisualEngine(output_path=self.base_dir / "assets/videos")
        
        # Ensure directories
        (self.base_dir / "assets/images").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "outputs").mkdir(parents=True, exist_ok=True)

    async def process_video(self, url: str, target_duration: int = 5, target_lang: str = "am", tone: str = "neutral", mission: str = "translate", genre: str = "sermon", status_callback=None):
        from processor.studio_engine import StudioEngine
        from processor.video_composer import VideoComposer
        studio = StudioEngine()
        en_recreator = EnglishVideoRecreator(studio_engine=studio)
        
        async def update_status(msg, progress):
            if status_callback:
                if asyncio.iscoroutinefunction(status_callback):
                    await status_callback(msg, progress)
                else:
                    status_callback(msg, progress)
            print(f"[{progress}%] {msg}")

        await update_status("🎬 Starting studio analysis...", 0)
        
        # 1. Download Content
        await update_status("📥 Downloading audio & video...", 10)
        # Run sequentially on Windows to avoid WinError 32 file lock collisions
        audio_path = await asyncio.to_thread(self.downloader.download_audio, url)
        video_path = await asyncio.to_thread(self.downloader.download_video, url)
        await update_status(f"✅ Content downloaded", 30)
        
        # 2. Transcribe
        await update_status("✍️ Transcribing full audio...", 40)
        # We need the segments for the editing guide
        whisper_model = self.transcriber.model
        
        # V30: Transcription Heartbeat (Prevents UI appearing 'stuck' on CPU)
        stop_heartbeat = asyncio.Event()
        
        async def heartbeat():
            heartbeat_count = 0
            while not stop_heartbeat.is_set():
                await asyncio.sleep(20) # Ping every 20 seconds
                if stop_heartbeat.is_set(): break
                heartbeat_count += 1
                msg = f"✍️ Still transcribing... (Step {heartbeat_count})"
                if heartbeat_count > 3:
                    msg += " [This is a long video, still working!]"
                await update_status(msg, 40)
        
        heartbeat_task = asyncio.create_task(heartbeat())
        try:
            result = await asyncio.to_thread(whisper_model.transcribe, audio_path)
        finally:
            stop_heartbeat.set()
            await heartbeat_task

        source_text = result["text"]
        segments = result["segments"]
        await update_status("✅ Transcription complete", 60)
        
        # 3. Script Analysis
        # 3. Studio Engine Analysis
        await update_status("🧠 Analyzing content strategy...", 70)
        studio = StudioEngine()
        
        # The UI sends target_duration in minutes.
        target_duration_mins = max(1, target_duration)
        
        # V17: Massive Parallelism Sprint
        print("⚡ Starting Parallel Studio Analysis...")
        
        if mission == "recreate" or mission == "shorts":
            print(f"🎬 Mission: {mission.upper()} - Using Synthesis/Rendering path (Genre: {genre})...")
            # V40: Pass full segments for precision timestamp tracking
            studio_script_data = en_recreator.condense_from_segments(segments, target_duration_mins=target_duration_mins, genre=genre)
            
            async def get_script():
                text = studio_script_data["text"]
                if target_lang != "en":
                    return await studio.translate_to_amharic(text, tone=tone) # Should ideally support other languages too
                return text

            studio_script_task = get_script()
            metadata_task = studio.generate_metadata_recommendations(Path(audio_path).stem, segments, target_lang, tone, genre=genre)
            editing_guide_task = en_recreator.extract_editing_roadmap(target_duration_mins)
        else:
            print(f"🌍 Mission: {mission.upper()} - Using Translation/Localization path...")
            studio_script_task = studio.translate_to_amharic(source_text, tone=tone)
            metadata_task = studio.generate_metadata_recommendations(Path(audio_path).stem, segments, target_lang, tone, genre=genre)
            editing_guide_task = studio.extract_editing_guide(segments, target_duration_mins, target_lang, tone, genre=genre)

        # Define all tasks (Directly await async ones, wrap sync ones in to_thread)
        tasks = {
            "studio_script": studio_script_task,
            "hooks": studio.generate_hooks(segments[:50], target_lang=target_lang),
            "thumbnail_data": studio.generate_thumbnail_prompt(Path(audio_path).stem, segments),
            "metadata": metadata_task,
            "chapters": studio.generate_chapters(segments),
            "shorts_clip": asyncio.to_thread(studio.shorts_clip_selector, segments),
            "growth_launchpad": studio.generate_community_posts(Path(audio_path).stem, segments),
            "social_thread": studio.generate_social_thread(source_text, target_lang=target_lang),
            "srt_content": studio.generate_srt(segments[:20], target_lang=target_lang),
            "editing_guide": editing_guide_task
        }
        
        # Run all concurrently
        results = await asyncio.gather(*tasks.values())
        results_map = dict(zip(tasks.keys(), results))
        print("✅ Massive Parallel Analysis complete.")

        result_data = {
            "english_script": source_text,
            "studio_script": results_map["studio_script"],
            "target_lang": target_lang,
            "editing_guide": results_map["editing_guide"],
            "viral_hooks": results_map["hooks"],
            "thumbnail_data": {"text_prompt": results_map["thumbnail_data"], "image_url": studio.generate_ai_image_url(results_map["thumbnail_data"])},
            "metadata": results_map["metadata"],
            "chapters": results_map["chapters"],
            "shorts_clip": results_map["shorts_clip"],
            "growth_launchpad": results_map["growth_launchpad"],
            "social_thread": results_map["social_thread"],
            "srt_content": results_map["srt_content"],
            "video_filename": Path(video_path).name,
            "target_duration": target_duration
        }

        # V22: Automated Video Editing Step
        print("🎬 Starting Automated Video Composition...")
        safe_stem = "".join([c if c.isalnum() else "_" for c in Path(audio_path).stem])[:50]
        composer = VideoComposer(self.base_dir / "assets/videos")
        try:
            rendered_video_path = await composer.compose_condensed_video(
                video_path, 
                results_map["editing_guide"], 
                f"rendered_{safe_stem}.mp4",
                status_callback=status_callback
            )
            result_data["rendered_video_path"] = rendered_video_path
            print(f"✅ Rendered Video Saved: {rendered_video_path}")
        except Exception as e:
            print(f"⚠️ Video Rendering Failed: {e}")
            result_data["rendered_video_path"] = None

        # Save result as JSON (Slugify filename to avoid Windows errors)
        output_file = self.base_dir / f"outputs/studio_{safe_stem}.json"
        
        print(f"Saving studio result to: {output_file}")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            print("Successfully saved JSON.")
        except Exception as e:
            print(f"CRITICAL: Failed to save JSON: {e}")
            # Save a minimal version if the full one fails
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({"error": "Serialization failed", "msg": str(e)}, f)
            
        await update_status(f"✨ STUDIO READY! Analysis saved.", 100)
        return str(output_file)

if __name__ == "__main__":
    creator = YouTubeAmharicCreator()
    url = input("🔗 Enter YouTube Link: ")
    if url.strip():
        asyncio.run(creator.process_video(url))
    else:
        print("❌ No URL provided. Exiting.")
