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
        """Forward call to Vapi agent - for suspected spam calls"""
        
        logger.info("🕵️ Forwarding to Vapi Detective Agent - Suspected spam call detected")
        
        # First, ask for the purpose of the call using Twilio
        # This allows us to capture the response for Layer 2 analysis
        response = VoiceResponse()
        
        response.say("Hello! I'm here to help you today.", voice="Polly.Joanna")
        
        # Gather the purpose of the call
        gather = response.gather(
            input='speech',
            action='/webhook/analyze-purpose',
            speech_timeout='auto',
            timeout=15,
            speech_model='experimental_conversations'
        )
        gather.say("What's the purpose of this call? Please answer after the tone.", voice="Polly.Joanna")
        
        # If no response, try again
        response.say("I didn't hear anything. Could you please tell me why you're calling?", voice="Polly.Joanna")
        
        # Second chance
        gather2 = response.gather(
            input='speech',
            action='/webhook/analyze-purpose',
            speech_timeout='auto',
            timeout=10
        )
        gather2.say("Hello? Are you there?", voice="Polly.Joanna")
        
        # If still no response, end call
        response.say("I'm sorry, I cannot hear you. Please try calling back. Goodbye!", voice="Polly.Joanna")
        response.hangup()
        
        return str(response)
    
    def connect_to_vapi_agent(self, form_data):
        """Transfer call to Vapi AI Agent using Twilio's REST API"""
        
        logger.info("🔄 Transferring call to Vapi AI Agent")
        
        # Get call SID from form data
        call_sid = form_data.get('CallSid')
        
        if call_sid:
            try:
                # Update the call to redirect to Vapi
                # Based on your Twilio settings, this should be the correct endpoint
                vapi_webhook = "https://api.vapi.ai/twilio/voice"
                
                # Update the call's webhook URL to point to Vapi
                call = self.client.calls(call_sid).update(
                    url=vapi_webhook,
                    method='POST'
                )
                
                logger.info(f"✅ Successfully transferred call {call_sid} to Vapi")
                
                # Return empty TwiML since we've transferred the call
                response = VoiceResponse()
                return str(response)
                
            except Exception as e:
                logger.error(f"❌ Failed to transfer call to Vapi: {e}")
                # Fallback to our detective agent
                return self._fallback_detective_agent()
        else:
            logger.error("❌ No CallSid found - cannot transfer to Vapi")
            return self._fallback_detective_agent()
    
    def _fallback_detective_agent(self):
        """Fallback detective agent conversation if Vapi transfer fails"""
        response = VoiceResponse()
        
        response.say("Thank you for that information. Let me connect you to our specialist.", voice="Polly.Joanna")
        response.pause(length=1)
        response.say("Hello! I understand you mentioned insurance. Can you tell me more about what you're offering?", voice="Polly.Joanna")
        
        gather = response.gather(
            input='speech',
            action='/webhook/detective-conversation',
            speech_timeout='auto',
            timeout=30
        )
        gather.say("I'm listening.", voice="Polly.Joanna")
        
        response.say("Thank you for your time. Goodbye!", voice="Polly.Joanna")
        response.hangup()
        
        return str(response)
    
    def forward_call_normally(self, form_data):
        """Forward call normally - for likely legitimate calls"""
        response = VoiceResponse()
        
        logger.info("📞 Forwarding call normally - Likely legitimate caller")
        
        # For legitimate calls - let's make this more welcoming
        response.say("Hello! Thank you for calling. I'm here to help you.", voice="Polly.Joanna")
        
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