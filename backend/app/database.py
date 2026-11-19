"""Connexion PostgreSQL (SQLAlchemy 2.x)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from . import config


class Base(DeclarativeBase):
    pass


engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """Dépendance FastAPI : une session SQLAlchemy par requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
