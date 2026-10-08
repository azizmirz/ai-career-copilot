# app/db/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///./career_copilot.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    # check_same_thread — SQLite üçün lazımdır:
    # FastAPI async mühitində fərqli thread-lər
    # eyni connection istifadə edə bilər
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency injection üçün DB session generator-u.
    Hər request üçün ayrı session açılır, request bitəndə bağlanır.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
