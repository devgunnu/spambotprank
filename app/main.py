from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from dotenv import load_dotenv
from .twilio_handler import TwilioHandler
from .ai_engine import ServerCommunicator
import logging
from contextlib import asynccontextmanager

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
        return twilio_handler.reject_call("Spam detected")
    
    # Layer 2: ML model check
    layer2_result = await server_communicator.layer2_ml_check(from_number, to_number, form_data)
    if layer2_result['is_spam']:
        logger.info(f"🚨 Layer 2 SPAM DETECTED: {from_number}")
        return twilio_handler.reject_call("Suspicious call pattern detected")
    
    # Not spam - forward to Vapi agent
    logger.info(f"✅ Call approved: {from_number} -> Forwarding to Vapi")
    return twilio_handler.forward_to_vapi(form_data)

@app.post("/webhook/status")
async def handle_call_status(request: Request):
    """Handle call status updates"""
    form_data = await request.form()
    return await twilio_handler.handle_call_status(form_data)

# Agent Functions - These will be called by Vapi agent
@app.get("/api/agent/get_user_information")
async def get_user_information(query: str):
    """Get user information from RAG database"""
    return await server_communicator.get_user_information(query)

@app.get("/api/agent/get_call_history")
async def get_call_history(query: str):
    """Get call history from RAG database"""
    return await server_communicator.get_call_history(query)

@app.post("/api/agent/post_suspect_information")
async def post_suspect_information(request: Request):
    """Post suspect information to RAG database"""
    data = await request.json()
    return await server_communicator.post_suspect_information(data['texts'])

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve spam detection dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
