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
            
            # Remove script, style, and navigation elements
            for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
                element.decompose()
            
            # Try to find main content areas first
            main_content = None
            
            # Look for common job posting content selectors
            selectors = [
                '[class*="job-description"]',
                '[class*="description"]',
                '[class*="content"]',
                '[class*="posting"]',
                'main',
                'article',
                '.content',
                '#content',
                '.job-content',
                '.posting-content'
            ]
            
            for selector in selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no specific content area found, use body
            if not main_content:
                main_content = soup.body or soup
            
            # Extract text with better structure
            text_parts = []
            
            # Get headings and their content
            for heading in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading_text = heading.get_text(strip=True)
                if heading_text:
                    text_parts.append(f"\n## {heading_text}")
                
                # Get content after heading until next heading
                next_elem = heading.find_next_sibling()
                while next_elem and next_elem.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if next_elem.name in ['p', 'div', 'li']:
                        content = next_elem.get_text(strip=True)
                        if content and len(content) > 10:  # Filter out very short content
                            text_parts.append(content)
                    next_elem = next_elem.find_next_sibling()
            
            # If no structured content found, get all paragraphs
            if len(text_parts) < 3:
                paragraphs = main_content.find_all(['p', 'div', 'li'])
                for p in paragraphs:
                    content = p.get_text(strip=True)
                    if content and len(content) > 20:  # Filter out very short content
                        text_parts.append(content)
            
            # Join all text parts
            text = '\n\n'.join(text_parts)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text length but preserve structure
            if len(text) > 12000:  # Increased limit for better extraction
                # Try to keep the most relevant parts
                sentences = text.split('. ')
                if len(sentences) > 10:
                    # Keep first 8 sentences and last 2
                    text = '. '.join(sentences[:8] + sentences[-2:]) + "..."
                else:
                    text = text[:12000] + "..."
            
            return text
        except Exception as e:
            logger.error(f"Failed to extract text content: {str(e)}")
            return ""
    
    def _extract_with_ai(self, text_content: str, url: str) -> Dict[str, Any]:
        """Use OpenAI to extract job details from job posting text with enhanced description extraction."""
        try:
            from openai import OpenAI
            
            # Set up OpenAI client
            client = OpenAI(api_key=self.api_key)
            
            # Create an enhanced prompt for better job extraction
            prompt = f"""
            Please extract comprehensive job details from the following job posting text. Focus on creating a well-structured and informative job description.

            Return the information in JSON format with the following fields:
            - job_title: The exact job title/position
            - company: The company name
            - location: The job location (city, state, country, or remote/hybrid/onsite)
            - job_description: A comprehensive, well-structured job description that includes:
              * Role overview and responsibilities
              * Key duties and tasks
              * What the candidate will be doing
              * Impact and goals of the position
              * Team and collaboration aspects
              * Growth opportunities (if mentioned)
              Format this as clear, readable paragraphs (max 1000 characters)
            - salary: Any salary information mentioned (range, benefits, etc.)
            - requirements: Key requirements, qualifications, and skills needed (max 500 characters)
            - benefits: Any benefits or perks mentioned (max 300 characters)
            - experience_level: Entry, Mid, Senior, or Executive level (if clear from posting)

            Guidelines for job_description:
            - Make it engaging and informative
            - Include specific responsibilities and duties
            - Mention technologies, tools, or methodologies if relevant
            - Highlight the impact and value of the role
            - Use clear, professional language
            - Structure it logically with proper paragraphs

            If any field cannot be determined from the text, set it to null.

            Job posting text:
            {text_content}

            Return only valid JSON without any additional text or formatting.
            """
            
            # Call OpenAI API with better parameters
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert job posting analyzer that extracts comprehensive job information. You excel at creating detailed, well-structured job descriptions that are informative and engaging. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,  # Increased for better descriptions
                temperature=0.2,  # Slightly higher for more creative descriptions
                presence_penalty=0.1,  # Encourage more detailed responses
                frequency_penalty=0.1   # Reduce repetition
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
                    'requirements': job_data.get('requirements'),
                    'benefits': job_data.get('benefits'),
                    'experience_level': job_data.get('experience_level')
                }
                
                # Validate that we got the essential information
                if not result.get('job_title') and not result.get('company'):
                    result['success'] = False
                    result['error'] = 'Could not extract basic job information from posting'
                
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                logger.error(f"AI Response: {ai_response}")
                return {
                    'success': False,
                    'error': 'Failed to parse AI response',
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