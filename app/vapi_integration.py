import requests
import os
import json
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class VapiIntegration:
    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY")
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    async def create_assistant(self, persona: Dict) -> Optional[str]:
        """Create a Vapi assistant with persona configuration"""
        try:
            # Create assistant configuration based on persona
            assistant_config = {
                "name": f"Spam Call Waster - {persona.get('persona_name', 'Default')}",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "maxTokens": 150
                },
                "voice": {
                    "provider": "11labs",
                    "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Natural female voice
                    "stability": 0.5,
                    "similarityBoost": 0.8
                },
                "firstMessage": persona.get("greeting_responses", ["Hello! How can I help you today?"])[0],
                "endCallMessage": "Thank you for calling! Have a great day!",
                "endCallPhrases": ["goodbye", "bye", "thank you", "have a good day"],
                "recordingEnabled": True,
                "silenceTimeoutSeconds": 10,
                "responseDelaySeconds": 1
            }
            
            response = requests.post(
                f"{self.base_url}/assistant",
                headers=self.headers,
                json=assistant_config
            )
            
            if response.status_code == 201:
                assistant_data = response.json()
                logger.info(f"Created Vapi assistant: {assistant_data.get('id')}")
                return assistant_data.get('id')
            else:
                logger.error(f"Failed to create assistant: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Vapi assistant: {e}")
            return None
    
    async def create_credential(self) -> Optional[str]:
        """Create a credential for Twilio integration"""
        try:
            credential_config = {
                "provider": "twilio"
            }
            
            response = requests.post(
                f"{self.base_url}/credential",
                headers=self.headers,
                json=credential_config
            )
            
            if response.status_code == 201:
                credential_data = response.json()
                logger.info(f"Created credential: {credential_data.get('id')}")
                return credential_data.get('id')
            else:
                logger.error(f"Failed to create credential: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating credential: {e}")
            return None
    
    async def create_phone_number(self, twilio_number: str, credential_id: str) -> Optional[str]:
        """Register Twilio phone number with Vapi"""
        try:
            phone_config = {
                "provider": "byo-phone-number",
                "name": f"Twilio Number - {twilio_number}",
                "number": twilio_number,
                "numberE164CheckEnabled": False,
                "credentialId": credential_id
            }
            
            response = requests.post(
                f"{self.base_url}/phone-number",
                headers=self.headers,
                json=phone_config
            )
            
            if response.status_code == 201:
                phone_data = response.json()
                logger.info(f"Registered phone number with Vapi: {phone_data.get('id')}")
                return phone_data.get('id')
            else:
                logger.error(f"Failed to register phone number: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error registering phone number: {e}")
            return None
    
    async def assign_assistant_to_number(self, phone_number_id: str, assistant_id: str) -> bool:
        """Assign assistant to phone number"""
        try:
            response = requests.patch(
                f"{self.base_url}/phone-number/{phone_number_id}",
                headers=self.headers,
                json={"assistantId": assistant_id}
            )
            
            if response.status_code == 200:
                logger.info(f"Assigned assistant {assistant_id} to phone number {phone_number_id}")
                return True
            else:
                logger.error(f"Failed to assign assistant: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error assigning assistant: {e}")
            return False
    
    async def get_assistants(self) -> list:
        """Get list of existing assistants"""
        try:
            response = requests.get(
                f"{self.base_url}/assistant",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get assistants: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting assistants: {e}")
            return []
    
    async def get_phone_numbers(self) -> list:
        """Get list of registered phone numbers"""
        try:
            response = requests.get(
                f"{self.base_url}/phone-number",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get phone numbers: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting phone numbers: {e}")
            return []
