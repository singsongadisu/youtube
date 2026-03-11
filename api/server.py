from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
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

# Temporary uploads for transcription
UPLOAD_DIR = (ROOT_DIR / "assets" / "uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

from main import YouTubeStudioCreator
from processor.tts_engine import TTSEngine
from processor.db import DatabaseManager
from processor.creative_engine import CreativeEngine
from processor.downloader import VideoDownloader
from processor.transcribe_engine import TranscriptionEngine

app = FastAPI()

# Shared instances
creator = YouTubeStudioCreator()
db_manager = DatabaseManager()
creative_engine = CreativeEngine()
video_downloader = VideoDownloader(download_path=DOWNLOAD_DIR)
transcription_engine = TranscriptionEngine(model_name="base")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5000", "https://bnox.org", "http://bnox.org"],
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

# Track active tasks and their respective WebSockets
# format: { project_id: [websocket1, ...], ... }
active_tasks = {}

async def background_process(project_id: str, req: dict):
    """Background task to process video and update DB/WebSockets."""
    try:
        url = req.get("url")
        target_duration = req.get("duration", 5)
        target_lang = req.get("language", "am")
        target_tone = req.get("tone", "neutral")
        mission = req.get("mission", "translate")
        genre = req.get("genre", "sermon")

        async def status_callback(message, progress):
            # Update Database
            await db_manager.update_project_status(project_id, "processing", progress, message)
            
            # Broadcast to all connected WebSockets for this project
            if project_id in active_tasks:
                dead_sockets = []
                for ws in active_tasks[project_id]:
                    try:
                        await ws.send_json({
                            "status": "processing",
                            "message": message,
                            "progress": progress,
                            "project_id": project_id
                        })
                    except:
                        dead_sockets.append(ws)
                for ws in dead_sockets:
                    active_tasks[project_id].remove(ws)

        result_path = await creator.process_video(
            url,
            target_duration=target_duration,
            target_lang=target_lang,
            tone=target_tone,
            mission=mission,
            status_callback=status_callback
        )

        # Load results
        with open(result_path, "r", encoding="utf-8") as f:
            studio_data = json.load(f)

        # Final DB Update with full data
        studio_data["status"] = "completed"
        studio_data["progress"] = 100
        
        # Merge with existing doc (preserves _id)
        existing = await db_manager.get_project_by_id(project_id)
        if existing:
            studio_data["title"] = existing.get("title", studio_data.get("video_filename", "Untitled"))
            
        # Convert local path to Downloadable URL
        if studio_data.get("rendered_video_path"):
            filename = os.path.basename(studio_data["rendered_video_path"])
            studio_data["download_url"] = f"http://localhost:8000/static/videos/{filename}"
            studio_data["rendered_video_path"] = studio_data["download_url"]

        # Save result
        from bson import ObjectId
        await db_manager.projects.update_one({"_id": ObjectId(project_id)}, {"$set": studio_data})

        # Notify completion
        if project_id in active_tasks:
            for ws in active_tasks[project_id]:
                try:
                    await ws.send_json({
                        "status": "completed",
                        "message": "Studio analysis complete!",
                        "progress": 100,
                        "studio_data": studio_data,
                        "project_id": project_id
                    })
                except:
                    pass
            active_tasks.pop(project_id, None)

    except Exception as e:
        print(f"❌ Background Error for project {project_id}: {e}")
        await db_manager.update_project_status(project_id, "error", 0, f"Error: {str(e)}")
        if project_id in active_tasks:
            for ws in active_tasks[project_id]:
                try:
                    await ws.send_json({"status": "error", "message": str(e), "project_id": project_id})
                except: pass
            active_tasks.pop(project_id, None)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    current_project_id = None
    try:
        while True:
            data = await websocket.receive_text()
            req = json.loads(data)
            
            # Reconnection Logic
            reconnect_id = req.get("reconnect_id")
            if reconnect_id:
                current_project_id = reconnect_id
                if current_project_id not in active_tasks:
                    active_tasks[current_project_id] = []
                active_tasks[current_project_id].append(websocket)
                print(f"🔗 Reconnected to project: {current_project_id}")
                continue

            # New Task Logic
            url = req.get("url")
            if not url:
                await websocket.send_json({"error": "No URL provided"})
                continue
            
            # Create placeholder project in DB
            title = url.split('/')[-1] or "New Project"
            project_id = await db_manager.save_project({
                "title": title,
                "status": "processing",
                "progress": 0,
                "mission": req.get("mission"),
                "target_lang": req.get("language"),
                "url": url
            })
            
            current_project_id = project_id
            if project_id not in active_tasks:
                active_tasks[project_id] = []
            active_tasks[project_id].append(websocket)
            
            # Start background task
            asyncio.create_task(background_process(project_id, req))
            await websocket.send_json({"status": "started", "project_id": project_id})

    except WebSocketDisconnect:
        print(f"WebSocket Disconnected for project: {current_project_id}")
        if current_project_id and current_project_id in active_tasks:
            try: active_tasks[current_project_id].remove(websocket)
            except: pass
    except Exception as e:
        print(f"WS Error: {e}")
    finally:
        if current_project_id and current_project_id in active_tasks:
            try: active_tasks[current_project_id].remove(websocket)
            except: pass
        try:
            await websocket.close()
        except:
            pass

@app.post("/generate-tts")
async def generate_tts(req: dict):
    text = req.get("text")
    lang = req.get("lang", "en")
    narrator_id = req.get("narratorId")
    persona = req.get("persona")
    tone = req.get("tone", "neutral")
    import time
    filename = req.get("filename", f"tts_{int(time.time())}.mp3")

    # Map narratorId to persona if not provided
    narrator_personas = {
        "guy": "anchor", 
        "aria": "studio_pro", 
        "chris": "expert", 
        "eric": "reporter", 
        "jenny": "specialist", 
        "sonia": "global_voice"
    }
    if not persona and narrator_id in narrator_personas:
        persona = narrator_personas[narrator_id]

    gender = req.get("gender", "female")
    narrators_map = {"guy": "male", "aria": "female", "ameha": "male", "mekdes": "female", "chris": "expert", "eric": "reporter", "jenny": "specialist", "sonia": "global"}
    if narrator_id in narrators_map: gender = narrators_map[narrator_id]
    
    tts = TTSEngine(output_dir=ROOT_DIR / "assets/audio")
    path = await tts.generate_speech(text, lang=lang, gender=gender, tone=tone, persona=persona, filename=filename)
    
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

@app.delete("/project/{project_id}")
async def delete_project(project_id: str):
    try:
        await db_manager.delete_project(project_id)
        return {"status": "success", "message": "Project deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/narrators")
async def get_narrators():
    return [
        {"id": "guy", "name": "Guy (Anchor)", "lang": "en", "gender": "male", "role": "News Anchor", "avatar": "/narrators/guy_pro.png", "persona": "anchor"},
        {"id": "aria", "name": "Aria (Narrator)", "lang": "en", "gender": "female", "role": "Storyteller", "avatar": "/narrators/aria_pro.png", "persona": "studio_pro"},
        {"id": "chris", "name": "Christopher (Expert)", "lang": "en", "gender": "expert", "role": "Technical Expert", "avatar": "/narrators/chris_pro.png", "persona": "expert"},
        {"id": "eric", "name": "Eric (Reporter)", "lang": "en", "gender": "reporter", "role": "Field Reporter", "avatar": "/narrators/eric_pro.png", "persona": "reporter"},
        {"id": "jenny", "name": "Jenny (Specialist)", "lang": "en", "gender": "specialist", "role": "AI Tutor", "avatar": "/narrators/jenny_pro.png", "persona": "specialist"},
        {"id": "sonia", "name": "Sonia (Global)", "lang": "en", "gender": "global", "role": "International Voice", "avatar": "/narrators/sonia_pro.png", "persona": "global_voice"},
        {"id": "ameha", "name": "Ameha", "lang": "am", "gender": "male", "role": "Wise Elder", "avatar": "/narrators/ameha_pro.png"},
        {"id": "mekdes", "name": "Mekdes", "lang": "am", "gender": "female", "role": "Warm Teacher", "avatar": "/narrators/mekdes_pro.png"}
    ]

@app.post("/approve-creative-project")
async def approve_creative_project(req: dict):
    # ... (keep same logic for audio/storyboard)
    script = req.get("script")
    lang = req.get("lang", "en")
    narrator_id = req.get("narratorId")
    persona = req.get("persona") # New: allow direct persona passing
    
    # Fallback/Mapping if persona not direct
    narrator_personas = {
        "guy": "anchor", 
        "aria": "studio_pro", 
        "chris": "expert", 
        "eric": "reporter", 
        "jenny": "specialist", 
        "sonia": "global_voice"
    }
    if not persona and narrator_id in narrator_personas:
        persona = narrator_personas[narrator_id]

    gender = "female"
    narrators = {"guy": "male", "aria": "female", "ameha": "male", "mekdes": "female", "chris": "expert", "eric": "reporter", "jenny": "specialist", "sonia": "global"}
    if narrator_id in narrators: gender = narrators[narrator_id]

    tts_engine = TTSEngine(output_dir=ROOT_DIR / "assets/audio")
    audio_path = await tts_engine.generate_speech(
        script, 
        lang=lang, 
        gender=gender, 
        persona=persona, 
        filename="creative_narration.mp3"
    )
    
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

@app.post("/transcribe")
async def transcribe_file(file: UploadFile = File(...)):
    """
    Receives an audio/video file, transcribes it, and returns text + SRT.
    """
    try:
        # Save uploaded file
        import time
        file_ext = os.path.splitext(file.filename)[1]
        temp_filename = f"transcribe_{int(time.time())}{file_ext}"
        file_path = UPLOAD_DIR / temp_filename
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Transcribe in a separate thread to avoid blocking the event loop
        result = await asyncio.to_thread(transcription_engine.transcribe_sync, str(file_path))
        
        # Cleanup
        try: os.remove(file_path)
        except: pass
            
        return {
            "status": "success",
            "text": result["text"],
            "srt": result["srt"],
            "language": result["language"]
        }
    except Exception as e:
        print(f"Transcription Error: {e}")
        return {"status": "error", "message": str(e)}

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
