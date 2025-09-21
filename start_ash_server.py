#!/usr/bin/env python3
"""
Script to start Ash's spam detection server
This script will start the server on port 5000 with external access enabled
"""

import subprocess
import sys
import os
import time

def start_ash_server():
    """Start Ash's spam detection server"""
    print("🚀 Starting Ash's Spam Detection Server...")
    print("=" * 50)
    
    # Change to ash directory
    ash_dir = os.path.join(os.path.dirname(__file__), 'ash')
    
    if not os.path.exists(ash_dir):
        print("❌ Error: ash/ directory not found!")
        return False
    
    try:
        # Start the server
        print(f"📁 Working directory: {ash_dir}")
        print("🌐 Starting server on http://0.0.0.0:5000")
        print("🔓 External access enabled")
        print("=" * 50)
        
        # Run the server
        process = subprocess.Popen(
            [sys.executable, "app.py"],
            cwd=ash_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Print output in real-time
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False
    
    return True

if __name__ == "__main__":
    start_ash_server()
