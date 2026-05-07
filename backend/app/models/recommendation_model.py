import uuid
from sqlalchemy import Column, Numeric, Text, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    career_id = Column(UUID(as_uuid=True), ForeignKey("careers.career_id"), nullable=False)

    match_score = Column(Numeric(5, 2), nullable=False)
    confidence_level = Column(String(50), nullable=True)
    eligibility_status = Column(String(50), nullable=True)

    matched_interests = Column(ARRAY(String), nullable=True)
    matched_skills = Column(ARRAY(String), nullable=True)
    matched_subjects = Column(ARRAY(String), nullable=True)

    missing_skills = Column(ARRAY(String), nullable=True)
    missing_subjects = Column(ARRAY(String), nullable=True)

    explanation = Column(Text, nullable=True)
    improvement_advice = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    career = relationship("Career")