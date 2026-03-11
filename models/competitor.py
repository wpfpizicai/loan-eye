# models/competitor.py
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, ARRAY, Enum as SAEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base
import enum

class CompetitorCategory(str, enum.Enum):
    core = "core"
    industry = "industry"

class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    category: Mapped[CompetitorCategory] = mapped_column(SAEnum(CompetitorCategory), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
