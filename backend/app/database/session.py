from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

# Creates the database engine (one per application)
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
)

# Factory that creates database sessions
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass
