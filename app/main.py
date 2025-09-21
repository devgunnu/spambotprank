from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from dotenv import load_dotenv
from .twilio_handler import TwilioHandler
from .ai_engine import ServerCommunicator
import logging
from contextlib import asynccontextmanager
from twilio.twiml.voice_response import VoiceResponse

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Spam Detection Gateway starting up...")
    yield
    # Shutdown
    logger.info("Spam Detection Gateway shutting down")

app = FastAPI(title="Spam Detection Gateway", version="2.0.0", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Initialize services
twilio_handler = TwilioHandler()
server_communicator = ServerCommunicator()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "spam-detection-gateway"}

@app.post("/webhook/voice")
async def handle_incoming_call(request: Request):
    """Main spam detection gateway - receives Twilio calls and routes them"""
    form_data = await request.form()
    
    # Extract call information
    from_number = form_data.get('From')
    to_number = form_data.get('To')
    call_sid = form_data.get('CallSid')
    
    logger.info(f"📞 Incoming call: {from_number} -> {to_number} (SID: {call_sid})")
    
    # Layer 1: Check spam database
    layer1_result = await server_communicator.layer1_spam_check(from_number, to_number, form_data)
    if layer1_result['is_spam']:
        logger.info(f"🚨 Layer 1 SPAM DETECTED: {from_number}")
        twiml_response = twilio_handler.reject_call("Spam detected")
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Layer 1 passed - forward directly to Vapi agent
    logger.info(f"✅ Layer 1 passed: {from_number} -> Forwarding to Vapi agent")
    twiml_response = twilio_handler.forward_to_vapi(form_data)
    return PlainTextResponse(content=twiml_response, media_type="text/xml")


@app.post("/webhook/voice-response")
async def handle_voice_response(request: Request):
    """Handle voice response from caller"""
    form_data = await request.form()
    
    # Extract speech result
    speech_result = form_data.get('SpeechResult', '')
    speech_confidence = form_data.get('SpeechConfidence', 0)
    from_number = form_data.get('From', '')
    
    logger.info(f"🎤 Voice response from {from_number}: {speech_result} (confidence: {speech_confidence})")
    
    # Layer 2: ML analysis of speech content
    if speech_result:
        # Create mock form data for ML analysis
        mock_form_data = {
            'From': from_number,
            'SpeechResult': speech_result,
            'SpeechConfidence': speech_confidence
        }
        
        # Get to_number from the original call data (we need to pass it from the original call)
        to_number = form_data.get('To', '+14806608282')  # Default to your Twilio number
        
        layer2_result = await server_communicator.layer2_ml_check(from_number, to_number, mock_form_data)
        if layer2_result['is_spam']:
            logger.info(f"🚨 Layer 2 SPAM DETECTED: {from_number} - {speech_result}")
            twiml_response = twilio_handler.reject_call("Suspicious content detected")
            return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # If not spam, continue conversation
    response = VoiceResponse()
    response.say("Thank you for that information. How else can I help you?", voice="Polly.Joanna")
    
    # Add another gather
    gather = response.gather(
        input='speech',
        action='/webhook/voice-response',
        speech_timeout='auto',
        timeout=10
    )
    gather.say("Please tell me more.", voice="Polly.Joanna")
    
    # If no input, end call
    response.say("Thank you for calling. Goodbye!", voice="Polly.Joanna")
    response.hangup()
    
    return PlainTextResponse(content=str(response), media_type="text/xml")

@app.post("/webhook/status")
async def handle_call_status(request: Request):
    """Handle call status updates"""
    form_data = await request.form()
    result = await twilio_handler.handle_call_status(form_data)
    return JSONResponse(content=result)

# Agent Functions - These will be called by Vapi agent
@app.post("/api/agent/get_user_information")
async def get_user_information(request: Request):
    """Get user information from RAG database"""
    data = await request.json()
    query = data.get('query', '')
    return await server_communicator.get_user_information(query)

@app.post("/api/agent/get_call_history")
async def get_call_history(request: Request):
    """Get call history from RAG database"""
    data = await request.json()
    query = data.get('query', '')
    return await server_communicator.get_call_history(query)

@app.post("/api/agent/post_suspect_information")
async def post_suspect_information(request: Request):
    """Post suspect information to RAG database"""
    data = await request.json()
    texts = data.get('texts', [])
    return await server_communicator.post_suspect_information(texts)

@app.post("/api/agent/analyze_call_purpose")
async def analyze_call_purpose(request: Request):
    """Analyze caller's stated purpose using ML model"""
    data = await request.json()
    call_purpose = data.get('call_purpose', '')
    
    # Create a mock form_data with the call purpose for Layer 2 analysis
    form_data = {
        'SpeechResult': call_purpose,
        'SpeechConfidence': '1.0',
        'From': 'Unknown',  # We don't have caller info in this context
        'To': 'Unknown'
    }
    
    # Use Layer 2 ML analysis
    layer2_result = await server_communicator.layer2_ml_check('Unknown', 'Unknown', form_data)
    
    return {
        "is_spam": layer2_result.get('is_spam', False),
        "confidence": layer2_result.get('confidence', 0.0),
        "reason": layer2_result.get('reason', 'Analysis complete'),
        "call_purpose": call_purpose
    }

@app.post("/")
async def handle_root_post(request: Request):
    """Handle POST requests to root URL (Vapi webhook)"""
    logger.info("📞 Vapi POST request to root URL - redirecting to webhook/voice")
    form_data = await request.form()
    
    # Extract call information
    from_number = form_data.get('From')
    to_number = form_data.get('To')
    call_sid = form_data.get('CallSid')
    
    logger.info(f"📞 Vapi call: {from_number} -> {to_number} (SID: {call_sid})")
    
    # Layer 1: Check spam database
    layer1_result = await server_communicator.layer1_spam_check(from_number, to_number, form_data)
    if layer1_result['is_spam']:
        logger.info(f"🚨 Layer 1 SPAM DETECTED: {from_number}")
        twiml_response = twilio_handler.reject_call("Spam detected")
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Layer 1 passed - forward directly to Vapi agent
    logger.info(f"✅ Layer 1 passed: {from_number} -> Forwarding to Vapi agent")
    twiml_response = twilio_handler.forward_to_vapi(form_data)
    return PlainTextResponse(content=twiml_response, media_type="text/xml")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve spam detection dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
