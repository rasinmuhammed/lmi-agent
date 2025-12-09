"""
Service for handling job ingestion operations
Refactored from scripts/ingest_data.py for use in backend API
"""
import logging
import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import JobPosting, JobChunk
from app.rag.embeddings import get_embedding_generator, prepare_job_chunks
from app.scraper.job_fetcher import JobFetcherManager
from app.config import settings

logger = logging.getLogger(__name__)

class JobIngestionService:
    """Service for fetching and ingesting jobs"""

    def __init__(self, db: Session):
        self.db = db
        self.embedding_gen = get_embedding_generator()
        self.stats = {
            "jobs_fetched": 0,
            "jobs_new": 0,
            "jobs_updated": 0,
            "jobs_skipped": 0,
            "chunks_created": 0,
            "errors": 0,
        }

    def fetch_and_ingest(
        self, 
        search_terms: List[str], 
        location: str = None, 
        max_jobs: int = 10
    ) -> Dict:
        """
        Fetch jobs from external sources and ingest them
        
        Args:
            search_terms: List of queries
            location: Location filter
            max_jobs: Limit per source
            
        Returns:
            Statistics dictionary
        """
        try:
            logger.info("=" * 60)
            logger.info("🚀 Starting Live Job Ingestion")
            logger.info("=" * 60)

            # Initialize fetcher with config from settings
            api_config = {
                "usajobs_email": settings.usajobs_email,
                "usajobs_api_key": settings.usajobs_api_key,
                "adzuna_app_id": settings.adzuna_app_id,
                "adzuna_app_key": settings.adzuna_app_key,
            }
            
            fetcher_manager = JobFetcherManager(api_config)
            jobs = fetcher_manager.fetch_all(
                search_terms=search_terms, 
                location=location, 
                max_jobs_per_source=max_jobs
            )

            self.stats["jobs_fetched"] = len(jobs)
            logger.info(f"Fetched {len(jobs)} jobs from all sources")

            if not jobs:
                return self.stats

            # Ingest jobs
            self._ingest_jobs(jobs)
            return self.stats

        except Exception as e:
            logger.error(f"Ingestion service error: {e}", exc_info=True)
            self.stats["errors"] += 1
            return self.stats

    def _ingest_jobs(self, jobs: List[Dict]):
        """Ingest job data into database"""
        logger.info("📝 Ingesting jobs into database...")
        
        for job_data in jobs:
            try:
                # Check if job exists
                existing = self.db.query(JobPosting).filter(
                    JobPosting.job_id == job_data["job_id"]
                ).first()

                if existing:
                    if self._should_update(existing, job_data):
                        self._update_job(existing, job_data)
                        self.stats["jobs_updated"] += 1
                    else:
                        self.stats["jobs_skipped"] += 1
                    continue

                # Create new job posting
                job = JobPosting(
                    job_id=job_data["job_id"],
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data.get("location", ""),
                    description=job_data.get("description", ""),
                    requirements=job_data.get("requirements", ""),
                    skills=job_data.get("skills", []),
                    salary_range=job_data.get("salary_range"),
                    source_url=job_data["source_url"],
                    source_platform=job_data.get("source_platform", "Unknown"),
                    scraped_date=job_data.get("scraped_date", datetime.utcnow()),
                    posted_date=job_data.get("posted_date"),
                    job_type=job_data.get("job_type"),
                    experience_level=job_data.get("experience_level"),
                    remote_option=job_data.get("remote_option"),
                )
                
                self.db.add(job)
                self.db.flush()  # Get job.id immediately
                
                logger.info(f"✅ Created job: {job.title} (ID: {job.id})")

                # Prepare and create chunks
                chunks = prepare_job_chunks(job_data)
                
                if not chunks:
                    self.stats["jobs_new"] += 1
                    continue

                # Generate embeddings in batches
                chunk_texts = [c["text"] for c in chunks]
                embeddings = self.embedding_gen.generate_embeddings_batch(chunk_texts, batch_size=5)
                
                # Create chunk records
                for chunk_data, embedding in zip(chunks, embeddings):
                    chunk = JobChunk(
                        job_posting_id=job.id,
                        chunk_text=chunk_data["text"],
                        chunk_index=chunk_data["index"],
                        embedding=embedding,
                        chunk_metadata=chunk_data["metadata"],
                    )
                    self.db.add(chunk)
                    self.stats["chunks_created"] += 1

                self.stats["jobs_new"] += 1
                
                # Commit frequently to avoid large transaction locks
                self.db.commit()

            except Exception as e:
                logger.error(f"❌ Error ingesting job {job_data.get('title', 'Unknown')}: {e}")
                self.db.rollback()
                self.stats["errors"] += 1

    @staticmethod
    def _should_update(existing: JobPosting, new_data: Dict) -> bool:
        """Check if existing job should be updated"""
        return (
            len(new_data.get("description", "")) > len(existing.description or "")
            or len(new_data.get("skills", [])) > len(existing.skills or [])
        )

    def _update_job(self, existing: JobPosting, new_data: Dict):
        """Update existing job with new data"""
        existing.description = new_data.get("description") or existing.description
        existing.requirements = new_data.get("requirements") or existing.requirements
        existing.skills = list(set((existing.skills or []) + new_data.get("skills", [])))
        existing.salary_range = new_data.get("salary_range") or existing.salary_range
        existing.scraped_date = datetime.utcnow()
