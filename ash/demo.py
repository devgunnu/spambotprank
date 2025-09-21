#!/usr/bin/env python3
"""
Quick start demo for the Spam Detection Functions Server
This script demonstrates the complete functionality
"""

import subprocess
import time
import sys
import os
from utilities.client import SpamDetectionClient, create_sample_training_csv

def check_dependencies():
    """Check if required dependencies are installed"""
    print("Checking dependencies...")
    
    try:
        import flask
        import qdrant_client
        import sklearn
        import transformers
        print("✅ All Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_servers():
    """Start both servers"""
    print("Starting servers...")
    
    # Check if Qdrant is running (Docker)
    print("Note: Make sure Qdrant is running:")
    print("docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant")
    print()
    
    # For this demo, we'll assume servers are started manually
    print("Please start the servers in separate terminals:")
    print("Terminal 1: cd rag && python qdrant_rag_server.py")
    print("Terminal 2: python app.py")
    print()
    input("Press Enter when both servers are running...")

def demo_workflow():
    """Demonstrate the complete spam detection workflow"""
    print("\n" + "="*60)
    print("SPAM DETECTION WORKFLOW DEMONSTRATION")
    print("="*60)
    
    client = SpamDetectionClient()
    
    # Test data
    spam_call = {
        "From": "+1234567890",  # This number is in our test spam database
        "To": "+0987654321",
        "CallSid": "CA_spam_example",
        "Direction": "inbound",
        "Status": "ringing",
        "FromCity": "Unknown",
        "FromState": "Unknown",
        "FromCountry": "Unknown"
    }
    
    legitimate_call = {
        "From": "+1111111111",  # This number is not in spam database
        "To": "+0987654321",
        "CallSid": "CA_legit_example",
        "Direction": "inbound",
        "Status": "ringing",
        "FromCity": "New York",
        "FromState": "NY",
        "FromCountry": "US"
    }
    
    print("1. Testing SPAM CALL Detection")
    print("-" * 40)
    
    # Layer 1 check for spam call
    result1 = client.check_spam_layer1(spam_call)
    print(f"Layer 1 (Database): {result1}")
    
    if result1.get('is_spam'):
        print("🚫 DECISION: REJECT CALL (Known spam number)")
    else:
        # Layer 2 check
        result2 = client.check_spam_layer2(spam_call)
        print(f"Layer 2 (ML): {result2}")
        
        if result2.get('is_spam'):
            print("🚫 DECISION: REJECT CALL (ML detected spam)")
        else:
            print("✅ DECISION: CONNECT TO AGENT")
    
    print("\n2. Testing LEGITIMATE CALL Detection")
    print("-" * 40)
    
    # Layer 1 check for legitimate call
    result1 = client.check_spam_layer1(legitimate_call)
    print(f"Layer 1 (Database): {result1}")
    
    if result1.get('is_spam'):
        print("🚫 DECISION: REJECT CALL (Known spam number)")
    else:
        # Layer 2 check
        result2 = client.check_spam_layer2(legitimate_call)
        print(f"Layer 2 (ML): {result2}")
        
        if result2.get('is_spam'):
            print("🚫 DECISION: REJECT CALL (ML detected spam)")
        else:
            print("✅ DECISION: CONNECT TO AGENT")
            
            # Demonstrate agent functions
            print("\n   👤 AGENT FUNCTIONS AVAILABLE:")
            
            # Add some sample user data
            user_docs = [
                "John Doe, VIP customer since 2020",
                "Preferred contact time: 9 AM - 5 PM weekdays",
                "Previous inquiry about premium service upgrade"
            ]
            
            add_result = client.add_user_documents(user_docs, {"user_id": "john_doe_123"})
            print(f"   📝 Added user info: {add_result.get('success', False)}")
            
            # Query user information
            user_info = client.get_user_information("John Doe customer information")
            print(f"   🔍 User query result: Found {user_info.get('count', 0)} documents")
            
            # Query call history (will be empty but demonstrates function)
            call_history = client.get_call_history("recent calls")
            print(f"   📞 Call history: Found {call_history.get('count', 0)} records")

def demo_training():
    """Demonstrate model training functionality"""
    print("\n" + "="*60)
    print("MODEL TRAINING DEMONSTRATION")
    print("="*60)
    
    client = SpamDetectionClient()
    
    # Create sample training data
    print("1. Creating sample training data...")
    create_sample_training_csv("demo_training_data.csv", 50)
    print("✅ Created demo_training_data.csv with 50 samples")
    
    # Add training samples via API
    print("\n2. Adding training samples via API...")
    
    training_samples = [
        {"text": "URGENT: Your car warranty expires today! Call now!", "label": 1},
        {"text": "Final notice: Credit card debt forgiveness available", "label": 1},
        {"text": "Hi, this is Dr. Smith's office confirming your appointment", "label": 0},
        {"text": "Your package delivery is scheduled for tomorrow", "label": 0}
    ]
    
    result = client.add_training_samples(training_samples)
    print(f"✅ Training result: {result.get('message', 'Success')}")
    
    # Test the model with direct text
    print("\n3. Testing model predictions...")
    
    test_texts = [
        "Congratulations! You've won $10,000! Call now!",
        "Hello, this is your bank calling about your account",
        "FREE MONEY!!! Click here to claim now!!!",
        "Your prescription is ready for pickup"
    ]
    
    # Note: Direct text prediction would need to be implemented in the client
    print("Test texts prepared (would test via /api/layer2/predict_text)")
    for i, text in enumerate(test_texts, 1):
        print(f"   {i}. {text}")

def demo_rag_functions():
    """Demonstrate RAG database functionality"""
    print("\n" + "="*60)
    print("RAG DATABASE DEMONSTRATION")
    print("="*60)
    
    client = SpamDetectionClient()
    
    print("1. Adding user information...")
    user_docs = [
        "Sarah Johnson - VIP customer, no telemarketing calls",
        "Michael Chen - Business account, prefer email contact",
        "Emma Wilson - Student discount applied, call restrictions after 8 PM"
    ]
    
    result = client.add_user_documents(user_docs, {"source": "demo", "batch": "user_profiles"})
    print(f"✅ Added user documents: {result.get('success', False)}")
    
    print("\n2. Adding suspect information...")
    suspect_docs = [
        "Phone number +1234567890 reported for IRS scam calls",
        "Caller ID spoofing detected from range +555-000-XXXX",
        "Robocall reports: Claims to be from Medicare, requests SSN"
    ]
    
    result = client.post_suspect_information(suspect_docs, {"source": "demo", "threat_level": "high"})
    print(f"✅ Added suspect information: {result.get('success', False)}")
    
    # Wait for indexing
    print("\n3. Waiting for vector indexing...")
    time.sleep(3)
    
    print("\n4. Querying information...")
    
    # Query user info
    user_result = client.get_user_information("VIP customer preferences")
    print(f"👤 User info query: Found {user_result.get('count', 0)} results")
    
    if user_result.get('results'):
        for i, doc in enumerate(user_result['results'][:2], 1):
            print(f"   {i}. {doc.get('text', '')[:50]}...")
    
    # Query suspects
    suspect_result = client.get_user_information("scam reports")  # Will search across categories
    print(f"🚨 Suspect query: Found {suspect_result.get('count', 0)} results")

def main():
    """Main demo function"""
    print("SPAM DETECTION FUNCTIONS SERVER DEMO")
    print("=" * 60)
    
    if not check_dependencies():
        sys.exit(1)
    
    start_servers()
    
    try:
        demo_workflow()
        demo_rag_functions()
        demo_training()
        
        print("\n" + "="*60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        print("\nNext steps:")
        print("1. Integrate with Twilio webhook")
        print("2. Connect to VAPI dashboard")
        print("3. Upload real training data")
        print("4. Configure production environment")
        print("\nFor testing: python test_server.py")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("Make sure both servers are running and accessible")

if __name__ == "__main__":
    main()