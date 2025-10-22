"""
Scrapy spider for job postings
"""
import scrapy
from scrapy.crawler import CrawlerProcess
from datetime import datetime
import json
import re
from urllib.parse import urljoin, urlparse
import hashlib


class JobSpider(scrapy.Spider):
    """
    Spider for scraping job postings from multiple sources
    
    Respects robots.txt and implements ethical scraping practices
    """
    name = "job_spider"
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'USER_AGENT': 'LMI-Agent-Bot/1.0 (Educational Purpose; +https://github.com/your-repo)',
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_EXPIRATION_SECS': 86400,  # 24 hours
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'AUTOTHROTTLE_MAX_DELAY': 10,
    }
    
    def __init__(self, search_terms=None, locations=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_terms = search_terms or ['machine learning engineer', 'data scientist']
        self.locations = locations or ['United States', 'Remote']
        self.scraped_jobs = []
    
    def start_requests(self):
        """
        Generate initial requests for job boards
        
        Note: This is a template. You'll need to customize for specific job boards.
        For production, use official APIs where available.
        """
        # Example: Indeed (respect their robots.txt and terms of service)
        base_urls = [
            'https://www.indeed.com',
            # Add other job boards here
        ]
        
        for term in self.search_terms:
            for location in self.locations:
                # Indeed search URL structure
                search_query = term.replace(' ', '+')
                location_query = location.replace(' ', '+')
                url = f"https://www.indeed.com/jobs?q={search_query}&l={location_query}"
                
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_indeed_search,
                    meta={'search_term': term, 'location': location}
                )
    
    def parse_indeed_search(self, response):
        """Parse Indeed search results page"""
        # Extract job links
        job_links = response.css('a.jcs-JobTitle::attr(href)').getall()
        
        for link in job_links[:20]:  # Limit to first 20 results
            full_url = urljoin(response.url, link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_indeed_job,
                meta={
                    'search_term': response.meta['search_term'],
                    'location': response.meta['location']
                }
            )
    
    def parse_indeed_job(self, response):
        """Parse individual Indeed job posting"""
        try:
            # Extract job details
            title = response.css('h1.jobsearch-JobInfoHeader-title span::text').get()
            company = response.css('div[data-company-name="true"] a::text').get()
            location = response.css('div[data-testid="job-location"]::text').get()
            
            # Description
            description_elem = response.css('div#jobDescriptionText')
            description = ' '.join(description_elem.css('::text').getall()).strip()
            
            # Extract skills (simple pattern matching)
            skills = self._extract_skills(description)
            
            # Generate unique job ID
            job_id = self._generate_job_id(title, company, response.url)
            
            job_data = {
                'job_id': job_id,
                'title': title,
                'company': company or 'Unknown',
                'location': location or response.meta['location'],
                'description': description,
                'requirements': description,  # Would need more sophisticated parsing
                'skills': skills,
                'source_url': response.url,
                'source_platform': 'Indeed',
                'scraped_date': datetime.utcnow().isoformat(),
                'search_term': response.meta['search_term']
            }
            
            self.scraped_jobs.append(job_data)
            yield job_data
            
        except Exception as e:
            self.logger.error(f"Error parsing job: {e}")
    
    def _extract_skills(self, text: str) -> list:
        """
        Extract technical skills from job description
        
        Args:
            text: Job description text
            
        Returns:
            List of identified skills
        """
        # Common technical skills (expand this list)
        skill_patterns = [
            r'\bPython\b', r'\bJava\b', r'\bJavaScript\b', r'\bC\+\+\b',
            r'\bReact\b', r'\bAngular\b', r'\bVue\.js\b',
            r'\bTensorFlow\b', r'\bPyTorch\b', r'\bKeras\b',
            r'\bDocker\b', r'\bKubernetes\b', r'\bAWS\b', r'\bAzure\b', r'\bGCP\b',
            r'\bSQL\b', r'\bNoSQL\b', r'\bMongoDB\b', r'\bPostgreSQL\b',
            r'\bGit\b', r'\bCI/CD\b', r'\bJenkins\b',
            r'\bMachine Learning\b', r'\bDeep Learning\b', r'\bNLP\b',
            r'\bRAG\b', r'\bLLM\b', r'\bGenerative AI\b',
            r'\bFastAPI\b', r'\bDjango\b', r'\bFlask\b',
            r'\bNext\.js\b', r'\bNode\.js\b',
            r'\bScrum\b', r'\bAgile\b',
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for pattern in skill_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                skill_name = re.search(pattern, text, re.IGNORECASE).group()
                if skill_name not in found_skills:
                    found_skills.append(skill_name)
        
        return found_skills
    
    def _generate_job_id(self, title: str, company: str, url: str) -> str:
        """
        Generate unique job ID from job details
        
        Args:
            title: Job title
            company: Company name
            url: Source URL
            
        Returns:
            Unique job identifier
        """
        composite = f"{title}_{company}_{url}".encode('utf-8')
        return hashlib.md5(composite).hexdigest()
    
    def closed(self, reason):
        """Called when spider finishes"""
        self.logger.info(f"Spider closed. Scraped {len(self.scraped_jobs)} jobs")
        
        # Save to JSON file
        with open('scraped_jobs.json', 'w') as f:
            json.dump(self.scraped_jobs, f, indent=2)


class LinkedInJobSpider(scrapy.Spider):
    """
    Spider for LinkedIn job postings
    
    Note: LinkedIn has strict scraping policies. Use their official API instead.
    This is for educational purposes only.
    """
    name = "linkedin_spider"
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
        'USER_AGENT': 'Mozilla/5.0 (Educational Research)',
    }
    
    def start_requests(self):
        """
        Important: LinkedIn actively blocks scrapers.
        Use their official Jobs API: https://docs.microsoft.com/en-us/linkedin/
        """
        self.logger.warning(
            "LinkedIn scraping is against their ToS. "
            "Use the official LinkedIn Jobs API instead."
        )
        return []


# Utility function to run the spider
def run_spider(search_terms=None, locations=None, output_file='scraped_jobs.json'):
    """
    Run the job spider
    
    Args:
        search_terms: List of job titles to search
        locations: List of locations
        output_file: Output JSON file path
        
    Returns:
        List of scraped jobs
    """
    process = CrawlerProcess({
        'USER_AGENT': 'LMI-Agent-Bot/1.0',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2,
        'FEEDS': {
            output_file: {'format': 'json', 'overwrite': True}
        }
    })
    
    process.crawl(
        JobSpider,
        search_terms=search_terms,
        locations=locations
    )
    process.start()


# Alternative: Use public job APIs
class JobAPIClient:
    """
    Client for fetching jobs from public APIs
    
    Recommended approach for production use
    """
    
    @staticmethod
    def fetch_from_github_jobs(search_term: str) -> list:
        """
        Fetch from GitHub Jobs API (if still available)
        Note: GitHub Jobs was deprecated. Use alternatives.
        """
        import requests
        
        # Example structure - adapt to actual available APIs
        url = f"https://jobs.github.com/positions.json?description={search_term}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching from API: {e}")
            return []
    
    @staticmethod
    def fetch_from_remoteok(search_term: str) -> list:
        """
        Fetch from RemoteOK API (has public API)
        """
        import requests
        import time
        
        url = "https://remoteok.com/api"
        headers = {
            'User-Agent': 'LMI-Agent-Bot/1.0 (Educational Purpose)',
        }
        
        try:
            time.sleep(2)  # Rate limiting
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            jobs = response.json()
            
            # Filter by search term
            filtered_jobs = []
            for job in jobs[1:]:  # First item is API info
                if search_term.lower() in job.get('position', '').lower():
                    filtered_jobs.append({
                        'job_id': job.get('id'),
                        'title': job.get('position'),
                        'company': job.get('company'),
                        'location': 'Remote',
                        'description': job.get('description', ''),
                        'requirements': '',
                        'skills': job.get('tags', []),
                        'source_url': job.get('url'),
                        'source_platform': 'RemoteOK',
                        'scraped_date': datetime.utcnow().isoformat()
                    })
            
            return filtered_jobs
            
        except Exception as e:
            print(f"Error fetching from RemoteOK: {e}")
            return []
    
    @staticmethod
    def fetch_from_adzuna(app_id: str, app_key: str, search_term: str, location: str = "us") -> list:
        """
        Fetch from Adzuna API (requires free API key)
        Sign up at: https://developer.adzuna.com/
        """
        import requests
        
        url = f"https://api.adzuna.com/v1/api/jobs/{location}/search/1"
        params = {
            'app_id': app_id,
            'app_key': app_key,
            'what': search_term,
            'results_per_page': 50
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            jobs = []
            for job in data.get('results', []):
                jobs.append({
                    'job_id': job.get('id'),
                    'title': job.get('title'),
                    'company': job.get('company', {}).get('display_name'),
                    'location': job.get('location', {}).get('display_name'),
                    'description': job.get('description', ''),
                    'requirements': '',
                    'skills': [],
                    'salary_range': f"${job.get('salary_min', 0)}-${job.get('salary_max', 0)}",
                    'source_url': job.get('redirect_url'),
                    'source_platform': 'Adzuna',
                    'scraped_date': datetime.utcnow().isoformat(),
                    'posted_date': job.get('created')
                })
            
            return jobs
            
        except Exception as e:
            print(f"Error fetching from Adzuna: {e}")
            return []


if __name__ == "__main__":
    # Example usage
    print("Starting job scraper...")
    print("Note: Always respect robots.txt and terms of service")
    print("For production, use official APIs like Adzuna, RemoteOK, etc.")
    
    # Run with default settings
    # run_spider(
    #     search_terms=['Machine Learning Engineer', 'Data Scientist'],
    #     locations=['United States', 'Remote']
    # )