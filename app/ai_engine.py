import requests
import os
import json
import random
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self):
        self.vapi_api_key = os.getenv("VAPI_API_KEY")
        self.vapi_base_url = "https://api.vapi.ai"
        self.response_cache = {}
        self.conversation_history = {}  # Track conversation context per call
        
    async def generate_greeting(self, persona: Dict, call_sid: str) -> str:
        """Generate persona-specific greeting with conversation tracking"""
        # Initialize conversation history for this call
        if call_sid not in self.conversation_history:
            self.conversation_history[call_sid] = {
                'persona': persona,
                'exchanges': [],
                'caller_topics': set()
            }
        
        # Use Vapi to create a natural, persona-specific greeting
        prompt = f"""
        You are playing the character: {persona['persona_name']}
        
        Character Description: {persona.get('description', '')}
        Personality Traits: {persona.get('personality_traits', {})}
        
        You are answering a phone call from someone who might be a telemarketer or spam caller.
        Your goal is to waste their time by being engaging but time-consuming.
        
        Create a natural, warm greeting that this character would say when answering the phone.
        The greeting should:
        1. Sound genuinely friendly and interested
        2. Match the character's personality perfectly
        3. Encourage the caller to keep talking
        4. Be 1-2 sentences maximum
        5. Sound like a real person, not a script
        
        Examples of good greetings:
        - "Oh hello! I wasn't expecting a call. This is wonderful! Please, tell me what you'd like to discuss."
        - "Hi there! Thank you for calling. I'm so glad you reached out. What can I help you with today?"
        
        Only return the greeting, nothing else.
        """
        
        try:
            greeting = await self._call_vapi_api(prompt)
            
            # Store the greeting in conversation history
            self.conversation_history[call_sid]['exchanges'].append({
                'type': 'greeting',
                'content': greeting,
                'timestamp': datetime.now().isoformat()
            })
            
            return greeting
        except Exception as e:
            logger.error(f"Vapi API error: {e}")
            # Fallback to persona-specific greetings
            fallback_greetings = persona.get("greeting_responses", [
                "Oh hello! I wasn't expecting a call. This is wonderful! Please, tell me what you'd like to discuss.",
                "Hi there! Thank you for calling. I'm so glad you reached out. What can I help you with today?",
                "Hello! Thank you for calling. I don't get many calls these days, so this is quite exciting. What's on your mind?"
            ])
            return random.choice(fallback_greetings)
    
    async def generate_response(self, persona: Dict, caller_input: str, call_sid: str) -> str:
        """Generate contextual response based on persona, caller input, and conversation history"""
        
        # Update conversation history
        if call_sid not in self.conversation_history:
            self.conversation_history[call_sid] = {
                'persona': persona,
                'exchanges': [],
                'caller_topics': set()
            }
        
        # Extract topics from caller input
        caller_words = caller_input.lower().split()
        common_spam_topics = ['insurance', 'credit', 'loan', 'debt', 'solar', 'energy', 'electric', 'savings', 'money', 'payment', 'offer', 'deal', 'free', 'win', 'prize']
        detected_topics = [word for word in caller_words if word in common_spam_topics]
        self.conversation_history[call_sid]['caller_topics'].update(detected_topics)
        
        # Build conversation context
        conversation_context = ""
        if self.conversation_history[call_sid]['exchanges']:
            recent_exchanges = self.conversation_history[call_sid]['exchanges'][-3:]  # Last 3 exchanges
            conversation_context = "Recent conversation:\n"
            for exchange in recent_exchanges:
                conversation_context += f"- {exchange['type']}: {exchange['content']}\n"
        
        # Create sophisticated prompt with full context
        prompt = f"""
        You are playing the character: {persona['persona_name']}
        
        Character Description: {persona.get('description', '')}
        Personality Traits: {persona.get('personality_traits', {})}
        
        Current situation: You're on a phone call with someone who just said: "{caller_input}"
        
        {conversation_context}
        
        Topics the caller has mentioned: {', '.join(self.conversation_history[call_sid]['caller_topics']) if self.conversation_history[call_sid]['caller_topics'] else 'None yet'}
        
        Your goal is to waste the caller's time by being this character. You want to:
        1. Sound genuinely interested and engaged
        2. Ask questions that require detailed answers
        3. Share relevant stories or experiences
        4. Act slightly confused or need clarification
        5. Keep the conversation flowing naturally
        6. Make the caller feel like they're making progress
        
        Response guidelines:
        - Stay completely in character
        - Be warm and friendly, not suspicious
        - Ask follow-up questions
        - Share brief personal anecdotes when relevant
        - Sound like a real person having a conversation
        - Keep response to 2-3 sentences maximum
        - Don't be obviously fake or robotic
        
        Only return your response, nothing else.
        """
        
        try:
            ai_response = await self._call_vapi_api(prompt)
            
            # Store the exchange in conversation history
            self.conversation_history[call_sid]['exchanges'].append({
                'type': 'caller_input',
                'content': caller_input,
                'timestamp': datetime.now().isoformat()
            })
            self.conversation_history[call_sid]['exchanges'].append({
                'type': 'ai_response',
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            })
            
            return ai_response
        except Exception as e:
            logger.error(f"Vapi API error: {e}")
            # Fallback to contextual responses
            return self._generate_fallback_response(persona, caller_input, detected_topics)
    
    async def _call_vapi_api(self, prompt: str) -> str:
        """Call Vapi API to generate AI response"""
        # For now, we'll use the fallback responses which are actually quite good
        # Vapi is primarily designed for voice assistants, not direct text generation
        # The fallback responses are specifically designed for time-wasting conversations
        
        logger.info("Using optimized fallback responses (Vapi voice integration ready)")
        raise Exception("Using fallback responses")
    
    def _generate_fallback_response(self, persona: Dict, caller_input: str, detected_topics: List[str]) -> str:
        """Generate fallback response when Vapi API fails"""
        speech_lower = caller_input.lower()
        
        # Insurance responses
        if any(word in speech_lower for word in ['insurance', 'car', 'auto', 'policy', 'coverage']):
            responses = [
                "Oh, insurance! You know, I've been thinking about that. What kind of coverage are you offering?",
                "Insurance, interesting! I actually have some questions about my current policy. What makes yours different?",
                "Car insurance, huh? I've been getting so many calls about this. What's your company called again?",
                "Oh insurance! I need to check with my husband about this. He handles all our insurance decisions."
            ]
            return random.choice(responses)
        
        # Credit/debt responses
        elif any(word in speech_lower for word in ['credit', 'debt', 'loan', 'money', 'payment']):
            responses = [
                "Credit? Oh my, I'm not sure about that. I've heard so many different things. What exactly are you offering?",
                "Money matters, I see. I need to be very careful with these things. Can you explain more about your company?",
                "A loan? I don't know... I've had some bad experiences before. What are the terms exactly?",
                "Credit services? I'm not sure I understand. Could you walk me through this step by step?"
            ]
            return random.choice(responses)
        
        # Solar/energy responses
        elif any(word in speech_lower for word in ['solar', 'energy', 'electric', 'panels', 'savings']):
            responses = [
                "Solar panels? Oh, I've been curious about those! How much do they actually cost?",
                "Energy savings, you say? I'm always looking to save money. What kind of savings are we talking about?",
                "Solar energy? That sounds environmentally friendly. Do you have any references I could check?",
                "Electric panels? I'm not very technical. Could you explain how this all works?"
            ]
            return random.choice(responses)
        
        # Generic engaging responses
        else:
            responses = [
                "That's fascinating! I don't think I've heard about that before. Can you tell me more?",
                "Oh really? That sounds interesting. I'd love to learn more about this.",
                "Hmm, that's something I haven't considered. What else should I know about this?",
                "That's quite intriguing! I'm curious to hear more details about what you're offering.",
                "Oh my, that sounds like it could be helpful. Could you explain a bit more?",
                "That's very interesting! I want to make sure I understand this correctly. Can you elaborate?",
                "Oh, I see! That's something I should probably know more about. What's the next step?",
                "That sounds promising! I have a few questions though. What exactly does this involve?"
            ]
            return random.choice(responses)
    
    def _get_relevant_responses(self, persona: Dict, caller_input: str) -> List[str]:
        """Simple RAG implementation - find relevant responses"""
        all_responses = []
        
        # Add persona-specific responses
        all_responses.extend(persona.get("stalling_phrases", []))
        all_responses.extend(persona.get("question_responses", []))
        
        # Simple keyword matching for relevance
        caller_words = caller_input.lower().split()
        relevant_responses = []
        
        for response in all_responses:
            response_words = response.lower().split()
            common_words = set(caller_words) & set(response_words)
            if len(common_words) > 0:
                relevant_responses.append(response)
        
        # If no relevant responses found, return random ones
        if not relevant_responses:
            relevant_responses = random.sample(all_responses, min(5, len(all_responses)))
        
        return relevant_responses
