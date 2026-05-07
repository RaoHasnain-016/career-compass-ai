from typing import List, Optional
from pydantic import BaseModel


class RecommendationCareerResponse(BaseModel):
    recommendation_id: str
    career_id: str

    title: str
    field: str
    overview: str
    required_education: str
    required_skills: List[str]
    required_subjects: List[str]
    future_scope: Optional[str] = None
    difficulty_level: Optional[str] = None

    match_score: float
    confidence_level: Optional[str] = None
    eligibility_status: Optional[str] = None

    matched_interests: List[str] = []
    matched_skills: List[str] = []
    matched_subjects: List[str] = []

    missing_skills: List[str] = []
    missing_subjects: List[str] = []

    explanation: Optional[str] = None
    improvement_advice: Optional[str] = None


class RecommendationListResponse(BaseModel):
    message: Optional[str] = None
    total_careers_analyzed: Optional[int] = None
    recommendations: List[RecommendationCareerResponse]