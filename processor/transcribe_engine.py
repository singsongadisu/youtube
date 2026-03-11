import os
import whisper
from pathlib import Path
import datetime

class TranscriptionEngine:
    def __init__(self, model_name="base"):
        """
        Initializes the Whisper model.
        'base' is a good balance between speed and accuracy.
        """
        print(f"Loading Whisper model: {model_name}...")
        self.model = whisper.load_model(model_name)

    def format_timestamp(self, seconds: float) -> str:
        """
        Formats seconds into SRT timestamp format: HH:MM:SS,mmm
        """
        td = datetime.timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        millis = int((seconds - total_seconds) * 1000)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def transcribe_sync(self, file_path: str):
        """
        Transcribes the given audio/video file and returns raw text and SRT content.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"Whisper processing: {file_path}")
        # Transcribe (Whisper runs in a thread, but we can call it directly)
        result = self.model.transcribe(file_path, verbose=False)
        
        raw_text = result["text"].strip()
        segments = result["segments"]
        
        # Generate SRT content
        srt_lines = []
        for i, segment in enumerate(segments, start=1):
            start = self.format_timestamp(segment["start"])
            end = self.format_timestamp(segment["end"])
            text = segment["text"].strip()
            srt_lines.append(f"{i}")
            srt_lines.append(f"{start} --> {end}")
            srt_lines.append(f"{text}\n")
            
        srt_content = "\n".join(srt_lines)
        
        return {
            "text": raw_text,
            "srt": srt_content,
            "language": result.get("language")
        }

if __name__ == "__main__":
    # Quick test if run directly
    import asyncio
    async def test():
        engine = TranscriptionEngine()
        # Ensure you have a test.mp3 or similar in the current dir for this to work
        try:
            res = await engine.transcribe("test.mp3")
            print("Transcription Success!")
            print(res["text"][:100])
        except Exception as e:
            print(f"Test failed: {e}")
    
    # asyncio.run(test())
    pass
