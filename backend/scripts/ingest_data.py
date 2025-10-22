"""
Data ingestion and embedding generation script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, JobPosting, JobChunk, init_db
from app.rag.embeddings import get_embedding_generator, prepare_job_chunks
from app.scraper.job_spider import JobAPIClient
from sqlalchemy import func
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ingest_from_json(json_file: str):
    """
    Ingest jobs from a JSON file
    
    Args:
        json_file: Path to JSON file with scraped jobs
    """
    db = SessionLocal()
    embedding_gen = get_embedding_generator()
    
    try:
        logger.info(f"Loading jobs from {json_file}")
        with open(json_file, 'r') as f:
            jobs = json.load(f)
        
        logger.info(f"Found {len(jobs)} jobs to ingest")
        
        ingested_count = 0
        skipped_count = 0
        
        for job_data in jobs:
            # Check if job already exists
            existing = db.query(JobPosting).filter(
                JobPosting.job_id == job_data['job_id']
            ).first()
            
            if existing:
                logger.debug(f"Job {job_data['job_id']} already exists, skipping")
                skipped_count += 1
                continue
            
            # Create job posting
            job = JobPosting(
                job_id=job_data['job_id'],
                title=job_data['title'],
                company=job_data['company'],
                location=job_data.get('location'),
                description=job_data['description'],
                requirements=job_data.get('requirements', ''),
                skills=job_data.get('skills', []),
                salary_range=job_data.get('salary_range'),
                source_url=job_data['source_url'],
                source_platform=job_data.get('source_platform', 'Unknown'),
                scraped_date=datetime.fromisoformat(job_data['scraped_date']),
                posted_date=datetime.fromisoformat(job_data['posted_date']) if job_data.get('posted_date') else None
            )
            
            db.add(job)
            db.flush()  # Get the job ID
            
            # Generate chunks and embeddings
            chunks = prepare_job_chunks(job_data)
            
            for chunk_data in chunks:
                # Generate embedding
                embedding = embedding_gen.generate_embedding(chunk_data['text'])
                
                # Create chunk
                chunk = JobChunk(
                    job_posting_id=job.id,
                    chunk_text=chunk_data['text'],
                    chunk_index=chunk_data['index'],
                    embedding=embedding,
                    metadata=chunk_data['metadata']
                )
                db.add(chunk)
            
            ingested_count += 1
            
            if ingested_count % 10 == 0:
                logger.info(f"Ingested {ingested_count} jobs...")
                db.commit()
        
        db.commit()
        logger.info(f"Ingestion complete! Ingested: {ingested_count}, Skipped: {skipped_count}")
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def ingest_from_api(search_terms: list, api_source: str = "remoteok"):
    """
    Ingest jobs directly from API
    
    Args:
        search_terms: List of job titles to search
        api_source: API source ('remoteok', 'adzuna')
    """
    db = SessionLocal()
    embedding_gen = get_embedding_generator()
    api_client = JobAPIClient()
    
    try:
        all_jobs = []
        
        for term in search_terms:
            logger.info(f"Fetching jobs for: {term}")
            
            if api_source == "remoteok":
                jobs = api_client.fetch_from_remoteok(term)
            elif api_source == "adzuna":
                # Requires API credentials
                app_id = os.getenv('ADZUNA_APP_ID')
                app_key = os.getenv('ADZUNA_APP_KEY')
                if app_id and app_key:
                    jobs = api_client.fetch_from_adzuna(app_id, app_key, term)
                else:
                    logger.warning("Adzuna credentials not found")
                    jobs = []
            else:
                logger.error(f"Unknown API source: {api_source}")
                jobs = []
            
            all_jobs.extend(jobs)
            logger.info(f"Fetched {len(jobs)} jobs for {term}")
        
        # Save to JSON
        output_file = f'jobs_{api_source}_{datetime.now().strftime("%Y%m%d")}.json'
        with open(output_file, 'w') as f:
            json.dump(all_jobs, f, indent=2)
        
        logger.info(f"Saved {len(all_jobs)} jobs to {output_file}")
        
        # Ingest from the JSON file
        ingest_from_json(output_file)
        
    except Exception as e:
        logger.error(f"Error fetching from API: {e}")
        raise
    finally:
        db.close()


def update_embeddings():
    """
    Regenerate embeddings for existing job chunks
    Useful when changing embedding model
    """
    db = SessionLocal()
    embedding_gen = get_embedding_generator()
    
    try:
        # Get all chunks without embeddings or needing update
        chunks = db.query(JobChunk).all()
        
        logger.info(f"Updating embeddings for {len(chunks)} chunks")
        
        batch_size = 32
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            texts = [chunk.chunk_text for chunk in batch]
            
            # Generate embeddings in batch
            embeddings = embedding_gen.generate_embeddings_batch(texts)
            
            # Update chunks
            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding
            
            if (i + batch_size) % 100 == 0:
                logger.info(f"Updated {i + batch_size} chunks...")
                db.commit()
        
        db.commit()
        logger.info("Embedding update complete!")
        
    except Exception as e:
        logger.error(f"Error updating embeddings: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_stats():
    """Print database statistics"""
    db = SessionLocal()
    
    try:
        total_jobs = db.query(func.count(JobPosting.id)).scalar()
        total_chunks = db.query(func.count(JobChunk.id)).scalar()
        
        companies = db.query(
            JobPosting.company,
            func.count(JobPosting.id)
        ).group_by(JobPosting.company).order_by(
            func.count(JobPosting.id).desc()
        ).limit(10).all()
        
        print("\n=== Database Statistics ===")
        print(f"Total Job Postings: {total_jobs}")
        print(f"Total Indexed Chunks: {total_chunks}")
        print(f"Avg Chunks per Job: {total_chunks / total_jobs if total_jobs > 0 else 0:.1f}")
        print("\nTop 10 Companies:")
        for company, count in companies:
            print(f"  {company}: {count} jobs")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest job data into LMI Agent")
    parser.add_argument(
        'command',
        choices=['json', 'api', 'update-embeddings', 'stats'],
        help='Command to execute'
    )
    parser.add_argument(
        '--file',
        help='JSON file path for json command'
    )
    parser.add_argument(
        '--search-terms',
        nargs='+',
        default=['Machine Learning Engineer', 'Data Scientist', 'MLOps Engineer'],
        help='Search terms for API command'
    )
    parser.add_argument(
        '--api-source',
        default='remoteok',
        choices=['remoteok', 'adzuna'],
        help='API source for fetching jobs'
    )
    
    args = parser.parse_args()
    
    # Initialize database if needed
    init_db()
    
    if args.command == 'json':
        if not args.file:
            print("Error: --file required for json command")
            sys.exit(1)
        ingest_from_json(args.file)
    
    elif args.command == 'api':
        ingest_from_api(args.search_terms, args.api_source)
    
    elif args.command == 'update-embeddings':
        update_embeddings()
    
    elif args.command == 'stats':
        get_stats()
    
    print("\nDone!")