import uuid
from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class LearningResource(Base):
    __tablename__ = "learning_resources"

    resource_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(150), nullable=False)
    platform = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)

    skill = Column(String(100), nullable=False)
    career_field = Column(String(100), nullable=True)

    difficulty = Column(String(50), nullable=True)
    resource_type = Column(String(50), nullable=True)

    description = Column(Text, nullable=True)

    is_free = Column(Boolean, default=True)
    status = Column(Boolean, default=True)