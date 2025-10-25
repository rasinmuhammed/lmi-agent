"""
Optimized production-grade job ingestion and embedding generation
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal, JobPosting, JobChunk, init_db
from app.rag.embeddings import get_embedding_generator, prepare_job_chunks
from app.scraper.job_fetcher import JobFetcherManager
from sqlalchemy import func
from tqdm import tqdm

# ---------------- Logging Setup ----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class JobIngestionPipeline:
    """Production-ready job ingestion pipeline with embeddings"""

    def __init__(self, commit_every: int = 5):
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
            logger.info(f"✅ Backup saved to: {backup_file}")

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

    def _ingest_jobs(self, jobs: List[Dict]):
        logger.info("📝 Ingesting jobs into database...")
        
        for idx, job_data in enumerate(tqdm(jobs, desc="Processing jobs", ncols=80)):
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

                # ✅ Create new job posting
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

                # ✅ Prepare and create chunks
                chunks = prepare_job_chunks(job_data)
                
                if not chunks:
                    logger.warning(f"⚠️ No chunks generated for job: {job.title}")
                    self.stats["jobs_new"] += 1
                    continue

                # Generate embeddings in batches
                chunk_texts = [c["text"] for c in chunks]
                embeddings = self.embedding_gen.generate_embeddings_batch(chunk_texts, batch_size=8)
                
                logger.info(f"Generated {len(embeddings)} embeddings for {job.title}")

                # ✅ Create chunk records
                for chunk_data, embedding in zip(chunks, embeddings):
                    chunk = JobChunk(
                        job_posting_id=job.id,
                        chunk_text=chunk_data["text"],
                        chunk_index=chunk_data["index"],
                        embedding=embedding,
                        chunk_metadata=chunk_data["metadata"],  # ✅ Use correct attribute name
                    )
                    self.db.add(chunk)
                    self.stats["chunks_created"] += 1

                self.stats["jobs_new"] += 1
                logger.info(f"✅ Created {len(chunks)} chunks for job ID {job.id}")

                # ✅ Commit every N jobs
                if (idx + 1) % self.commit_every == 0:
                    self.db.commit()
                    logger.info(f"💾 Committed batch at index {idx + 1}")

            except Exception as e:
                logger.error(f"❌ Error ingesting job {job_data.get('title', 'Unknown')}: {e}", exc_info=True)
                self.db.rollback()
                self.stats["errors"] += 1

        # ✅ Final commit for remaining jobs
        try:
            self.db.commit()
            logger.info("✅ Final commit completed")
        except Exception as e:
            logger.error(f"❌ Final commit failed: {e}")
            self.db.rollback()

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

    def _print_summary(self):
        """Print ingestion statistics"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 INGESTION SUMMARY")
        logger.info("=" * 60)
        for key, val in self.stats.items():
            logger.info(f"{key.replace('_', ' ').title():25s}: {val}")

        total_jobs = self.db.query(func.count(JobPosting.id)).scalar()
        total_chunks = self.db.query(func.count(JobChunk.id)).scalar()
        avg_chunks = total_chunks / total_jobs if total_jobs > 0 else 0

        logger.info(f"{'Total Jobs in DB':25s}: {total_jobs}")
        logger.info(f"{'Total Chunks in DB':25s}: {total_chunks}")
        logger.info(f"{'Avg Chunks per Job':25s}: {avg_chunks:.1f}")
        logger.info("=" * 60)


# ---------------- Entry Points ----------------
def ingest_from_apis(search_terms: List[str], location: str = None, api_config: Dict = None):
    """Ingest jobs from API sources"""
    pipeline = JobIngestionPipeline(commit_every=5)
    return pipeline.fetch_and_ingest(search_terms, location=location, api_config=api_config)


def ingest_from_json(json_file: str):
    """Ingest jobs from JSON file"""
    with open(json_file, "r") as f:
        jobs = json.load(f)
    
    # Handle both array and single object formats
    if isinstance(jobs, dict):
        jobs = [jobs]
    
    pipeline = JobIngestionPipeline(commit_every=5)
    pipeline._ingest_jobs(jobs)
    pipeline._print_summary()


def get_stats():
    """Print database statistics"""
    db = SessionLocal()
    try:
        total_jobs = db.query(func.count(JobPosting.id)).scalar()
        total_chunks = db.query(func.count(JobChunk.id)).scalar()
        
        print(f"\n{'=' * 40}")
        print(f"Total Jobs:   {total_jobs}")
        print(f"Total Chunks: {total_chunks}")
        print(f"{'=' * 40}\n")
        
        if total_jobs > 0:
            recent_jobs = db.query(JobPosting).order_by(JobPosting.scraped_date.desc()).limit(5).all()
            print("Recent Jobs:")
            for job in recent_jobs:
                print(f"  - {job.title} at {job.company}")
    finally:
        db.close()


# ---------------- CLI ----------------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Ingestion Pipeline")
    parser.add_argument("command", choices=["ingest", "stats", "json"], help="Command to run")
    parser.add_argument("--terms", nargs="+", default=["Machine Learning Engineer"], help="Search terms")
    parser.add_argument("--location", help="Location filter")
    parser.add_argument("--file", help="JSON file to ingest")
    
    args = parser.parse_args()
    
    if args.command == "ingest":
        api_config = {
            "usajobs_email": os.getenv("USAJOBS_EMAIL"),
            "usajobs_api_key": os.getenv("USAJOBS_API_KEY"),
            "adzuna_app_id": os.getenv("ADZUNA_APP_ID"),
            "adzuna_app_key": os.getenv("ADZUNA_APP_KEY"),
        }
        ingest_from_apis(args.terms, args.location, api_config)
    
    elif args.command == "json":
        if not args.file:
            print("Error: --file required for json command")
            sys.exit(1)
        ingest_from_json(args.file)
    
    elif args.command == "stats":
        get_stats()