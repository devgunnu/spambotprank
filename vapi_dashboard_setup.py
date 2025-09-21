#!/usr/bin/env python3
"""
Vapi Dashboard Setup Instructions
Since the API approach is having issues, let's use the Vapi dashboard to set this up
"""

import os
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    print("🎯 Vapi Dashboard Setup Instructions")
    print("=" * 40)
    print()
    print("Since the API registration is having issues, let's use the Vapi dashboard:")
    print()
    print("📋 Step-by-Step Instructions:")
    print()
    print("1. 🌐 Go to Vapi Dashboard:")
    print("   https://dashboard.vapi.ai")
    print()
    print("2. 📞 Go to Phone Numbers section:")
    print("   - Click on 'Phone Numbers' in the sidebar")
    print("   - Click 'Import from Twilio'")
    print()
    print("3. 🔑 Enter your Twilio credentials:")
    print(f"   - Account SID: {os.getenv('TWILIO_ACCOUNT_SID')}")
    print(f"   - Auth Token: {os.getenv('TWILIO_AUTH_TOKEN')}")
    print(f"   - Phone Number: {os.getenv('TWILIO_PHONE_NUMBER')}")
    print()
    print("4. 🤖 Assign the assistant:")
    print("   - Select 'Spam Call Waster - price_haggler'")
    print("   - Assistant ID: ef10f4aa-68ea-488b-9ee4-1c19f02fda3a")
    print()
    print("5. ✅ Save the configuration")
    print()
    print("🎯 Alternative: Use the existing 'Riley' assistant")
    print("   - If you prefer, you can assign the existing 'Riley' assistant")
    print("   - Assistant ID: b95149c1-b265-4326-b630-9e02bf78d5f2")
    print()
    print("📞 After setup, test by calling your Twilio number!")
    print(f"   Number: {os.getenv('TWILIO_PHONE_NUMBER')}")
    print()
    print("🔧 Current Twilio Webhook (should stay as is):")
    print("   URL: https://api.vapi.ai/twilio/inbound_call")
    print("   Method: POST")

if __name__ == "__main__":
    main()
