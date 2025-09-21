#!/usr/bin/env python3
"""
Spam Bot Prank - System Monitor
Monitors your Vapi and Twilio setup, checks health, and provides status updates
"""

import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

class SystemMonitor:
    def __init__(self):
        load_dotenv()
        self.vapi_api_key = os.getenv('VAPI_API_KEY')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.ngrok_url = os.getenv('NGROK_TUNNEL_URL')
        
    def check_environment(self):
        """Check if all required environment variables are set"""
        required_vars = {
            'VAPI_API_KEY': self.vapi_api_key,
            'TWILIO_ACCOUNT_SID': self.twilio_sid,
            'TWILIO_AUTH_TOKEN': self.twilio_token,
            'TWILIO_PHONE_NUMBER': self.twilio_number,
            'NGROK_TUNNEL_URL': self.ngrok_url
        }
        
        missing = [var for var, value in required_vars.items() if not value]
        
        if missing:
            print("❌ Missing environment variables:")
            for var in missing:
                print(f"   - {var}")
            return False
        
        print("✅ All environment variables configured")
        return True
    
    def check_vapi_status(self):
        """Check Vapi API status and assistant configuration"""
        if not self.vapi_api_key:
            print("❌ VAPI_API_KEY not set")
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.vapi_api_key}'}
            response = requests.get('https://api.vapi.ai/assistant', headers=headers, timeout=10)
            
            if response.status_code == 200:
                assistants = response.json()
                print(f"✅ Vapi API accessible - {len(assistants)} assistants found")
                
                # Check for your specific assistant
                for assistant in assistants:
                    if 'Random Personality' in assistant.get('name', ''):
                        print(f"✅ Found your assistant: {assistant['name']}")
                        print(f"   Status: {assistant.get('status', 'Unknown')}")
                        return True
                
                print("⚠️  Your 'Random Personality' assistant not found")
                return False
            else:
                print(f"❌ Vapi API error: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Vapi API connection failed: {e}")
            return False
    
    def check_twilio_status(self):
        """Check Twilio API status"""
        if not all([self.twilio_sid, self.twilio_token]):
            print("❌ Twilio credentials not set")
            return False
            
        try:
            from twilio.rest import Client
            client = Client(self.twilio_sid, self.twilio_token)
            account = client.api.accounts(self.twilio_sid).fetch()
            
            print(f"✅ Twilio API accessible - Account: {account.friendly_name}")
            print(f"   Phone Number: {self.twilio_number}")
            return True
            
        except Exception as e:
            print(f"❌ Twilio API error: {e}")
            return False
    
    def check_ngrok_status(self):
        """Check if ngrok tunnel is accessible"""
        if not self.ngrok_url:
            print("❌ NGROK_TUNNEL_URL not set")
            return False
            
        try:
            response = requests.get(self.ngrok_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Ngrok tunnel accessible: {self.ngrok_url}")
                return True
            else:
                print(f"⚠️  Ngrok tunnel responding with status: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Ngrok tunnel not accessible: {e}")
            return False
    
    def get_system_status(self):
        """Get overall system status"""
        print("🔍 Spam Bot Prank - System Status Check")
        print("=" * 50)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        checks = [
            ("Environment Variables", self.check_environment),
            ("Vapi API", self.check_vapi_status),
            ("Twilio API", self.check_twilio_status),
            ("Ngrok Tunnel", self.check_ngrok_status)
        ]
        
        results = []
        for name, check_func in checks:
            print(f"🔍 Checking {name}...")
            result = check_func()
            results.append((name, result))
            print()
        
        # Summary
        print("📊 System Status Summary:")
        print("-" * 30)
        all_good = True
        for name, result in results:
            status = "✅ OK" if result else "❌ FAIL"
            print(f"{name}: {status}")
            if not result:
                all_good = False
        
        print()
        if all_good:
            print("🎉 All systems operational! Your spam bot is ready to waste time!")
        else:
            print("⚠️  Some issues detected. Please check the errors above.")
        
        return all_good
    
    def monitor_continuously(self, interval=300):
        """Monitor system continuously"""
        print(f"🔄 Starting continuous monitoring (every {interval} seconds)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.get_system_status()
                print(f"⏳ Next check in {interval} seconds...")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")

def main():
    monitor = SystemMonitor()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        monitor.monitor_continuously()
    else:
        monitor.get_system_status()

if __name__ == "__main__":
    main()
