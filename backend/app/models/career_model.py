import uuid
from sqlalchemy import Column, String, Text, Boolean, Numeric
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.database import Base


class Career(Base):
    __tablename__ = "careers"

    career_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(150), nullable=False)
    field = Column(String(100), nullable=False)
    overview = Column(Text, nullable=False)
    required_education = Column(Text, nullable=False)
    required_skills = Column(ARRAY(String), nullable=False)
    required_subjects = Column(ARRAY(String), nullable=True)
    related_interests = Column(ARRAY(String), nullable=True)
    minimum_marks = Column(Numeric(5, 2), nullable=True, default=0)
    future_scope = Column(Text, nullable=True)
    difficulty_level = Column(String(50), nullable=True)
    status = Column(Boolean, default=True)