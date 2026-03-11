# models/comment.py
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
import enum

class SentimentLabel(str, enum.Enum):
    positive = "positive"
    negative = "negative"
    neutral = "neutral"

class Comment(Base):
    __tablename__ = "comments"

    comment_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    note_id: Mapped[str] = mapped_column(String(100), ForeignKey("notes.note_id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(100), default="")
    likes: Mapped[int] = mapped_column(Integer, default=0)
    publish_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sentiment_label: Mapped[SentimentLabel | None] = mapped_column(SAEnum(SentimentLabel), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
