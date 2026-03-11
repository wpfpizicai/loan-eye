# models/base.py
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

@event.listens_for(Base, "init", propagate=True)
def _apply_column_defaults(target, args, kwargs):
    """Apply SQLAlchemy column defaults at object construction time."""
    for col in target.__table__.columns:
        if col.name not in kwargs and col.default is not None:
            if col.default.is_scalar:
                kwargs[col.name] = col.default.arg
            elif callable(col.default.arg):
                kwargs[col.name] = col.default.arg({})

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
