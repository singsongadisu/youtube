import asyncio
import random
import os
import re
from pathlib import Path
from processor.studio_engine import StudioEngine

class CreativeEngine:
    def __init__(self):
        self.studio = StudioEngine()
        
        # 1. STORY VAULT: High-quality, pre-written core narratives for specific entities
        self.story_vault = {
            "samson": {
                "hook": "He was a man of impossible strength, a Nazirite set apart from birth. But the story of Samson is more than just a tale of muscle—it is a journey of pride, betrayal, and ultimate redemption.",
                "core": "Samson's power came from a sacred vow, symbolized by his hair. When he allowed his heart to be led astray by Delilah, he lost his power and was defeated. Yet, in his final moments of humility and prayer, God granted him one last victory that surpassed all others.",
                "depth": [
                    "His failure was not a lack of strength, but a lack of discipline. It shows that even the most gifted can fall when they lose sight of their calling.",
                    "The betrayal by Delilah represents the seductive nature of compromise. Samson's hair was just a symbol; the real source of his power was his connection to the divine.",
                    "Even in his blindness and captivity, Samson found a strength that was deeper than physical might—the strength of true repentance.",
                    "His final victory in the temple of Dagon reminds us that God's grace is greater than our greatest failures."
                ]
            },
            "samuel": {
                "hook": "In a time when the word of the Lord was rare, a young boy named Samuel heard a voice in the temple that would change history.",
                "core": "Samuel's success wasn't built on power, but on his willingness to say: 'Speak, Lord, for your servant is listening.' From his miraculous birth to his role as a prophet and judge, Samuel became the foundation of the Israelite monarchy.",
                "depth": [
                    "He was the bridge between the era of judges and the age of kings, a man of unwavering integrity.",
                    "His life proves that success in the eyes of the divine is about faithful obedience in the small things.",
                    "Even when the people demanded a king, Samuel remained a voice of truth, guiding them with a father's heart.",
                    "The transition from Eli's leadership to Samuel's represented a restoration of spiritual clarity to the nation."
                ]
            },
            "jesus": {
                "hook": "The life of Jesus remains the most profound intersection of the divine and the human experience.",
                "core": "His message of love, sacrifice, and redemption bypassed the religious structures of his time to speak directly to the soul. Through his teachings and ultimate sacrifice, he provided a path for all to find peace.",
                "depth": [
                    "The Sermon on the Mount redefined what it means to be truly blessed in a broken world.",
                    "His miracles were not just displays of power, but acts of deep compassion for the marginalized.",
                    "By choosing common fishermen as his disciples, he showed that greatness is available to the humble.",
                    "The empty tomb stands as a testament to the victory of light over even the darkest of circumstances."
                ]
            },
            "kids": {
                "hook": "Raising a child is perhaps the greatest and most humbling responsibility we are ever entrusted with.",
                "core": "The biblical foundation for parenting isn't about control, but about modeling the love and discipline that God shows us. It’s about training up a child in the way they should go, so that their heart is rooted in truth.",
                "depth": [
                    "Discipline, when applied with love, provides the boundaries that allow a child's character to flourish.",
                    "Every day is an opportunity to show your children the grace that has been so freely given to you.",
                    "The greatest legacy you can leave is not your wealth, but the spiritual foundation you build in their hearts.",
                    "Parenting requires a patience that can only be found by leaning into a strength greater than your own."
                ]
            },
            "ai": {
                "hook": "We are weaving a new intelligence into the fabric of our reality, and the implications are breathtaking.",
                "core": "Artificial Intelligence is not just a tool; it's a mirror reflecting our own desire to create and understand. As we move into this new era, the challenge is ensuring that our technology remains a servant to our humanity.",
                "depth": [
                    "The speed of innovation is challenging our traditional views of labor, creativity, and even identity.",
                    "We must navigate the ethical landscape of AI with a commitment to transparency and equity.",
                    "The convergence of silicon and soul is the next great frontier of the human journey.",
                    "Success in the age of AI will be defined by our ability to maintain our human connection amidst the data."
                ]
            }
        }
        
        # 2. MUSIC VAULT: Maps blueprints to production vibes
        self.music_vault = {
            "spiritual_journey": {"genre": "Ambient Soul / Cinematic Hope", "bpm": "70-85"},
            "historical_epic": {"genre": "Epic Orchestral / War Drums", "bpm": "90-110"},
            "futurist_vision": {"genre": "Cyberpunk Synth / High-Tech", "bpm": "110-130"},
            "masterclass": {"genre": "Lo-Fi Study / Minimal Modern", "bpm": "80-95"},
            "explainer": {"genre": "Corporate Upbeat / Modern Clean", "bpm": "100-120"}
        }

        # 3. PRODUCTION METADATA: Visual & Emotional specs
        self.production_specs = {
            "spiritual_journey": {"mood": "Solemn and Grand", "palette": "Gold, Deep Wood, Velvet Red", "pacing": "Slow, contemplative cuts with slow-mo transitions"},
            "historical_epic": {"mood": "Dignified & Cinematic", "palette": "Sepia, Stone Grey, Naval Blue", "pacing": "Steady, rhythmic builds with dramatic reveals"},
            "futurist_vision": {"mood": "High-Energy & Sleek", "palette": "Electric Blue, Neon Purple, Carbon Black", "pacing": "Fast, glitch-style transitions with dynamic kinetic energy"},
            "masterclass": {"mood": "Educational & Warm", "palette": "Teal, Soft Orange, Clean White", "pacing": "Smooth, clear cuts focused on clarity and focus"},
            "explainer": {"mood": "Fresh & Optimistic", "palette": "Mint Green, Sky Blue, Soft Grey", "pacing": "Lively, constant movement to maintain engagement"}
        }

    def _synthesize_thematic_depth(self, topic: str, blueprint: str):
        """V7 PERFECTION: Generates topic-aware sentences to expand duration."""
        topic_clean = topic.capitalize()
        
        # Topic-specific kernels
        kernels = {
            "samson": ["the weight of destiny", "the fragility of strength", "the cost of a broken vow"],
            "samuel": ["the clarity of the call", "the power of a listening heart", "the burden of leadership"],
            "jesus": ["the miracle of grace", "the paradox of sacrifice", "the light that transcends darkness"],
            "kids": ["the seeds of the future", "the art of patience", "the reflection of pure wonder"],
            "ai": ["the boundary of creation", "the shadow of the silicon", "the mirror of human thought"]
        }
        
        kernel = random.choice(kernels.get(topic.lower(), ["the hidden layers of this truth", "the intricate patterns of growth"]))
        
        blueprints_syntheses = {
            "spiritual_journey": [
                f"It is in {kernel} that we find our most profound connection to the eternal.",
                f"We must ask ourselves: are we ready to face {kernel} in our search for truth?",
                f"Every step toward {topic_clean} is a step toward understanding {kernel}.",
                f"True faith is not just seeing, but embracing {kernel} when the path is unclear."
            ],
            "historical_epic": [
                f"History has always been shaped by {kernel}, a force that echoes through time.",
                f"The archives reveal that {topic_clean} was never just a moment, but a struggle with {kernel}.",
                f"To understand the past, we must first look at the legacy of {kernel}.",
                f"The stones of the ancient world still whisper the story of {kernel}."
            ],
            "futurist_vision": [
                f"We are standing on the precipice of {kernel}, where the old world fades.",
                f"The code of the future is being written in the language of {kernel}.",
                f"Will {topic_clean} survive the transition into the age of {kernel}?",
                f"Our survival depends on our ability to navigate the complexity of {kernel}."
            ],
            "masterclass": [
                f"To master this, you must first master the concept of {kernel}.",
                f"Notice how {topic_clean} aligns perfectly with the principles of {kernel}.",
                f"The most successful practitioners always start by stabilizing {kernel}.",
                f"Don't just look at the results; look at the foundation built on {kernel}."
            ],
            "explainer": [
                f"This brings us to a vital realization: {topic_clean} is actually driven by {kernel}.",
                f"Most people miss the connection between this and {kernel}.",
                f"Think of {kernel} as the invisible engine behind everything we've discussed.",
                f"The data suggests that {kernel} is the primary factor in this equation."
            ]
        }
        
        return blueprints_syntheses.get(blueprint, blueprints_syntheses["explainer"])

    def _purify_topic(self, idea_str):
        """Strips filler phrases to find the core entity/topic."""
        filler_patterns = [
            r"the story of", r"how to", r"in the bible", r"how it is successful",
            r"successful", r"what is", r"explain", r"as the bible says"
        ]
        purified = idea_str.lower()
        for pattern in filler_patterns:
            purified = re.sub(pattern, "", purified).strip()
        
        # FIXED V5: Use word boundaries (\b) to avoid matching inside other words (e.g., "ai" in "fails")
        for key in self.story_vault.keys():
            if re.search(rf"\b{re.escape(key)}\b", purified):
                return key
        return purified

    async def generate_script(self, idea: str, duration_mins: int = 3, lang: str = 'en'):
        """
        🚀 SCRIPT MASTERY V5: Extreme Context Fix
        Uses regex word boundaries and Expanded Story Vaulting.
        """
        target_words = int(duration_mins) * 160
        idea_lower = idea.lower()
        core_topic = self._purify_topic(idea_lower)
        
        # 1. Blueprint Selection (Fixed: Spiritual > Masterclass)
        spiritual_keywords = ["bible", "god", "jesus", "spirit", "faith", "pastor", "preach", "samuel", "david", "samson", "daniel", "ruth"]
        if any(re.search(rf"\b{re.escape(w)}\b", idea_lower) for w in spiritual_keywords):
            blueprint_type = "spiritual_journey"
        elif any(w in idea_lower for w in ["history", "war", "ancient", "biography"]):
            blueprint_type = "historical_epic"
        elif any(re.search(rf"\b{re.escape(w)}\b", idea_lower) for w in ["future", "ai", "technology", "space", "science"]):
            blueprint_type = "futurist_vision"
        elif any(w in idea_lower for w in ["how to", "tutorial", "guide", "master"]):
            blueprint_type = "masterclass"
        else:
            blueprint_type = "explainer"

        # 2. Vault Match - Use real narrative if available
        vault_data = self.story_vault.get(core_topic)

        # 3. Dynamic Narrative Construction
        blueprints = {
            "spiritual_journey": [
                ("The Calling", "{hook}"),
                ("The Divine Truth", "{core}"),
                ("The Internal Struggle", "Walking the path of spiritual growth is rarely easy. It requires us to look inward and face the parts of our hearts that need refinement."),
                ("The Transformation", "But in that refinement, there is beauty. The way {topic} impacts our lives is through a steady, quiet transformation of the spirit."),
                ("The Deep Wisdom", "{depth_1}"),
                ("The Legacy", "{depth_2}"),
                ("The Conclusion", "Final thought: Let the essence of {topic} be your guide. Grace is always available for those who seek it.")
            ],
            "explainer": [
                ("The Concept", "{hook} {core}"),
                ("The Logic", "If we break down the structure of {topic}, we find a fascinating array of interdependent systems."),
                ("The Context", "{depth_1}"),
                ("The Impact", "{depth_2}"),
                ("The Deep Dive", "When we look beyond the surface of {topic}, the true complexity begins to reveal itself."),
                ("The Summary", "In conclusion, understanding {topic} is about seeing the hidden patterns in the world around us.")
            ]
        }
        
        active_blueprint_template = blueprints.get(blueprint_type, blueprints["explainer"])
        
        # Prepare context variables
        topic_display = core_topic.capitalize()
        hook_val = vault_data["hook"] if vault_data else f"The world of {topic_display} is more complex than it first appears."
        core_val = vault_data["core"] if vault_data else f"At its heart, {topic_display} represents a fundamental shift in how we understand our environment."
        depth_1 = vault_data["depth"][0] if vault_data else f"Experts often point to the foundational principles of {topic_display} as the key to its success."
        depth_2 = vault_data["depth"][1] if vault_data and len(vault_data["depth"]) > 1 else f"The long-term implications of {topic_display} are still being calculated by researchers today."

        script_parts = []
        words_per_part = target_words // len(active_blueprint_template)

        for section_title, template_str in active_blueprint_template:
            content = f"[{section_title}]\n"
            content += template_str.format(
                topic=topic_display,
                hook=hook_val,
                core=core_val,
                depth_1=depth_1,
                depth_2=depth_2
            ) + "\n"
            
            thematic_depth = self._synthesize_thematic_depth(core_topic, blueprint_type)
            
            while len(content.split()) < words_per_part:
                content += " " + random.choice(thematic_depth)
            
            script_parts.append(content)

        full_script = "\n\n".join(script_parts)
        full_script = full_script.replace("  ", " ").strip()

        # Generate Segments for UI
        segments = []
        current_time_s = 0
        for i, part in enumerate(script_parts):
            # Header is typically "[Title]"
            header_match = re.search(r"\[(.*?)\]", part)
            title = header_match.group(1) if header_match else f"Scene {i+1}"
            text_only = re.sub(r"\[.*?\]", "", part).strip()
            
            # Simple word-based timing estimation (~160 words per minute = 2.6 words per second)
            word_count = len(text_only.split())
            duration_s = int(word_count / 2.6)
            
            minutes = current_time_s // 60
            seconds = current_time_s % 60
            timestamp = f"{minutes}:{seconds:02d}"
            
            segments.append({
                "title": title,
                "timestamp": timestamp,
                "text": text_only,
                "duration": f"{duration_s}s",
                "visual_suggestion": self._generate_broll_suggestion(title, text_only)
            })
            current_time_s += duration_s

        music = self.music_vault.get(blueprint_type, self.music_vault["explainer"])
        production = self.production_specs.get(blueprint_type, self.production_specs["explainer"])

        result = {
            "script": full_script,
            "blueprint": blueprint_type.replace("_", " ").title(),
            "segments": segments,
            "music": music,
            "production": production
        }

        if lang != 'en':
            from deep_translator import GoogleTranslator
            try:
                translator = GoogleTranslator(source='auto', target=lang)
                result["script"] = await asyncio.to_thread(translator.translate, full_script)
                for seg in result["segments"]:
                    seg["text"] = await asyncio.to_thread(translator.translate, seg["text"])
                    seg["title"] = await asyncio.to_thread(translator.translate, seg["title"])
            except Exception as e:
                print(f"Translation error: {e}")
                
        return result

    async def refine_script(self, script: str, style: str):
        """
        AI SCRIPT REFINERS: Viral, Emotional, Simple
        """
        if style == "viral":
            # Add dramatic hooks and clickbaity transitions
            refinement = "ALERT: Most people ignore this, but you can't afford to. "
            script = refinement + script
            script = script.replace(". ", "! ").replace("However,", "But wait, it gets crazier. ")
        elif style == "emotional":
            # Add soul-stirring language
            refinement = "Feel the heart behind these words. "
            script = refinement + script
            script = script.replace("Success", "A soul-deep fulfillment").replace("result", "sacred outcome")
        elif style == "simple":
            # Simplify language for ease of understanding
            script = script.replace("contemporary data", "current facts").replace("implementation", "plan")
            script = "Here is the simple truth: " + script
            
        return script

    def _generate_broll_suggestion(self, title: str, text: str):
        """Generates a professional B-roll suggestion based on scene content."""
        if "Calling" in title or "Hook" in title:
            return "Cinematic wide shot, sunrise or epic landscape, high contrast."
        elif "Divine" in title or "Spiritual" in title:
            return "Close-up of hands, ancient book, or soft light filtered through trees."
        elif "Logic" in title or "Concept" in title:
            return "Macro shot of clockwork, circuit boards, or geometric patterns."
        elif "Impact" in title or "Legacy" in title:
            return "Slow motion tracking shot of a bustling city or peaceful garden."
        
        return f"Dynamic visual capturing the essence of {title}."

    async def generate_visual_prompts(self, script: str):
        sections = script.split('\n\n')
        prompts = []
        for i, section in enumerate(sections[:5]):
            sentences = [s.strip() for s in section.split('.') if len(s.strip()) > 30]
            if sentences:
                best_s = max(sentences, key=len)
                p = await self.studio.generate_visual_prompt(best_s)
                prompts.append(p)
        return prompts
