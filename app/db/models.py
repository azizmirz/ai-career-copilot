# app/db/models.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class User(Base):
    """
    İstifadəçi cədvəli.
    Şifrə heç vaxt açıq saxlanılmır — yalnız bcrypt hash-i.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # İstifadəçinin bütün analiz tarixçəsi
    analyses = relationship("AnalysisHistory", back_populates="user")


class AnalysisHistory(Base):
    """
    Hər CV-JD analizi bir sətir kimi saxlanılır.

    Niyə JSON string?
    - matched_skills, missing_skills kimi mürəkkəb strukturları
      ayrı cədvəllərdə saxlamaq çox mürəkkəbləşdirər
    - SQLite-da JSON tipi yoxdur, Text istifadə edirik
    """

    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # CV məlumatları
    cv_owner = Column(String, nullable=True)

    # JD məlumatları
    job_title = Column(String, nullable=True)
    company = Column(String, nullable=True)

    # Analiz nəticəsi
    match_score = Column(Float, nullable=False)
    match_level = Column(String, nullable=False)
    summary = Column(Text, nullable=True)

    # Strukturlaşdırılmış data JSON string kimi
    matched_skills_json = Column(Text, nullable=True)
    missing_skills_json = Column(Text, nullable=True)
    recommendations_json = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="analyses")
