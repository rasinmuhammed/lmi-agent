#!/usr/bin/env python3
"""
Interactive troubleshooting script for common issues
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def check_env_file():
    """Check if .env file exists"""
    print_header("1. Checking Environment Setup")
    
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        print("\n🔧 Quick Fix:")
        print("   cd backend")
        print("   cp .env.example .env")
        print("   # Then edit .env with your API keys")
        return False
    
    print(f"✅ .env file found at: {env_path}")
    
    # Check file size (should be more than just template)
    size = os.path.getsize(env_path)
    if size < 100:
        print("⚠️  .env file looks empty or incomplete")
        return False
    
    return True


def diagnose_embeddings():
    """Diagnose embedding issues"""
    print_header("2. Diagnosing Embeddings")
    
    key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not key:
        print("❌ HUGGINGFACE_API_KEY not found")
        print("\n🔧 Quick Fix:")
        print("   1. Get free token: https://huggingface.co/settings/tokens")
        print("   2. Add to backend/.env:")
        print("      HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx")
        print("   3. Restart backend server")
        return False
    
    if key.startswith("hf_your_") or key.startswith("your_"):
        print("❌ API key is still a placeholder")
        print("\n🔧 Quick Fix:")
        print("   Replace with real token from:")
        print("   https://huggingface.co/settings/tokens")
        return False
    
    if not key.startswith("hf_"):
        print("⚠️  API key format looks wrong")
        print("   Expected: hf_xxxxxxxxxxxx")
        print(f"   Got: {key[:10]}...")
    
    print(f"✅ API key configured: {key[:10]}...{key[-5:]}")
    
    # Test API call
    print("\nTesting API connection...")
    try:
        import requests
        url = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2"
        headers = {"Authorization": f"Bearer {key}"}
        payload = {"inputs": ["test"], "options": {"wait_for_model": True}}
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            print("✅ HuggingFace API working!")
            return True
        elif response.status_code == 401:
            print("❌ API key invalid (401)")
            print("\n🔧 Quick Fix:")
            print("   Get new token: https://huggingface.co/settings/tokens")
            return False
        elif response.status_code == 503:
            print("⏳ Model loading... (this is normal)")
            print("   Wait 10-30 seconds and try again")
            return True
        else:
            print(f"⚠️  API returned: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def diagnose_database():
    """Diagnose database issues"""
    print_header("3. Diagnosing Database")
    
    db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ DATABASE_URL not found")
        print("\n🔧 Quick Fix:")
        print("   1. Get free database: https://neon.tech")
        print("   2. Add to backend/.env:")
        print("      DATABASE_URL=postgresql://user:pass@host/db")
        return False
    
    if "your-neon" in db_url or "username" in db_url:
        print("❌ DATABASE_URL is still a placeholder")
        print("\n🔧 Quick Fix:")
        print("   Replace with real connection string from Neon")
        return False
    
    print(f"✅ DATABASE_URL configured")
    
    # Test connection
    print("\nTesting database connection...")
    try:
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from sqlalchemy import create_engine, text
        
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            
            # Check pgvector
            result = conn.execute(text(
                "SELECT * FROM pg_extension WHERE extname = 'vector'"
            ))
            if result.fetchone():
                print("✅ pgvector extension installed")
            else:
                print("❌ pgvector extension missing!")
                print("\n🔧 Quick Fix:")
                print("   1. Go to Neon SQL Editor")
                print("   2. Run: CREATE EXTENSION IF NOT EXISTS vector;")
                print("   3. Then run: python scripts/setup_db.py setup")
                return False
            
            # Check tables
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
            
            if table_count == 0:
                print("❌ No tables found!")
                print("\n🔧 Quick Fix:")
                print("   python scripts/setup_db.py setup")
                return False
            
            print(f"✅ Found {table_count} tables")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Common Fixes:")
        print("   • Check DATABASE_URL is correct")
        print("   • Verify Neon project is running")
        print("   • Check firewall/network settings")
        return False


def diagnose_groq():
    """Diagnose Groq API issues"""
    print_header("4. Diagnosing Groq LLM")
    
    key = os.getenv("GROQ_API_KEY")
    
    if not key:
        print("❌ GROQ_API_KEY not found")
        print("\n🔧 Quick Fix:")
        print("   1. Get free key: https://console.groq.com")
        print("   2. Add to backend/.env:")
        print("      GROQ_API_KEY=gsk_xxxxxxxxxxxxx")
        return False
    
    if key.startswith("gsk_your_") or key.startswith("your_"):
        print("❌ API key is still a placeholder")
        print("\n🔧 Quick Fix:")
        print("   Replace with real key from console.groq.com")
        return False
    
    print(f"✅ API key configured: {key[:10]}...{key[-5:]}")
    
    # Test API
    print("\nTesting Groq API...")
    try:
        from groq import Groq
        client = Groq(api_key=key)
        
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": "Say 'OK' if working"}],
            max_tokens=5
        )
        
        print("✅ Groq API working!")
        print(f"   Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Groq API test failed: {e}")
        
        if "rate_limit" in str(e).lower():
            print("\n🔧 Rate Limit Hit:")
            print("   Free tier: 30 requests/minute, 14,400/day")
            print("   Wait a minute and try again")
        elif "invalid" in str(e).lower():
            print("\n🔧 Invalid API Key:")
            print("   Get new key: https://console.groq.com")
        
        return False


def diagnose_data():
    """Check if database has data"""
    print_header("5. Checking Database Data")
    
    try:
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from app.database import SessionLocal, JobPosting, JobChunk
        from sqlalchemy import func
        
        db = SessionLocal()
        
        job_count = db.query(func.count(JobPosting.id)).scalar()
        chunk_count = db.query(func.count(JobChunk.id)).scalar()
        
        print(f"Jobs in database: {job_count}")
        print(f"Chunks in database: {chunk_count}")
        
        if job_count == 0:
            print("\n⚠️  No job data found!")
            print("\n🔧 Quick Fix:")
            print("   python scripts/ingest_data.py api \\")
            print("     --search-terms 'Machine Learning Engineer' \\")
            print("     --api-source remoteok")
            return False
        
        if chunk_count == 0:
            print("\n⚠️  Jobs exist but no chunks!")
            print("   This means embeddings weren't generated")
            print("\n🔧 Quick Fix:")
            print("   python scripts/ingest_data.py api \\")
            print("     --search-terms 'Data Scientist' \\")
            print("     --api-source remoteok")
            return False
        
        print(f"✅ Database has {job_count} jobs with {chunk_count} chunks")
        
        # Check recent jobs
        recent = db.query(JobPosting).order_by(
            JobPosting.scraped_date.desc()
        ).limit(3).all()
        
        print("\nRecent jobs:")
        for job in recent:
            print(f"  • {job.title} at {job.company}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Data check failed: {e}")
        return False


def diagnose_api_server():
    """Check if API server is running"""
    print_header("6. Checking API Server")
    
    try:
        import requests
        
        response = requests.get("http://localhost:8000/health", timeout=2)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API server is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            return True
        else:
            print(f"⚠️  API returned: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        print("\n🔧 Quick Fix:")
        print("   cd backend")
        print("   source venv/bin/activate")
        print("   uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ API check failed: {e}")
        return False


def suggest_next_steps(results):
    """Suggest next steps based on results"""
    print_header("Recommended Next Steps")
    
    failed_checks = [name for name, passed in results.items() if not passed]
    
    if not failed_checks:
        print("🎉 Everything looks good!")
        print("\nYou can now:")
        print("  1. Start using the app at http://localhost:3000")
        print("  2. Ingest more data for better results")
        print("  3. Deploy to production")
        return
    
    print("⚠️  Fix these issues in order:\n")
    
    priority_fixes = {
        "Environment": [
            "cd backend",
            "cp .env.example .env",
            "# Edit .env with your API keys"
        ],
        "Embeddings": [
            "# Get token: https://huggingface.co/settings/tokens",
            "# Add to .env: HUGGINGFACE_API_KEY=hf_xxx"
        ],
        "Database": [
            "# Get database: https://neon.tech",
            "# Add to .env: DATABASE_URL=postgresql://...",
            "# Then run:",
            "python scripts/setup_db.py setup"
        ],
        "Groq": [
            "# Get key: https://console.groq.com",
            "# Add to .env: GROQ_API_KEY=gsk_xxx"
        ],
        "Data": [
            "python scripts/ingest_data.py api \\",
            "  --search-terms 'ML Engineer' \\",
            "  --api-source remoteok"
        ],
        "API Server": [
            "cd backend",
            "source venv/bin/activate",
            "uvicorn app.main:app --reload"
        ]
    }
    
    for i, check_name in enumerate(failed_checks, 1):
        print(f"{i}. Fix {check_name}:")
        if check_name in priority_fixes:
            for cmd in priority_fixes[check_name]:
                print(f"   {cmd}")
        print()


def interactive_menu():
    """Interactive troubleshooting menu"""
    print_header("LMI Agent - Interactive Troubleshooter")
    
    print("Select what to troubleshoot:")
    print("  1. All checks (recommended)")
    print("  2. Environment setup only")
    print("  3. Embeddings only")
    print("  4. Database only")
    print("  5. Groq LLM only")
    print("  6. Data ingestion")
    print("  7. API server")
    print("  0. Exit")
    
    choice = input("\nEnter choice (1-7, 0 to exit): ").strip()
    
    if choice == "0":
        print("Goodbye!")
        return
    
    checks = {
        "1": [
            ("Environment", check_env_file),
            ("Embeddings", diagnose_embeddings),
            ("Database", diagnose_database),
            ("Groq", diagnose_groq),
            ("Data", diagnose_data),
            ("API Server", diagnose_api_server)
        ],
        "2": [("Environment", check_env_file)],
        "3": [("Embeddings", diagnose_embeddings)],
        "4": [("Database", diagnose_database)],
        "5": [("Groq", diagnose_groq)],
        "6": [("Data", diagnose_data)],
        "7": [("API Server", diagnose_api_server)]
    }
    
    if choice not in checks:
        print("Invalid choice!")
        return
    
    results = {}
    for name, check_func in checks[choice]:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ Check crashed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    suggest_next_steps(results)


def quick_test():
    """Quick automated test of all components"""
    print_header("Quick System Test")
    
    checks = [
        ("Environment", check_env_file),
        ("Embeddings", diagnose_embeddings),
        ("Database", diagnose_database),
        ("Groq", diagnose_groq),
        ("Data", diagnose_data),
        ("API Server", diagnose_api_server)
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n❌ {name} check crashed: {e}")
            results[name] = False
    
    # Summary
    print_header("Test Summary")
    
    for name, passed in results.items():
        symbol = "✅" if passed else "❌"
        print(f"{symbol} {name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"Result: {passed_count}/{total} checks passed")
    print(f"{'='*60}\n")
    
    suggest_next_steps(results)
    
    return passed_count == total


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = quick_test()
        sys.exit(0 if success else 1)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()