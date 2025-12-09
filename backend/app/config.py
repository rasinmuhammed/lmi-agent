"""
Configuration management for LMI Agent
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = "LMI Agent - Labor Market Intelligence"
    app_version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    
    # Database Configuration
    database_url: str
    db_pool_size: int = 5
    db_max_overflow: int = 10
    
    # Groq Configuration
    groq_api_key: str
    groq_model: str = "mixtral-8x7b-32768"
    groq_temperature: float = 0.3
    groq_max_tokens: int = 2048
    
    # HuggingFace Configuration - Optional now that we use local models
    huggingface_api_key: Optional[str] = None
    
    # Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    chunk_size: int = 512
    chunk_overlap: int = 100
    
    # RAG Configuration
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Scraping Configuration
    scrape_user_agent: str = "LMI-Agent-Bot/1.0 (Educational Purpose)"
    scrape_delay: float = 2.0
    scrape_concurrent_requests: int = 2

    adzuna_app_id: Optional[str] = None
    adzuna_app_key: Optional[str] = None

    usajobs_api_key: Optional[str] = None
    usajobs_email: Optional[str] = None
    
    # CORS Configuration
    cors_origins: list = ["http://localhost:3000", "https://*.vercel.app"]
    
    # Rate Limiting
    rate_limit_per_minute: int = 10
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


# Export settings instance
settings = get_settings()