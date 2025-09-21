#!/usr/bin/env python3
"""
Spam Call Time-Waster - Main Entry Point
Run this file to start the application
"""

import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN", 
        "TWILIO_PHONE_NUMBER",
        "VAPI_API_KEY",
        "NGROK_TUNNEL_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file before running the application.")
        exit(1)
    
    print("🎭 Starting Spam Detection Gateway...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("🔗 Make sure your ngrok tunnel is running and webhooks are configured!")
    print("🤖 Spam calls will be forwarded to Vapi agent")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
