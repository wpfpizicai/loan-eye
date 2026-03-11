# config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/loan_eye"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/loan_eye"
    xhs_cookie: str = ""
    scrape_max_notes_per_keyword: int = 50
    scrape_comments_per_note: int = 100
    hot_note_multiplier: float = 3.0
    sentiment_model: str = "uer/roberta-base-finetuned-jd-binary-chinese"

    class Config:
        env_file = ".env"

settings = Settings()
