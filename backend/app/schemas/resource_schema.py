from typing import Optional
from pydantic import BaseModel


class LearningResourceBase(BaseModel):
    title: str
    platform: str
    url: str
    skill: str
    career_field: Optional[str] = None
    difficulty: Optional[str] = None
    resource_type: Optional[str] = None
    description: Optional[str] = None
    is_free: Optional[bool] = True
    status: Optional[bool] = True


class LearningResourceCreate(LearningResourceBase):
    pass


class LearningResourceUpdate(BaseModel):
    title: Optional[str] = None
    platform: Optional[str] = None
    url: Optional[str] = None
    skill: Optional[str] = None
    career_field: Optional[str] = None
    difficulty: Optional[str] = None
    resource_type: Optional[str] = None
    description: Optional[str] = None
    is_free: Optional[bool] = None
    status: Optional[bool] = None