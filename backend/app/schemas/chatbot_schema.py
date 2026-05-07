from typing import Optional
from pydantic import BaseModel


class ChatbotRequest(BaseModel):
    message: str
    career_id: Optional[str] = None


class ChatbotResponse(BaseModel):
    message_id: str
    question: str
    response: str