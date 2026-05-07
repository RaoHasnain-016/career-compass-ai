import uuid
from sqlalchemy import Column, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    profile_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), unique=True, nullable=False)

    age = Column(String(10), nullable=True)
    academic_level = Column(String(50), nullable=False)
    class_degree = Column(String(100), nullable=True)
    marks_cgpa = Column(Numeric(5, 2), nullable=True)

    favorite_subjects = Column(ARRAY(String), nullable=True)
    weak_subjects = Column(ARRAY(String), nullable=True)
    interests = Column(ARRAY(String), nullable=True)
    skills = Column(ARRAY(String), nullable=True)
    study_preference = Column(Text, nullable=True)

    user = relationship("User")
