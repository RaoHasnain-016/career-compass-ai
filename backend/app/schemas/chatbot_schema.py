from typing import Literal, Optional
from pydantic import BaseModel


class ChatbotRequest(BaseModel):
    message: str
    career_id: Optional[str] = None
    mode: Literal["guidance", "pilot"] = "guidance"


class ChatbotResponse(BaseModel):
    message_id: str
    question: str
    response: str
