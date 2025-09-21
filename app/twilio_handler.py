from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TwilioHandler:
    def __init__(self):
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.vapi_webhook_url = os.getenv("VAPI_WEBHOOK_URL", "https://your-vapi-webhook-url.com")

    def reject_call(self, reason: str = "Call rejected"):
        """Reject a call with a message"""
        response = VoiceResponse()
        response.say(f"Sorry, {reason}. Goodbye.", voice="Polly.Joanna")
        response.hangup()
        return str(response)
    
    
    def forward_to_vapi(self, form_data):
        """Forward call to Vapi agent"""
        response = VoiceResponse()
        # Based on Vapi documentation: Vapi should call YOUR server URL
        # Your Vapi dashboard should have Server URL set to your ngrok URL
        # This way, Vapi calls your server and you handle the conversation
        
        logger.info("🔄 Call passed spam check - Vapi will call our server URL")
        
        # Since Vapi is configured to call our server URL, we handle the conversation
        # The Vapi agent will call our /webhook/voice endpoint and we respond with TwiML
        
        # Start the conversation
        response.say("Hello! How can I help you today?", voice="Polly.Joanna")
        
        # Add a gather to collect speech input
        gather = response.gather(
            input='speech',
            action='/webhook/voice-response',
            speech_timeout='auto',
            timeout=10
        )
        gather.say("Please tell me what you need.", voice="Polly.Joanna")
        
        # If no input, say goodbye
        response.say("I didn't hear anything. Goodbye!", voice="Polly.Joanna")
        response.hangup()
        
        return str(response)
    
    async def handle_call_status(self, form_data):
        """Handle call status updates"""
        call_sid = form_data.get("CallSid")
        status = form_data.get("CallStatus")
        duration = form_data.get("CallDuration", 0)
        
        logger.info(f"Call {call_sid} status: {status} (Duration: {duration}s)")
        return {"status": "received"}