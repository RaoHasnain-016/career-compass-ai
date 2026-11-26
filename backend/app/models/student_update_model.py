from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text, Uuid, func

from app.database import Base


class StudentUpdate(Base):
    __tablename__ = "student_updates"
    __table_args__ = (Index("ix_student_updates_user_date", "user_id", "published_at"),)

    update_id = Column(Uuid, primary_key=True, default=uuid4)
    user_id = Column(Uuid, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    category = Column(String(24), nullable=False)
    title = Column(String(180), nullable=False)
    summary = Column(Text, nullable=False)
    url = Column(String(120), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class StudentUpdateRead(Base):
    __tablename__ = "student_update_reads"

    user_id = Column(Uuid, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    notification_id = Column(String(120), primary_key=True)
    read_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
