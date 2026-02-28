import asyncio
import edge_tts
from pathlib import Path

class TTSEngine:
    def __init__(self, output_dir: str = "assets/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Free Neural Voices from Microsoft Edge
        self.voices = {
            "am": {
                "male": "am-ET-AmehaNeural",
                "female": "am-ET-MekdesNeural"
            },
            "en": {
                "male": "en-US-GuyNeural",
                "female": "en-US-AriaNeural"
            },
            "ar": {
                "male": "ar-SA-HamedNeural",
                "female": "ar-SA-ZariyahNeural"
            },
            "es": {
                "male": "es-ES-AlvaroNeural",
                "female": "es-ES-ElviraNeural"
            },
            "fr": {
                "male": "fr-FR-HenriNeural",
                "female": "fr-FR-DeniseNeural"
            }
        }

    async def generate_speech(self, text: str, lang: str = 'am', gender: str = 'female', tone: str = 'neutral', filename: str = "narration.mp3"):
        if not text:
            return None
            
        # Select the correct neural voice
        voice = self.voices.get(lang, self.voices["en"]).get(gender, self.voices["en"]["female"])
        
        # Adjust prosody based on Tone/Vibe
        # Viral: Fast, slightly high pitch
        # Preaching: Slow, deep pitch
        # News: Steady, professional
        rate = "+0%"
        pitch = "+0Hz"
        
        if tone == "viral":
            rate = "+15%"
            pitch = "+2Hz"
        elif tone == "preaching":
            rate = "-10%"
            pitch = "-3Hz"
        elif tone == "news":
            rate = "+5%"
            pitch = "+0Hz"
        elif tone == "storytelling":
            # Storytelling: Slower, more rhythmic, slightly lower pitch for "gravity"
            rate = "-15%"
            pitch = "-1Hz"
            # We can also add volume or other SSML-like hints if edge-tts supports them
            # For now, rate and pitch are the primary levers.


        try:
            output_path = self.output_dir / filename
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await communicate.save(str(output_path))
            return str(output_path)
        except Exception as e:
            print(f"Edge-TTS Error: {e}")
            return None

if __name__ == "__main__":
    # Test
    engine = TTSEngine()
    # engine.generate_speech("ሰላም፣ እንዴት ነህ?", lang='am', filename="test_am.mp3")
    pass
