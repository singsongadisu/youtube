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

    def condense_from_segments(self, segments: list, target_duration_mins: int = 5, genre: str = "sermon") -> dict:
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
            
            # Genre-Specific Scoring
            genre_bonus = 1.0
            if genre == "interview":
                q_words = ["who", "what", "how", "why", "tell", "explain", "question"]
                if any(w in words[0:3] for w in q_words) or "?" in text:
                    genre_bonus = 1.5
            elif genre == "podcast":
                hooks = ["interesting", "crazy", "secret", "imagine", "actually", "wow"]
                if any(h in words for h in hooks):
                    genre_bonus = 1.4
            
            scored_segments.append({
                "original": seg,
                "clean_text": clean_text,
                "score": (density * multiplier) * genre_bonus,
                "duration": duration,
                "start_time": seg['start'],
                "end_time": seg['end']
            })

        # 3. Selection Strategy (Dynamic Duration Fix)
        # We need to ensure we pick enough segments to actually fill the target duration
        target_seconds = target_duration_mins * 60
        
        # Sort by score but maintain some chronological proximity
        ranked = sorted(scored_segments, key=lambda x: x['score'], reverse=True)
        
        selection = []
        current_duration = 0
        
        # Selection phase: Pick the "Gold" segments until duration is met
        for item in ranked:
            if current_duration + item['duration'] <= target_seconds:
                selection.append(item)
                current_duration += item['duration']
            if current_duration >= target_seconds * 0.95: # Close enough
                break
        
        # 4. Sequential Order & Context-Bridge (Insight Islands)
        final_clips = sorted(selection, key=lambda x: x['start_time'])
        
        # V45: Insight Islands Clustering
        # If two highlights are within 30s of each other, we merge them into one continuous block
        clustered_clips = []
        if final_clips:
            current_block = final_clips[0]
            for i in range(1, len(final_clips)):
                next_clip = final_clips[i]
                gap = next_clip['start_time'] - current_block['end_time']
                
                if gap < 45: # Merge if gap is small/contextually relevant
                    current_block['end_time'] = next_clip['end_time']
                    current_block['clean_text'] += " " + next_clip['clean_text']
                    current_block['duration'] = current_block['end_time'] - current_block['start_time']
                else:
                    clustered_clips.append(current_block)
                    current_block = next_clip
            clustered_clips.append(current_block)

        self.selected_segments = clustered_clips
        full_text = ". ".join([c['clean_text'] for c in clustered_clips])
        
        return {
            "text": full_text + ".",
            "clips_count": len(clustered_clips),
            "total_duration": sum(c['duration'] for c in clustered_clips)
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
