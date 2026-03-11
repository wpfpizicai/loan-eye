# models/analysis.py
import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    competitor_id: Mapped[str] = mapped_column(String, ForeignKey("competitors.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    note_count: Mapped[int] = mapped_column(Integer, default=0)
    total_engagement: Mapped[int] = mapped_column(Integer, default=0)
    sentiment_positive_rate: Mapped[float] = mapped_column(Float, default=0.0)
    top_complaints: Mapped[list] = mapped_column(JSONB, default=list)
    top_praises: Mapped[list] = mapped_column(JSONB, default=list)
    product_features: Mapped[dict] = mapped_column(JSONB, default=dict)
    hot_notes: Mapped[list] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
