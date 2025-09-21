from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from .database import AsyncSessionLocal, Call, Conversation
from .models import AnalyticsSummary
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    async def get_summary(self) -> dict:
        """Get analytics summary for dashboard"""
        # For now, return mock data to get the app working
        return {
            "total_calls_today": 0,
            "avg_duration_today": 0.0,
            "most_effective_persona": "None",
            "total_time_wasted": 0.0
        }
    
    async def get_recent_calls(self, limit: int = 20) -> list:
        """Get recent calls for dashboard"""
        # For now, return empty list to get the app working
        return []
    
    async def get_call_details(self, call_id: str) -> dict:
        """Get detailed call information including conversation"""
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            # Get call info
            call_result = await db.execute(text(f"SELECT * FROM calls WHERE id = {call_id}"))
            call = call_result.fetchone()
            
            if not call:
                return {"error": "Call not found"}
            
            # Get conversation
            conversation_result = await db.execute(text(f"""
                SELECT timestamp, speaker, message, confidence_score
                FROM conversations 
                WHERE call_id = {call_id}
                ORDER BY timestamp ASC
            """))
            
            conversations = []
            for row in conversation_result.fetchall():
                conversations.append({
                    "timestamp": row[0].isoformat(),
                    "speaker": row[1],
                    "message": row[2],
                    "confidence_score": row[3]
                })
            
            return {
                "call": {
                    "id": call[0],
                    "caller_number": call[1],
                    "start_time": call[3].isoformat() if call[3] else None,
                    "end_time": call[4].isoformat() if call[4] else None,
                    "duration": call[5],
                    "persona_used": call[6],
                    "status": call[8]
                },
                "conversation": conversations
            }
