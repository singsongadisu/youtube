import os
from moviepy import VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip
import requests
from pathlib import Path
import asyncio

class VideoComposer:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir = output_dir.parent / "temp_assets"
        self.assets_dir.mkdir(parents=True, exist_ok=True)

    async def download_image(self, url: str, filename: str, max_retries: int = 3) -> Path:
        """Downloads an image with exponential backoff and seed jiggling on failure."""
        target_path = self.assets_dir / filename
        if target_path.exists() and target_path.stat().st_size > 0:
            return target_path
            
        loop = asyncio.get_event_loop()
        
        for attempt in range(max_retries):
            # Jiggle seed if retrying
            current_url = url
            if attempt > 0:
                import random
                # Replace existing seed or append new one
                if "seed=" in url:
                    import re
                    current_url = re.sub(r"seed=\d+", f"seed={random.randint(1, 9999)}", url)
                else:
                    current_url += f"&seed={random.randint(1, 9999)}"

            def _download():
                try:
                    response = requests.get(current_url, stream=True, timeout=60)
                    if response.status_code == 200:
                        with open(target_path, "wb") as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        if target_path.exists() and target_path.stat().st_size > 0:
                            return target_path
                    return None # Signal failure
                except Exception as e:
                    print(f"Download attempt {attempt+1} failed: {e}")
                    return None

            result = await loop.run_in_executor(None, _download)
            if result:
                return target_path
                
            # Wait with backoff
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"Retrying download in {wait_time}s... (Attempt {attempt+2})")
                await asyncio.sleep(wait_time)

        raise Exception(f"Failed to download image after {max_retries} attempts for: {url}")

    async def compose_condensed_video(self, source_video_path: str, editing_guide: list, output_filename: str, status_callback=None):
        """
        Automates the video editing process:
        1. Cuts clips from the source video based on the roadmap.
        2. Overlays AI images for visual prompts.
        3. Collates everything into a final file.
        """
        if status_callback: await status_callback("🎞️ Loading source video...", 75)
        
        video = VideoFileClip(source_video_path)
        clips = []
        
        for i, item in enumerate(editing_guide):
            # Precision V40: Use timestamp_start/end if available, else fallback to MM:SS
            if "timestamp_start" in item and "timestamp_end" in item:
                # Format: MM:SS
                m1, s1 = map(int, item["timestamp_start"].split(":"))
                m2, s2 = map(int, item["timestamp_end"].split(":"))
                start_sec = m1 * 60 + s1
                end_sec = m2 * 60 + s2
            else:
                start_str = item["timestamp"]
                # Convert MM:SS to seconds
                m, s = map(int, start_str.split(":"))
                start_sec = m * 60 + s
                duration = 5 
                end_sec = min(start_sec + duration, video.duration)
            
            if status_callback:
                progress = 75 + int((i / len(editing_guide)) * 20)
                await status_callback(f"🎬 Processing clip {i+1}/{len(editing_guide)}...", progress)

            # Subclip from original
            if hasattr(video, "subclipped"):
                subclip = video.subclipped(start_sec, end_sec)
            else:
                subclip = video.subclip(start_sec, end_sec)
            
            # If there's a visual prompt, download and overlay an image as a B-roll
            # For simplicity in V22, we use the image_url if provided in a later step 
            # or generate on the fly for specific moments.
            # Here we just prepare the concatenation.
            clips.append(subclip)

        if status_callback: await status_callback("🏗️ Rendering final composite...", 95)
        
        final_video = concatenate_videoclips(clips, method="compose")
        target_path = self.output_dir / output_filename
        
        # Rendering is CPU intensive, run in executor
        loop = asyncio.get_event_loop()
        def _render():
            final_video.write_videofile(str(target_path), codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)
            return target_path
            
        result_path = await loop.run_in_executor(None, _render)
        
        # Cleanup
        video.close()
        final_video.close()
        
        return str(result_path)

    async def render_forge_video(self, audio_path: str, segments: list, output_filename: str, bg_music_genre: str = None, status_callback=None):
        """
        V10 CINEMA: Stable & High-Quality Rendering Engine.
        """
        from moviepy import AudioFileClip, ImageClip, ColorClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip
        import numpy as np
        import asyncio

        async def _safe_status(msg, progress):
            if status_callback:
                try:
                    if asyncio.iscoroutinefunction(status_callback):
                        await status_callback(msg, progress)
                    else:
                        status_callback(msg, progress)
                except Exception as e:
                    print(f"Callback error: {e}")
            print(f"[{progress}%] {msg}")

        await _safe_status("🎨 Preparing Cinematic Canvas...", 10)
        
        try:
            narration_audio = AudioFileClip(audio_path)
            print(f"✅ Audio Loaded: {narration_audio.duration}s")
        except Exception as e:
            print(f"❌ Audio Load Failed: {e}")
            raise Exception(f"Audio Load Error: {e}")

        visual_clips = []
        
        # Ensure segments
        if not segments:
            segments = [{"title": "Cinematic Story", "text": "...", "duration": f"{int(narration_audio.duration)}s"}]

        for i, seg in enumerate(segments):
            await _safe_status(f"🖼️ Scene {i+1}: {seg.get('title', '...')}", 10 + int((i / len(segments)) * 60))
            
            # Duration logic
            try:
                dur_raw = str(seg.get('duration', '5s'))
                dur_s = float(dur_raw.replace('s', ''))
                if dur_s <= 0: dur_s = 2.0
            except:
                dur_s = 5.0

            # Image Download
            prompt_src = seg.get('title', seg.get('text', 'Cinematic scene'))[:120]
            clean_p = prompt_src.replace("\n", " ").strip()
            import urllib.parse
            encoded = urllib.parse.quote(clean_p)
            # Use hash for variety but preserve order with i
            img_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={hash(clean_p + str(i)) % 10000}"
            
            try:
                img_path = await self.download_image(img_url, f"forge_v10_{i}_{hash(clean_p) % 100}.png")
                # Create Clip
                img_clip = ImageClip(str(img_path)).with_duration(dur_s).with_fps(24)
                # Ensure 1280x720 via background composition
                canvas = ColorClip(size=(1280, 720), color=(25, 25, 25)).with_duration(dur_s).with_fps(24)
                img_clip = img_clip.with_position("center")
                scene = CompositeVideoClip([canvas, img_clip], size=(1280, 720))
                
            except Exception as e:
                print(f"⚠️ Scene Generation fallback: {e}")
                scene = ColorClip(size=(1280, 720), color=(30, 30, 30)).with_duration(dur_s).with_fps(24)

            # Simple Crossfade attempt (MoviePy v2 style)
            if i > 0:
                try:
                    scene = scene.with_crossfadein(0.5)
                except:
                    pass
            
            visual_clips.append(scene)

        # Concatenate
        await _safe_status("🏗️ Assembling Master Sequence...", 80)
        # Use simple concatenation (padding for overlap if MoviePy supports it)
        final_video = concatenate_videoclips(visual_clips, method="compose")
        
        # Audio Mixing
        final_audio = narration_audio
        audio_dir = self.assets_dir.parent / "audio"
        bg_candidates = list(audio_dir.glob("bg_*.mp3")) + list(audio_dir.glob("*.mp3"))
        bg_path = next((c for c in bg_candidates if "narration" not in c.name.lower()), None)
        
        if bg_path:
            try:
                bg_music = AudioFileClip(str(bg_path)).multiply_volume(0.12)
                if bg_music.duration < narration_audio.duration:
                    from moviepy.audio.fx.all import audio_loop
                    bg_music = audio_loop(bg_music, duration=narration_audio.duration)
                else:
                    bg_music = bg_music.with_duration(narration_audio.duration)
                from moviepy import CompositeAudioClip
                final_audio = CompositeAudioClip([narration_audio, bg_music])
            except:
                pass

        final_video = final_video.with_audio(final_audio)
        
        # Final safety check: ensure duration matches audio
        if final_video.duration != narration_audio.duration:
             final_video = final_video.with_duration(narration_audio.duration)

        target_path = self.output_dir / output_filename
        await _safe_status("🚀 Rendering High-Quality Master...", 90)
        
        loop = asyncio.get_event_loop()
        def _render():
            final_video.write_videofile(
                str(target_path), 
                codec="libx264", 
                audio_codec="aac", 
                fps=24,
                threads=4,
                logger=None,
                preset="ultrafast" # Speed up testing
            )
            return target_path
            
        result_path = await loop.run_in_executor(None, _render)
        
        # Cleanup
        narration_audio.close()
        final_video.close()
        for c in visual_clips: c.close()
        
        return str(result_path)
