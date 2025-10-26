#!/usr/bin/env python3
"""
Complete system verification script
Tests all components before deployment
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dotenv

dotenv.load_dotenv()
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def check_env_vars():
    """Check required environment variables"""
    print_section("1. Environment Variables")
    
    required_vars = {
        'DATABASE_URL': 'Neon PostgreSQL connection string',
        'GROQ_API_KEY': 'Groq LLM API key',
        'HUGGINGFACE_API_KEY': 'HuggingFace API token'
    }
    
    optional_vars = {
        'ADZUNA_APP_ID': 'Adzuna job API',
        'ADZUNA_APP_KEY': 'Adzuna job API',
        'USAJOBS_API_KEY': 'USAJobs API'
    }
    
    all_good = True
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and not value.startswith('your_') and not value.startswith('postgresql://username'):
            print(f"  ✅ {var}: Configured")
        else:
            print(f"  ❌ {var}: NOT SET - {description}")
            all_good = False
    
    print("\nOptional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and not value.startswith('your_'):
            print(f"  ✅ {var}: Configured")
        else:
            print(f"  ⚠️  {var}: Not set - {description}")
    
    return all_good


def check_database():
    """Check database connection and setup"""
    print_section("2. Database Connection")
    
    try:
        from app.database import engine, SessionLocal, JobPosting, JobChunk
        from sqlalchemy import func
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"  ✅ Connected to PostgreSQL")
            print(f"     Version: {version[:50]}...")
            
            # Check pgvector
            result = conn.execute(text(
                "SELECT * FROM pg_extension WHERE extname = 'vector'"
            ))
            if result.fetchone():
                print(f"  ✅ pgvector extension: Installed")
            else:
                print(f"  ❌ pgvector extension: NOT INSTALLED")
                print(f"     Run: CREATE EXTENSION IF NOT EXISTS vector;")
                return False
            
            # Check tables
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]
            
            if 'job_postings' in tables and 'job_chunks' in tables:
                print(f"  ✅ Tables: Found {len(tables)} tables")
            else:
                print(f"  ❌ Tables: Missing required tables")
                print(f"     Run: python scripts/setup_db.py setup")
                return False
        
        # Check data
        db = SessionLocal()
        job_count = db.query(func.count(JobPosting.id)).scalar()
        chunk_count = db.query(func.count(JobChunk.id)).scalar()
        
        print(f"  ℹ️  Data: {job_count} jobs, {chunk_count} chunks")
        
        if job_count == 0:
            print(f"  ⚠️  No data yet. Run ingestion:")
            print(f"     python scripts/ingest_data.py api --search-terms 'ML Engineer'")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        return False


def check_embeddings():
    """Test embedding generation"""
    print_section("3. Embedding Generation")
    
    try:
        from app.rag.embeddings import get_embedding_generator
        
        generator = get_embedding_generator()
        
        # Test single embedding
        test_text = "Machine learning engineer with Python experience"
        embedding = generator.generate_embedding(test_text)
        
        print(f"  ✅ Single embedding: Success")
        print(f"     Dimension: {len(embedding)}")
        print(f"     Sample: [{embedding[0]:.4f}, {embedding[1]:.4f}, ...]")
        
        # Test batch
        test_texts = [
            "Data scientist",
            "Full stack developer",
            "DevOps engineer"
        ]
        embeddings = generator.generate_embeddings_batch(test_texts)
        
        print(f"  ✅ Batch embeddings: {len(embeddings)} generated")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Embedding test failed: {e}")
        if "HUGGINGFACE_API_KEY" in str(e):
            print(f"     Get free token: https://huggingface.co/settings/tokens")
        return False


def check_llm():
    """Test LLM connection"""
    print_section("4. LLM (Groq) Connection")
    
    try:
        from groq import Groq
        from app.config import settings
        
        client = Groq(api_key=settings.groq_api_key)
        
        # Test simple completion
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "user", "content": "Say 'Hello' if you're working!"}
            ],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"  ✅ Groq API: Connected")
        print(f"     Model: {settings.groq_model}")
        print(f"     Test response: {result}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Groq API test failed: {e}")
        print(f"     Get free key: https://console.groq.com")
        return False


def check_retrieval():
    """Test RAG retrieval"""
    print_section("5. RAG Retrieval System")
    
    try:
        from app.database import SessionLocal
        from app.rag.retriever import RAGRetriever
        
        db = SessionLocal()
        retriever = RAGRetriever(db)
        
        # Test retrieval
        results = retriever.retrieve(
            query="machine learning engineer",
            top_k=3
        )
        
        print(f"  ✅ Vector search: Success")
        print(f"     Retrieved: {len(results)} chunks")
        
        if results:
            print(f"     Top similarity: {results[0]['similarity_score']:.3f}")
        else:
            print(f"  ⚠️  No results (database might be empty)")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Retrieval test failed: {e}")
        return False


def check_api():
    """Test API server"""
    print_section("6. FastAPI Server")
    
    try:
        import requests
        import subprocess
        import time
        
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ API Server: Running")
                print(f"     Status: {data.get('status')}")
                print(f"     Version: {data.get('version')}")
                return True
            else:
                print(f"  ⚠️  API Server: Not responding correctly")
                return False
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️  API Server: Not running")
            print(f"     Start with: uvicorn app.main:app --reload")
            return False
            
    except Exception as e:
        print(f"  ❌ API check failed: {e}")
        return False


def main():
    """Run all checks"""
    print("\n" + "=" * 60)
    print("  LMI Agent - System Verification")
    print("=" * 60)
    
    checks = [
        ("Environment", check_env_vars),
        ("Database", check_database),
        ("Embeddings", check_embeddings),
        ("LLM", check_llm),
        ("Retrieval", check_retrieval),
        ("API", check_api)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"  ❌ {name} check crashed: {e}")
            results[name] = False
    
    # Summary
    print_section("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"  {symbol} {name}")
    
    print(f"\n  Score: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n  🎉 All checks passed! System ready to use.")
        print("\n  Next steps:")
        print("    1. Start backend: uvicorn app.main:app --reload")
        print("    2. Start frontend: cd frontend && npm run dev")
        print("    3. Visit: http://localhost:3000")
    else:
        print("\n  ⚠️  Some checks failed. Fix issues above before proceeding.")
        print("\n  Quick fixes:")
        print("    • Missing keys: Update backend/.env file")
        print("    • Database: Run python scripts/setup_db.py setup")
        print("    • No data: Run python scripts/ingest_data.py api")
    
    print("\n" + "=" * 60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)