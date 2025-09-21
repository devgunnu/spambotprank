#!/usr/bin/env python3
"""
Register Twilio phone number with Vapi
This script will register your Twilio number so Vapi can handle calls to it
"""

import asyncio
import os
import sys
import requests
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from vapi_integration import VapiIntegration

async def register_phone_number():
    """Register Twilio phone number with Vapi"""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["VAPI_API_KEY", "TWILIO_PHONE_NUMBER", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    vapi = VapiIntegration()
    
    print("🚀 Registering Twilio phone number with Vapi...")
    
    # Step 1: Create Twilio credential
    print("\n🔑 Step 1: Creating Twilio credential...")
    credential_config = {
        "provider": "twilio",
        "accountSid": os.getenv("TWILIO_ACCOUNT_SID"),
        "authToken": os.getenv("TWILIO_AUTH_TOKEN")
    }
    
    try:
        response = requests.post(
            "https://api.vapi.ai/credential",
            headers=vapi.headers,
            json=credential_config
        )
        
        if response.status_code == 201:
            credential_data = response.json()
            credential_id = credential_data.get('id')
            print(f"✅ Created Twilio credential: {credential_id}")
        else:
            print(f"❌ Failed to create credential: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating credential: {e}")
        return False
    
    # Step 2: Register phone number
    print("\n📞 Step 2: Registering phone number with Vapi...")
    phone_config = {
        "provider": "twilio",
        "number": os.getenv("TWILIO_PHONE_NUMBER"),
        "credentialId": credential_id
    }
    
    try:
        response = requests.post(
            "https://api.vapi.ai/phone-number",
            headers=vapi.headers,
            json=phone_config
        )
        
        if response.status_code == 201:
            phone_data = response.json()
            phone_number_id = phone_data.get('id')
            print(f"✅ Registered phone number: {os.getenv('TWILIO_PHONE_NUMBER')}")
            print(f"   Phone Number ID: {phone_number_id}")
        else:
            print(f"❌ Failed to register phone number: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error registering phone number: {e}")
        return False
    
    # Step 3: Assign assistant to phone number
    print("\n🔗 Step 3: Assigning assistant to phone number...")
    assistant_id = "ef10f4aa-68ea-488b-9ee4-1c19f02fda3a"  # Our spam call waster assistant
    
    try:
        response = requests.patch(
            f"https://api.vapi.ai/phone-number/{phone_number_id}",
            headers=vapi.headers,
            json={"assistantId": assistant_id}
        )
        
        if response.status_code == 200:
            print(f"✅ Assigned assistant to phone number")
        else:
            print(f"❌ Failed to assign assistant: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error assigning assistant: {e}")
        return False
    
    print("\n🎉 Phone number registration complete!")
    print(f"📞 Your Twilio number {os.getenv('TWILIO_PHONE_NUMBER')} is now registered with Vapi")
    print("🎯 Calls should now be handled by Vapi with natural voice models!")
    
    return True

async def main():
    """Main function"""
    print("🎯 Register Twilio Phone Number with Vapi")
    print("=" * 40)
    
    success = await register_phone_number()
    
    if success:
        print("\n✅ Registration successful!")
        print("📞 Test your phone number now - it should work with Vapi!")
    else:
        print("\n❌ Registration failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
