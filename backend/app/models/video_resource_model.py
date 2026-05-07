import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class VideoResource(Base):
    __tablename__ = "video_resources"

    video_resource_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    youtube_video_id = Column(String(100), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    channel_title = Column(String(150), nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    video_url = Column(Text, nullable=False)

    skill = Column(String(100), nullable=False)
    career_field = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=True, default="Beginner")

    source = Column(String(50), default="YouTube")
    is_free = Column(Boolean, default=True)
    status = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())