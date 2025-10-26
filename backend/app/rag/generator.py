"""
LLM generation using Groq API
"""
from groq import Groq
from typing import List, Dict, Optional
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class SkillAnalysisGenerator:
    """Generates skill analysis reports using Groq LLM"""
    
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model
    
    def generate_skill_analysis(
        self,
        query: str,
        retrieved_context: List[Dict],
        job_role: Optional[str] = None
    ) -> Dict:
        """Generate comprehensive skill analysis from retrieved job data"""
        try:
            context_text = self._prepare_context(retrieved_context)
            prompt = self._build_analysis_prompt(query, context_text, job_role)
            
            logger.info(f"Generating analysis for query: {query}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert career analyst specializing in labor market intelligence "
                            "and skill gap analysis. Provide data-driven insights based strictly on the provided job posting data."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.groq_temperature,
                max_tokens=settings.groq_max_tokens,
                response_format={"type": "json_object"}  # ✅ FIXED: must be an object
            )
            
            # Safely parse JSON response
            analysis = json.loads(response.choices[0].message.content)

            
            # Add citations and stats
            analysis["citations"] = self._extract_citations(retrieved_context)
            analysis["total_jobs_analyzed"] = len(
                {chunk["job_posting_id"] for chunk in retrieved_context if "job_posting_id" in chunk}
            )
            
            logger.info("✅ Successfully generated skill analysis")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error generating analysis: {e}", exc_info=True)
            raise
    
    def _prepare_context(self, retrieved_context: List[Dict]) -> str:
        """Prepare retrieved context for LLM prompt"""
        context_parts = []
        for idx, chunk in enumerate(retrieved_context, 1):
            metadata = chunk.get("metadata", {})
            context_parts.append(
                f"""
[Job Posting {idx}]
Title: {metadata.get('title', 'N/A')}
Company: {metadata.get('company', 'N/A')}
Location: {metadata.get('location', 'N/A')}
Content: {chunk.get('text', '')[:500]}...
Relevance Score: {chunk.get('similarity_score', 0):.2f}
---
                """.strip()
            )
        return "\n\n".join(context_parts)
    
    def _build_analysis_prompt(
        self,
        query: str,
        context: str,
        job_role: Optional[str]
    ) -> str:
        """Build the analysis prompt for LLM"""
        role_context = f" for {job_role} positions" if job_role else ""
        prompt = f"""
Based on the following job posting data{role_context}, provide a comprehensive skill gap analysis.

User Query: {query}

Job Posting Data:
{context}

Analyze this data and provide a JSON response with the following structure:
{{
    "summary": "Brief overview of the analysis findings",
    "top_skills": [
        {{
            "skill": "skill name",
            "frequency": "percentage or count",
            "necessity_level": "mandatory/highly_desired/nice_to_have",
            "explanation": "why this skill is important"
        }}
    ],
    "emerging_trends": ["trend 1", "trend 2"],
    "skill_categories": {{
        "technical_skills": ["skill1", "skill2"],
        "soft_skills": ["skill1", "skill2"],
        "tools_and_platforms": ["tool1", "tool2"],
        "certifications": ["cert1", "cert2"]
    }},
    "experience_requirements": {{
        "entry_level": "requirements description",
        "mid_level": "requirements description",
        "senior_level": "requirements description"
    }},
    "salary_insights": {{
        "range": "salary range if available",
        "factors": ["factor affecting salary"]
    }},
    "geographic_trends": {{
        "hot_locations": ["location1", "location2"],
        "remote_opportunities": "percentage or availability"
    }},
    "recommendations": [
        "actionable recommendation 1",
        "actionable recommendation 2"
    ]
}}

Requirements:
1. Base ALL findings strictly on the provided job posting data.
2. Quantify findings with percentages or frequencies when possible.
3. Identify patterns across multiple job postings.
4. Distinguish between mandatory vs. desired skills.
5. Provide actionable, specific recommendations.
6. Do NOT hallucinate or add information not present in the data.
"""
        return prompt
    
    def _extract_citations(self, retrieved_context: List[Dict]) -> List[Dict]:
        """Extract citation information from retrieved context"""
        citations = []
        seen_jobs = set()
        for chunk in retrieved_context:
            metadata = chunk.get("metadata", {})
            job_id = chunk.get("job_posting_id")
            if job_id and job_id not in seen_jobs:
                citations.append({
                    "job_id": job_id,
                    "title": metadata.get("title"),
                    "company": metadata.get("company"),
                    "source_url": metadata.get("source_url"),
                    "relevance_score": chunk.get("similarity_score"),
                })
                seen_jobs.add(job_id)
        return citations
    
    def generate_comparison_report(
        self,
        role_a: str,
        role_b: str,
        context_a: List[Dict],
        context_b: List[Dict]
    ) -> Dict:
        """Generate comparative analysis between two roles"""
        try:
            context_text_a = self._prepare_context(context_a)
            context_text_b = self._prepare_context(context_b)
            
            prompt = f"""
Compare the skill requirements and market characteristics between two roles:

ROLE A: {role_a}
{context_text_a}

ROLE B: {role_b}
{context_text_b}

Provide a JSON comparison report with:
{{
    "role_a_name": "{role_a}",
    "role_b_name": "{role_b}",
    "unique_to_role_a": ["skill1", "skill2"],
    "unique_to_role_b": ["skill1", "skill2"],
    "common_skills": ["skill1", "skill2"],
    "salary_comparison": "comparison text",
    "career_progression": "which role leads to which",
    "market_demand": "comparison of demand",
    "recommendations": "who should choose which role and why"
}}
"""
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a career comparison analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=settings.groq_temperature,
                max_tokens=settings.groq_max_tokens,
                response_format={"type": "json_object"}  # ✅ FIXED HERE TOO
            )
            
            content = response.choices[0].message["content"]
            comparison = json.loads(content)
            return comparison
            
        except Exception as e:
            logger.error(f"Error generating comparison: {e}", exc_info=True)
            raise
