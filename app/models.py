"""
Database models for Go2.Ninja
PostgreSQL compatible
"""
from sqlalchemy import Column, Integer, String, DateTime, Index, Text
from sqlalchemy.sql import func
from .database import Base


class URL(Base):
    """URL model with indexes for fast lookups."""
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(20), unique=True, nullable=False, index=True)
    clicks = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_original_url", "original_url", postgresql_ops={"original_url": "text_pattern_ops"}),
    )
