from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from dotenv import load_dotenv
from .database import init_db, get_db
from .twilio_handler import TwilioHandler
from .analytics import AnalyticsService
import logging
from contextlib import asynccontextmanager

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Application shutting down")

app = FastAPI(title="Spam Call Time-Waster", version="1.0.0", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static")

# Initialize services
twilio_handler = TwilioHandler()
analytics_service = AnalyticsService()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "spam-call-waster"}

@app.post("/webhook/voice")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio voice webhook"""
    form_data = await request.form()
    twiml_response = await twilio_handler.handle_incoming_call(form_data)
    return Response(content=twiml_response, media_type="text/xml")

@app.post("/webhook/speech")
async def handle_speech(request: Request):
    """Handle speech recognition results"""
    form_data = await request.form()
    twiml_response = await twilio_handler.handle_speech_result(form_data)
    return Response(content=twiml_response, media_type="text/xml")

@app.post("/webhook/status")
async def handle_call_status(request: Request):
    """Handle call status updates"""
    form_data = await request.form()
    return await twilio_handler.handle_call_status(form_data)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve analytics dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get analytics summary for dashboard"""
    return await analytics_service.get_summary()

@app.get("/api/calls")
async def get_recent_calls():
    """Get recent calls list"""
    return await analytics_service.get_recent_calls()

@app.get("/api/calls/{call_id}")
async def get_call_details(call_id: str):
    """Get specific call details"""
    return await analytics_service.get_call_details(call_id)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
