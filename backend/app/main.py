"""
FastAPI main application
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import Optional
from app.config import settings
from app.database import get_db
from app.rag.pipeline import LMIRAGPipeline
from pydantic import BaseModel, Field
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Labor Market Intelligence Agent - AI-powered skill gap analysis"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class SkillAnalysisRequest(BaseModel):
    query: str = Field(..., description="Search query for job analysis")
    job_role: Optional[str] = Field(None, description="Specific job role to analyze")
    location: Optional[str] = Field(None, description="Geographic location filter")
    use_cache: bool = Field(True, description="Use cached results if available")


class CompareRolesRequest(BaseModel):
    role_a: str = Field(..., description="First job role")
    role_b: str = Field(..., description="Second job role")
    location: Optional[str] = Field(None, description="Location filter")


class HealthResponse(BaseModel):
    status: str
    version: str
    service: str


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "service": "LMI Agent API"
    }


# Main analysis endpoint
@app.post("/api/v1/analyze")
async def analyze_skills(
    request: SkillAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze skill requirements and market trends
    
    Performs comprehensive skill gap analysis based on real job posting data.
    """
    try:
        logger.info(f"Received analysis request: {request.query}")
        
        pipeline = LMIRAGPipeline(db)
        result = pipeline.analyze_skills(
            query=request.query,
            job_role=request.job_role,
            location=request.location,
            use_cache=request.use_cache
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error processing analysis request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process analysis: {str(e)}"
        )


# Role comparison endpoint
@app.post("/api/v1/compare")
async def compare_roles(
    request: CompareRolesRequest,
    db: Session = Depends(get_db)
):
    """
    Compare skill requirements between two job roles
    
    Provides side-by-side analysis of different career paths.
    """
    try:
        logger.info(f"Comparing roles: {request.role_a} vs {request.role_b}")
        
        pipeline = LMIRAGPipeline(db)
        result = pipeline.compare_roles(
            role_a=request.role_a,
            role_b=request.role_b,
            location=request.location
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error comparing roles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare roles: {str(e)}"
        )


# Trending skills endpoint
@app.get("/api/v1/trending")
async def get_trending_skills(
    category: str = Query("all", description="Skill category"),
    days: int = Query(30, description="Time period in days"),
    db: Session = Depends(get_db)
):
    """
    Get trending skills across all job postings
    
    Identifies emerging and in-demand skills based on recent job market data.
    """
    try:
        logger.info(f"Fetching trending skills for last {days} days")
        
        pipeline = LMIRAGPipeline(db)
        result = pipeline.get_trending_skills(
            category=category,
            time_period_days=days
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error fetching trending skills: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch trending skills: {str(e)}"
        )


# Statistics endpoint
@app.get("/api/v1/stats")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get system statistics
    
    Returns overall statistics about the indexed job data.
    """
    try:
        from app.database import JobPosting, JobChunk, SkillAnalysis
        from sqlalchemy import func
        
        total_jobs = db.query(func.count(JobPosting.id)).scalar()
        total_chunks = db.query(func.count(JobChunk.id)).scalar()
        total_analyses = db.query(func.count(SkillAnalysis.id)).scalar()
        
        # Get date range
        oldest_job = db.query(func.min(JobPosting.scraped_date)).scalar()
        newest_job = db.query(func.max(JobPosting.scraped_date)).scalar()
        
        # Top companies
        top_companies = db.query(
            JobPosting.company,
            func.count(JobPosting.id).label('count')
        ).group_by(JobPosting.company).order_by(
            func.count(JobPosting.id).desc()
        ).limit(10).all()
        
        return {
            "success": True,
            "data": {
                "total_job_postings": total_jobs,
                "total_indexed_chunks": total_chunks,
                "total_analyses_performed": total_analyses,
                "data_range": {
                    "oldest": oldest_job.isoformat() if oldest_job else None,
                    "newest": newest_job.isoformat() if newest_job else None
                },
                "top_companies": [
                    {"company": company, "job_count": count}
                    for company, count in top_companies
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch statistics: {str(e)}"
        )


# Search jobs endpoint
@app.get("/api/v1/jobs/search")
async def search_jobs(
    query: str = Query(..., description="Search query"),
    location: Optional[str] = Query(None, description="Location filter"),
    limit: int = Query(10, le=50, description="Number of results"),
    db: Session = Depends(get_db)
):
    """
    Search job postings directly
    
    Returns raw job posting data matching the search criteria.
    """
    try:
        from app.database import JobPosting
        
        base_query = db.query(JobPosting)
        
        # Apply filters
        if location:
            base_query = base_query.filter(
                JobPosting.location.ilike(f"%{location}%")
            )
        
        # Simple text search on title and description
        search_filter = (
            JobPosting.title.ilike(f"%{query}%") |
            JobPosting.description.ilike(f"%{query}%")
        )
        base_query = base_query.filter(search_filter)
        
        # Get results
        jobs = base_query.order_by(
            JobPosting.scraped_date.desc()
        ).limit(limit).all()
        
        results = [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "description": job.description[:500] + "..." if len(job.description) > 500 else job.description,
                "skills": job.skills,
                "source_url": job.source_url,
                "posted_date": job.posted_date.isoformat() if job.posted_date else None
            }
            for job in jobs
        ]
        
        return {
            "success": True,
            "data": {
                "jobs": results,
                "total": len(results),
                "query": query
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search jobs: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)