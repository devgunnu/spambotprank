import requests
import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class ServerCommunicator:
    def __init__(self):
        # Friend's server URLs (to be configured)
        self.layer1_server_url = os.getenv("LAYER1_SERVER_URL", "http://localhost:8001")
        self.layer2_server_url = os.getenv("LAYER2_SERVER_URL", "http://localhost:8002")
        self.rag_server_url = os.getenv("RAG_SERVER_URL", "http://localhost:8003")
    
    async def layer1_spam_check(self, from_number: str, to_number: str, call_data: Dict) -> Dict:
        """Layer 1: Check spam database"""
        try:
            payload = {
                "from_number": from_number,
                "to_number": to_number,
                "call_data": dict(call_data)
            }
            
            response = requests.post(
                f"{self.layer1_server_url}/check_spam",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"is_spam": False, "reason": "Layer 1 server error"}
                
        except requests.RequestException as e:
            logger.error(f"Layer 1 communication error: {e}")
            return {"is_spam": False, "reason": "Layer 1 communication failed"}
    
    async def layer2_ml_check(self, from_number: str, to_number: str, call_data: Dict) -> Dict:
        """Layer 2: ML model check"""
        try:
            payload = {
                "from_number": from_number,
                "to_number": to_number,
                "call_data": dict(call_data)
            }
            
            response = requests.post(
                f"{self.layer2_server_url}/ml_check",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"is_spam": False, "reason": "Layer 2 server error"}
                
        except requests.RequestException as e:
            logger.error(f"Layer 2 communication error: {e}")
            return {"is_spam": False, "reason": "Layer 2 communication failed"}
    
    async def get_user_information(self, query: str) -> Dict:
        """Get user information from RAG database"""
        try:
            payload = {"query": query, "category": "user_information"}
            response = requests.post(f"{self.rag_server_url}/search", json=payload, timeout=10)
            return response.json() if response.status_code == 200 else {"documents": []}
        except:
            return {"documents": []}
    
    async def get_call_history(self, query: str) -> Dict:
        """Get call history from RAG database"""
        try:
            payload = {"query": query, "category": "call_history"}
            response = requests.post(f"{self.rag_server_url}/search", json=payload, timeout=10)
            return response.json() if response.status_code == 200 else {"documents": []}
        except:
            return {"documents": []}
    
    async def post_suspect_information(self, texts: List[str]) -> Dict:
        """Post suspect information to RAG database"""
        try:
            payload = {"texts": texts, "category": "suspects"}
            response = requests.post(f"{self.rag_server_url}/add_documents", json=payload, timeout=10)
            return response.json() if response.status_code == 200 else {"success": False}
        except:
            return {"success": False}