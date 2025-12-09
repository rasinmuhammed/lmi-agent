"""
Production-grade job fetching from multiple reliable APIs
"""
import requests
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)


class BaseJobFetcher:
    """Base class for job fetchers"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LMI-Agent/1.0 (Career Research Tool)',
            'Accept': 'application/json',
        })

    def _generate_job_id(self, title: str, company: str, source: str) -> str:
        """Generate unique job ID"""
        composite = f"{title}_{company}_{source}".lower().strip()
        return hashlib.md5(composite.encode()).hexdigest()

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        # Remove HTML tags
        text = BeautifulSoup(text, 'html.parser').get_text()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_skills(self, text: str) -> List[str]:
        """
        Enhanced skill extraction
        """
        if not text:
            return []
            
        text_lower = text.lower()
        
        # Extended skill database (adds Indian market + more global skills)
        skills_database = {
            # Programming Languages (existing + more)
            'Python': r'\bpython\b',
            'Java': r'\bjava\b(?!script)',
            'JavaScript': r'\bjavascript\b|\bjs\b',
            'TypeScript': r'\btypescript\b',
            'C++': r'\bc\+\+\b',
            'C#': r'\bc#\b',
            'Go': r'\bgolang\b|\bgo\b',
            'Rust': r'\brust\b',
            'Ruby': r'\bruby\b',
            'PHP': r'\bphp\b',
            'Swift': r'\bswift\b',
            'Kotlin': r'\bkotlin\b',
            'Scala': r'\bscala\b',
            'R': r'\br\b',
            'SQL': r'\bsql\b',
            
            # ML/AI (expanded)
            'Machine Learning': r'\bmachine\s+learning\b|\bml\b',
            'Deep Learning': r'\bdeep\s+learning\b',
            'TensorFlow': r'\btensorflow\b',
            'PyTorch': r'\bpytorch\b',
            'Keras': r'\bkeras\b',
            'Scikit-learn': r'\bscikit-learn\b|\bsklearn\b',
            'Pandas': r'\bpandas\b',
            'NumPy': r'\bnumpy\b',
            'NLP': r'\bnlp\b|\bnatural\s+language\b',
            'Computer Vision': r'\bcomputer\s+vision\b|\bcv\b',
            'LLM': r'\bllm\b|\blarge\s+language\s+model',
            'GenAI': r'\bgen\s*ai\b|\bgenerative\s+ai\b',
            'RAG': r'\brag\b|\bretrieval.{0,20}generation\b',
            'Transformers': r'\btransformers\b',
            'Hugging Face': r'\bhugging\s*face\b',
            'LangChain': r'\blangchain\b',
            'OpenAI': r'\bopenai\b',
            
            # Web Frameworks
            'React': r'\breact\b',
            'React Native': r'\breact\s+native\b',
            'Angular': r'\bangular\b',
            'Vue.js': r'\bvue\.?js\b|\bvue\b',
            'Next.js': r'\bnext\.?js\b',
            'Node.js': r'\bnode\.?js\b',
            'Express': r'\bexpress\b',
            'Django': r'\bdjango\b',
            'Flask': r'\bflask\b',
            'FastAPI': r'\bfastapi\b',
            'Spring Boot': r'\bspring\s+boot\b',
            'Spring': r'\bspring\b',
            'NET': r'\b\.net\b|\bdotnet\b',
            'ASP.NET': r'\basp\.net\b',
            
            # Mobile
            'Android': r'\bandroid\b',
            'iOS': r'\bios\b',
            'Flutter': r'\bflutter\b',
            'Swift': r'\bswift\b',
            'Kotlin': r'\bkotlin\b',
            
            # Cloud & DevOps
            'AWS': r'\baws\b|\bamazon\s+web\s+services\b',
            'Azure': r'\bazure\b',
            'GCP': r'\bgcp\b|\bgoogle\s+cloud\b',
            'Docker': r'\bdocker\b',
            'Kubernetes': r'\bkubernetes\b|\bk8s\b',
            'Jenkins': r'\bjenkins\b',
            'GitLab CI': r'\bgitlab\s+ci\b',
            'GitHub Actions': r'\bgithub\s+actions\b',
            'Terraform': r'\bterraform\b',
            'Ansible': r'\bansible\b',
            'CI/CD': r'\bci/cd\b',
            
            # Databases
            'PostgreSQL': r'\bpostgresql\b|\bpostgres\b',
            'MySQL': r'\bmysql\b',
            'MongoDB': r'\bmongodb\b|\bmongo\b',
            'Redis': r'\bredis\b',
            'Elasticsearch': r'\belasticsearch\b',
            'Cassandra': r'\bcassandra\b',
            'DynamoDB': r'\bdynamodb\b',
            'Oracle': r'\boracle\b',
            'SQL Server': r'\bsql\s+server\b',
            
            # Big Data
            'Spark': r'\bspark\b|\bpyspark\b',
            'Hadoop': r'\bhadoop\b',
            'Airflow': r'\bairflow\b',
            'Kafka': r'\bkafka\b',
            'Tableau': r'\btableau\b',
            'Power BI': r'\bpower\s+bi\b',
            'Snowflake': r'\bsnowflake\b',
            
            # Tools
            'Git': r'\bgit\b',
            'GitHub': r'\bgithub\b',
            'GitLab': r'\bgitlab\b',
            'Jira': r'\bjira\b',
            'REST API': r'\brest\s+api\b|\brestful\b',
            'GraphQL': r'\bgraphql\b',
            'Microservices': r'\bmicroservices\b',
            
            # Soft Skills (important for Indian market)
            'Communication': r'\bcommunication\b',
            'Leadership': r'\bleadership\b',
            'Agile': r'\bagile\b',
            'Scrum': r'\bscrum\b',
        }
        
        found_skills = []
        for skill_name, pattern in skills_database.items():
            if re.search(pattern, text_lower):
                found_skills.append(skill_name)
        
        return list(set(found_skills))


    def fetch_jobs(self, search_term: str, location: str = None) -> List[Dict]:
        """Abstract method"""
        raise NotImplementedError
    
    def _infer_experience_level(self, title: str) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director']):
            return 'Senior'
        elif any(w in title_lower for w in ['junior', 'jr.', 'entry', 'graduate', 'intern']):
            return 'Entry'
        return 'Mid'

    def _infer_remote_option(self, description: str) -> str:
        desc_lower = description.lower()
        if 'remote' in desc_lower or 'work from home' in desc_lower:
            return 'Hybrid' if 'hybrid' in desc_lower else 'Remote'
        return 'On-site'


class RemoteOKFetcher(BaseJobFetcher):
    """Fetch jobs from RemoteOK API"""

    API_URL = "https://remoteok.com/api"

    def fetch_jobs(self, search_term: str, location: str = None) -> List[Dict]:
        try:
            logger.info(f"Fetching RemoteOK listings for: {search_term}")
            response = self.session.get(self.API_URL, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data[1:]:  # first element is metadata
                title = job.get("position", "")
                company = job.get("company", "")
                description = self._clean_text(job.get("description", ""))
                full_text = f"{title} {description}"

                # Safe datetime parsing
                try:
                    posted_date = datetime.fromtimestamp(job.get("epoch", time.time()))
                except Exception:
                    posted_date = datetime.utcnow()

                standardized_job = {
                    "job_id": self._generate_job_id(title, company, "remoteok"),
                    "title": title,
                    "company": company,
                    "location": job.get("location", "Remote"),
                    "description": description,
                    "requirements": "",
                    "skills": self._extract_skills(full_text),
                    "salary_range": job.get("salary", None),
                    "source_url": job.get("url", ""),
                    "source_platform": "RemoteOK",
                    "posted_date": posted_date,
                    "scraped_date": datetime.utcnow(),
                    "job_type": job.get("type", "Full-time"),
                    "experience_level": self._infer_experience_level(title),
                    "remote_option": self._infer_remote_option(description),
                }

                jobs.append(standardized_job)

            logger.info(f"Fetched {len(jobs)} jobs from RemoteOK.")
            return jobs

        except Exception as e:
            logger.error(f"Error fetching RemoteOK jobs: {e}")
            return []


# -------------------------------------------------------------
# USAJobs Fetcher (Official API)
# -------------------------------------------------------------
class USAJobsFetcher(BaseJobFetcher):
    """Fetch jobs from USAJobs API"""

    BASE_URL = "https://data.usajobs.gov/api/Search"

    def __init__(self, email: str, api_key: str):
        super().__init__()
        self.session.headers.update({
            "Host": "data.usajobs.gov",
            "User-Agent": email,
            "Authorization-Key": api_key
        })

    def fetch_jobs(self, search_term: str, location: str = None) -> List[Dict]:
        try:
            logger.info(f"Fetching USAJobs listings for: {search_term}")

            params = {
                "Keyword": search_term,
                "ResultsPerPage": 50,
            }
            if location:
                params["LocationName"] = location

            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            results = data.get("SearchResult", {}).get("SearchResultItems", [])
            standardized_jobs = []

            for item in results:
                job = item.get("MatchedObjectDescriptor", {})
                title = job.get("PositionTitle", "")
                org = job.get("OrganizationName", "")
                description = self._clean_text(
                    job.get("UserArea", {}).get("Details", {}).get("JobSummary", "")
                )

                full_text = f"{title} {description}"
                salary = job.get("PositionRemuneration", [{}])[0]
                salary_range = None
                if salary.get("MinimumRange") and salary.get("MaximumRange"):
                    salary_range = f"${salary['MinimumRange']} - ${salary['MaximumRange']} {salary.get('RateIntervalCode', '')}"

                # Safe date parsing
                pub_date = job.get("PublicationStartDate")
                try:
                    posted_date = (
                        datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                        if pub_date else datetime.utcnow()
                    )
                except Exception:
                    posted_date = datetime.utcnow()

                standardized_job = {
                    "job_id": self._generate_job_id(title, org, "usajobs"),
                    "title": title,
                    "company": org,
                    "location": job.get("PositionLocationDisplay", ""),
                    "description": description,
                    "requirements": "",
                    "skills": self._extract_skills(full_text),
                    "salary_range": salary_range,
                    "source_url": job.get("PositionURI", ""),
                    "source_platform": "USAJobs",
                    "posted_date": posted_date,
                    "scraped_date": datetime.utcnow(),
                    "job_type": job.get("PositionSchedule", [{}])[0].get("Name", "Full-time"),
                    "experience_level": self._infer_experience_level(title),
                    "remote_option": self._infer_remote_option(description),
                }

                standardized_jobs.append(standardized_job)

            logger.info(f"Fetched {len(standardized_jobs)} jobs from USAJobs.")
            return standardized_jobs

        except Exception as e:
            logger.error(f"Error fetching USAJobs listings: {e}")
            return []



class AdzunaFetcher(BaseJobFetcher):
    """Fetch jobs from Adzuna API"""

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self, app_id: str, app_key: str):
        super().__init__()
        self.app_id = app_id
        self.app_key = app_key

    def fetch_jobs(self, search_term: str, location: str = "us") -> List[Dict]:
        try:
            logger.info(f"Fetching jobs from Adzuna for: {search_term} in {location}")

            url = f"{self.BASE_URL}/{location}/search/1"
            params = {
                'app_id': self.app_id,
                'app_key': self.app_key,
                'what': search_term,
                'results_per_page': 50,
                'sort_by': 'date',
            }

            time.sleep(1)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            jobs_data = data.get('results', [])
            standardized_jobs = []

            for job in jobs_data:
                description = job.get('description', '')
                title = job.get('title', '')
                full_text = f"{title} {description}"

                salary_min, salary_max = job.get('salary_min'), job.get('salary_max')
                salary_range = f"${int(salary_min):,} - ${int(salary_max):,}" if salary_min and salary_max else None

                standardized_job = {
                    'job_id': self._generate_job_id(title, job.get('company', {}).get('display_name', ''), 'adzuna'),
                    'title': title,
                    'company': job.get('company', {}).get('display_name', 'Unknown'),
                    'location': job.get('location', {}).get('display_name', ''),
                    'description': self._clean_text(description),
                    'requirements': '',
                    'skills': self._extract_skills(full_text),
                    'salary_range': salary_range,
                    'source_url': job.get('redirect_url', ''),
                    'source_platform': 'Adzuna',
                    'posted_date': datetime.fromisoformat(job.get('created', '').replace('Z', '+00:00')) if job.get('created') else datetime.utcnow(),
                    'scraped_date': datetime.utcnow(),
                    'job_type': job.get('contract_type', 'Full-time'),
                    'experience_level': self._infer_experience_level(title),
                    'remote_option': self._infer_remote_option(description),
                }

                standardized_jobs.append(standardized_job)

            logger.info(f"Found {len(standardized_jobs)} jobs from Adzuna")
            return standardized_jobs

        except Exception as e:
            logger.error(f"Error fetching from Adzuna: {e}")
            return []

    def _infer_experience_level(self, title: str) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ['senior', 'sr.', 'lead', 'principal', 'staff', 'director']):
            return 'Senior'
        elif any(w in title_lower for w in ['junior', 'jr.', 'entry', 'graduate', 'intern']):
            return 'Entry'
        return 'Mid'

    def _infer_remote_option(self, description: str) -> str:
        desc_lower = description.lower()
        if 'remote' in desc_lower or 'work from home' in desc_lower:
            return 'Hybrid' if 'hybrid' in desc_lower else 'Remote'
        return 'On-site'


class RemotiveJobsFetcher:
    """
    Remotive.io - Free API, good coverage of remote jobs
    Including many India-friendly positions
    """
    
    API_URL = "https://remotive.com/api/remote-jobs"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LMI-Agent/1.0',
            'Accept': 'application/json',
        })
    
    def _generate_job_id(self, title: str, company: str, source: str) -> str:
        composite = f"{title}_{company}_{source}".lower().strip()
        return hashlib.md5(composite.encode()).hexdigest()
    
    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = BeautifulSoup(text, 'html.parser').get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_skills(self, text: str) -> List[str]:
        """Enhanced skill extraction"""
        text_lower = text.lower()
        
        skills_patterns = {
            'Python': r'\bpython\b',
            'Java': r'\bjava\b(?!script)',
            'JavaScript': r'\bjavascript\b',
            'React': r'\breact\b',
            'Node.js': r'\bnode\.?js\b',
            'Django': r'\bdjango\b',
            'Flask': r'\bflask\b',
            'AWS': r'\baws\b',
            'Docker': r'\bdocker\b',
            'Kubernetes': r'\bkubernetes\b',
            'Machine Learning': r'\bmachine\s+learning\b',
            'Data Science': r'\bdata\s+science\b',
            'SQL': r'\bsql\b',
            'PostgreSQL': r'\bpostgresql\b',
            'MongoDB': r'\bmongodb\b',
            'Git': r'\bgit\b',
            'REST API': r'\brest\s+api\b',
        }
        
        found_skills = []
        for skill, pattern in skills_patterns.items():
            if re.search(pattern, text_lower):
                found_skills.append(skill)
        
        return list(set(found_skills))
    
    def fetch_jobs(self, search_term: str, location: str = None) -> List[Dict]:
        """Fetch remote jobs from Remotive"""
        try:
            logger.info(f"Fetching from Remotive: {search_term}")
            
            time.sleep(1)  # Rate limiting
            response = self.session.get(self.API_URL, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            jobs_data = data.get('jobs', [])
            
            # Filter for India-relevant and search term match
            indian_keywords = ['india', 'indian', 'ist', 'asia', 'bangalore', 'remote']
            
            standardized_jobs = []
            for job in jobs_data:
                title = job.get('title', '')
                company = job.get('company_name', '')
                description = self._clean_text(job.get('description', ''))
                
                # Check relevance
                job_text = f"{title} {company} {description}".lower()
                
                # Match search term
                if search_term.lower() not in job_text:
                    continue
                
                # Check India relevance
                is_indian_relevant = any(kw in job_text for kw in indian_keywords)
                
                full_text = f"{title} {description}"
                
                standardized_job = {
                    'job_id': self._generate_job_id(title, company, 'remotive'),
                    'title': title,
                    'company': company,
                    'location': 'Remote (India-friendly)' if is_indian_relevant else 'Remote',
                    'description': description[:500],  # Truncate long descriptions
                    'requirements': '',
                    'skills': self._extract_skills(full_text),
                    'salary_range': job.get('salary', None),
                    'source_url': job.get('url', ''),
                    'source_platform': 'Remotive',
                    'posted_date': datetime.fromisoformat(job.get('publication_date', '').replace('Z', '+00:00')) if job.get('publication_date') else datetime.utcnow(),
                    'scraped_date': datetime.utcnow(),
                    'job_type': job.get('job_type', 'Full-time'),
                    'experience_level': self._infer_experience_level(title),
                    'remote_option': 'Remote',
                }
                
                standardized_jobs.append(standardized_job)
            
            logger.info(f"Fetched {len(standardized_jobs)} jobs from Remotive")
            return standardized_jobs
            
        except Exception as e:
            logger.error(f"Error fetching from Remotive: {e}")
            return []
    
    def _infer_experience_level(self, title: str) -> str:
        title_lower = title.lower()
        if any(w in title_lower for w in ['senior', 'sr.', 'lead', 'principal']):
            return 'Senior'
        elif any(w in title_lower for w in ['junior', 'jr.', 'entry']):
            return 'Entry'
        return 'Mid'

class JobSpyFetcher(BaseJobFetcher):
    """
    JobSpy Fetcher - Scrapes LinkedIn, Indeed, Glassdoor using python-jobspy
    """
    
    def fetch_jobs(self, search_term: str, location: str = None) -> List[Dict]:
        try:
            from jobspy import scrape_jobs
            
            logger.info(f"🕵️ JobSpy scraping for: {search_term} in {location or 'India'}")
            
            # Use 'India' as default if no location
            search_location = location if location else "India"
            
            jobs = scrape_jobs(
                site_name=["indeed", "linkedin", "glassdoor", "google"],
                search_term=search_term,
                location=search_location,
                results_wanted=25,  # Fetch 25 jobs per site
                hours_old=72,       # Last 3 days
                country_indeed='India' if 'india' in search_location.lower() else 'USA'
            )
            
            logger.info(f"🕵️ JobSpy found {len(jobs)} raw jobs")
            
            standardized_jobs = []
            
            # Convert DataFrame/List to dictionary
            if hasattr(jobs, 'to_dict'):
                jobs_list = jobs.to_dict(orient='records')
            else:
                jobs_list = jobs
                
            for job in jobs_list:
                # JobSpy keys: title, company, location, description, job_url, site, date_posted
                title = job.get('title', '')
                company = job.get('company', '')
                site = job.get('site', 'JobSpy')
                
                # Verify we actually have a title/company
                if not title:
                    continue
                    
                description = self._clean_text(job.get('description', ''))
                if not description:
                    # Some sites don't return full description in list view
                    description = f"{title} at {company}. (Description not fully scraped)"
                
                full_text = f"{title} {description}"
                
                # Generate reliable ID
                short_id = self._generate_job_id(title, company, site)
                
                standardized_job = {
                    'job_id': short_id,
                    'title': title,
                    'company': company,
                    'location': job.get('location', search_location),
                    'description': description,
                    'requirements': '',
                    'skills': self._extract_skills(full_text),
                    'salary_range': job.get('salary_range') or job.get('min_amount') or None,
                    'source_url': job.get('job_url', ''),
                    'source_platform': f"{site.title()} (Live)",
                    'posted_date': datetime.utcnow(), # JobSpy dates can be messy strings
                    'scraped_date': datetime.utcnow(),
                    'job_type': job.get('job_type', 'Full-time'),
                    'experience_level': self._infer_experience_level(title),
                    'remote_option': self._infer_remote_option(description),
                }
                standardized_jobs.append(standardized_job)
                
            logger.info(f"✅ JobSpy standardized {len(standardized_jobs)} jobs")
            return standardized_jobs
            
        except ImportError:
            logger.error("❌ python-jobspy not installed")
            return []
        except Exception as e:
            logger.error(f"❌ JobSpy Error: {e}")
            return []

class JobFetcherManager:
    """
    UPDATED Manager - keeps all existing sources + adds new ones
    This REPLACES your existing JobFetcherManager
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        self.fetchers = []
        
        # 1. Add JobSpy (Primary/Best)
        self.fetchers.append(("JobSpy", JobSpyFetcher()))
        logger.info("✅ JobSpy fetcher enabled (LinkedIn, Indeed, Glassdoor)")
        
        # 2. KEEP: Remotive (Good for Remote)
        self.fetchers.append(("Remotive", RemotiveJobsFetcher()))
        logger.info("✅ Remotive enabled (FREE)")
        
        # 3. Adzuna (Backup)
        if config.get('adzuna_app_id') and config.get('adzuna_app_key'):
            from app.scraper.job_fetcher import AdzunaFetcher
            self.fetchers.append((
                'Adzuna',
                AdzunaFetcher(config['adzuna_app_id'], config['adzuna_app_key'])
            ))
            logger.info("✅ Adzuna fetcher enabled")

        logger.info(f"🚀 Total fetchers initialized: {len(self.fetchers)}")
    
    def fetch_all(
        self, 
        search_terms: List[str], 
        location: str = None,
        max_jobs_per_source: int = 50
    ) -> List[Dict]:
        """
        Fetch from ALL sources (existing + new)
        Automatically handles global vs India-specific searches
        """
        all_jobs = []
        seen_ids = set()
        
        for term in search_terms:
            logger.info(f"📋 Fetching jobs for: {term}")
            
            for source_name, fetcher in self.fetchers:
                try:
                    # Determine location based on source
                    if 'India' in source_name or source_name == 'JobSpy':
                        fetch_location = location if location else "India"
                    else:
                        fetch_location = location
                    
                    logger.info(f"  🔍 {source_name} - {fetch_location or 'global'}")
                    jobs = fetcher.fetch_jobs(term, fetch_location)
                    
                    added = 0
                    for job in jobs:
                        if job['job_id'] not in seen_ids:
                            seen_ids.add(job['job_id'])
                            all_jobs.append(job)
                            added += 1
                            
                            if added >= max_jobs_per_source:
                                break
                    
                    logger.info(f"    ✅ Added {added} jobs from {source_name}")
                    
                    # Rate limiting between sources
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"    ❌ Error from {source_name}: {e}")
                    continue
        
        logger.info(f"🎉 Total unique jobs fetched: {len(all_jobs)}")
        logger.info(f"📊 Breakdown by source:")
        
        # Show breakdown
        source_counts = {}
        for job in all_jobs:
            source = job.get('source_platform', 'Unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {source:20s}: {count:3d} jobs")
        
        return all_jobs
