from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from datetime import datetime, timezone
from app.database import Base


class AppelOffre(Base):
    __tablename__ = "appels_offres"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    organisme = Column(String(500), nullable=True)
    date_publication = Column(DateTime, nullable=True)
    date_cloture = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=False)  # BOAMP, DECP
    url = Column(Text, nullable=True)
    lieu_execution = Column(String(500), nullable=True)
    nature_marche = Column(String(255), nullable=True)
    montant_estime = Column(Float, nullable=True)
    cpv_codes = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(255), unique=True, nullable=False)
    category = Column(String(100), nullable=True)  # e.g., "tech", "domain", "skill"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    query = Column(Text, nullable=True)
    results_count = Column(Integer, default=0)
    status = Column(String(50), default="success")
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
