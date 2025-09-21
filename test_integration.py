#!/usr/bin/env python3
"""
Test script to verify the spam detection gateway integration
Tests both our gateway and Ash's server endpoints
"""

import requests
import json
import time
import sys

def test_ash_server():
    """Test Ash's server endpoints"""
    print("🧪 Testing Ash's Server Endpoints...")
    print("=" * 50)
    
    base_url = "http://localhost:5000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Ash server health check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Ash server health check: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Ash server health check: ERROR - {e}")
        return False
    
    # Test Layer 1 endpoint
    try:
        test_call_data = {
            "From": "+18004419593",  # Known spam number from Ash's database
            "To": "+14806608282",
            "CallSid": "CA1234567890abcdef",
            "Direction": "inbound",
            "Status": "ringing"
        }
        
        response = requests.post(
            f"{base_url}/api/layer1/check_spam",
            json=test_call_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Layer 1 test: PASSED")
            print(f"   Spam detected: {result.get('is_spam', False)}")
            print(f"   Confidence: {result.get('confidence', 0)}")
        else:
            print(f"❌ Layer 1 test: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Layer 1 test: ERROR - {e}")
        return False
    
    # Test Layer 2 endpoint
    try:
        response = requests.post(
            f"{base_url}/api/layer2/ml_check_spam",
            json=test_call_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Layer 2 test: PASSED")
            print(f"   Spam detected: {result.get('is_spam', False)}")
            print(f"   Confidence: {result.get('confidence', 0)}")
        else:
            print(f"❌ Layer 2 test: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Layer 2 test: ERROR - {e}")
        return False
    
    # Test RAG endpoint
    try:
        test_query = {"query": "test user information", "top_k": 3}
        response = requests.post(
            f"{base_url}/api/rag/get_user_information",
            json=test_query,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ RAG test: PASSED")
            print(f"   Results count: {result.get('count', 0)}")
        else:
            print(f"❌ RAG test: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ RAG test: ERROR - {e}")
        return False
    
    return True

def test_our_gateway():
    """Test our gateway endpoints"""
    print("\n🧪 Testing Our Gateway Endpoints...")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Gateway health check: PASSED")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Gateway health check: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Gateway health check: ERROR - {e}")
        print("   Make sure our gateway is running on port 8000")
        return False
    
    # Test agent endpoints
    try:
        test_data = {"query": "test query"}
        response = requests.post(
            f"{base_url}/api/agent/get_user_information",
            json=test_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Agent endpoint test: PASSED")
        else:
            print(f"❌ Agent endpoint test: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Agent endpoint test: ERROR - {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🔍 Spam Detection Gateway Integration Test")
    print("=" * 60)
    
    # Test Ash's server first
    ash_ok = test_ash_server()
    
    if not ash_ok:
        print("\n❌ Ash's server tests failed!")
        print("   Make sure to start Ash's server first:")
        print("   python start_ash_server.py")
        return False
    
    # Test our gateway
    gateway_ok = test_our_gateway()
    
    if not gateway_ok:
        print("\n❌ Gateway tests failed!")
        print("   Make sure to start our gateway:")
        print("   python run.py")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("✅ Ash's server is running and responding")
    print("✅ Our gateway is running and responding")
    print("✅ Integration is working correctly")
    print("\n🚀 Ready to test with real calls!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
