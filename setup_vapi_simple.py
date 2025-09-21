#!/usr/bin/env python3
"""
Simple Vapi integration setup
This script will:
1. Use the existing Vapi assistant
2. Provide instructions for updating Twilio webhook
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from vapi_integration import VapiIntegration

async def setup_simple_vapi_integration():
    """Set up simple Vapi integration with existing assistant"""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["VAPI_API_KEY", "TWILIO_PHONE_NUMBER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    vapi = VapiIntegration()
    
    print("🚀 Setting up simple Vapi integration...")
    
    # Step 1: Get existing assistants
    print("\n🤖 Step 1: Checking existing Vapi assistants...")
    assistants = await vapi.get_assistants()
    
    if not assistants:
        print("❌ No assistants found in Vapi account")
        return False
    
    # Use the first available assistant
    assistant = assistants[0]
    assistant_id = assistant.get('id')
    assistant_name = assistant.get('name', 'Unnamed')
    
    print(f"✅ Found assistant: {assistant_name} (ID: {assistant_id})")
    
    # Step 2: Display configuration instructions
    print("\n📋 Step 2: Twilio Configuration Instructions")
    print("=" * 50)
    print("To integrate Vapi with your Twilio number, follow these steps:")
    print()
    print("1. Go to your Twilio Console:")
    print("   https://console.twilio.com/us1/develop/phone-numbers/manage/incoming")
    print()
    print("2. Find your phone number and click on it")
    print(f"   Phone Number: {os.getenv('TWILIO_PHONE_NUMBER')}")
    print()
    print("3. In the 'Voice & Fax' section, update the webhook:")
    print("   - Webhook URL: https://api.vapi.ai/twilio/inbound_call")
    print("   - HTTP Method: POST")
    print()
    print("4. Save the configuration")
    print()
    print("🎯 That's it! Your calls will now be handled by Vapi with natural voice models!")
    print()
    print("📞 Test by calling your Twilio number")
    print(f"   Number: {os.getenv('TWILIO_PHONE_NUMBER')}")
    print()
    print("🔧 Vapi Assistant Details:")
    print(f"   - Name: {assistant_name}")
    print(f"   - ID: {assistant_id}")
    print(f"   - Voice: {assistant.get('voice', {}).get('provider', 'Unknown')}")
    
    return True

async def main():
    """Main setup function"""
    print("🎯 Simple Vapi + Twilio Integration Setup")
    print("=" * 45)
    
    success = await setup_simple_vapi_integration()
    
    if success:
        print("\n🎉 Setup instructions provided!")
        print("📞 Your Twilio number will use Vapi's natural voice models!")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
