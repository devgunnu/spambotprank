"""
Example Python FastAPI backend for call routing system.
This is a minimal implementation to test your mobile app.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal
import uvicorn

app = FastAPI(title="Call Routing Backend", version="1.0.0")

# Data models
class CallRouteRequest(BaseModel):
    callerId: str
    timestamp: str
    deviceId: str
    action: Literal["route", "reject", "forward"]

class CallRouteResponse(BaseModel):
    success: bool
    action: Literal["allow", "reject", "redirect"]
    redirectNumber: Optional[str] = None
    message: Optional[str] = None

class CallStatusRequest(BaseModel):
    callerId: str
    status: Literal["answered", "rejected", "missed"]
    timestamp: str

class DeviceRegistration(BaseModel):
    deviceId: str
    phoneNumber: Optional[str] = None
    platform: str
    timestamp: str

# In-memory storage (use a database in production)
registered_devices = {}
call_history = []
blocked_numbers = [
    "+1234567890",  # Example blocked number
    "spam",         # Block any caller ID containing "spam"
]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/route-call", response_model=CallRouteResponse)
async def route_call(request: CallRouteRequest):
    """
    Main call routing logic.
    Decides what to do with incoming calls based on caller ID.
    """
    print(f"📞 Incoming call from {request.callerId} on device {request.deviceId}")
    
    # Log the call
    call_history.append({
        "callerId": request.callerId,
        "deviceId": request.deviceId,
        "timestamp": request.timestamp,
        "action": request.action
    })
    
    # Check if caller should be blocked
    caller_id_lower = request.callerId.lower()
    should_block = any(
        blocked_num in caller_id_lower 
        for blocked_num in [num.lower() for num in blocked_numbers]
    )
    
    if should_block:
        print(f"🚫 Blocking call from {request.callerId}")
        return CallRouteResponse(
            success=True,
            action="reject",
            message=f"Call from {request.callerId} blocked"
        )
    
    # Check if it's a known spam pattern
    spam_indicators = ["telemarketer", "unknown", "private"]
    is_spam = any(indicator in caller_id_lower for indicator in spam_indicators)
    
    if is_spam:
        print(f"🔄 Redirecting potential spam call from {request.callerId}")
        return CallRouteResponse(
            success=True,
            action="redirect",
            redirectNumber="+1800VOICEMAIL",  # Example redirect number
            message="Potential spam call redirected to voicemail"
        )
    
    # Allow the call by default
    print(f"✅ Allowing call from {request.callerId}")
    return CallRouteResponse(
        success=True,
        action="allow",
        message="Call allowed"
    )

@app.post("/call-status")
async def call_status(request: CallStatusRequest):
    """Receive call status updates from the mobile app"""
    print(f"📊 Call status update: {request.callerId} - {request.status}")
    
    # Update call history
    for call in reversed(call_history):
        if call["callerId"] == request.callerId:
            call["final_status"] = request.status
            break
    
    return {"success": True, "message": "Status updated"}

@app.post("/register-device")
async def register_device(request: DeviceRegistration):
    """Register a device for call routing"""
    print(f"📱 Registering device: {request.deviceId}")
    
    registered_devices[request.deviceId] = {
        "phoneNumber": request.phoneNumber,
        "platform": request.platform,
        "registeredAt": request.timestamp,
        "lastSeen": datetime.now().isoformat()
    }
    
    return {"success": True, "message": "Device registered successfully"}

@app.get("/routing-config")
async def get_routing_config():
    """Get routing configuration"""
    return {
        "blockedNumbers": blocked_numbers,
        "redirectNumber": "+1800VOICEMAIL",
        "spamDetection": True,
        "autoBlock": True
    }

@app.get("/call-history")
async def get_call_history(limit: int = 50):
    """Get recent call history"""
    return {
        "calls": call_history[-limit:],
        "total": len(call_history)
    }

@app.get("/devices")
async def get_registered_devices():
    """Get all registered devices"""
    return registered_devices

@app.post("/block-number")
async def block_number(number: str):
    """Add a number to the block list"""
    if number not in blocked_numbers:
        blocked_numbers.append(number)
        print(f"🚫 Added {number} to block list")
    return {"success": True, "blockedNumbers": blocked_numbers}

@app.post("/unblock-number")
async def unblock_number(number: str):
    """Remove a number from the block list"""
    if number in blocked_numbers:
        blocked_numbers.remove(number)
        print(f"✅ Removed {number} from block list")
    return {"success": True, "blockedNumbers": blocked_numbers}

# CORS middleware for development
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your mobile app's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    print("🚀 Starting Call Routing Backend Server")
    print("📱 Connect your mobile app to: http://YOUR_IP_ADDRESS:8000")
    print("🔧 API docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,
        log_level="info"
    )