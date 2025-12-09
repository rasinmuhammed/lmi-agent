"""
Complete RAG pipeline orchestration
"""
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from app.rag.retriever import RAGRetriever
from app.rag.generator import SkillAnalysisGenerator
from app.database import SkillAnalysis
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class LMIRAGPipeline:
    """Orchestrates the complete RAG pipeline for Labor Market Intelligence"""
    
    def __init__(self, db: Session):
        self.db = db
        self.retriever = RAGRetriever(db)
        self.generator = SkillAnalysisGenerator()
    
    def analyze_skills(
        self,
        query: str,
        job_role: Optional[str] = None,
        location: Optional[str] = None,
        use_cache: bool = True,
        cache_max_age_hours: int = 24,
        live_fetch: bool = False  # ✅ New parameter
    ) -> Dict:
        """
        Complete skill analysis pipeline
        """
        try:
            # Step 0: Live Fetch (if enabled)
            if live_fetch:
                logger.info(f"🌐 Live fetch enabled for query: {query}")
                from app.services.ingestion import JobIngestionService
                ingestion_service = JobIngestionService(self.db)
                stats = ingestion_service.fetch_and_ingest(
                    search_terms=[query],
                    location=location,
                    max_jobs=10  # Limit for speed
                )
                logger.info(f"Live fetch stats: {stats}")
                # Disable cache for this run since we just got new data
                use_cache = False

            # Check cache if enabled
            if use_cache:
                cached_result = self._get_cached_analysis(
                    query,
                    job_role,
                    location,
                    cache_max_age_hours
                )
                if cached_result:
                    logger.info(f"Returning cached analysis for query: {query}")
                    return cached_result
            
            # Step 1: Retrieve relevant job data
            logger.info(f"Starting analysis for query: {query}")
            filters = {}
            if location:
                filters['location'] = location
            
            retrieved_chunks = self.retriever.retrieve(
                query=query,
                top_k=10,
                filters=filters if filters else None
            )
            
            if not retrieved_chunks:
                logger.warning(f"No results found for query: {query}")
                return {
                    'error': 'No relevant job postings found',
                    'query': query,
                    'suggestions': [
                        'Try broader search terms',
                        'Check spelling',
                        'Try different job titles'
                    ]
                }
            
            # Step 2: Get full job context
            chunk_ids = [chunk['chunk_id'] for chunk in retrieved_chunks]
            job_context = self.retriever.get_job_context(chunk_ids)
            
            # Step 3: Generate analysis using LLM
            analysis = self.generator.generate_skill_analysis(
                query=query,
                retrieved_context=retrieved_chunks,
                job_role=job_role
            )
            
            # ✅ Normalize response structure
            if 'skill_frequencies' not in analysis:
                freqs = {}
                for s in analysis.get('top_skills', []):
                    # Try to parse frequency
                    val = s.get('frequency', 0)
                    if isinstance(val, str):
                        try:
                            # Extract number from string like "85%"
                            import re
                            nums = re.findall(r"[\d\.]+", val)
                            val = float(nums[0]) if nums else 0
                        except:
                            val = 0
                    freqs[s.get('skill', 'Unknown')] = val
                    
                    # ✅ Inject 'score' for frontend compatibility (Radar Chart)
                    s['score'] = val / 100.0 if val > 1 else val # Normalize to 0-1 range for consistency, or keep as is? 
                    # Frontend renders s.score * 100. So we need score to be 0-1 if frequency is 0-100?
                    # "frequency" from LLM is usually "85%" or "0.85". 
                    # If val is 85, score should be 0.85.
                    if val > 1:
                        s['score'] = val / 100.0
                    else:
                        s['score'] = val

                analysis['skill_frequencies'] = freqs

            # ✅ Normalize emerging_skills (Generator returns 'emerging_trends')
            if 'emerging_trends' in analysis and 'emerging_skills' not in analysis:
                analysis['emerging_skills'] = analysis['emerging_trends']

            # Step 4: Enrich with job context
            analysis['job_postings_sample'] = job_context[:5]
            analysis['query'] = query
            analysis['generated_at'] = datetime.utcnow().isoformat()
            
            # Step 5: Cache the result
            self._cache_analysis(query, job_role, location, analysis, retrieved_chunks)
            
            logger.info(f"Analysis completed successfully for query: {query}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in analysis pipeline: {e}")
            raise
    
    def compare_roles(
        self,
        role_a: str,
        role_b: str,
        location: Optional[str] = None
    ) -> Dict:
        """
        Compare two different job roles
        
        Args:
            role_a: First job role
            role_b: Second job role
            location: Optional location filter
            
        Returns:
            Comparative analysis
        """
        try:
            filters = {'location': location} if location else None
            
            # Retrieve data for both roles
            context_a = self.retriever.retrieve(
                query=role_a,
                top_k=10,
                filters=filters
            )
            
            context_b = self.retriever.retrieve(
                query=role_b,
                top_k=10,
                filters=filters
            )
            
            # Generate comparison
            comparison = self.generator.generate_comparison_report(
                role_a=role_a,
                role_b=role_b,
                context_a=context_a,
                context_b=context_b
            )
            
            comparison['generated_at'] = datetime.utcnow().isoformat()
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing roles: {e}")
            raise
    
    def get_trending_skills(
        self,
        category: str = "all",
        time_period_days: int = 30
    ) -> Dict:
        """
        Analyze trending skills across all job postings
        
        Args:
            category: Skill category filter
            time_period_days: Time period to analyze
            
        Returns:
            Trending skills report
        """
        try:
            # Query recent skill analyses
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            
            recent_analyses = self.db.query(SkillAnalysis).filter(
                SkillAnalysis.analysis_date >= cutoff_date
            ).all()
            
            # Aggregate skill frequencies
            skill_counts = {}
            total_jobs = 0
            
            for analysis in recent_analyses:
                if analysis.top_skills:
                    for skill_data in analysis.top_skills:
                        skill = skill_data.get('skill')
                        if skill:
                            skill_counts[skill] = skill_counts.get(skill, 0) + 1
                total_jobs += analysis.total_jobs_analyzed or 0
            
            # Sort by frequency
            trending_skills = sorted(
                skill_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]
            
            return {
                'trending_skills': [
                    {
                        'skill': skill,
                        'mention_count': count,
                        'trend_score': count / len(recent_analyses) if recent_analyses else 0
                    }
                    for skill, count in trending_skills
                ],
                'time_period_days': time_period_days,
                'total_analyses': len(recent_analyses),
                'total_jobs_analyzed': total_jobs,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting trending skills: {e}")
            raise
    
    def _get_cached_analysis(
        self,
        query: str,
        job_role: Optional[str],
        location: Optional[str],
        max_age_hours: int
    ) -> Optional[Dict]:
        """
        Retrieve cached analysis if available and fresh
        
        Args:
            query: Search query
            job_role: Job role filter
            location: Location filter
            max_age_hours: Maximum cache age
            
        Returns:
            Cached analysis or None
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            cached = self.db.query(SkillAnalysis).filter(
                SkillAnalysis.query == query,
                SkillAnalysis.job_role == job_role,
                SkillAnalysis.location == location,
                SkillAnalysis.analysis_date >= cutoff_time
            ).order_by(SkillAnalysis.analysis_date.desc()).first()
            
            if cached:
                return {
                    'summary': 'Cached result',
                    'top_skills': cached.top_skills,
                    'skill_frequencies': cached.skill_frequencies,
                    'skill_necessity_scores': cached.skill_necessity_scores,
                    'emerging_skills': cached.emerging_skills,
                    'total_jobs_analyzed': cached.total_jobs_analyzed,
                    'query': cached.query,
                    'generated_at': cached.analysis_date.isoformat(),
                    'from_cache': True
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Error retrieving cached analysis: {e}")
            return None
    
    def _cache_analysis(
        self,
        query: str,
        job_role: Optional[str],
        location: Optional[str],
        analysis: Dict,
        retrieved_chunks: List[Dict]
    ):
        """
        Cache analysis results
        
        Args:
            query: Search query
            job_role: Job role
            location: Location
            analysis: Analysis results
            retrieved_chunks: Retrieved context
        """
        try:
            # Extract job IDs
            job_ids = list(set([
                chunk['job_posting_id'] for chunk in retrieved_chunks
            ]))
            
            # Create cache entry
            cache_entry = SkillAnalysis(
                query=query,
                job_role=job_role,
                location=location,
                top_skills=analysis.get('top_skills', []),
                skill_frequencies=analysis.get('skill_frequencies', {}), # ✅ Fixed key
                skill_necessity_scores=analysis.get('skill_necessity_scores', {}),
                emerging_skills=analysis.get('emerging_trends', []),
                total_jobs_analyzed=len(job_ids),
                source_job_ids=job_ids
            )
            
            self.db.add(cache_entry)
            self.db.commit()
            logger.info(f"Cached analysis for query: {query}")
            
        except Exception as e:
            logger.warning(f"Error caching analysis: {e}")
            self.db.rollback()