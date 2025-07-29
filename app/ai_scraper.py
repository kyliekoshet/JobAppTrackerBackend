"""
AI-Powered Web Scraping Module for Job Application Tracker

This module uses OpenAI's GPT models to intelligently extract job details from any job posting URL.
It's designed to work with any job board and requires a valid OpenAI API key.
"""

import os
import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from datetime import datetime
import json
from urllib.parse import urlparse

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIScraper:
    """
    An AI-powered job scraping class that uses OpenAI to extract job details from any job posting URL.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_job_details(self, url: str) -> Dict[str, Any]:
        """
        Main method to scrape job details from any job posting URL using AI.
        
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
            
            # Check if OpenAI API key is available
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'OpenAI API key not found. Please set OPENAI_API_KEY environment variable.',
                    'url': url
                }
            
            # Fetch the webpage content
            html_content = self._fetch_webpage(url)
            if not html_content:
                return {
                    'success': False,
                    'error': 'Failed to fetch job page content',
                    'url': url
                }
            
            # Extract text content from HTML
            text_content = self._extract_text_content(html_content)
            
            # Use AI to extract job details
            job_details = self._extract_with_ai(text_content, url)
            
            return job_details
            
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
    
    def _fetch_webpage(self, url: str) -> Optional[str]:
        """Fetch job page content."""
        try:
            logger.info(f"Fetching job page: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch job page {url}: {str(e)}")
            return None
    
    def _extract_text_content(self, html_content: str) -> str:
        """Extract clean text content from job page HTML."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length to avoid token limits
            if len(text) > 8000:
                text = text[:8000] + "..."
            
            return text
        except Exception as e:
            logger.error(f"Failed to extract text content: {str(e)}")
            return ""
    
    def _extract_with_ai(self, text_content: str, url: str) -> Dict[str, Any]:
        """Use OpenAI to extract job details from job posting text."""
        try:
            from openai import OpenAI
            
            # Set up OpenAI client
            client = OpenAI(api_key=self.api_key)
            
            # Create the prompt for job extraction
            prompt = f"""
            Please extract job details from the following job posting text. Return the information in JSON format with the following fields:
            - job_title: The job title/position
            - company: The company name
            - location: The job location (city, state, country, or remote/hybrid/onsite)
            - job_description: A summary of the job description (max 500 characters)
            - salary: Any salary information mentioned
            - requirements: Key requirements or qualifications (max 300 characters)
            
            If any field cannot be determined from the text, set it to null.
            
            Job posting text:
            {text_content}
            
            Return only valid JSON without any additional text or formatting.
            """
            
            # Call OpenAI API using the new format
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts job information from job postings. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            # Parse the response
            ai_response = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            try:
                # Remove any markdown formatting if present
                if ai_response.startswith('```json'):
                    ai_response = ai_response[7:]
                if ai_response.endswith('```'):
                    ai_response = ai_response[:-3]
                
                job_data = json.loads(ai_response)
                
                # Validate and structure the response
                result = {
                    'success': True,
                    'url': url,
                    'job_board': 'ai_extracted',
                    'scraped_at': datetime.now().isoformat(),
                    'job_title': job_data.get('job_title'),
                    'company': job_data.get('company'),
                    'location': job_data.get('location'),
                    'job_description': job_data.get('job_description'),
                    'salary': job_data.get('salary'),
                    'requirements': job_data.get('requirements')
                }
                
                # Validate that we got at least some basic information
                if not result.get('job_title') and not result.get('company'):
                    result['success'] = False
                    result['error'] = 'Could not extract basic job information from posting'
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to parse AI response: {str(e)}',
                    'url': url
                }
                
        except Exception as e:
            logger.error(f"AI extraction failed: {str(e)}")
            return {
                'success': False,
                'error': f'AI extraction failed: {str(e)}',
                'url': url
            }


# Create a global AI scraper instance
ai_scraper = AIScraper()


def scrape_job_details_with_ai(url: str) -> Dict[str, Any]:
    """
    Convenience function to scrape job details from any job posting URL using AI.
    
    Args:
        url (str): The job posting URL
        
    Returns:
        Dict[str, Any]: Scraped job details or error information
    """
    return ai_scraper.scrape_job_details(url) 