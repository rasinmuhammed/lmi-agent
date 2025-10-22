"""
Database initialization script
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, SessionLocal, engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_database():
    """Initialize database with pgvector extension and tables"""
    try:
        logger.info("Starting database setup...")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info(f"Connected to PostgreSQL: {version}")
            
            # Enable pgvector extension
            logger.info("Enabling pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("pgvector extension enabled successfully")
        
        # Create tables
        logger.info("Creating database tables...")
        init_db()
        logger.info("Database tables created successfully")
        
        # Verify tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]
            logger.info(f"Created tables: {', '.join(tables)}")
        
        # Create indexes for better performance
        logger.info("Creating additional indexes...")
        with engine.connect() as conn:
            # Index for faster job searches
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_postings_title_gin 
                ON job_postings USING gin(to_tsvector('english', title))
            """))
            
            # Index for location searches
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_postings_location_gin 
                ON job_postings USING gin(to_tsvector('english', location))
            """))
            
            # Index for vector similarity searches (HNSW for better performance)
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_job_chunks_embedding_hnsw
                ON job_chunks USING hnsw (embedding vector_cosine_ops)
            """))
            
            conn.commit()
            logger.info("Indexes created successfully")
        
        logger.info("✅ Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error setting up database: {e}")
        return False


def reset_database():
    """Drop all tables and recreate (WARNING: deletes all data)"""
    try:
        response = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Operation cancelled")
            return False
        
        logger.info("Dropping all tables...")
        from app.database import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("Tables dropped")
        
        # Recreate
        setup_database()
        return True
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return False


def check_database_health():
    """Check database connection and table status"""
    try:
        logger.info("Checking database health...")
        
        with engine.connect() as conn:
            # Check connection
            conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection: OK")
            
            # Check pgvector
            result = conn.execute(text("""
                SELECT * FROM pg_extension WHERE extname = 'vector'
            """))
            if result.fetchone():
                logger.info("✅ pgvector extension: OK")
            else:
                logger.warning("⚠️  pgvector extension: NOT INSTALLED")
            
            # Check tables
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
            logger.info(f"✅ Tables found: {table_count}")
            
            # Check data
            from app.database import JobPosting, JobChunk
            db = SessionLocal()
            job_count = db.query(JobPosting).count()
            chunk_count = db.query(JobChunk).count()
            logger.info(f"✅ Job postings: {job_count}")
            logger.info(f"✅ Indexed chunks: {chunk_count}")
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database setup utility")
    parser.add_argument(
        'command',
        choices=['setup', 'reset', 'check'],
        help='Command to execute'
    )
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        success = setup_database()
        sys.exit(0 if success else 1)
    
    elif args.command == 'reset':
        success = reset_database()
        sys.exit(0 if success else 1)
    
    elif args.command == 'check':
        success = check_database_health()
        sys.exit(0 if success else 1)