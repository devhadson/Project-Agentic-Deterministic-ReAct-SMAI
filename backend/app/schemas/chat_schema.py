from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatMessage(BaseModel):
    role: str
    content: str

class AgentRequest(BaseModel):
    messages: List[ChatMessage]
    patient_id: str
    patient_name: str
    glucose_level: float
    doctor_id: Optional[int] = None

class AgentResponse(BaseModel):
    response: str
    session_closed: bool = False
