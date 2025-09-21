#!/usr/bin/env python3
"""
Script to start both Ash's server and your gateway
This will start both servers in the background and monitor them
"""

import subprocess
import sys
import os
import time
import signal
import threading

class ServerManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_ash_server(self):
        """Start Ash's spam detection server"""
        print("🚀 Starting Ash's Spam Detection Server...")
        ash_dir = os.path.join(os.path.dirname(__file__), 'ash')
        
        try:
            process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=ash_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(("Ash Server", process))
            print("✅ Ash's server started on port 5000")
        except Exception as e:
            print(f"❌ Failed to start Ash's server: {e}")
    
    def start_gateway(self):
        """Start your spam detection gateway"""
        print("🚀 Starting Spam Detection Gateway...")
        
        try:
            process = subprocess.Popen(
                [sys.executable, "run.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(("Gateway", process))
            print("✅ Gateway started on port 8000")
        except Exception as e:
            print(f"❌ Failed to start gateway: {e}")
    
    def monitor_processes(self):
        """Monitor all processes and print their output"""
        while self.running:
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"⚠️  {name} process ended")
                    self.running = False
                    break
            time.sleep(1)
    
    def stop_all(self):
        """Stop all processes"""
        print("\n🛑 Stopping all servers...")
        self.running = False
        
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except:
                try:
                    process.kill()
                    print(f"🔨 {name} force killed")
                except:
                    print(f"❌ Failed to stop {name}")
    
    def run(self):
        """Main run function"""
        print("🎭 Spam Detection System Startup")
        print("=" * 50)
        
        # Start both servers
        self.start_ash_server()
        time.sleep(2)  # Give Ash's server time to start
        self.start_gateway()
        time.sleep(2)  # Give gateway time to start
        
        print("\n🎉 Both servers are starting up!")
        print("=" * 50)
        print("📍 Ash's Server: http://localhost:5000")
        print("📍 Your Gateway: http://localhost:8000")
        print("🔗 Health checks:")
        print("   - Ash: http://localhost:5000/health")
        print("   - Gateway: http://localhost:8000/health")
        print("\n⏳ Waiting for servers to fully start...")
        print("Press Ctrl+C to stop all servers")
        print("=" * 50)
        
        # Wait a bit for servers to start
        time.sleep(5)
        
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
        finally:
            self.stop_all()

def main():
    """Main function"""
    manager = ServerManager()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Shutdown requested...")
        manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        manager.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        manager.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main()
