import whisper
import os
from pathlib import Path

class Transcriber:
    def __init__(self, model_size: str = "base"):
        """
        Initializes the Whisper model.
        Model sizes: tiny, base, small, medium, large
        """
        print(f"Loading Whisper model '{model_size}'...")
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path: str):
        """Transcribes audio file to text."""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print(f"Transcribing {audio_path}...")
        result = self.model.transcribe(audio_path)
        return result["text"]

    def transcribe_to_file(self, audio_path: str, output_path: str):
        """Transcribes audio and saves it to a text file."""
        text = self.transcribe(audio_path)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return output_path

if __name__ == "__main__":
    # Example usage
    # transcriber = Transcriber()
    # text = transcriber.transcribe("assets/downloads/sample.mp3")
    # print(text)
    pass
