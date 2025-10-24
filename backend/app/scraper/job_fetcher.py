"""
Production-grade job fetching from multiple reliable APIs
"""
import requests
import time
import logging
from typing import List, Dict
from datetime import datetime
import hashlib
from bs4 import BeautifulSoup
import re

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
        """Extract technical skills from text"""
        text_lower = text.lower()

        skills_patterns = {
            # Programming Languages
            'Python': r'\bpython\b',
            'Java': r'\bjava\b(?!script)',
            'JavaScript': r'\bjavascript\b|\bjs\b',
            'TypeScript': r'\btypescript\b|\bts\b',
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

            # ML/AI Frameworks
            'TensorFlow': r'\btensorflow\b',
            'PyTorch': r'\bpytorch\b',
            'Keras': r'\bkeras\b',
            'Scikit-learn': r'\bscikit-learn\b|\bsklearn\b',
            'Hugging Face': r'\bhugging\s*face\b|\btransformers\b',
            'LangChain': r'\blangchain\b',
            'OpenAI': r'\bopenai\b',
            'RAG': r'\brag\b|\bretrieval.{0,20}generation\b',
            'LLM': r'\bllm\b|\blarge\s+language\s+model',

            # Web Frameworks
            'React': r'\breact\b',
            'Angular': r'\bangular\b',
            'Vue.js': r'\bvue\.?js\b|\bvue\b',
            'Next.js': r'\bnext\.?js\b',
            'Node.js': r'\bnode\.?js\b',
            'Django': r'\bdjango\b',
            'Flask': r'\bflask\b',
            'FastAPI': r'\bfastapi\b',
            'Spring': r'\bspring\b',

            # Cloud & DevOps
            'AWS': r'\baws\b|\bamazon\s+web\s+services\b',
            'Azure': r'\bazure\b|\bms\s+azure\b',
            'GCP': r'\bgcp\b|\bgoogle\s+cloud\b',
            'Docker': r'\bdocker\b',
            'Kubernetes': r'\bkubernetes\b|\bk8s\b',
            'Jenkins': r'\bjenkins\b',
            'GitHub Actions': r'\bgithub\s+actions\b',
            'Terraform': r'\bterraform\b',
            'Ansible': r'\bansible\b',

            # Databases
            'PostgreSQL': r'\bpostgresql\b|\bpostgres\b',
            'MySQL': r'\bmysql\b',
            'MongoDB': r'\bmongodb\b|\bmongo\b',
            'Redis': r'\bredis\b',
            'Elasticsearch': r'\belasticsearch\b|\belastic\b',
            'Cassandra': r'\bcassandra\b',
            'DynamoDB': r'\bdynamodb\b',

            # Data Engineering
            'Spark': r'\bspark\b|\bpyspark\b',
            'Hadoop': r'\bhadoop\b',
            'Airflow': r'\bairflow\b',
            'Kafka': r'\bkafka\b',
            'Pandas': r'\bpandas\b',
            'NumPy': r'\bnumpy\b',

            # MLOps
            'MLflow': r'\bmlflow\b',
            'Kubeflow': r'\bkubeflow\b',
            'SageMaker': r'\bsagemaker\b',
            'Vertex AI': r'\bvertex\s+ai\b',

            # Collaboration
            'Git': r'\bgit\b',
            'GitHub': r'\bgithub\b',
            'GitLab': r'\bgitlab\b',
            'Jira': r'\bjira\b',

            # Methodologies
            'Agile': r'\bagile\b',
            'Scrum': r'\bscrum\b',
            'CI/CD': r'\bci/cd\b|\bcontinuous\s+integration\b',
        }

        found_skills = [skill for skill, pattern in skills_patterns.items() if re.search(pattern, text_lower)]
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


class JobFetcherManager:
    """Manages multiple job fetchers"""

    def __init__(self, config: Dict = None):
        config = config or {}
        self.fetchers = []

        if config.get('usajobs_email') and config.get('usajobs_api_key'):
            self.fetchers.append((
                'USAJobs',
                USAJobsFetcher(config['usajobs_email'], config['usajobs_api_key'])
            ))
            logger.info("USAJobs fetcher enabled")

        
        self.fetchers.append(("RemoteOK", RemoteOKFetcher()))
        logger.info("RemoteOK fetcher enabled.")


        if config.get('adzuna_app_id') and config.get('adzuna_app_key'):
            self.fetchers.append((
                'Adzuna',
                AdzunaFetcher(config['adzuna_app_id'], config['adzuna_app_key'])
            ))
            logger.info("Adzuna fetcher enabled")

        self.default_location = config.get('adzuna_location', 'us')
        logger.info(f"Initialized {len(self.fetchers)} job fetchers")

    def fetch_all(self, search_terms: List[str], location: str = None, max_jobs_per_source: int = 50) -> List[Dict]:
        all_jobs, seen_ids = [], set()
        location = location or self.default_location

        for term in search_terms:
            logger.info(f"Fetching jobs for: {term}")
            for source_name, fetcher in self.fetchers:
                try:
                    jobs = fetcher.fetch_jobs(term, location)
                    added = 0
                    for job in jobs:
                        if job['job_id'] not in seen_ids:
                            seen_ids.add(job['job_id'])
                            all_jobs.append(job)
                            added += 1
                            if added >= max_jobs_per_source:
                                break
                    logger.info(f"Added {added} jobs from {source_name}")
                except Exception as e:
                    logger.error(f"Error fetching from {source_name}: {e}")

        logger.info(f"Total unique jobs fetched: {len(all_jobs)}")
        return all_jobs
