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

# Simple file-based storage for call purposes (for Vapi to access)
import json
import os
from pathlib import Path

CALL_PURPOSES_FILE = Path("call_purposes.json")

def load_call_purposes():
    """Load call purposes from file"""
    if CALL_PURPOSES_FILE.exists():
        try:
            with open(CALL_PURPOSES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_call_purposes(purposes):
    """Save call purposes to file"""
    try:
        with open(CALL_PURPOSES_FILE, 'w') as f:
            json.dump(purposes, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save call purposes: {e}")

call_purposes = load_call_purposes()

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
    
    # Layer 1 returns binary results: confidence is 1.0 if spam, 0.0 if not
    if layer1_result.get('is_spam', False):
        logger.info(f"🚨 Layer 1 SPAM DETECTED: {from_number} - Known spam number in database")
        twiml_response = twilio_handler.reject_call("Known spam number")
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Layer 2: Pretrained spam ML model
    layer2_result = await server_communicator.layer2_ml_check(from_number, to_number, form_data)
    
    # Calculate combined confidence from both layers
    # Layer 1: Binary (passed if we reach here, so confidence = 0.0)
    # Layer 2: Stochastic confidence (0.0-1.0 range from ML model)
    layer1_conf = 0.0  # Layer 1 passed (not spam), so confidence is 0
    layer2_conf = layer2_result.get('confidence', 0.0) if layer2_result.get('is_spam', False) else 0.0
    
    # For routing decision, we primarily use Layer 2's ML confidence
    spam_confidence = layer2_conf
    
    logger.info(f"🔍 Analysis complete - L1: passed (not in spam DB), L2: {layer2_conf:.2f}, Spam confidence: {spam_confidence:.2f}")
    
    # Note: Insurance keyword detection happens in analyze-purpose endpoint
    
    # If 50%+ confidence that call is likely a scammer -> Detective Agent (VAPI)
    if spam_confidence >= 0.5:
        logger.info(f"🕵️ 50%+ spam confidence ({spam_confidence:.2f}) - Forwarding to Detective Agent (VAPI)")
        twiml_response = twilio_handler.forward_to_vapi(form_data)
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Low confidence - likely legitimate call, forward normally
    logger.info(f"✅ Low spam confidence ({spam_confidence:.2f}) - Likely legitimate call, forwarding normally")
    twiml_response = twilio_handler.forward_call_normally(form_data)
    return PlainTextResponse(content=twiml_response, media_type="text/xml")


@app.post("/webhook/analyze-purpose")
async def analyze_call_purpose_and_forward(request: Request):
    """Analyze the caller's stated purpose and then forward to Vapi Detective Agent"""
    form_data = await request.form()
    
    # Extract speech result
    speech_result = form_data.get('SpeechResult', '')
    speech_confidence = form_data.get('SpeechConfidence', 0)
    from_number = form_data.get('From', '')
    to_number = form_data.get('To', '+14806608282')
    
    logger.info(f"🎤 Purpose analysis from {from_number}: '{speech_result}' (confidence: {speech_confidence})")
    
    # Analyze the caller's purpose using Layer 2 ML if we got a response
    if speech_result and len(speech_result.strip()) > 3:
        # Enhanced Layer 2 analysis with speech content
        enhanced_form_data = dict(form_data)
        enhanced_form_data['SpeechResult'] = speech_result
        enhanced_form_data['SpeechConfidence'] = speech_confidence
        
        layer2_result = await server_communicator.layer2_ml_check(from_number, to_number, enhanced_form_data)
        spam_confidence = layer2_result.get('confidence', 0.0) if layer2_result.get('is_spam', False) else 0.0
        
        # Check for insurance-related keywords to force detective agent
        speech_lower = speech_result.lower()
        insurance_keywords = ['insurance', 'policy', 'coverage', 'premium', 'claim', 'sell you', 'offer you']
        if any(keyword in speech_lower for keyword in insurance_keywords):
            logger.info(f"🎯 Insurance/Sales keyword detected: '{speech_result}' - Forcing Detective Agent")
            spam_confidence = 0.8  # Force high confidence for insurance/sales calls
        
        logger.info(f"🔍 Purpose analysis result: spam_confidence={spam_confidence:.2f}")
        
        # If very high confidence spam (>80%), reject immediately
        if spam_confidence > 0.8 and 'insurance' not in speech_lower:
            logger.info(f"🚨 HIGH CONFIDENCE SPAM DETECTED: {from_number} - '{speech_result}' (confidence: {spam_confidence:.2f})")
            twiml_response = twilio_handler.reject_call("Thank you for your call. Goodbye.")
            return PlainTextResponse(content=twiml_response, media_type="text/xml")
        
        # Store the call purpose for Vapi to access later
        call_purposes[from_number] = {
            'purpose': speech_result,
            'confidence': speech_confidence,
            'spam_confidence': spam_confidence,
            'timestamp': datetime.now().isoformat()
        }
        save_call_purposes(call_purposes)  # Persist to file
        logger.info(f"📝 Stored call purpose for Vapi: '{speech_result}' from {from_number}")
    
    # Now connect to Vapi Detective Agent
    # Vapi will take over and can call our functions to get the stored purpose
    logger.info("🔄 Connecting to Vapi Detective Agent")
    
    twiml_response = twilio_handler.connect_to_vapi_agent(form_data)
    return PlainTextResponse(content=twiml_response, media_type="text/xml")

@app.post("/webhook/detective-conversation")
async def handle_detective_conversation(request: Request):
    """Handle Detective Agent conversation - gather information from suspected scammers"""
    form_data = await request.form()
    
    speech_result = form_data.get('SpeechResult', '')
    from_number = form_data.get('From', '')
    
    logger.info(f"🕵️ Detective Agent conversation from {from_number}: '{speech_result}'")
    
    response = VoiceResponse()
    
    if speech_result and len(speech_result.strip()) > 2:
        # Store the conversation
        if from_number in call_purposes:
            if 'conversation' not in call_purposes[from_number]:
                call_purposes[from_number]['conversation'] = []
            call_purposes[from_number]['conversation'].append({
                'timestamp': datetime.now().isoformat(),
                'speech': speech_result
            })
            save_call_purposes(call_purposes)
        
        # Detective Agent responses - act interested to gather more info
        responses = [
            "That's very interesting! Tell me more about that.",
            "I see. Can you give me more details about your company?",
            "That sounds great! What kind of rates are you offering?",
            "Fascinating! How long have you been in this business?",
            "I'm definitely interested. What information do you need from me?",
            "That's exactly what I've been looking for! Can you tell me more?"
        ]
        
        import random
        detective_response = random.choice(responses)
        response.say(detective_response, voice="Polly.Joanna")
        
        # Continue gathering information
        gather = response.gather(
            input='speech',
            action='/webhook/detective-conversation',
            speech_timeout='auto',
            timeout=30
        )
        gather.say("I'm listening.", voice="Polly.Joanna")
        
        # After 5 exchanges, start wrapping up
        conversation_count = len(call_purposes.get(from_number, {}).get('conversation', []))
        if conversation_count >= 5:
            response.say("Thank you so much for all this information. I need to discuss this with my spouse. Can I call you back?", voice="Polly.Joanna")
            response.hangup()
    else:
        response.say("I'm sorry, I didn't catch that. Could you repeat what you said?", voice="Polly.Joanna")
        
        gather = response.gather(
            input='speech',
            action='/webhook/detective-conversation',
            speech_timeout='auto',
            timeout=15
        )
        gather.say("Please speak clearly.", voice="Polly.Joanna")
        
        response.say("I'm having trouble hearing you. Please try calling back later.", voice="Polly.Joanna")
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

@app.post("/api/agent/get_call_purpose")
async def get_call_purpose(request: Request):
    """Get the stored call purpose for a phone number"""
    data = await request.json()
    phone_number = data.get('phone_number', '')
    
    if phone_number in call_purposes:
        purpose_data = call_purposes[phone_number]
        logger.info(f"📋 Vapi requested call purpose for {phone_number}: '{purpose_data['purpose']}'")
        return {
            "success": True,
            "phone_number": phone_number,
            "purpose": purpose_data['purpose'],
            "confidence": purpose_data['confidence'],
            "spam_confidence": purpose_data['spam_confidence'],
            "timestamp": purpose_data['timestamp']
        }
    else:
        logger.info(f"❓ No stored call purpose found for {phone_number}")
        return {
            "success": False,
            "phone_number": phone_number,
            "message": "No call purpose found for this number"
        }

@app.post("/api/agent/analyze_call_purpose")
async def analyze_call_purpose(request: Request):
    """Analyze caller's stated purpose using ML model - matches your existing Vapi function"""
    data = await request.json()
    call_purpose = data.get('call_purpose', '')
    
    # Get caller info from the current call context (Vapi should provide this)
    # For now, we'll extract from the stored call purposes or use a default
    phone_number = 'Unknown'
    
    # Try to find the phone number from our stored call purposes
    # This is a simple approach - in production you might want a more robust solution
    for stored_number, stored_data in call_purposes.items():
        if stored_data['purpose'].lower() in call_purpose.lower() or call_purpose.lower() in stored_data['purpose'].lower():
            phone_number = stored_number
            break
    
    logger.info(f"🔍 Analyzing call purpose: '{call_purpose}' for {phone_number}")
    
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
        "phone_number": phone_number
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
    
    # Layer 1: Check spam database (binary result)
    layer1_result = await server_communicator.layer1_spam_check(from_number, to_number, form_data)
    
    # Layer 1 returns binary results: if spam detected, reject immediately
    if layer1_result.get('is_spam', False):
        logger.info(f"🚨 Layer 1 SPAM DETECTED: {from_number} - Known spam number in database")
        twiml_response = twilio_handler.reject_call("Known spam number")
        return PlainTextResponse(content=twiml_response, media_type="text/xml")
    
    # Layer 1 passed - proceed with Layer 2 analysis
    logger.info(f"✅ Layer 1 passed: {from_number} - Not in spam database")
    
    # Layer 2: ML model analysis
    layer2_result = await server_communicator.layer2_ml_check(from_number, to_number, form_data)
    layer2_conf = layer2_result.get('confidence', 0.0) if layer2_result.get('is_spam', False) else 0.0
    
    # Route based on Layer 2 confidence
    if layer2_conf >= 0.5:
        logger.info(f"🕵️ Layer 2 detected potential spam ({layer2_conf:.2f}) - Forwarding to Detective Agent")
        twiml_response = twilio_handler.forward_to_vapi(form_data)
    else:
        logger.info(f"✅ Low spam confidence ({layer2_conf:.2f}) - Forwarding normally")
        twiml_response = twilio_handler.forward_call_normally(form_data)
    
    return PlainTextResponse(content=twiml_response, media_type="text/xml")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve spam detection dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
