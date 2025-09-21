#!/usr/bin/env python3
"""
Setup script for Vapi integration with Twilio
This script will:
1. Create a Vapi assistant with persona configuration
2. Register your Twilio phone number with Vapi
3. Assign the assistant to handle calls on that number
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from vapi_integration import VapiIntegration
from personas import PersonaManager

async def setup_vapi_integration():
    """Set up Vapi integration with Twilio"""
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["VAPI_API_KEY", "TWILIO_PHONE_NUMBER"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    vapi = VapiIntegration()
    persona_manager = PersonaManager()
    
    print("🚀 Setting up Vapi integration...")
    
    # Step 1: Get a persona for the assistant
    print("\n📋 Step 1: Selecting persona...")
    persona = persona_manager.select_random_persona()
    print(f"✅ Selected persona: {persona.get('persona_name', 'Default')}")
    
    # Step 2: Create Vapi assistant
    print("\n🤖 Step 2: Creating Vapi assistant...")
    assistant_id = await vapi.create_assistant(persona)
    
    if not assistant_id:
        print("❌ Failed to create Vapi assistant")
        return False
    
    print(f"✅ Created assistant with ID: {assistant_id}")
    
    # Step 3: Create credential
    print("\n🔑 Step 3: Creating credential for Twilio integration...")
    credential_id = await vapi.create_credential()
    
    if not credential_id:
        print("❌ Failed to create credential")
        return False
    
    print(f"✅ Created credential: {credential_id}")
    
    # Step 4: Register Twilio phone number
    print("\n📞 Step 4: Registering Twilio phone number with Vapi...")
    twilio_number = os.getenv("TWILIO_PHONE_NUMBER")
    phone_number_id = await vapi.create_phone_number(twilio_number, credential_id)
    
    if not phone_number_id:
        print("❌ Failed to register phone number with Vapi")
        return False
    
    print(f"✅ Registered phone number: {twilio_number}")
    
    # Step 5: Assign assistant to phone number
    print("\n🔗 Step 5: Assigning assistant to phone number...")
    success = await vapi.assign_assistant_to_number(phone_number_id, assistant_id)
    
    if not success:
        print("❌ Failed to assign assistant to phone number")
        return False
    
    print("✅ Assistant assigned to phone number")
    
    # Step 5: Display next steps
    print("\n🎉 Vapi integration setup complete!")
    print("\n📋 Next steps:")
    print("1. Update your Twilio webhook URL to: https://api.vapi.ai/twilio/inbound_call")
    print("2. Set the webhook method to: HTTP POST")
    print("3. Test with a call to your Twilio number")
    print("\n🔧 Twilio Console Configuration:")
    print(f"   - Phone Number: {twilio_number}")
    print("   - Webhook URL: https://api.vapi.ai/twilio/inbound_call")
    print("   - Method: HTTP POST")
    
    return True

async def check_existing_setup():
    """Check if Vapi integration is already set up"""
    vapi = VapiIntegration()
    
    print("🔍 Checking existing Vapi setup...")
    
    # Check assistants
    assistants = await vapi.get_assistants()
    print(f"📋 Found {len(assistants)} existing assistants")
    
    # Check phone numbers
    phone_numbers = await vapi.get_phone_numbers()
    print(f"📞 Found {len(phone_numbers)} registered phone numbers")
    
    if assistants and phone_numbers:
        print("\n✅ Vapi integration appears to be already set up!")
        print("📋 Existing assistants:")
        for assistant in assistants:
            print(f"   - {assistant.get('name', 'Unnamed')} (ID: {assistant.get('id')})")
        
        print("\n📞 Registered phone numbers:")
        for phone in phone_numbers:
            print(f"   - {phone.get('number', 'Unknown')} (ID: {phone.get('id')})")
        
        return True
    
    return False

async def main():
    """Main setup function"""
    print("🎯 Vapi + Twilio Integration Setup")
    print("=" * 40)
    
    # Check if already set up
    if await check_existing_setup():
        print("\n❓ Do you want to set up a new integration anyway? (y/N)")
        response = input().strip().lower()
        if response != 'y':
            print("👋 Setup cancelled.")
            return
    
    # Run setup
    success = await setup_vapi_integration()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("📞 Your Twilio number is now integrated with Vapi's natural voice models!")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")

if __name__ == "__main__":
    asyncio.run(main())
