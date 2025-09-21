from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class CallCreate(BaseModel):
    caller_number: str
    twilio_call_sid: str
    persona_used: str

class CallResponse(BaseModel):
    id: int
    caller_number: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    persona_used: str
    status: str

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    call_id: int
    speaker: str
    message: str
    confidence_score: Optional[float]

class ConversationResponse(BaseModel):
    id: int
    timestamp: datetime
    speaker: str
    message: str
    confidence_score: Optional[float]

    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_calls_today: int
    avg_duration_today: float
    most_effective_persona: str
    total_time_wasted: float
