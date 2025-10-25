"""
Debug script to check why chunks aren't being created
"""
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag.embeddings import prepare_job_chunks, chunk_text

# Load the job data
with open('debug_data/jobs_backup_20251022_231300.json', 'r') as f:
    job_data = json.load(f)

print("="*60)
print("JOB DATA ANALYSIS")
print("="*60)
print(f"Title: {job_data.get('title')}")
print(f"Company: {job_data.get('company')}")
print(f"Description length: {len(job_data.get('description', ''))}")
print(f"Requirements length: {len(job_data.get('requirements', ''))}")
print(f"Skills: {job_data.get('skills')}")
print()

# Test chunk_text function
description = job_data.get('description', '')
print("="*60)
print("TESTING chunk_text() FUNCTION")
print("="*60)
chunks = chunk_text(description)
print(f"Number of chunks from description: {len(chunks)}")
if chunks:
    print(f"First chunk preview: {chunks[0][:100]}...")
print()

# Test prepare_job_chunks
print("="*60)
print("TESTING prepare_job_chunks() FUNCTION")
print("="*60)
prepared_chunks = prepare_job_chunks(job_data)
print(f"Number of prepared chunks: {len(prepared_chunks)}")
if prepared_chunks:
    print(f"\nFirst chunk:")
    print(f"  Text length: {len(prepared_chunks[0]['text'])}")
    print(f"  Index: {prepared_chunks[0]['index']}")
    print(f"  Metadata: {prepared_chunks[0]['metadata']}")
    print(f"\n  Text preview:")
    print(f"  {prepared_chunks[0]['text'][:200]}...")
else:
    print("❌ NO CHUNKS GENERATED!")
    print("\nDebugging full_text construction:")
    full_text = f"""
Job Title: {job_data.get('title', '')}
Company: {job_data.get('company', '')}
Location: {job_data.get('location', '')}

Description:
{job_data.get('description', '')}

Requirements:
{job_data.get('requirements', '')}

Skills: {', '.join(job_data.get('skills', []))}
""".strip()
    print(f"Full text length: {len(full_text)}")
    print(f"Full text preview:\n{full_text[:500]}...")
print()