"""
Python client SDK for the Spam Detection Functions Server
Provides easy access to all spam detection, RAG, and training endpoints
"""

import requests
import json
import csv
from typing import List, Dict, Any, Optional


class SpamDetectionClient:
    """Client for interacting with the Spam Detection Functions Server
    
    Examples:
        # Local usage
        client = SpamDetectionClient()
        
        # External server usage
        client = SpamDetectionClient("http://192.168.1.100:5000")
        client = SpamDetectionClient("http://your-server.com:5000")
    """
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        print(f"🔗 Connecting to spam detection server: {self.base_url}")
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict:
        """Make a request to the server"""
        url = f"{self.base_url}{endpoint}"
        
        # Add headers for external requests
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SpamDetectionClient/1.0'
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                if files:
                    # Remove Content-Type header for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, data=data, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}", "url": url}
    
    def health_check(self) -> Dict:
        """Check overall server health"""
        return self._make_request("/health")
    
    def get_all_endpoints(self) -> Dict:
        """Get list of all available endpoints"""
        return self._make_request("/")
    
    def get_network_info(self) -> Dict:
        """Get server network configuration and access URLs"""
        return self._make_request("/network-info")
    
    # ==================== LAYER 1 FUNCTIONS ====================
    
    def check_spam_layer1(self, phone_number: str, **kwargs) -> Dict:
        """Check spam using Layer 1 (database lookup)"""
        data = {"From": phone_number}
        data.update(kwargs)
        return self._make_request("/api/layer1/check_spam", "POST", data)
    
    # ==================== LAYER 2 FUNCTIONS ====================
    
    def check_spam_layer2(self, phone_number: str, content: str = "", **kwargs) -> Dict:
        """Check spam using Layer 2 (ML model)"""
        data = {"From": phone_number, "content": content}
        data.update(kwargs)
        return self._make_request("/api/layer2/ml_check_spam", "POST", data)
    
    # ==================== RAG FUNCTIONS ====================
    
    def rag_health(self) -> Dict:
        """Check RAG system health"""
        return self._make_request("/api/rag/health")
    
    def search_all_documents(self, query: str, top_k: int = 5) -> Dict:
        """Search across all document categories"""
        data = {"query": query, "top_k": top_k}
        return self._make_request("/api/rag/search_all", "POST", data)
    
    def post_suspect_information(self, documents: List[str], metadata: Dict = None) -> Dict:
        """Add suspect information to RAG storage"""
        data = {"documents": documents, "metadata": metadata or {}}
        return self._make_request("/api/rag/post_suspect_information", "POST", data)
    
    def add_user_documents(self, documents: List[str], metadata: Dict = None) -> Dict:
        """Add user information documents to RAG storage"""
        data = {"documents": documents, "metadata": metadata or {}}
        return self._make_request("/api/rag/add_user_documents", "POST", data)
    
    # ==================== TRAINING FUNCTIONS ====================
    
    def add_training_samples(self, samples: List[Dict]) -> Dict:
        """Add individual training samples"""
        data = {"samples": samples}
        return self._make_request("/api/training/add_training_samples", "POST", data)
    
    def download_sample_csv(self) -> str:
        """Download sample training CSV content"""
        try:
            response = requests.get(f"{self.base_url}/api/training/download_sample_csv")
            response.raise_for_status()
            return response.text
        except Exception as e:
            return f"Error downloading sample CSV: {str(e)}"


def example_usage():
    """Example usage of the SpamDetectionClient"""
    client = SpamDetectionClient()
    
    print("=== Testing Spam Detection Server ===")
    print("Health check:", client.health_check())
    
    # Test Layer 1
    result1 = client.check_spam_layer1("+18004419593")
    print("Layer 1 result:", result1)
    
    # Test Layer 2  
    result2 = client.check_spam_layer2("+15551234567", "FREE GIFT!")
    print("Layer 2 result:", result2)
    
    # Test RAG
    client.post_suspect_information(["Test suspect info"], {"phone": "+15551234567"})
    search_result = client.search_all_documents("suspect")
    print("RAG search result:", search_result)


if __name__ == "__main__":
    example_usage()