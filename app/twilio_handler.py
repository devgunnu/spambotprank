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
        """Forward call to Detective Agent (VAPI) - for suspected spam calls"""
        response = VoiceResponse()
        
        logger.info("🕵️ Forwarding to Detective Agent (VAPI) - Suspected spam call")
        
        # The Detective Agent will engage with the caller to gather information
        # and determine if they are indeed a scammer
        response.say("Hello! I'm here to help you today. What can I do for you?", voice="Polly.Joanna")
        
        # Add a gather to collect speech input for analysis
        gather = response.gather(
            input='speech',
            action='/webhook/voice-response',
            speech_timeout='auto',
            timeout=15,
            speech_model='experimental_conversations'
        )
        gather.say("Please tell me the purpose of your call.", voice="Polly.Joanna")
        
        # If no input, try again
        response.say("I didn't hear anything. Could you please tell me why you're calling?", voice="Polly.Joanna")
        
        # Second chance to respond
        gather2 = response.gather(
            input='speech',
            action='/webhook/voice-response',
            speech_timeout='auto',
            timeout=10
        )
        gather2.say("Hello? Are you there?", voice="Polly.Joanna")
        
        # If still no response, end call
        response.say("I'm sorry, I cannot hear you. Please try calling back. Goodbye!", voice="Polly.Joanna")
        response.hangup()
        
        return str(response)
    
    def forward_call_normally(self, form_data):
        """Forward call normally - for likely legitimate calls"""
        response = VoiceResponse()
        
        logger.info("📞 Forwarding call normally - Likely legitimate caller")
        
        # For legitimate calls, we can either:
        # 1. Forward to the actual user's phone
        # 2. Handle with a simpler greeting
        # 3. Connect to a different service
        
        # For now, let's handle it as a normal call
        response.say("Hello! Thank you for calling. How can I help you today?", voice="Polly.Joanna")
        
        gather = response.gather(
            input='speech',
            action='/webhook/legitimate-response',
            speech_timeout='auto',
            timeout=10
        )
        gather.say("Please let me know what you need assistance with.", voice="Polly.Joanna")
        
        # If no response, end politely
        response.say("Thank you for calling. Have a great day!", voice="Polly.Joanna")
        response.hangup()
        
        return str(response)
    
    async def handle_call_status(self, form_data):
        """Handle call status updates"""
        call_sid = form_data.get("CallSid")
        status = form_data.get("CallStatus")
        duration = form_data.get("CallDuration", 0)
        
        logger.info(f"Call {call_sid} status: {status} (Duration: {duration}s)")
        return {"status": "received"}