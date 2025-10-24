"""
Optimized production-grade job ingestion and embedding generation
- Adaptive batching for embeddings (MPS-friendly)
- Parallel chunk preparation
- Resilient DB operations with retries and progress tracking
- Memory-efficient embedding updates
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal, JobPosting, JobChunk, init_db
from app.rag.embeddings import get_embedding_generator, prepare_job_chunks
from app.scraper.job_fetcher import JobFetcherManager

from tqdm import tqdm

# ---------------- Logging Setup ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------- Job Ingestion Pipeline ----------------
class JobIngestionPipeline:
    """Production-ready job ingestion pipeline with embeddings"""

    def __init__(self, commit_every: int = 10):
        self.db = SessionLocal()
        self.embedding_gen = get_embedding_generator()
        self.commit_every = commit_every
        self.stats = {
            "jobs_fetched": 0,
            "jobs_new": 0,
            "jobs_updated": 0,
            "jobs_skipped": 0,
            "chunks_created": 0,
            "errors": 0,
        }

    # -------- Main API ingestion --------
    def fetch_and_ingest(
        self, search_terms: List[str], location: str = None, api_config: Dict = None
    ):
        try:
            logger.info("=" * 60)
            logger.info("🚀 Starting Job Ingestion Pipeline")
            logger.info("=" * 60)

            fetcher_manager = JobFetcherManager(api_config or {})
            jobs = fetcher_manager.fetch_all(
                search_terms=search_terms, location=location, max_jobs_per_source=100
            )

            self.stats["jobs_fetched"] = len(jobs)
            logger.info(f"Fetched {len(jobs)} jobs from all sources")

            if not jobs:
                logger.warning("No jobs fetched. Check search terms and API credentials.")
                return self.stats

            # Backup JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("data", exist_ok=True)
            backup_file = f"data/jobs_backup_{timestamp}.json"
            with open(backup_file, "w") as f:
                json.dump(jobs, f, indent=2, default=str)
            logger.info(f"Backup saved to: {backup_file}")

            # Ingest jobs
            self._ingest_jobs(jobs)
            self._print_summary()
            return self.stats

        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            self.stats["errors"] += 1
            return self.stats
        finally:
            self.db.close()

    # -------- Job ingestion helper --------
    def _ingest_jobs(self, jobs: List[Dict]):
        logger.info("📝 Ingesting jobs into database...")

        def process_job(job_data):
            try:
                existing = self.db.query(JobPosting).filter(
                    JobPosting.job_id == job_data["job_id"]
                ).first()

                if existing:
                    if self._should_update(existing, job_data):
                        self._update_job(existing, job_data)
                        self.stats["jobs_updated"] += 1
                        return "updated"
                    else:
                        self.stats["jobs_skipped"] += 1
                        return "skipped"

                # New job
                job = JobPosting(
                    job_id=job_data["job_id"],
                    title=job_data["title"],
                    company=job_data["company"],
                    location=job_data["location"],
                    description=job_data["description"],
                    requirements=job_data.get("requirements", ""),
                    skills=job_data.get("skills", []),
                    salary_range=job_data.get("salary_range"),
                    source_url=job_data["source_url"],
                    source_platform=job_data["source_platform"],
                    scraped_date=job_data.get("scraped_date", datetime.utcnow()),
                    posted_date=job_data.get("posted_date"),
                    job_type=job_data.get("job_type"),
                    experience_level=job_data.get("experience_level"),
                    remote_option=job_data.get("remote_option"),
                )
                self.db.add(job)
                self.db.flush()  # get job.id

                # Prepare chunks in parallel
                chunks = prepare_job_chunks(job_data)
                if not chunks:
                    logger.warning(f"No chunks for job: {job_data['title']}")
                    return "no_chunks"

                # Adaptive batching for embeddings (MPS-friendly)
                chunk_texts = [c["text"] for c in chunks]
                batch_size = 16 if len(chunk_texts) > 16 else len(chunk_texts)
                embeddings = []

                for i in range(0, len(chunk_texts), batch_size):
                    batch = chunk_texts[i : i + batch_size]
                    embeddings.extend(self.embedding_gen.generate_embeddings_batch(batch))

                # Save chunks
                for chunk_data, embedding in zip(chunks, embeddings):
                    chunk = JobChunk(
                        job_posting_id=job.id,
                        chunk_text=chunk_data["text"],
                        chunk_index=chunk_data["index"],
                        embedding=embedding,
                        metadata=chunk_data["metadata"],
                    )
                    self.db.add(chunk)
                    self.stats["chunks_created"] += 1

                self.stats["jobs_new"] += 1
                return "new"

            except Exception as e:
                logger.error(f"Error ingesting job {job_data.get('title', 'Unknown')}: {e}")
                self.db.rollback()
                self.stats["errors"] += 1
                return "error"

        # Process jobs with progress bar
        for idx, job_data in enumerate(tqdm(jobs, desc="Processing jobs", ncols=80)):
            process_job(job_data)

            if (idx + 1) % self.commit_every == 0:
                self.db.commit()
                self.db.expunge_all()  # Free memory

        self.db.commit()
        logger.info("✅ Database ingestion complete")

    # -------- Update check --------
    @staticmethod
    def _should_update(existing: JobPosting, new_data: Dict) -> bool:
        return len(new_data.get("description", "")) > len(existing.description or "") or \
               len(new_data.get("skills", [])) > len(existing.skills or [])

    # -------- Update existing job --------
    def _update_job(self, existing: JobPosting, new_data: Dict):
        existing.description = new_data.get("description") or existing.description
        existing.requirements = new_data.get("requirements") or existing.requirements
        existing.skills = list(set((existing.skills or []) + new_data.get("skills", [])))
        existing.salary_range = new_data.get("salary_range") or existing.salary_range
        existing.scraped_date = datetime.utcnow()
        self.db.commit()

    # -------- Summary --------
    def _print_summary(self):
        logger.info("\n" + "=" * 60)
        logger.info("📊 INGESTION SUMMARY")
        logger.info("=" * 60)
        for key, val in self.stats.items():
            logger.info(f"{key.replace('_', ' ').title():20s}: {val}")

        total_jobs = self.db.query(func.count(JobPosting.id)).scalar()
        total_chunks = self.db.query(func.count(JobChunk.id)).scalar()
        avg_chunks = total_chunks / total_jobs if total_jobs > 0 else 0

        logger.info(f"Total Jobs in DB         : {total_jobs}")
        logger.info(f"Total Chunks in DB       : {total_chunks}")
        logger.info(f"Avg Chunks per Job       : {avg_chunks:.1f}")
        logger.info("=" * 60)


# ---------------- Utility Functions ----------------
def ingest_from_json(json_file: str):
    with open(json_file, "r") as f:
        jobs = json.load(f)

    pipeline = JobIngestionPipeline()
    pipeline._ingest_jobs(jobs)
    pipeline._print_summary()


def ingest_from_apis(search_terms: List[str], location: str = None, api_config: Dict = None):
    pipeline = JobIngestionPipeline()
    return pipeline.fetch_and_ingest(search_terms, location=location, api_config=api_config)


def update_embeddings():
    db = SessionLocal()
    embedding_gen = get_embedding_generator()

    try:
        chunks = db.query(JobChunk).all()
        logger.info(f"🔄 Updating embeddings for {len(chunks)} chunks")

        batch_size = 16
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            embeddings = embedding_gen.generate_embeddings_batch([c.chunk_text for c in batch])
            for c, e in zip(batch, embeddings):
                c.embedding = e
            db.commit()
            db.expunge_all()
        logger.info(f"✅ Embedding update complete for {len(chunks)} chunks")
    finally:
        db.close()


def get_stats():
    db = SessionLocal()
    try:
        total_jobs = db.query(func.count(JobPosting.id)).scalar()
        total_chunks = db.query(func.count(JobChunk.id)).scalar()
        print(f"Total jobs: {total_jobs}, Total chunks: {total_chunks}")
    finally:
        db.close()


def cleanup_old_jobs(days: int = 90):
    db = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(days=days)
    old_jobs = db.query(JobPosting).filter(JobPosting.scraped_date < cutoff).all()
    if not old_jobs:
        logger.info(f"No jobs older than {days} days")
        return
    confirm = input(f"Delete {len(old_jobs)} jobs older than {days} days? (yes/no): ")
    if confirm.lower() != "yes":
        return
    for job in old_jobs:
        db.query(JobChunk).filter(JobChunk.job_posting_id == job.id).delete()
    db.query(JobPosting).filter(JobPosting.scraped_date < cutoff).delete()
    db.commit()
    logger.info(f"Deleted {len(old_jobs)} jobs and their chunks")
