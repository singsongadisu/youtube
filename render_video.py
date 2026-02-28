import asyncio
import json
from pathlib import Path
from processor.video_composer import VideoComposer

async def render_from_json(json_path: str):
    if not Path(json_path).exists():
        print(f"❌ Error: {json_path} not found.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Resolve source video path
    source_video = Path("assets/downloads") / data["video_filename"]
    if not source_video.exists():
        # Try finding any mp4 in downloads if name mismatch
        print(f"⚠️ {source_video} not found, searching downloads folder...")
        found = list(Path("assets/downloads").glob("*.mp4"))
        if found:
            source_video = found[0]
            print(f"📌 Using: {source_video}")
        else:
            print("❌ Error: Original video source not found in assets/downloads.")
            return

    guide = data["editing_guide"]
    
    print(f"🎬 Manually rendering video from {json_path}...")
    composer = VideoComposer(Path("assets/videos"))
    
    output_name = f"manual_render_{Path(json_path).stem}.mp4"
    path = await composer.compose_condensed_video(
        str(source_video), 
        guide, 
        output_name,
        status_callback=lambda msg, prog: print(f"[{prog}%] {msg}")
    )
    print(f"\n✅ Video successfully rendered at: {path}")

if __name__ == "__main__":
    # You can change this path to any studio JSON you've generated
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "outputs/studio_Prayer___Fasting__Dr__Myles_Munroe_s_Guide_To_Spir.json"
    asyncio.run(render_from_json(target))
