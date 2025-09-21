import json
import random
import os
from typing import Dict, List

class PersonaManager:
    def __init__(self):
        self.personas = self._load_personas()
    
    def _load_personas(self) -> List[Dict]:
        """Load all persona configurations"""
        personas = []
        persona_files = [
            "elderly_confused.json",
            "overly_interested.json", 
            "technical_questioner.json",
            "price_haggler.json",
            "story_teller.json"
        ]
        
        for filename in persona_files:
            filepath = f"data/personas/{filename}"
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    personas.append(json.load(f))
            else:
                # Create default persona if file doesn't exist
                personas.append(self._create_default_persona(filename))
        
        return personas
    
    def _create_default_persona(self, filename: str) -> Dict:
        """Create default persona data"""
        persona_name = filename.replace('.json', '')
        
        defaults = {
            "elderly_confused": {
                "persona_name": "elderly_confused",
                "greeting_responses": [
                    "Hello? Who is this? I can't hear very well.",
                    "Yes? Is this my doctor?",
                    "Hello dear, I was just making tea. What did you say?"
                ],
                "stalling_phrases": [
                    "Could you speak up? I'm a bit hard of hearing.",
                    "Wait, let me get my glasses.",
                    "Hold on, let me turn down the TV.",
                    "What was that? You'll have to repeat that.",
                    "Is this about my grandson? He usually handles these things."
                ],
                "question_responses": [
                    "I don't understand all this modern technology.",
                    "You'll have to explain that in simple terms.",
                    "I need to ask my grandson about this.",
                    "This sounds complicated. Can you call back when he's here?"
                ],
                "personality_traits": {
                    "speech_pace": "slow",
                    "repetition_frequency": "high",
                    "confusion_level": "high"
                }
            },
            "overly_interested": {
                "persona_name": "overly_interested", 
                "greeting_responses": [
                    "Oh wonderful! I've been waiting for a call like this!",
                    "This is so exciting! Tell me everything!",
                    "Perfect timing! I was just thinking about this!"
                ],
                "stalling_phrases": [
                    "This is fascinating! Tell me more!",
                    "I have so many questions!",
                    "This sounds amazing! How did you get into this business?",
                    "I want to know everything about your company!"
                ],
                "personality_traits": {
                    "enthusiasm_level": "extremely_high",
                    "question_frequency": "constant"
                }
            }
        }
        
        return defaults.get(persona_name, {
            "persona_name": persona_name,
            "greeting_responses": ["Hello! How can I help you?"],
            "stalling_phrases": ["That's interesting. Tell me more."],
            "personality_traits": {}
        })
    
    def select_random_persona(self) -> Dict:
        """Select a random persona for the call"""
        return random.choice(self.personas)
    
    def get_persona_by_name(self, name: str) -> Dict:
        """Get specific persona by name"""
        for persona in self.personas:
            if persona["persona_name"] == name:
                return persona
        return self.personas[0]  # Default to first persona
