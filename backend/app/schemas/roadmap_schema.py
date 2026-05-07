from typing import List, Optional
from pydantic import BaseModel


class RoadmapStageBase(BaseModel):
    career_id: str
    stage_order: int
    title: str
    description: str
    required_skills: Optional[List[str]] = []
    suggested_resources: Optional[List[str]] = []
    status: Optional[bool] = True


class RoadmapStageCreate(RoadmapStageBase):
    pass


class RoadmapStageUpdate(BaseModel):
    stage_order: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    suggested_resources: Optional[List[str]] = None
    status: Optional[bool] = None