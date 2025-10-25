"""
Check what's actually in the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, JobPosting, JobChunk
from sqlalchemy import func

db = SessionLocal()

try:
    print("="*60)
    print("DATABASE INSPECTION")
    print("="*60)
    
    # Check jobs
    jobs = db.query(JobPosting).all()
    print(f"\nTotal Jobs: {len(jobs)}")
    
    for job in jobs:
        print(f"\n{'='*60}")
        print(f"Job ID: {job.id}")
        print(f"Job ID (external): {job.job_id}")
        print(f"Title: {job.title}")
        print(f"Company: {job.company}")
        print(f"Description length: {len(job.description or '')}")
        print(f"Requirements length: {len(job.requirements or '')}")
        print(f"Skills: {job.skills}")
        print(f"Source: {job.source_platform}")
        print(f"Scraped: {job.scraped_date}")
        
        # Count chunks for this job
        chunk_count = db.query(func.count(JobChunk.id)).filter(
            JobChunk.job_posting_id == job.id
        ).scalar()
        
        print(f"\n📦 Chunks for this job: {chunk_count}")
        
        if chunk_count > 0:
            chunks = db.query(JobChunk).filter(
                JobChunk.job_posting_id == job.id
            ).limit(3).all()
            
            print("\nFirst few chunks:")
            for i, chunk in enumerate(chunks, 1):
                print(f"\n  Chunk {i}:")
                print(f"    ID: {chunk.id}")
                print(f"    Index: {chunk.chunk_index}")
                print(f"    Text length: {len(chunk.chunk_text)}")
                print(f"    Text preview: {chunk.chunk_text[:100]}...")
                print(f"    Embedding length: {len(chunk.embedding) if chunk.embedding else 0}")
                print(f"    Metadata: {chunk.chunk_metadata}")
    
    print("\n" + "="*60)
    
finally:
    db.close()