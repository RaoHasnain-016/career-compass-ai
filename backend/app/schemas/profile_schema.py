from typing import List, Optional
from pydantic import BaseModel


class StudentProfileBase(BaseModel):
    age: Optional[str] = None
    academic_level: str
    class_degree: Optional[str] = None
    marks_cgpa: Optional[float] = None
    favorite_subjects: Optional[List[str]] = []
    weak_subjects: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    study_preference: Optional[str] = None


class StudentProfileCreate(StudentProfileBase):
    pass


class StudentProfileUpdate(BaseModel):
    age: Optional[str] = None
    academic_level: Optional[str] = None
    class_degree: Optional[str] = None
    marks_cgpa: Optional[float] = None
    favorite_subjects: Optional[List[str]] = None
    weak_subjects: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    skills: Optional[List[str]] = None
    study_preference: Optional[str] = None


class StudentProfileResponse(StudentProfileBase):
    profile_id: str
    user_id: str

    class Config:
        from_attributes = True