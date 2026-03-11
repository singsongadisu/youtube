import asyncio
import edge_tts
import subprocess
import os
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
                "female": "en-US-AriaNeural",
                "expert": "en-US-ChristopherNeural",
                "reporter": "en-US-EricNeural",
                "specialist": "en-US-JennyNeural",
                "global": "en-GB-SoniaNeural"
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

        # Personas map a logical role to a voice + tone combo
        self.personas = {
            "anchor": {"gender": "male", "tone": "cyber_news", "desc": "Main news anchor, authoritative & fast"},
            "expert": {"gender": "expert", "tone": "studio_pro", "desc": "Technical deep-diver, calm & professional"},
            "reporter": {"gender": "reporter", "tone": "news", "desc": "On-the-ground reporting style"},
            "specialist": {"gender": "specialist", "tone": "studio_pro", "desc": "Friendly, tutorial-style guidance"},
            "global_voice": {"gender": "global", "tone": "storytelling", "desc": "Sophisticated international perspective"}
        }

    def _humanize_ssml(self, text: str, voice: str, rate: str = "+0%", pitch: str = "+0Hz") -> str:
        """
        Wraps plain text into SSML with natural pauses and prosody.
        """
        # Clean text and handle basic punctuation for pauses
        # . -> 300ms pause, , -> 150ms pause, !/? -> 200ms pause
        humanized = text.replace(". ", ". <break time='400ms'/>") # Slightly longer for anchor
        humanized = humanized.replace(", ", ", <break time='200ms'/>")
        humanized = humanized.replace("! ", "! <break time='250ms'/>")
        humanized = humanized.replace("? ", "? <break time='300ms'/>")
        
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
            <voice name='{voice}'>
                <prosody rate='{rate}' pitch='{pitch}'>
                    {humanized}
                </prosody>
            </voice>
        </speak>
        """
        return ssml

    async def _post_process_audio(self, input_path: Path):
        """
        Uses FFmpeg to normalize and compress audio for a 'Studio' feel.
        """
        output_path = input_path.with_name(f"processed_{input_path.name}")
        
        # FFmpeg filters:
        # loudnorm: EBU R128 loudness normalization
        # acompressor: Add some punch/consistency
        # volume: Final gain adjustment
        cmd = [
            "ffmpeg", "-y", "-i", str(input_path),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,acompressor=threshold=-18dB:ratio=3:attack=5:release=50",
            "-codec:a", "libmp3lame", "-q:a", "2",
            str(output_path)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Replace original with processed
                if output_path.exists():
                    os.replace(output_path, input_path)
                    return True
                return False
            else:
                print(f"FFmpeg Error: {stderr.decode()}")
                return False
        except Exception as e:
            print(f"Post-processing failed: {e}")
            return False

    async def generate_speech(self, text: str, lang: str = 'en', gender: str = 'female', tone: str = 'neutral', persona: str = None, filename: str = "narration.mp3"):
        if not text:
            return None

        # Resolve Persona if provided
        if persona and persona in self.personas:
            p_config = self.personas[persona]
            gender = p_config["gender"]
            tone = p_config["tone"]
            
        # Select the correct neural voice
        voice_map = self.voices.get(lang, self.voices["en"])
        voice = voice_map.get(gender, voice_map.get("female"))
        
        # Adjust prosody based on Tone/Vibe
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
            rate = "-15%"
            pitch = "-1Hz"
        elif tone == "studio_pro":
            # For the new Cyber Insights channel: Professional yet engaging
            rate = "+3%"
            pitch = "+0Hz"
        elif tone == "cyber_news":
            # Fast-paced, authoritative, news-style
            rate = "+10%"
            pitch = "+1Hz"

        ssml = self._humanize_ssml(text, voice, rate, pitch)

        try:
            output_path = self.output_dir / filename
            communicate = edge_tts.Communicate(ssml, voice)
            await communicate.save(str(output_path))
            
            # Post-process for that "Model" voice quality
            await self._post_process_audio(output_path)
            
            return str(output_path)
        except Exception as e:
            print(f"Edge-TTS Error: {e}")
            return None

if __name__ == "__main__":
    # Test
    # engine = TTSEngine()
    # asyncio.run(engine.generate_speech("Security update: A new critical vulnerability was found.", lang='en', persona='anchor', filename="persona_anchor.mp3"))
    pass
