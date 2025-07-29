"""
Web Scraping Module for Job Application Tracker

This module provides functionality to scrape job details from various job posting URLs.
It supports multiple scraping strategies and handles different job board formats.
"""

import re
import logging
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobScraper:
    """
    A comprehensive job scraping class that supports multiple job boards and scraping strategies.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Common job board patterns
        self.job_boards = {
            'linkedin': {
                'domain': 'linkedin.com',
                'selectors': {
                    'title': ['h1', '.job-details-jobs-unified-top-card__job-title', '.top-card-layout__title'],
                    'company': ['.job-details-jobs-unified-top-card__company-name', '.top-card-layout__company-name'],
                    'location': ['.job-details-jobs-unified-top-card__bullet', '.top-card-layout__location'],
                    'description': ['.job-details-jobs-unified-top-card__job-description', '.description__text'],
                    'salary': ['.job-details-jobs-unified-top-card__salary-info', '.compensation__salary']
                }
            },
            'indeed': {
                'domain': 'indeed.com',
                'selectors': {
                    'title': ['h1', '.jobsearch-JobInfoHeader-title'],
                    'company': ['.jobsearch-JobInfoHeader-companyName', '.companyName'],
                    'location': ['.jobsearch-JobInfoHeader-companyLocation', '.location'],
                    'description': ['.jobsearch-jobDescriptionText', '#jobDescriptionText'],
                    'salary': ['.jobsearch-JobInfoHeader-salary', '.salary-snippet']
                }
            },
            'glassdoor': {
                'domain': 'glassdoor.com',
                'selectors': {
                    'title': ['h1', '.job-title'],
                    'company': ['.employer-name', '.company-name'],
                    'location': ['.location', '.job-location'],
                    'description': ['.jobDescriptionContent', '.desc'],
                    'salary': ['.salary-estimate', '.salary']
                }
            },
            'microsoft': {
                'domain': 'careers.microsoft.com',
                'selectors': {
                    'title': ['h1', '.job-title', '.title'],
                    'company': ['.company-name', '.employer', '.organization'],
                    'location': ['.location', '.job-location', '.work-location'],
                    'description': ['.job-description', '.description', '.content'],
                    'salary': ['.salary', '.compensation', '.pay']
                }
            }
        }
    
    def scrape_job_details(self, url: str) -> Dict[str, Any]:
        """
        Main method to scrape job details from a URL.
        
        Args:
            url (str): The job posting URL
            
        Returns:
            Dict[str, Any]: Scraped job details or error information
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                return {
                    'success': False,
                    'error': 'Invalid URL format',
                    'url': url
                }
            
            # Determine job board type
            job_board = self._identify_job_board(url)
            
            # Try scraping with requests + BeautifulSoup
            scraped_data = self._scrape_with_requests(url, job_board)
            
            return scraped_data
            
        except Exception as e:
            logger.error(f"Error scraping job details from {url}: {str(e)}")
            return {
                'success': False,
                'error': f'Scraping failed: {str(e)}',
                'url': url
            }
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate if the URL is properly formatted."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _identify_job_board(self, url: str) -> Optional[str]:
        """Identify the job board from the URL."""
        domain = urlparse(url).netloc.lower()
        
        for board_name, board_info in self.job_boards.items():
            if board_info['domain'] in domain:
                return board_name
        
        return None
    
    def _scrape_with_requests(self, url: str, job_board: Optional[str]) -> Dict[str, Any]:
        """Scrape using requests and BeautifulSoup."""
        try:
            logger.info(f"Attempting to scrape with requests: {url}")
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract data based on job board
            if job_board and job_board in self.job_boards:
                return self._extract_with_selectors(soup, job_board, url)
            else:
                return self._extract_generic(soup, url)
                
        except requests.RequestException as e:
            logger.warning(f"Requests scraping failed for {url}: {str(e)}")
            return {'success': False, 'error': f'HTTP request failed: {str(e)}', 'url': url}
        except Exception as e:
            logger.warning(f"BeautifulSoup parsing failed for {url}: {str(e)}")
            return {'success': False, 'error': f'Parsing failed: {str(e)}', 'url': url}
    
    def _extract_with_selectors(self, soup: BeautifulSoup, job_board: str, url: str) -> Dict[str, Any]:
        """Extract job details using predefined selectors for known job boards."""
        selectors = self.job_boards[job_board]['selectors']
        extracted_data = {
            'success': True,
            'url': url,
            'job_board': job_board,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract job title
        title = self._extract_text_with_selectors(soup, selectors.get('title', []))
        if title:
            extracted_data['job_title'] = title.strip()
        
        # Extract company name
        company = self._extract_text_with_selectors(soup, selectors.get('company', []))
        if company:
            extracted_data['company'] = company.strip()
        
        # Extract location
        location = self._extract_text_with_selectors(soup, selectors.get('location', []))
        if location:
            extracted_data['location'] = location.strip()
        
        # Extract job description
        description = self._extract_text_with_selectors(soup, selectors.get('description', []))
        if description:
            extracted_data['job_description'] = description.strip()
        
        # Extract salary information
        salary = self._extract_text_with_selectors(soup, selectors.get('salary', []))
        if salary:
            extracted_data['salary'] = salary.strip()
        
        # Validate that we got at least some basic information
        if not extracted_data.get('job_title') and not extracted_data.get('company'):
            extracted_data['success'] = False
            extracted_data['error'] = 'Could not extract basic job information'
        
        return extracted_data
    
    def _extract_generic(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Generic extraction for unknown job boards."""
        extracted_data = {
            'success': True,
            'url': url,
            'job_board': 'generic',
            'scraped_at': datetime.now().isoformat()
        }
        
        # Try to find job title in h1 tags
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            text = h1.get_text(strip=True)
            if text and len(text) > 5 and len(text) < 200:
                extracted_data['job_title'] = text
                break
        
        # Try to find company name in common patterns
        company_patterns = [
            'company', 'employer', 'organization', 'corporation',
            'inc', 'llc', 'ltd', 'corp', 'company'
        ]
        
        for pattern in company_patterns:
            elements = soup.find_all(text=re.compile(pattern, re.IGNORECASE))
            for element in elements:
                parent = element.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if text and len(text) > 2 and len(text) < 100:
                        extracted_data['company'] = text
                        break
            if extracted_data.get('company'):
                break
        
        # Try to find location
        location_patterns = [
            'location', 'address', 'city', 'state', 'country',
            'remote', 'hybrid', 'onsite'
        ]
        
        for pattern in location_patterns:
            elements = soup.find_all(text=re.compile(pattern, re.IGNORECASE))
            for element in elements:
                parent = element.parent
                if parent:
                    text = parent.get_text(strip=True)
                    if text and len(text) > 2 and len(text) < 100:
                        extracted_data['location'] = text
                        break
            if extracted_data.get('location'):
                break
        
        # Try to find job description
        description_selectors = [
            'div[class*="description"]',
            'div[class*="content"]',
            'div[class*="details"]',
            'section[class*="description"]',
            'article[class*="description"]'
        ]
        
        for selector in description_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 100:
                    extracted_data['job_description'] = text[:2000]  # Limit length
                    break
            if extracted_data.get('job_description'):
                break
        
        # Validate that we got at least some basic information
        if not extracted_data.get('job_title') and not extracted_data.get('company'):
            extracted_data['success'] = False
            extracted_data['error'] = 'Could not extract basic job information'
        
        return extracted_data
    
    def _extract_text_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple selectors."""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text:
                        return text
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {str(e)}")
                continue
        
        return None


# Create a global scraper instance
job_scraper = JobScraper()


def scrape_job_details_from_url(url: str) -> Dict[str, Any]:
    """
    Convenience function to scrape job details from a URL.
    
    Args:
        url (str): The job posting URL
        
    Returns:
        Dict[str, Any]: Scraped job details or error information
    """
    return job_scraper.scrape_job_details(url) 