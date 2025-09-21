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
        response.redirect(self.vapi_webhook_url)
        return str(response)
    
    async def handle_call_status(self, form_data):
        """Handle call status updates"""
        call_sid = form_data.get("CallSid")
        status = form_data.get("CallStatus")
        duration = form_data.get("CallDuration", 0)
        
        logger.info(f"Call {call_sid} status: {status} (Duration: {duration}s)")
        return {"status": "received"}