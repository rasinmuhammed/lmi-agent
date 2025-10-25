"""
Ultra-minimal memory-safe ingestion for M1/M2 Macs
Uses dummy embeddings to avoid MPS memory crashes
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, JobPosting, JobChunk
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simple_ingest(json_file: str, use_real_embeddings: bool = False):
    """Minimal ingestion with optional dummy embeddings for testing"""
    db = SessionLocal()
    
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Handle both dict and list
        jobs = [data] if isinstance(data, dict) else data
        
        logger.info(f"Processing {len(jobs)} job(s)...")
        
        for job_data in jobs:
            # Check if exists
            existing = db.query(JobPosting).filter(
                JobPosting.job_id == job_data["job_id"]
            ).first()
            
            if existing:
                # Check if it has chunks
                chunk_count = db.query(JobChunk).filter(
                    JobChunk.job_posting_id == existing.id
                ).count()
                
                if chunk_count > 0:
                    logger.info(f"⏭️  Job already exists with {chunk_count} chunks, skipping: {job_data['title']}")
                    continue
                else:
                    logger.info(f"⚠️  Job exists but has NO chunks: {job_data['title']}")
                    logger.info(f"   Will create chunks for existing job ID: {existing.id}")
                    job = existing
            else:
                # Create job without chunks first
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
                    scraped_date=datetime.now(),
                    job_type=job_data.get("job_type"),
                    experience_level=job_data.get("experience_level"),
                    remote_option=job_data.get("remote_option"),
                )
                
                db.add(job)
                db.commit()
                db.refresh(job)
                
                logger.info(f"✅ Created job: {job.title} (ID: {job.id})")
            
            # Now add chunks
            from app.rag.embeddings import prepare_job_chunks
            
            chunks = prepare_job_chunks(job_data)
            
            if not chunks:
                logger.warning(f"⚠️  No chunks generated for {job.title}")
                continue
            
            logger.info(f"📝 Creating {len(chunks)} chunks...")
            
            # Load embedding generator only if needed
            embedding_gen = None
            if use_real_embeddings:
                try:
                    from app.rag.embeddings import get_embedding_generator
                    embedding_gen = get_embedding_generator()
                    logger.info("Using real embeddings (may be slow)")
                except Exception as e:
                    logger.warning(f"Failed to load embeddings, using dummy: {e}")
                    use_real_embeddings = False
            
            if not use_real_embeddings:
                logger.info("Using dummy embeddings (for testing)")
            
            for idx, chunk_data in enumerate(chunks):
                try:
                    # Generate embedding
                    if use_real_embeddings and embedding_gen:
                        embedding = embedding_gen.generate_embedding(chunk_data["text"])
                    else:
                        # Dummy embedding - zeros
                        embedding = [0.0] * 384
                    
                    chunk = JobChunk(
                        job_posting_id=job.id,
                        chunk_text=chunk_data["text"],
                        chunk_index=chunk_data["index"],
                        embedding=embedding,
                        chunk_metadata=chunk_data["metadata"],
                    )
                    
                    db.add(chunk)
                    db.commit()
                    
                    logger.info(f"  ✅ Chunk {idx+1}/{len(chunks)} created")
                    
                except Exception as e:
                    logger.error(f"  ❌ Chunk {idx+1} failed: {e}")
                    db.rollback()
                    continue
            
            logger.info(f"✅ Completed job: {job.title} with {len(chunks)} chunks")
        
        # Print summary
        total_jobs = db.query(JobPosting).count()
        total_chunks = db.query(JobChunk).count()
        
        logger.info("\n" + "="*50)
        logger.info("📊 DATABASE SUMMARY")
        logger.info("="*50)
        logger.info(f"Total Jobs:   {total_jobs}")
        logger.info(f"Total Chunks: {total_chunks}")
        logger.info("="*50)
        
        if not use_real_embeddings:
            logger.warning("\n⚠️  NOTE: Using dummy embeddings!")
            logger.warning("Run with --real-embeddings flag to generate actual embeddings")
            logger.warning("Or use: python scripts/update_embeddings.py")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python minimal_ingest.py <json_file> [--real-embeddings]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    use_real_embeddings = "--real-embeddings" in sys.argv
    
    simple_ingest(json_file, use_real_embeddings)