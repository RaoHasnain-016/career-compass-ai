import uuid
from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class SavedCareer(Base):
    __tablename__ = "saved_careers"

    saved_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    career_id = Column(UUID(as_uuid=True), ForeignKey("careers.career_id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    career = relationship("Career")

    __table_args__ = (
        UniqueConstraint("user_id", "career_id", name="unique_user_career"),
    )