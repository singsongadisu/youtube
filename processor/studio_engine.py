from deep_translator import GoogleTranslator
from pathlib import Path
import json
import asyncio

class StudioEngine:
    def __init__(self):
        self.translator = GoogleTranslator(source='auto', target='am')
        self.en_translator = GoogleTranslator(source='auto', target='en')



    def generate_ai_image_url(self, prompt: str):
        """Returns a stable, typo-free Pollinations URL."""
        import urllib.parse
        clean_p = prompt.replace("\n", " ").strip()[:180]
        encoded = urllib.parse.quote(clean_p)
        # Seed ensures variety; using standard height/width params
        return f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true&seed={hash(clean_p) % 10000}"

    def shorts_clip_selector(self, segments):
        """Finds the most 'High Energy' 60-second clip for a YouTube Short."""
        if not segments: return None
        
        # Heuristic: Density of words + presence of '?' or '!'
        scores = []
        for i, seg in enumerate(segments):
            score = len(seg['text'].split())
            if '!' in seg['text']: score += 10
            if '?' in seg['text']: score += 5
            scores.append(score)
            
        # Find 60s window with highest score
        max_score = -1
        best_start_idx = 0
        
        for i in range(len(segments)):
            current_window_score = 0
            current_window_duration = 0
            for j in range(i, len(segments)):
                current_window_score += scores[j]
                current_window_duration = segments[j]['end'] - segments[i]['start']
                if current_window_duration > 60: break
                
                if current_window_score > max_score:
                    max_score = current_window_score
                    best_start_idx = i
                    
        best_seg = segments[best_start_idx]
    async def translate_to_amharic(self, text: str, tone: str = "neutral"):
        """
        Translates text to Amharic with an optional 'Tone'.
        Tones: 'neutral', 'viral', 'preaching', 'news'
        """
        if not text: return ""
        try:
            # Add tone instructions if needed
            pre_prompt = ""
            if tone == "viral": pre_prompt = "🔥 Viral Style: "
            elif tone == "preaching": pre_prompt = "🙏 Deep Spiritual Style: "
            elif tone == "news": pre_prompt = "📰 News Anchor Style: "
            
            # deep-translator is synchronous, wrap in to_thread
            result = await asyncio.to_thread(self.translator.translate, f"{pre_prompt}{text}")
            return result
        except Exception as e:
            print(f"Translation error: {e}")
            return text

    async def generate_community_posts(self, theme: str, segments: list):
        """Generates 2 types of community engagement posts."""
        teaser = (
            f"🚀 NEW VIDEO ALERT: {theme[:60]}...\n\n"
            f"I just deep-dived into this and found something mind-blowing. "
            f"Check it out and let me know what you think! 🎬🔥 #YouTubeStudio"
        )
        poll = {
            "question": f"Which part of '{theme[:40]}...' was most helpful?",
            "options": ["The Opening Hook", "The Deep Dive", "The Summary", "The Editing Road"]
        }
        return {"teaser": teaser, "poll": poll}

    async def generate_social_thread(self, script: str, target_lang: str = "am"):
        """Converts script into a 5-step viral Twitter/X thread."""
        lines = script.split(".")[:10]
        lang_text = "Amharic" if target_lang == "am" else "English"
        thread = [
            f"🧵 I just analyzed a fascinating video about '{lines[0][:50]}'. Here are the 5 key takeaways you NEED to know: (Thread) 👇",
            f"1️⃣ {lines[1].strip() if len(lines)>1 else 'Insightful point 1'}",
            f"2️⃣ {lines[2].strip() if len(lines)>2 else 'Insightful point 2'}",
            f"3️⃣ {lines[3].strip() if len(lines)>3 else 'Insightful point 3'}",
            f"4️⃣ {lines[4].strip() if len(lines)>4 else 'Insightful point 4'}",
            f"5️⃣ Final thought: This is a game-changer for content creators in {lang_text}! 🚀✨\n\nWatch full video: [Link]"
        ]
        return thread

    async def extract_editing_guide(self, whisper_segments, target_duration_mins: int, target_lang: str = "am", tone: str = "neutral", genre: str = "sermon"):
        """
        🧬 V70: Topic-Driven Context Trimming
        Detects natural idea boundaries (pauses, transitions) to ensure clips start and end perfectly.
        """
        if not whisper_segments: return []
        
        def clean_seg(seg):
            return {
                "start": float(seg.get("start", 0)),
                "end": float(seg.get("end", 0)),
                "text": str(seg.get("text", "")).strip(),
                "duration": float(seg.get("end", 0)) - float(seg.get("start", 0))
            }
        
        cleaned_segments = [clean_seg(s) for s in whisper_segments]
        target_seconds = target_duration_mins * 60
        
        # 1. Boundary Detection Helper
        def is_natural_boundary(seg, prev_seg=None):
            text = seg['text'].lower()
            # Transition Words (English & Amharic)
            transitions = ["now", "first", "finally", "so", "but", "however", "therefore", "ስለዚህ", "ነገር ግን", "በመጀመሪያ", "በመጨረሻ"]
            # Pause Detection (> 1.5 seconds gap)
            pause = (seg['start'] - prev_seg['end']) > 1.5 if prev_seg else False
            # Syntactic / Genre Markers
            is_trans = any(text.startswith(t) for t in transitions)
            is_question = "?" in text or "?" in (prev_seg['text'] if prev_seg else "")
            
            return pause or is_trans or is_question

        # 2. Scoring Phase
        scored_segments = []
        for i, s in enumerate(cleaned_segments):
            text = s['text'].lower()
            if not text: continue
            
            score = len(text)
            # Bonus for starters
            if is_natural_boundary(s, cleaned_segments[i-1] if i > 0 else None):
                score *= 1.4
            
            # Genre Bonuses
            if genre == "interview" and ("?" in text): score *= 1.6
            elif genre == "podcast" and any(w in text for w in ["interesting", "incredible"]): score *= 1.3
            
            scored_segments.append({**s, "relevance": score, "used": False, "orig_idx": i})

        # 3. Greedy Idea Filling
        islands = []
        current_dur = 0
        ranked = sorted(scored_segments, key=lambda x: x['relevance'], reverse=True)
        
        # Max reasonable idea size (5 mins), but we prefer natural ends
        MAX_IDEA_DUR = 300 
        
        for root in ranked:
            if current_dur >= target_seconds: break
            if root['used']: continue
            
            idx = root['orig_idx']
            island_indices = {idx}
            root['used'] = True
            
            # Expand Backward until a boundary or limit
            curr_start_idx = idx
            while curr_start_idx > 0:
                prev = scored_segments[curr_start_idx - 1]
                if prev['used']: break
                
                # If we found a boundary, we STOP before it (so the current clip starts at the boundary)
                if is_natural_boundary(cleaned_segments[curr_start_idx], cleaned_segments[curr_start_idx-1]):
                    break
                
                prev['used'] = True
                island_indices.add(prev['orig_idx'])
                curr_start_idx -= 1
                if (cleaned_segments[idx]['end'] - cleaned_segments[curr_start_idx]['start']) > MAX_IDEA_DUR: break

            # Expand Forward until a boundary or limit
            curr_end_idx = idx
            while curr_end_idx < len(scored_segments) - 1:
                nxt = scored_segments[curr_end_idx + 1]
                if nxt['used']: break
                
                # Check if the NEXT segment is a boundary (meaning this idea ends here)
                if is_natural_boundary(cleaned_segments[curr_end_idx+1], cleaned_segments[curr_end_idx]):
                    break
                    
                nxt['used'] = True
                island_indices.add(nxt['orig_idx'])
                curr_end_idx += 1
                if (cleaned_segments[curr_end_idx]['end'] - cleaned_segments[idx]['start']) > MAX_IDEA_DUR: break

            sorted_idxs = sorted(list(island_indices))
            island_segments = [cleaned_segments[i] for i in sorted_idxs]
            
            island_text = " ".join([s['text'] for s in island_segments])
            actual_dur = island_segments[-1]['end'] - island_segments[0]['start']
            
            # Precision V41: Hard Stop & Micro-Trimming
            if current_dur + actual_dur > target_seconds * 1.05:
                # If it overflows, try to trim the final island to fit perfectly
                remaining = target_seconds - current_dur
                if remaining > 30: # Only bother if we have a decent chunk left
                    island_segments[-1]['end'] = island_segments[0]['start'] + remaining
                    actual_dur = remaining
                else:
                    # Too small to bother, skip this island
                    continue

            islands.append({
                "start": island_segments[0]['start'],
                "end": island_segments[-1]['end'],
                "text": island_text,
                "duration": actual_dur
            })
            current_dur += actual_dur
            if current_dur >= target_seconds: break

        # Sort chronologically
        islands.sort(key=lambda x: x['start'])
        
        # 4. Packaging
        tasks = []
        for i, island in enumerate(islands):
            async def process_island(idx, data):
                suggestion = await self.translate_to_amharic(data['text'][:300] + "...", tone=tone) if target_lang == "am" else data['text']
                vis_p = await self.generate_visual_prompt(data['text'])
                vid_p = await self.generate_video_prompt(data['text'])
                label = "💡 Concept" if genre == "sermon" else "🤝 Q&A" if genre == "interview" else "🎙️ Topic"
                
                return {
                    "index": idx,
                    "timestamp_start": f"{int(data['start'] // 60):02d}:{int(data['start'] % 60):02d}",
                    "timestamp_end": f"{int(data['end'] // 60):02d}:{int(data['end'] % 60):02d}",
                    "duration": data['duration'],
                    "original_text": data['text'],
                    "narration_suggestion": suggestion,
                    "visual_prompt": vis_p,
                    "video_clip_prompt": vid_p,
                    "edit_action": f"{label}: {round(data['duration'])}s (Idea-based cut)"
                }
            tasks.append(process_island(i, island))

        results = await asyncio.gather(*tasks)
        print(f"🎨 Topic-Driven Selection: Request {target_duration_mins}m | Planned {round(current_dur/60, 2)}m")
        return results

    async def generate_visual_prompt(self, text: str):
        """Generates a professional AI image prompt with aspect ratio and transparency handling."""
        # This is strictly logic, but we make it async for consistency
        text_lower = text.lower()
        base_suffix = "high resolution, 8k, photorealistic, cinematic lighting, 16:9 aspect ratio"
        
        # Category-based prompt engineering
        if any(w in text_lower for w in ["god", "spirit", "faith", "divine"]):
            return f"Cinematic shot of ethereal divine golden light breaking through storm clouds, spiritual atmosphere, {base_suffix}"
        
        if any(w in text_lower for w in ["mountain", "high", "climb", "peak"]):
            return f"Majestic snow-capped mountain peaks at sunrise, purple mist, glowing horizon, wide angle, {base_suffix}"
            
        if any(w in text_lower for w in ["money", "billionaire", "wealth", "business"]):
            return f"Abstract visualization of flowing golden energy particles forming currency symbols, professional financial aesthetic, {base_suffix}"
            
        if any(w in text_lower for w in ["heart", "love", "passion"]):
            return f"A glowing anatomical heart silhouette floating in a deep blue nebula, vibrant colors, {base_suffix}"

        # Overlay/Transparency handling (for elements that might be used as floating graphics)
        if any(w in text_lower for w in ["icon", "symbol", "key", "badge"]):
            return f"Isolated 3D golden key icon, floating, professional studio lighting, transparent background style, high contrast, 16:9"

        return f"Hyper-realistic cinematic b-roll scene for: {text[:60]}, professional videography, {base_suffix}"

    async def generate_video_prompt(self, text: str):
        """Generates a professional 5-second AI video prompt with camera movement."""
        text_lower = text.lower()
        v_suffix = "cinematic 4k, slow motion, highly detailed, realistic textures, professional color grading"
        
        if any(w in text_lower for w in ["god", "spirit", "faith", "divine"]):
            return f"A cinematic slow-motion drone shot flying through golden clouds towards a blinding divine light, {v_suffix}"
            
        if any(w in text_lower for w in ["mountain", "high", "climb", "peak"]):
            return f"A dramatic pan across snow-capped peaks at sunset, snow particles blowing in the wind, {v_suffix}"
            
        if any(w in text_lower for w in ["money", "billionaire", "wealth", "business"]):
            return f"Slow dolly shot over a dark mahogany desk with stacks of gold coins and digital data holograms floating above, {v_suffix}"

        return f"Cinematic b-roll footage of: {text[:60]}, 5-second clip, soft camera movement, dolly in, {v_suffix}"

    async def generate_hooks(self, transcript_segments, target_lang: str = "am"):
        """Generates 3 viral hooks based on the first few minutes."""
        first_min = " ".join([s['text'] for s in transcript_segments[:5]])
        
        hooks = [
            f"Stop scrolling! This video changes everything about {first_min[:40]}...",
            f"You won't believe what happens when {first_min[:40]}...",
            f"The truth about {first_min[:40]} revealed."
        ]
        
        if target_lang == "am":
            tasks = [self.translate_to_amharic(h, tone="viral") for h in hooks]
            return await asyncio.gather(*tasks)
            
        return hooks

    async def generate_thumbnail_prompt(self, video_title: str, transcript_segments):
        """Generates a high-impact YouTube thumbnail prompt in English."""
        # Visual prompt engineering
        return f"Hyper-realistic YouTube thumbnail design for a video titled '{video_title}', high contrast, saturated colors, expressive face, dramatic lighting, 8k, professional graphic design style"

    async def generate_srt(self, segments, target_lang: str = "am"):
        """Generates a standard SRT subtitle content mapping text to timestamps."""
        srt_content = ""
        for i, seg in enumerate(segments):
            start = self._format_srt_time(seg['start'])
            end = self._format_srt_time(seg['end'])
            
            if target_lang == "am":
                # We only translate short snippets to avoid server heavy load
                text = await self.translate_to_amharic(seg['text'][:100])
            else:
                text = seg['text']
            
            srt_content += f"{i+1}\n{start} --> {end}\n{text}\n\n"
        return srt_content

    async def generate_metadata_recommendations(self, title: str, transcript_segments, target_lang: str, tone: str = "neutral", genre: str = "sermon"):
        """Generates 3 titles and a full SEO description in the target language."""
        content_sample = " ".join([s['text'] for s in transcript_segments[:10]])
        theme = title if title else content_sample[:60]
        
        # Genre-Specific English Templates
        if genre == "interview":
            en_titles = [
                f"INTERVIEW: The Truth about {theme}",
                f"Exclusive: {theme} (Full Discussion)",
                f"How {theme} Changed Their Life"
            ]
            en_desc = f"In this exclusive interview, we explore {theme}. Listen to the deep insights shared by the experts.\n\n#Interview #Discussion #{theme.replace(' ', '')}"
        elif genre == "podcast":
            en_titles = [
                f"PODCAST: Why {theme} Matters Now",
                f"Decoding {theme} (Deep Dive)",
                f"The Real Story behind {theme}"
            ]
            en_desc = f"Welcome back to the podcast. Today we are deep-diving into {theme} and uncovering the secrets most people miss.\n\n#Podcast #DeepDive #{theme.replace(' ', '')}"
        else: # sermon
            en_titles = [
                f"SERMON: The Power of {theme}",
                f"Life Changing: {theme} (Message)",
                f"Why You Need {theme} in Your Life"
            ]
            en_desc = f"A powerful message about {theme}. Let this word transform your perspective and bring clarity for your journey.\n\n#Sermon #Faith #Blessing #{theme.replace(' ', '')}"
        
        if target_lang == "en":
            return {"titles": en_titles, "description": en_desc}
            
        # For Amharic, we translate the high-energy templates in parallel
        tasks = [self.translate_to_amharic(t, tone=tone) for t in en_titles]
        tasks.append(self.translate_to_amharic(en_desc, tone=tone))
        
        results = await asyncio.gather(*tasks)
        am_titles = results[:3]
        am_desc = results[3]
        
        return {"titles": am_titles, "description": am_desc}

    async def generate_chapters(self, transcript_segments):
        """
        🏆 V23: Advanced Chapter Generator
        Generates thematic and descriptive YouTube chapters.
        """
        if not transcript_segments: return "00:00 - Introduction"
        
        chapters = []
        # Ensure it always starts at 00:00
        chapters.append("00:00 - Introduction & Hook")
        
        # Determine logical spacing (aim for 5-8 chapters)
        num_goals = 6
        step = len(transcript_segments) // num_goals
        
        for i in range(1, num_goals):
            idx = i * step
            if idx >= len(transcript_segments): break
            
            seg = transcript_segments[idx]
            time_str = f"{int(seg['start'] // 60):02d}:{int(seg['start'] % 60):02d}"
            
            # Use V20 ranking logic to find the "Heaviest" sentence nearby for a title
            sub_segments = transcript_segments[max(0, idx-2):min(len(transcript_segments), idx+3)]
            best_seg = max(sub_segments, key=lambda x: len(x['text'])) # Shorthand for "Descriptive"
            
            # Clean title (remove fluff)
            raw_title = best_seg['text'].strip().split(".")[0]
            title = (raw_title[:35] + "...") if len(raw_title) > 35 else raw_title
            
            # Capitalize and clean
            title = ' '.join(word.capitalize() for word in title.split())
            chapters.append(f"{time_str} - {title}")
            
        return "\n".join(chapters)

    def condense_english(self, text: str, target_ratio: float = 0.3, target_duration_mins: int = 5):
        """
        🧬 V20: English Condensation Evolution
        Condenses English text using Contextual Density & Punchy-fication.
        V21 Update: Reading-Speed Aware (Fits target_duration_mins exactly).
        """
        if not text: return ""
        
        # 1. Clean verbal fluff and fillers (Punchy-fication)
        fillers = ["you know", "i mean", "sort of", "kind of", "basically", "actually", "literally", "to be honest", "obviously"]
        clean_text = text.lower()
        for f in fillers:
            clean_text = clean_text.replace(f, "")
        
        sentences = text.split(". ")
        if len(sentences) < 5: return text
        
        # 2. Contextual Density (Favoring nouns and action verbs)
        stop_words = {"the", "is", "at", "which", "on", "and", "to", "of", "a", "in", "that", "it", "with", "from", "for"}
        words = [w.strip(",.").lower() for w in text.split() if w.strip(",.").lower() not in stop_words]
        
        freq_map = {}
        for w in words:
            weight = 1.0
            if len(w) > 6: weight = 1.5 
            freq_map[w] = freq_map.get(w, 0) + weight
            
        # 3. Sentence Ranking
        sentence_scores = []
        for s in sentences:
            s_clean = s.strip().lower()
            if not s_clean: continue
            
            words_in_s = [w.strip(",.") for w in s_clean.split()]
            if len(words_in_s) < 3: continue 
            
            raw_score = sum(freq_map.get(w, 0) for w in words_in_s)
            action_starters = ["imagine", "discover", "this", "learn", "stop", "here", "why", "how"]
            if words_in_s and words_in_s[0] in action_starters:
                raw_score *= 1.2
                
            density_score = raw_score / (len(words_in_s) ** 0.5) 
            sentence_scores.append((s, density_score))
            
        # 4. Smart Pruning (Preserving chronological flow and matching Duration)
        # Average reading speed is ~150 words per minute
        MAX_WORDS = target_duration_mins * 150
        
        # Sort by density to find the "Must Have" sentences
        must_have = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
        
        final_list = []
        current_word_count = 0
        
        # Add sentences until we hit the word limit
        for s, score in must_have:
            word_count = len(s.split())
            if current_word_count + word_count <= MAX_WORDS:
                final_list.append(s)
                current_word_count += word_count
            if current_word_count >= MAX_WORDS:
                break
        
        # 5. Re-sort by original appearance to keep logic flow
        final_sentences_ordered = []
        for s, score in sentence_scores:
            if s in final_list:
                final_sentences_ordered.append(s.strip())
        
        return ". ".join(final_sentences_ordered) + "."

    def _format_srt_time(self, seconds):
        """Converts seconds to SRT time format HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int((seconds % 1) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"

if __name__ == "__main__":
    # Test
    # engine = StudioEngine()
    # print(engine.translate_to_amharic("Hello, how are you?"))
    pass
