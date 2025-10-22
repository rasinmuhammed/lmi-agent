"""
Vector similarity search and retrieval logic
"""
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_
from typing import List, Dict, Optional
from app.database import JobChunk, JobPosting
from app.rag.embeddings import get_embedding_generator
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Handles retrieval of relevant job information using vector similarity"""
    
    def __init__(self, db: Session):
        self.db = db
        self.embedding_gen = get_embedding_generator()
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Retrieve most relevant job chunks based on query
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional filters (location, job_type, etc.)
            
        Returns:
            List of retrieved chunks with metadata and similarity scores
        """
        if top_k is None:
            top_k = settings.retrieval_top_k
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_gen.generate_embedding(query)
            
            # Build the similarity search query
            similarity_query = self._build_similarity_query(
                query_embedding,
                top_k,
                filters
            )
            
            # Execute query
            results = self.db.execute(similarity_query).fetchall()
            
            # Format results
            retrieved_chunks = []
            for row in results:
                chunk_data = {
                    'chunk_id': row[0],
                    'text': row[1],
                    'similarity_score': float(row[2]),
                    'metadata': row[3],
                    'job_posting_id': row[4]
                }
                retrieved_chunks.append(chunk_data)
            
            logger.info(f"Retrieved {len(retrieved_chunks)} chunks for query: {query[:50]}...")
            return retrieved_chunks
            
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            raise
    
    def _build_similarity_query(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict]
    ):
        """
        Build pgvector similarity search query with optional filters
        
        Args:
            query_embedding: Query vector
            top_k: Number of results
            filters: Optional metadata filters
            
        Returns:
            SQLAlchemy query object
        """
        # Convert embedding to pgvector format
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Base query with cosine similarity
        base_query = f"""
        SELECT 
            jc.id,
            jc.chunk_text,
            1 - (jc.embedding <=> '{embedding_str}'::vector) as similarity,
            jc.metadata,
            jc.job_posting_id
        FROM job_chunks jc
        """
        
        # Add filters if provided
        where_clauses = []
        if filters:
            if filters.get('location'):
                where_clauses.append(
                    f"jc.metadata->>'location' ILIKE '%{filters['location']}%'"
                )
            if filters.get('min_date'):
                where_clauses.append(
                    f"(jc.metadata->>'posted_date')::timestamp >= '{filters['min_date']}'"
                )
        
        if where_clauses:
            base_query += " WHERE " + " AND ".join(where_clauses)
        
        # Add ordering and limit
        base_query += f"""
        ORDER BY jc.embedding <=> '{embedding_str}'::vector
        LIMIT {top_k}
        """
        
        return text(base_query)
    
    def get_job_context(self, chunk_ids: List[int]) -> List[Dict]:
        """
        Get full job posting context for retrieved chunks
        
        Args:
            chunk_ids: List of chunk IDs
            
        Returns:
            List of job posting data
        """
        try:
            # Get unique job posting IDs from chunks
            chunks = self.db.query(JobChunk).filter(
                JobChunk.id.in_(chunk_ids)
            ).all()
            
            job_ids = list(set([chunk.job_posting_id for chunk in chunks]))
            
            # Fetch full job postings
            jobs = self.db.query(JobPosting).filter(
                JobPosting.id.in_(job_ids)
            ).all()
            
            # Format job data
            job_context = []
            for job in jobs:
                job_data = {
                    'id': job.id,
                    'job_id': job.job_id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'requirements': job.requirements,
                    'skills': job.skills,
                    'salary_range': job.salary_range,
                    'source_url': job.source_url,
                    'posted_date': job.posted_date.isoformat() if job.posted_date else None,
                    'experience_level': job.experience_level,
                    'remote_option': job.remote_option
                }
                job_context.append(job_data)
            
            return job_context
            
        except Exception as e:
            logger.error(f"Error fetching job context: {e}")
            return []
    
    def hybrid_search(
        self,
        query: str,
        keywords: List[str],
        top_k: int = None
    ) -> List[Dict]:
        """
        Combine vector similarity with keyword matching
        
        Args:
            query: Semantic search query
            keywords: Keywords for exact matching
            top_k: Number of results
            
        Returns:
            Combined search results
        """
        # Get semantic results
        semantic_results = self.retrieve(query, top_k * 2)
        
        # Boost results containing keywords
        for result in semantic_results:
            keyword_boost = 0
            text_lower = result['text'].lower()
            
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    keyword_boost += 0.1
            
            # Apply boost
            result['similarity_score'] = min(
                result['similarity_score'] + keyword_boost,
                1.0
            )
        
        # Re-sort and limit
        semantic_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return semantic_results[:top_k or settings.retrieval_top_k]