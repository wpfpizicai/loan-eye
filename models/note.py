# models/note.py
from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class Note(Base):
    __tablename__ = "notes"

    note_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    competitor_id: Mapped[str | None] = mapped_column(String, ForeignKey("competitors.id"), nullable=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(100), default="")
    publish_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    likes: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    collects: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False)
    url: Mapped[str] = mapped_column(String(500), default="")
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    @property
    def engagement(self) -> int:
        return self.likes + self.comments + self.collects + self.shares
