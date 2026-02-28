from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path so we can import modules
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# Directory setup (Absolute paths)
VIDEO_DIR = (ROOT_DIR / "assets" / "videos").resolve()
DOWNLOAD_DIR = (ROOT_DIR / "assets" / "downloads").resolve()
AUDIO_DIR = (ROOT_DIR / "assets" / "audio").resolve()

VIDEO_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

from main import YouTubeAmharicCreator
from processor.tts_engine import TTSEngine
from processor.db import DatabaseManager
from processor.creative_engine import CreativeEngine
from processor.downloader import VideoDownloader

app = FastAPI()

# Shared instances
creator = YouTubeAmharicCreator()
db_manager = DatabaseManager()
creative_engine = CreativeEngine()
video_downloader = VideoDownloader(download_path=DOWNLOAD_DIR)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/videos")
async def list_videos():
    # Fetch from MongoDB instead of scanning folder
    projects = await db_manager.get_all_projects()
    return projects

@app.get("/project/{project_id}")
async def get_project(project_id: str):
    project = await db_manager.get_project_by_id(project_id)
    if project:
        return project
    return {"error": "Project not found"}

@app.websocket("/ws/process")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        req = json.loads(data)
        url = req.get("url")
        target_duration = req.get("duration", 5) 
        target_lang = req.get("language", "am")
        target_tone = req.get("tone", "neutral")
        mission = req.get("mission", "translate")
        genre = req.get("genre", "sermon")
        
        if not url:
            await websocket.send_json({"error": "No URL provided"})
            return
        
        async def send_status(message, progress):
            try:
                await websocket.send_json({
                    "status": "processing",
                    "message": message,
                    "progress": progress
                })
            except Exception as e:
                print(f"Failed to send status: {e}")

        try:
            result_path = await creator.process_video(
                url, 
                target_duration=target_duration, 
                target_lang=target_lang,
                tone=target_tone,
                mission=mission,
                status_callback=send_status
            )
            
            # Load the studio result JSON
            with open(result_path, "r", encoding="utf-8") as f:
                studio_data = json.load(f)

            # SAVE TO MONGODB
            project_id = await db_manager.save_project(studio_data)
            studio_data["mongodb_id"] = project_id
            
            # Convert local path to Downloadable URL
            if studio_data.get("rendered_video_path"):
                filename = os.path.basename(studio_data["rendered_video_path"])
                studio_data["download_url"] = f"http://localhost:8000/static/videos/{filename}"
                studio_data["rendered_video_path"] = studio_data["download_url"] # Compatibility
                
            if "_id" in studio_data:
                del studio_data["_id"] # ObjectId is not JSON serializable
            if "created_at" in studio_data and hasattr(studio_data["created_at"], "isoformat"):
                studio_data["created_at"] = studio_data["created_at"].isoformat()

            await websocket.send_json({
                "status": "completed",
                "message": "Studio analysis complete! Saved to MongoDB.",
                "progress": 100,
                "studio_data": studio_data
            })
            print(f"✅ Saved to MongoDB with ID: {project_id}")
        except Exception as e:
            # ... (error handling keep same)
            print(f"❌ Server Error during WS processing: {e}")
            try:
                await websocket.send_json({
                    "status": "error",
                    "message": f"Server Error: {str(e)}"
                })
            except:
                pass
            
    except WebSocketDisconnect:
        print("WebSocket Disconnected")
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

@app.post("/generate-tts")
async def generate_tts(req: dict):
    text = req.get("text")
    lang = req.get("lang", "am")
    gender = req.get("gender", "female")
    tone = req.get("tone", "neutral")
    filename = req.get("filename", "narration.mp3")
    
    tts = TTSEngine(output_dir=ROOT_DIR / "assets/audio")
    path = await tts.generate_speech(text, lang, gender, tone, filename)
    
    if path:
        return {"url": f"http://localhost:8000/static/audio/{filename}"}
    return {"error": "TTS Generation Failed"}

@app.post("/generate-creative-script")
async def generate_creative_script(req: dict):
    idea = req.get("idea")
    duration = int(req.get("duration", 3))
    lang = req.get("lang", "en")
    
    result = await creative_engine.generate_script(idea, duration, lang)
    return result

@app.post("/refine-script")
async def refine_script(req: dict):
    script = req.get("script")
    style = req.get("style", "viral")
    refined = await creative_engine.refine_script(script, style)
    return {"script": refined}

@app.get("/narrators")
async def get_narrators():
    return [
        {"id": "guy", "name": "Guy", "lang": "en", "gender": "male", "role": "Professional Narrator", "avatar": "/narrators/guy_pro.png"},
        {"id": "aria", "name": "Aria", "lang": "en", "gender": "female", "role": "Calm Storyteller", "avatar": "/narrators/aria_pro.png"},
        {"id": "ameha", "name": "Ameha", "lang": "am", "gender": "male", "role": "Wise Elder", "avatar": "/narrators/ameha_pro.png"},
        {"id": "mekdes", "name": "Mekdes", "lang": "am", "gender": "female", "role": "Warm Teacher", "avatar": "/narrators/mekdes_pro.png"},
        {"id": "hamed", "name": "Hamed", "lang": "ar", "gender": "male", "role": "Cultural Guide", "avatar": "/narrators/hamed_pro.png"},
        {"id": "zariyah", "name": "Zariyah", "lang": "ar", "gender": "female", "role": "Faithful Voice", "avatar": "/narrators/zariyah_pro.png"},
        {"id": "alvaro", "name": "Alvaro", "lang": "es", "gender": "male", "role": "Engaging Host", "avatar": "/narrators/alvaro_pro.png"},
        {"id": "elvira", "name": "Elvira", "lang": "es", "gender": "female", "role": "Lyrical Soul", "avatar": "/narrators/elvira_pro.png"},
        {"id": "henri", "name": "Henri", "lang": "fr", "gender": "male", "role": "Distinguished Voice", "avatar": "/narrators/henri_pro.png"},
        {"id": "denise", "name": "Denise", "lang": "fr", "gender": "female", "role": "Articulate Artist", "avatar": "/narrators/denise_pro.png"}
    ]

@app.post("/approve-creative-project")
async def approve_creative_project(req: dict):
    # ... (keep same logic for audio/storyboard)
    script = req.get("script")
    lang = req.get("lang", "en")
    narrator_id = req.get("narratorId")
    segments = req.get("segments", [])
    idea = req.get("idea", "Creative Project")
    
    gender = "female"
    narrators = {"guy": "male", "aria": "female", "ameha": "male", "mekdes": "female", "hamed": "male", "zariyah": "female", "alvaro": "male", "elvira": "female", "henri": "male", "denise": "female"}
    if narrator_id in narrators: gender = narrators[narrator_id]

    tts_engine = TTSEngine(output_dir=ROOT_DIR / "assets/audio")
    audio_path = await tts_engine.generate_speech(script, lang=lang, gender=gender, tone="storytelling", filename="creative_narration.mp3")
    
    storyboard = []
    for i, seg in enumerate(segments[:6]):
        prompt = await creative_engine.studio.generate_visual_prompt(seg["text"])
        storyboard.append({"timestamp": seg["timestamp"], "title": seg["title"], "prompt": prompt})
    
    if audio_path:
        return {
            "audio_url": f"http://localhost:8000/static/audio/creative_narration.mp3",
            "storyboard": storyboard,
            "audio_path": str(audio_path) # Send absolute path for rendering step
        }
    return {"error": "Asset generation failed"}

@app.post("/generate-forge-video")
async def generate_forge_video(req: dict):
    audio_path = req.get("audio_path")
    segments = req.get("segments", [])
    bg_music_genre = req.get("bg_music", "explainer")
    
    if not audio_path or not segments:
        return {"error": "Missing audio_path or segments"}
    
    from processor.video_composer import VideoComposer
    composer = VideoComposer(ROOT_DIR / "assets/videos")
    
    safe_name = f"forge_video_{hash(audio_path) % 10000}.mp4"
    try:
        # Long running task
        rendered_path = await composer.render_forge_video(
            audio_path, 
            segments, 
            safe_name, 
            bg_music_genre=bg_music_genre
        )
        return {
            "video_url": f"http://localhost:8000/static/videos/{safe_name}",
            "filename": safe_name
        }
    except Exception as e:
        print(f"Rendering error: {e}")
        return {"error": str(e)}

@app.get("/video-info")
async def get_video_info(url: str):
    if not url:
        return {"error": "No URL provided"}
    # Use to_thread to prevent blocking the event loop
    info = await asyncio.to_thread(video_downloader.get_video_info, url)
    return info

@app.post("/download-social")
async def download_social(req: dict):
    url = req.get("url")
    format_id = req.get("format_id")
    if not url:
        return {"error": "No URL provided"}
    
    try:
        # Use to_thread to prevent blocking the event loop for long downloads
        file_path = await asyncio.to_thread(video_downloader.download_video, url, format_id)
        filename = os.path.basename(file_path)
        return {
            "status": "completed",
            "filename": filename,
            "download_url": f"http://localhost:8000/static/downloads/{filename}"
        }
    except Exception as e:
        return {"error": str(e)}

# Serve static files for generated videos, downloads, and audio

app.mount("/static/videos", StaticFiles(directory=str(VIDEO_DIR)), name="static_videos")
app.mount("/static/downloads", StaticFiles(directory=str(DOWNLOAD_DIR)), name="static_downloads")
app.mount("/static/audio", StaticFiles(directory=str(AUDIO_DIR)), name="static_audio")

@app.get("/download-file")
async def download_file(type: str, filename: str):
    """Securely returns a file as an attachment to force browser download."""
    if type == "video":
        path = VIDEO_DIR / filename
    elif type == "download":
        path = DOWNLOAD_DIR / filename
    elif type == "audio":
        path = AUDIO_DIR / filename
    else:
        return {"error": "Invalid type"}
    
    if not path.exists():
        return {"error": "File not found"}
    
    # Setting filename here forces 'Content-Disposition: attachment'
    return FileResponse(path, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
