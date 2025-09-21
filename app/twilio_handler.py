from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
from .ai_engine import AIEngine
from .personas import PersonaManager
from .database import AsyncSessionLocal, Call, Conversation
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

class TwilioHandler:
    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.ai_engine = AIEngine()
        self.persona_manager = PersonaManager()
        self.active_calls = {}  # Store call state

    async def handle_incoming_call(self, form_data):
        """Handle incoming call and start conversation with persona"""
        try:
            call_sid = form_data.get("CallSid")
            caller_number = form_data.get("From")
            
            logger.info(f"Incoming call from {caller_number}, SID: {call_sid}")
            
            # Select a random persona for this call
            persona = self.persona_manager.select_random_persona()
            logger.info(f"Selected persona: {persona['persona_name']} for call {call_sid}")
            
            # Generate persona-specific greeting using Gemini
            greeting = await self.ai_engine.generate_greeting(persona, call_sid)
            
            # Store call info for tracking
            self.active_calls[call_sid] = {
                "persona": persona,
                "caller_number": caller_number,
                "start_time": datetime.now()
            }
            
            # Create TwiML response with AI-generated greeting and optimized voice settings
            response = VoiceResponse()
            response.say(greeting, voice="Polly.Joanna", rate=1, pitch=1.0)
            
            # Start gathering speech
            gather = response.gather(
                input="speech",
                action=f"{os.getenv('NGROK_TUNNEL_URL')}/webhook/speech",
                speech_timeout="5",
                timeout=15
            )
            
            # Fallback if no speech detected
            response.say("I didn't hear anything. Could you repeat that?", voice="Polly.Joanna", rate=1)
            response.redirect(f"{os.getenv('NGROK_TUNNEL_URL')}/webhook/speech")
            
            return response.to_xml()
        except Exception as e:
            logger.error(f"Error in handle_incoming_call: {e}")
            # Return a simple response on error
            response = VoiceResponse()
            response.say("Hello! Thank you for calling. Please hold on.", voice="alice")
            response.hangup()
            return response.to_xml()

    async def handle_speech_result(self, form_data):
        """Handle speech recognition results and generate AI-powered response"""
        try:
            call_sid = form_data.get("CallSid")
            speech_result = form_data.get("SpeechResult", "")
            confidence = float(form_data.get("Confidence", 0.0))
            
            logger.info(f"Speech from {call_sid}: {speech_result} (confidence: {confidence})")
            
            # Get the persona for this call
            if call_sid not in self.active_calls:
                logger.warning(f"No active call found for {call_sid}, using default persona")
                persona = self.persona_manager.select_random_persona()
                self.active_calls[call_sid] = {"persona": persona}
            else:
                persona = self.active_calls[call_sid]["persona"]
            
            # Generate AI-powered response based on persona and conversation context
            if confidence < 0.5:
                # Low confidence - ask for clarification
                response_text = "I'm sorry, I didn't quite catch that. Could you speak a bit louder?"
            else:
                # Use Gemini AI to generate contextual response
                response_text = await self.ai_engine.generate_response(persona, speech_result, call_sid)
            
            # Create TwiML response with optimized voice settings
            response = VoiceResponse()
            response.say(response_text, voice="Polly.Joanna", rate=1, pitch=1.0)
            
            # Continue gathering speech
            gather = response.gather(
                input="speech",
                action=f"{os.getenv('NGROK_TUNNEL_URL')}/webhook/speech",
                speech_timeout="5",
                timeout=15
            )
            
            # Fallback
            response.say("I'm still here. Please continue talking.", voice="Polly.Joanna", rate=1)
            response.redirect(f"{os.getenv('NGROK_TUNNEL_URL')}/webhook/speech")
            
            return response.to_xml()
        except Exception as e:
            logger.error(f"Error in handle_speech_result: {e}")
            # Return a simple response on error
            response = VoiceResponse()
            response.say("I'm sorry, I didn't catch that. Could you repeat?", voice="Polly.Joanna", rate=1)
            response.redirect(f"{os.getenv('NGROK_TUNNEL_URL')}/webhook/speech")
            return response.to_xml()
    

    async def handle_call_status(self, form_data):
        """Handle call status updates (completed, failed, etc.)"""
        call_sid = form_data.get("CallSid")
        call_status = form_data.get("CallStatus")
        call_duration = form_data.get("CallDuration")
        
        logger.info(f"Call {call_sid} status: {call_status}, duration: {call_duration}")
        
        if call_status == "completed" and call_sid in self.active_calls:
            # Update call in database
            async with AsyncSessionLocal() as db:
                call = await db.get(Call, self.active_calls[call_sid]["call_id"])
                if call:
                    call.end_time = datetime.utcnow()
                    call.duration = float(call_duration) if call_duration else 0.0
                    call.status = "completed"
                    await db.commit()
            
            # Remove from active calls
            del self.active_calls[call_sid]
        
        return {"status": "ok"}

    def _default_response(self):
        """Default response for unknown calls"""
        response = VoiceResponse()
        response.say("Hello! I'm not quite ready to talk right now. Please call back later!", voice="alice")
        response.hangup()
        return response.to_xml(), 200, {"Content-Type": "text/xml"}
