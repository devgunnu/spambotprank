#!/usr/bin/env python3
"""
Test script for the Spam Detection Functions Server
Tests all endpoints and functionality
"""

import requests
import json
import time
import sys
import os

# Configuration
MAIN_SERVER_URL = "http://localhost:5000"
RAG_SERVER_URL = "http://localhost:6334"

def test_endpoint(url, method="GET", data=None, files=None):
    """Test an endpoint and return results"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            if files:
                response = requests.post(url, files=files)
            else:
                response = requests.post(url, json=data)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def test_health_checks():
    """Test all health check endpoints"""
    print("Testing Health Checks...")
    print("=" * 50)
    
    endpoints = [
        ("Main Server", f"{MAIN_SERVER_URL}/health"),
        ("RAG Server", f"{RAG_SERVER_URL}/health"),
        ("Layer 1", f"{MAIN_SERVER_URL}/api/layer1/health"),
        ("Layer 2", f"{MAIN_SERVER_URL}/api/layer2/health"),
        ("RAG Functions", f"{MAIN_SERVER_URL}/api/rag/health"),
        ("Training", f"{MAIN_SERVER_URL}/api/training/health")
    ]
    
    for name, url in endpoints:
        result = test_endpoint(url)
        status = "✅ PASS" if result["success"] and result.get("status_code") == 200 else "❌ FAIL"
        print(f"{name}: {status}")
        if not result["success"]:
            print(f"  Error: {result['error']}")
        print()

def test_layer1_functions():
    """Test Layer 1 spam detection"""
    print("Testing Layer 1 Functions...")
    print("=" * 50)
    
    # Test with sample Twilio call object
    test_call = {
        "From": "+1234567890",
        "To": "+0987654321",
        "CallSid": "CA1234567890abcdef",
        "Direction": "inbound",
        "Status": "ringing"
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/layer1/check_spam", "POST", test_call)
    
    if result["success"]:
        response = result["response"]
        print(f"✅ Layer 1 Check: {response.get('is_spam', 'Unknown')}")
        print(f"   Confidence: {response.get('confidence', 'N/A')}")
        print(f"   Method: {response.get('method', 'N/A')}")
    else:
        print(f"❌ Layer 1 Failed: {result['error']}")
    
    print()

def test_layer2_functions():
    """Test Layer 2 ML spam detection"""
    print("Testing Layer 2 Functions...")
    print("=" * 50)
    
    # Test with sample call data
    test_call = {
        "From": "+1234567890",
        "To": "+0987654321",
        "CallSid": "CA1234567890abcdef",
        "Direction": "inbound",
        "Status": "ringing",
        "FromCity": "New York",
        "FromState": "NY",
        "FromCountry": "US",
        "threshold": 0.5
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/layer2/ml_check_spam", "POST", test_call)
    
    if result["success"]:
        response = result["response"]
        print(f"✅ Layer 2 ML Check: {response.get('is_spam', 'Unknown')}")
        print(f"   Confidence: {response.get('confidence', 'N/A')}")
        print(f"   Model Type: {response.get('model_type', 'N/A')}")
    else:
        print(f"❌ Layer 2 Failed: {result['error']}")
    
    # Test direct text prediction
    test_text = {
        "text": "Congratulations! You've won $1000! Call now!",
        "threshold": 0.5
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/layer2/predict_text", "POST", test_text)
    
    if result["success"]:
        response = result["response"]
        print(f"✅ Text Prediction: {response.get('is_spam', 'Unknown')}")
        print(f"   Confidence: {response.get('confidence', 'N/A')}")
    else:
        print(f"❌ Text Prediction Failed: {result['error']}")
    
    print()

def test_rag_functions():
    """Test RAG database functions"""
    print("Testing RAG Functions...")
    print("=" * 50)
    
    # Test adding user documents
    user_docs = {
        "documents": [
            "John Smith, preferred contact time: 9 AM - 5 PM",
            "VIP customer since 2020, no telemarketing calls"
        ],
        "metadata": {
            "user_id": "test_user_123",
            "source": "test_script"
        }
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/rag/add_user_documents", "POST", user_docs)
    
    if result["success"]:
        print("✅ Added user documents")
    else:
        print(f"❌ Add user documents failed: {result['error']}")
    
    # Test adding suspect information
    suspect_docs = {
        "documents": [
            "Reported for robocall scams, multiple complaints",
            "Uses spoofed numbers, claims to be from IRS"
        ],
        "metadata": {
            "phone_number": "+1234567890",
            "source": "test_script"
        }
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/rag/post_suspect_information", "POST", suspect_docs)
    
    if result["success"]:
        print("✅ Added suspect information")
    else:
        print(f"❌ Add suspect information failed: {result['error']}")
    
    # Wait a moment for indexing
    time.sleep(2)
    
    # Test querying user information
    user_query = {
        "query": "John Smith contact preferences",
        "top_k": 3
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/rag/get_user_information", "POST", user_query)
    
    if result["success"]:
        response = result["response"]
        print(f"✅ User info query: Found {response.get('count', 0)} results")
    else:
        print(f"❌ User info query failed: {result['error']}")
    
    # Test querying call history (will be empty but should work)
    history_query = {
        "query": "calls from suspicious numbers",
        "top_k": 5
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/rag/get_call_history", "POST", history_query)
    
    if result["success"]:
        response = result["response"]
        print(f"✅ Call history query: Found {response.get('count', 0)} results")
    else:
        print(f"❌ Call history query failed: {result['error']}")
    
    print()

def test_training_functions():
    """Test model training functions"""
    print("Testing Training Functions...")
    print("=" * 50)
    
    # Test adding training samples
    training_samples = {
        "samples": [
            {"text": "FREE MONEY! Click here to get rich!", "label": 1},
            {"text": "Hi, this is your colleague from work", "label": 0},
            {"text": "URGENT: Your account will be closed!", "label": 1},
            {"text": "Your prescription is ready for pickup", "label": 0}
        ]
    }
    
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/training/add_training_samples", "POST", training_samples)
    
    if result["success"]:
        response = result["response"]
        print(f"✅ Added training samples: {response.get('message', 'Success')}")
    else:
        print(f"❌ Add training samples failed: {result['error']}")
    
    # Test downloading sample CSV
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/training/download_sample_csv")
    
    if result["success"]:
        print("✅ Sample CSV download available")
    else:
        print(f"❌ Sample CSV download failed: {result['error']}")
    
    # Test training history
    result = test_endpoint(f"{MAIN_SERVER_URL}/api/training/training_history")
    
    if result["success"]:
        response = result["response"]
        model_info = response.get('model_info', {})
        print(f"✅ Training history: Model loaded = {model_info.get('model_loaded', 'Unknown')}")
    else:
        print(f"❌ Training history failed: {result['error']}")
    
    print()

def main():
    """Run all tests"""
    print("Spam Detection Functions Server Test Suite")
    print("=" * 60)
    print()
    
    # Check if servers are running
    print("Checking server availability...")
    main_server_check = test_endpoint(MAIN_SERVER_URL)
    rag_server_check = test_endpoint(RAG_SERVER_URL)
    
    if not main_server_check["success"]:
        print(f"❌ Main server not available at {MAIN_SERVER_URL}")
        print("Please start the main server: python app.py")
        sys.exit(1)
    
    if not rag_server_check["success"]:
        print(f"❌ RAG server not available at {RAG_SERVER_URL}")
        print("Please start the RAG server: cd rag && python qdrant_rag_server.py")
        sys.exit(1)
    
    print("✅ Both servers are running")
    print()
    
    # Run tests
    test_health_checks()
    test_layer1_functions()
    test_layer2_functions()
    test_rag_functions()
    test_training_functions()
    
    print("Test suite completed!")
    print()
    print("For full functionality testing:")
    print("1. Upload a CSV file to /api/training/retrain_model")
    print("2. Test with real Twilio webhook data")
    print("3. Integrate with VAPI dashboard")

if __name__ == "__main__":
    main()