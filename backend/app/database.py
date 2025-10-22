"""
Database connection and models using SQLAlchemy with pgvector
"""
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Float, JSON, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app.config import settings

# ---------------------------------------------------------------------
# Database Engine
# ---------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.debug,
    future=True,  # ✅ ensures SQLAlchemy 2.x style execution
)

# ---------------------------------------------------------------------
# Session Factory
# ---------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# ---------------------------------------------------------------------
# Declarative Base
# ---------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------
# MODELS
# ---------------------------------------------------------------------
class JobPosting(Base):
    """Job posting model with vector embeddings"""
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    company = Column(String(500), nullable=False)
    location = Column(String(500))
    description = Column(Text, nullable=False)
    requirements = Column(Text)
    skills = Column(JSON)
    salary_range = Column(String(200))
    source_url = Column(String(1000), nullable=False)
    source_platform = Column(String(100))
    posted_date = Column(DateTime, default=datetime.utcnow)
    scraped_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Metadata for filtering
    job_type = Column(String(100))           # Full-time, Contract, etc.
    experience_level = Column(String(100))   # Entry, Mid, Senior
    remote_option = Column(String(100))      # Remote, Hybrid, On-site
    
    def __repr__(self):
        return f"<JobPosting(title='{self.title}', company='{self.company}')>"


class JobChunk(Base):
    """Text chunks with embeddings for RAG retrieval"""
    __tablename__ = "job_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    job_posting_id = Column(Integer, index=True)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer)
    
    # Vector embedding for similarity search
    embedding = Column(Vector(settings.embedding_dimension))
    
    # ✅ FIX: rename reserved 'metadata' to 'chunk_metadata'
    chunk_metadata = Column("metadata", JSON)  # Column name in DB remains 'metadata'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<JobChunk(job_id={self.job_posting_id}, index={self.chunk_index})>"


class SkillAnalysis(Base):
    """Cached skill analysis results"""
    __tablename__ = "skill_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), nullable=False, index=True)
    job_role = Column(String(200))
    location = Column(String(200))
    
    # Analysis results
    top_skills = Column(JSON)
    skill_frequencies = Column(JSON)
    skill_necessity_scores = Column(JSON)
    emerging_skills = Column(JSON)
    
    # Metadata
    total_jobs_analyzed = Column(Integer)
    analysis_date = Column(DateTime, default=datetime.utcnow, index=True)
    source_job_ids = Column(JSON)
    
    def __repr__(self):
        return f"<SkillAnalysis(query='{self.query}', jobs={self.total_jobs_analyzed})>"


# ---------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database with pgvector extension"""
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")
