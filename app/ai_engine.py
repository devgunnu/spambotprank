import requests
import os
import logging
from typing import Dict, List, Union
from starlette.datastructures import FormData

logger = logging.getLogger(__name__)

class ServerCommunicator:
    def __init__(self):
        # Ash's server URLs (single server on port 5000)
        self.layer1_server_url = os.getenv("LAYER1_SERVER_URL", "http://localhost:5000/api/layer1")
        self.layer2_server_url = os.getenv("LAYER2_SERVER_URL", "http://localhost:5000/api/layer2")
        self.rag_server_url = os.getenv("RAG_SERVER_URL", "http://localhost:5000/api/rag")
    
    def _extract_twilio_data(self, call_data: Union[Dict, FormData], from_number: str, to_number: str) -> Dict:
        """Extract Twilio fields from call data and create proper JSON payload"""
        payload = {
            "From": from_number,
            "To": to_number,
            "CallSid": "",
            "Direction": "inbound",
            "Status": "ringing"
        }
        
        if call_data:
            # Handle both dict and FormData objects
            if hasattr(call_data, 'get'):
                payload.update({
                    "From": call_data.get('From') or from_number,
                    "To": call_data.get('To') or to_number,
                    "CallSid": call_data.get('CallSid', ''),
                    "Direction": call_data.get('Direction', 'inbound'),
                    "Status": call_data.get('Status', 'ringing'),
                    "FromCity": call_data.get('FromCity', ''),
                    "FromState": call_data.get('FromState', ''),
                    "FromCountry": call_data.get('FromCountry', ''),
                    "CallerName": call_data.get('CallerName', ''),
                    "Timestamp": call_data.get('Timestamp', ''),
                    "Duration": call_data.get('Duration', ''),
                    "SpeechResult": call_data.get('SpeechResult', ''),
                    "SpeechConfidence": call_data.get('SpeechConfidence', ''),
                })
            elif isinstance(call_data, dict):
                payload.update(call_data)
        
        return payload
    
    async def layer1_spam_check(self, from_number: str, to_number: str, call_data: Union[Dict, FormData]) -> Dict:
        """Layer 1: Check spam database"""
        try:
            # Extract and format Twilio data properly
            payload = self._extract_twilio_data(call_data, from_number, to_number)
            
            response = requests.post(
                f"{self.layer1_server_url}/check_spam",
                json=payload,
                timeout=10  # Increased timeout for better reliability
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Layer 1 server error: {response.status_code} - {response.text}")
                return {"is_spam": False, "reason": "Layer 1 server error", "confidence": 0.0, "layer": 1}
                
        except requests.Timeout as e:
            logger.error(f"Layer 1 timeout error: {e}")
            return {"is_spam": False, "reason": "Layer 1 timeout", "confidence": 0.0, "layer": 1}
        except requests.ConnectionError as e:
            logger.error(f"Layer 1 connection error: {e}")
            return {"is_spam": False, "reason": "Layer 1 connection failed", "confidence": 0.0, "layer": 1}
        except requests.RequestException as e:
            logger.error(f"Layer 1 communication error: {e}")
            return {"is_spam": False, "reason": "Layer 1 communication failed", "confidence": 0.0, "layer": 1}
        except Exception as e:
            logger.error(f"Layer 1 unexpected error: {e}")
            return {"is_spam": False, "reason": "Layer 1 unexpected error", "confidence": 0.0, "layer": 1}
    
    async def layer2_ml_check(self, from_number: str, to_number: str, call_data: Union[Dict, FormData]) -> Dict:
        """Layer 2: ML model check"""
        try:
            # Extract and format Twilio data properly
            payload = self._extract_twilio_data(call_data, from_number, to_number)
            
            # Add default threshold if not provided (Layer 2 uses this for stochastic analysis)
            if 'threshold' not in payload:
                payload['threshold'] = 0.5  # Base threshold for ML model
            
            response = requests.post(
                f"{self.layer2_server_url}/ml_check_spam",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Layer 2 returns complex stochastic results - log details for debugging
                if 'details' in result:
                    logger.debug(f"Layer 2 detailed analysis: {result['details']}")
                return result
            else:
                logger.error(f"Layer 2 server error: {response.status_code} - {response.text}")
                return {"is_spam": False, "reason": "Layer 2 server error", "confidence": 0.0, "layer": 2}
                
        except requests.Timeout as e:
            logger.error(f"Layer 2 timeout error: {e}")
            return {"is_spam": False, "reason": "Layer 2 timeout", "confidence": 0.0, "layer": 2}
        except requests.ConnectionError as e:
            logger.error(f"Layer 2 connection error: {e}")
            return {"is_spam": False, "reason": "Layer 2 connection failed", "confidence": 0.0, "layer": 2}
        except requests.RequestException as e:
            logger.error(f"Layer 2 communication error: {e}")
            return {"is_spam": False, "reason": "Layer 2 communication failed", "confidence": 0.0, "layer": 2}
        except Exception as e:
            logger.error(f"Layer 2 unexpected error: {e}")
            return {"is_spam": False, "reason": "Layer 2 unexpected error", "confidence": 0.0, "layer": 2}
    
    async def get_user_information(self, query: str) -> Dict:
        """Get user information from RAG database"""
        try:
            # Match the expected payload format from ash/api/rag_functions.py
            payload = {
                "query": query,
                "top_k": 5
            }
            
            response = requests.post(
                f"{self.rag_server_url}/get_user_information", 
                json=payload, 
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG get_user_information error: {response.status_code} - {response.text}")
                return {"results": [], "query": query, "count": 0}
                
        except requests.RequestException as e:
            logger.error(f"RAG get_user_information communication error: {e}")
            return {"results": [], "query": query, "count": 0}
    
    async def get_call_history(self, query: str) -> Dict:
        """Get call history from RAG database"""
        try:
            # Match the expected payload format from ash/api/rag_functions.py
            payload = {
                "query": query,
                "top_k": 10
            }
            
            response = requests.post(
                f"{self.rag_server_url}/get_call_history", 
                json=payload, 
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG get_call_history error: {response.status_code} - {response.text}")
                return {"results": [], "query": query, "count": 0}
                
        except requests.RequestException as e:
            logger.error(f"RAG get_call_history communication error: {e}")
            return {"results": [], "query": query, "count": 0}
    
    async def post_suspect_information(self, texts: List[str], metadata: Dict = None) -> Dict:
        """Post suspect information to RAG database"""
        try:
            # Match the expected payload format from ash/api/rag_functions.py
            if metadata is None:
                metadata = {"source": "vapi_agent"}
            
            payload = {
                "documents": texts,
                "metadata": metadata
            }
            
            response = requests.post(
                f"{self.rag_server_url}/post_suspect_information", 
                json=payload, 
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"RAG post_suspect_information error: {response.status_code} - {response.text}")
                return {"success": False, "message": "Server error"}
                
        except requests.RequestException as e:
            logger.error(f"RAG post_suspect_information communication error: {e}")
            return {"success": False, "message": "Communication failed"}