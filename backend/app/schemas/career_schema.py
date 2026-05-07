from typing import List, Optional
from pydantic import BaseModel


class CareerBase(BaseModel):
    title: str
    field: str
    overview: str
    required_education: str
    required_skills: List[str]
    required_subjects: Optional[List[str]] = []
    related_interests: Optional[List[str]] = []
    minimum_marks: Optional[float] = 0
    future_scope: Optional[str] = None
    difficulty_level: Optional[str] = None
    status: Optional[bool] = True


class CareerCreate(CareerBase):
    pass


class CareerUpdate(BaseModel):
    title: Optional[str] = None
    field: Optional[str] = None
    overview: Optional[str] = None
    required_education: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_subjects: Optional[List[str]] = None
    related_interests: Optional[List[str]] = None
    minimum_marks: Optional[float] = None
    future_scope: Optional[str] = None
    difficulty_level: Optional[str] = None
    status: Optional[bool] = None