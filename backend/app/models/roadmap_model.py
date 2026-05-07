import uuid
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class RoadmapStage(Base):
    __tablename__ = "roadmap_stages"

    stage_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    career_id = Column(UUID(as_uuid=True), ForeignKey("careers.career_id"), nullable=False)

    stage_order = Column(Integer, nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)

    required_skills = Column(ARRAY(String), nullable=True)
    suggested_resources = Column(ARRAY(String), nullable=True)

    status = Column(Boolean, default=True)

    career = relationship("Career")