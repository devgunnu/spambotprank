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
from datetime import datetime

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
    
    # Layer 1: Basic call number scan
    layer1_result = await server_communicator.layer1_spam_check(from_number, to_number, form_data)
    
    # If Layer 1 has high confidence it's spam, reject immediately
    if (layer1_result.get('is_spam', False) and 
        layer1_result.get('confidence', 0.0) > 0.9):
        logger.info(f"🚨 Layer 1 HIGH CONFIDENCE SPAM: {from_number} (confidence: {layer1_result.get('confidence', 0.0)})")
        twiml_response = twilio_handler.reject_call("Known spam number")
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Layer 2: Pretrained spam ML model
    layer2_result = await server_communicator.layer2_ml_check(from_number, to_number, form_data)
    
    # Calculate combined confidence from both layers
    layer1_conf = layer1_result.get('confidence', 0.0) if layer1_result.get('is_spam', False) else 0.0
    layer2_conf = layer2_result.get('confidence', 0.0) if layer2_result.get('is_spam', False) else 0.0
    combined_confidence = max(layer1_conf, layer2_conf)
    
    logger.info(f"🔍 Analysis complete - L1: {layer1_conf:.2f}, L2: {layer2_conf:.2f}, Combined: {combined_confidence:.2f}")
    
    # If 50%+ confidence that call is likely a scammer -> Detective Agent (VAPI)
    if combined_confidence >= 0.5:
        logger.info(f"🕵️ 50%+ spam confidence ({combined_confidence:.2f}) - Forwarding to Detective Agent (VAPI)")
        twiml_response = twilio_handler.forward_to_vapi(form_data)
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Low confidence - likely legitimate call, reject politely
    logger.info(f"✅ Low spam confidence ({combined_confidence:.2f}) - Likely legitimate call, forwarding normally")
    twiml_response = twilio_handler.forward_call_normally(form_data)
    return PlainTextResponse(content=twiml_response, media_type="text/xml")


@app.post("/webhook/voice-response")
async def handle_voice_response(request: Request):
    """Detective Agent - Handle suspected spam caller responses"""
    form_data = await request.form()
    
    # Extract speech result
    speech_result = form_data.get('SpeechResult', '')
    speech_confidence = form_data.get('SpeechConfidence', 0)
    from_number = form_data.get('From', '')
    
    logger.info(f"🕵️ Detective Agent analyzing response from {from_number}: '{speech_result}' (confidence: {speech_confidence})")
    
    # Analyze the caller's purpose using Layer 2 ML
    if speech_result and len(speech_result.strip()) > 3:
        to_number = form_data.get('To', '+14806608282')
        
        # Enhanced Layer 2 analysis with speech content
        enhanced_form_data = dict(form_data)
        enhanced_form_data['SpeechResult'] = speech_result
        enhanced_form_data['SpeechConfidence'] = speech_confidence
        
        layer2_result = await server_communicator.layer2_ml_check(from_number, to_number, enhanced_form_data)
        
        spam_confidence = layer2_result.get('confidence', 0.0) if layer2_result.get('is_spam', False) else 0.0
        
        logger.info(f"🔍 Detective Agent analysis: spam_confidence={spam_confidence:.2f}")
        
        # If high confidence spam (>70%), reject the call
        if spam_confidence > 0.7:
            logger.info(f"🚨 Detective Agent CONFIRMED SPAM: {from_number} - '{speech_result}' (confidence: {spam_confidence:.2f})")
            
            # Post suspect information to RAG database
            suspect_info = [
                f"Confirmed spam call from {from_number}",
                f"Caller statement: '{speech_result}'",
                f"Confidence: {spam_confidence:.2f}",
                f"Date: {datetime.now().isoformat()}"
            ]
            
            await server_communicator.post_suspect_information(
                suspect_info, 
                {"phone_number": from_number, "source": "detective_agent", "confidence": spam_confidence}
            )
            
            twiml_response = twilio_handler.reject_call("Thank you, we have all the information we need")
            return PlainTextResponse(content=twiml_response, media_type="text/xml")
        
        # If medium confidence (30-70%), gather more information
        elif spam_confidence > 0.3:
            logger.info(f"🤔 Detective Agent gathering more info: {from_number} (confidence: {spam_confidence:.2f})")
            
            response = VoiceResponse()
            response.say("I see. Can you tell me more about that?", voice="Polly.Joanna")
            
            gather = response.gather(
                input='speech',
                action='/webhook/voice-response',
                speech_timeout='auto',
                timeout=15
            )
            gather.say("Please provide more details about your request.", voice="Polly.Joanna")
            
            # If no response, end call
            response.say("Thank you for calling. Goodbye!", voice="Polly.Joanna")
            response.hangup()
            
            return PlainTextResponse(content=str(response), media_type="text/xml")
        
        # Low confidence (<30%), likely legitimate - forward the call
        else:
            logger.info(f"✅ Detective Agent: Likely legitimate caller {from_number} (confidence: {spam_confidence:.2f})")
            
            # Get the original target number (the actual user's number)
            to_number = form_data.get('To')
            
            response = VoiceResponse()
            response.say("Thank you for that information. I'll connect you now.", voice="Polly.Joanna")
            
            # Directly dial the target user's number
            response.dial(to_number, timeout=30, caller_id=from_number)
            
            # If dial fails or times out
            response.say("I wasn't able to connect your call. Please try again later.", voice="Polly.Joanna")
            response.hangup()
            
            return PlainTextResponse(content=str(response), media_type="text/xml")
    
    # If no meaningful speech, ask again
    response = VoiceResponse()
    response.say("I'm sorry, I didn't understand that. Could you please repeat?", voice="Polly.Joanna")
    
    gather = response.gather(
        input='speech',
        action='/webhook/voice-response',
        speech_timeout='auto',
        timeout=10
    )
    gather.say("Please tell me clearly what you need.", voice="Polly.Joanna")
    
    response.say("I'm having trouble hearing you. Please try calling back. Goodbye!", voice="Polly.Joanna")
    response.hangup()
    
    return PlainTextResponse(content=str(response), media_type="text/xml")

@app.post("/webhook/legitimate-response")
async def handle_legitimate_response(request: Request):
    """Handle responses from likely legitimate callers"""
    form_data = await request.form()
    
    speech_result = form_data.get('SpeechResult', '')
    from_number = form_data.get('From', '')
    
    logger.info(f"📞 Legitimate caller response from {from_number}: '{speech_result}'")
    
    # For legitimate callers, provide helpful responses
    response = VoiceResponse()
    response.say("Thank you for calling. I understand you need assistance.", voice="Polly.Joanna")
    
    # You could add logic here to route to different departments
    # or forward to the actual user's phone
    
    response.say("Your call is important to us. Please try calling during business hours for better assistance.", voice="Polly.Joanna")
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
    phone_number = data.get('phone_number', '')
    
    # Create metadata with additional context
    metadata = {
        "source": "vapi_agent",
        "timestamp": data.get('timestamp', ''),
        "phone_number": phone_number
    }
    
    # Filter out empty values
    metadata = {k: v for k, v in metadata.items() if v}
    
    return await server_communicator.post_suspect_information(texts, metadata)

@app.post("/api/agent/analyze_call_purpose")
async def analyze_call_purpose(request: Request):
    """Analyze caller's stated purpose using ML model"""
    data = await request.json()
    call_purpose = data.get('call_purpose', '')
    phone_number = data.get('phone_number', 'Unknown')
    
    # Create proper JSON payload for Layer 2 analysis
    call_data = {
        'From': phone_number,
        'To': 'Unknown',
        'CallSid': '',
        'Direction': 'inbound',
        'Status': 'completed',
        'SpeechResult': call_purpose,
        'SpeechConfidence': '1.0',
        'threshold': 0.7  # Higher threshold for purpose analysis
    }
    
    # Use Layer 2 ML analysis
    layer2_result = await server_communicator.layer2_ml_check(phone_number, 'Unknown', call_data)
    
    return {
        "is_spam": layer2_result.get('is_spam', False),
        "confidence": layer2_result.get('confidence', 0.0),
        "reason": layer2_result.get('reason', 'Analysis complete'),
        "call_purpose": call_purpose,
        "layer": layer2_result.get('layer', 2),
        "method": layer2_result.get('method', 'ml_analysis')
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
    
    # Check if Layer 1 detected spam and the result is reliable
    if (layer1_result.get('is_spam', False) and 
        layer1_result.get('confidence', 0.0) > 0.5 and
        layer1_result.get('layer') == 1):
        logger.info(f"🚨 Layer 1 SPAM DETECTED: {from_number} (confidence: {layer1_result.get('confidence', 0.0)})")
        twiml_response = twilio_handler.reject_call("Spam detected")
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Layer 1 passed or failed - forward to Vapi agent
    if layer1_result.get('is_spam', False):
        logger.warning(f"⚠️ Layer 1 detected potential spam but confidence too low: {from_number}")
    else:
        logger.info(f"✅ Layer 1 passed: {from_number}")
    
    logger.info(f"➡️ Forwarding to Vapi agent: {from_number}")
    twiml_response = twilio_handler.forward_to_vapi(form_data)
    return PlainTextResponse(content=twiml_response, media_type="text/xml")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve spam detection dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
