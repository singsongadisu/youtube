import asyncio
import re
from pathlib import Path

class EnglishVideoRecreator:
    def __init__(self, studio_engine=None):
        """
        🧬 V40: Precision English Recreator
        Focuses on exact timestamp mapping and sequential 'from-to' editing.
        """
        self.studio = studio_engine
        self.selected_segments = []

    def _format_timestamp(self, seconds: float) -> str:
        """Converts seconds to MM:SS format."""
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m:02d}:{s:02d}"

    def condense_from_segments(self, segments: list, target_duration_mins: int = 5) -> dict:
        """
        🧬 V41: Segment-Aware Condensation
        Analyzes Whisper segments directly to preserve timing.
        Returns both condensed text AND the mapping of segments used.
        """
        if not segments: return {"text": "", "clips": []}
        
        # 1. Cleaner: Define filler removal
        fillers = [
            r"\b(you know)\b", r"\b(i mean)\b", r"\b(basically)\b", 
            r"\b(actually)\b", r"\b(literally)\b", r"\b(to be honest)\b", 
            r"\b(obviously)\b", r"\b(kind of)\b", r"\b(sort of)\b"
        ]
        
        stop_words = {"the", "is", "at", "which", "on", "and", "to", "of", "a", "in", "that", "it", "with", "from", "for"}
        
        # 2. Score Segments individually
        scored_segments = []
        for seg in segments:
            text = seg['text'].strip()
            if not text: continue
            
            # Clean text for scoring
            clean_text = text
            for pattern in fillers:
                clean_text = re.sub(pattern + r"[,]?\s*", "", clean_text, flags=re.IGNORECASE)
            
            words = [w.strip(",.").lower() for w in clean_text.split()]
            if len(words) < 3: continue
            
            # Density Score
            content_words = [w for w in words if w not in stop_words]
            density = len(content_words) / (len(words) ** 0.8)
            
            # Action Starter Bonus
            action_starters = ["imagine", "discover", "learn", "stop", "how", "why", "here", "why", "what"]
            multiplier = 1.3 if words[0] in action_starters else 1.0
            
            duration = seg['end'] - seg['start']
            
            scored_segments.append({
                "original": seg,
                "clean_text": clean_text,
                "score": density * multiplier,
                "duration": duration,
                "start_time": seg['start'],
                "end_time": seg['end']
            })

        # 3. Selection Strategy (Greedy Density Selection)
        MAX_SECONDS = target_duration_mins * 60
        # Sort by score to find the highlights
        ranked = sorted(scored_segments, key=lambda x: x['score'], reverse=True)
        
        selection = []
        current_duration = 0
        
        for item in ranked:
            if current_duration + item['duration'] <= MAX_SECONDS:
                selection.append(item)
                current_duration += item['duration']
            if current_duration >= MAX_SECONDS:
                break
        
        # 4. Sequential Order (Keep the flow of the video)
        final_clips = sorted(selection, key=lambda x: x['start_time'])
        self.selected_segments = final_clips # Store for roadmap generation
        
        full_text = ". ".join([c['clean_text'] for c in final_clips])
        
        return {
            "text": full_text + ".",
            "clips_count": len(final_clips),
            "total_duration": current_duration
        }

    async def generate_metadata(self, title: str, condensed_text: str):
        """Generates high-CTR English titles and descriptions."""
        theme = title if title else "Insightful Session"
        
        titles = [
            f"THE TRUTH ABOUT {theme.upper()} 🚀",
            f"How to {theme} (Masterclass)",
            f"Stop doing this: {theme} Guide"
        ]
        
        description = (
            f"Decoding the secrets of {theme}.\n\n"
            "In this video, we break down the core principles for maximum impact.\n\n"
            "This summary was automatically generated to capture the high-density insights."
        )
        
        return {
            "titles": titles,
            "description": description,
            "tags": ["English", "Recreation", "Summary", theme.replace(" ", "")]
        }

    async def extract_editing_roadmap(self, target_duration_mins: int):
        """
        V42: Returns a sequential list of 'From-To' editing actions.
        Uses the segments selected during condensation.
        """
        if not self.selected_segments:
            return [{"edit_action": "No clips selected (Check condensation step)"}]
            
        guide = []
        for i, item in enumerate(self.selected_segments):
            vis_p = await self.studio.generate_visual_prompt(item['clean_text']) if self.studio else "Cinematic shot"
            vid_p = await self.studio.generate_video_prompt(item['clean_text']) if self.studio else "Soft camera movement"
            
            start_str = self._format_timestamp(item['start_time'])
            end_str = self._format_timestamp(item['end_time'])
            
            guide.append({
                "index": i,
                "timestamp_start": start_str,
                "timestamp_end": end_str,
                "duration": round(item['duration'], 2),
                "original_text": item['clean_text'],
                "narration_suggestion": item['clean_text'],
                "visual_prompt": vis_p,
                "video_clip_prompt": vid_p,
                "edit_action": f"🎬 Cut from {start_str} to {end_str}",
                "vibe": "🌟 Opening Hook" if i == 0 else "🔥 Key Insight"
            })
            
        return guide
