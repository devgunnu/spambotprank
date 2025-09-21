#!/usr/bin/env python3
"""
Setup script for Spam Call Time-Waster
"""

import os
import subprocess
import sys

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists(".env"):
        print("📝 Creating .env file...")
        with open(".env", "w") as f:
            f.write("""# Spam Call Time-Waster Environment Variables
# Replace these with your actual values

TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number
GEMINI_API_KEY=your_gemini_api_key_here
NGROK_TUNNEL_URL=https://your-ngrok-url.ngrok.io
DATABASE_URL=sqlite:///./database.db
""")
        print("✅ .env file created")
        print("⚠️  Please update .env file with your actual API keys and credentials")
    else:
        print("✅ .env file already exists")

def check_directories():
    """Check if required directories exist"""
    required_dirs = ["app", "data", "data/personas", "static"]
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Missing directory: {directory}")
            return False
    print("✅ All required directories exist")
    return True

def main():
    """Main setup function"""
    print("🎭 Spam Call Time-Waster Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check directories
    if not check_directories():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create .env file
    create_env_file()
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update your .env file with actual API keys")
    print("2. Set up your Twilio phone number webhooks")
    print("3. Start ngrok: ngrok http 8000")
    print("4. Run the application: python run.py")
    print("\n📖 See README.md for detailed instructions")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
