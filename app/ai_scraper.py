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
        # Use more realistic headers to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
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
            
            # Log content length for debugging
            logger.info(f"Extracted text content length: {len(text_content)} characters")
            if len(text_content) < 100:
                logger.warning(f"Very short content extracted. First 200 chars: {text_content[:200]}")
                return {
                    'success': False,
                    'error': 'Unable to scrape job details. This could be due to: (1) The website blocking automated access, (2) JavaScript-heavy content, or (3) Login requirements. Please copy and paste the job details manually.',
                    'url': url
                }
            else:
                logger.info(f"Content preview: {text_content[:200]}...")
            
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
            You are a precise job posting analyzer. Extract ONLY the information that is explicitly stated in the job posting text. DO NOT infer, assume, or generate any information that is not directly mentioned.

            Return the information in JSON format with the following fields:
            - job_title: The exact job title/position as written
            - company: The company name as stated
            - location: The job location if explicitly mentioned (city, state, country, remote/hybrid/onsite)
            - job_description: A clean, well-structured description based ONLY on what's written in the posting
            - salary: ONLY if salary/compensation is explicitly mentioned (range, benefits, etc.)
            - requirements: ONLY the explicitly stated requirements, qualifications, and skills
            - benefits: ONLY the explicitly mentioned benefits or perks
            - experience_level: ONLY if clearly stated (Entry, Mid, Senior, Executive)

            CRITICAL RULES:
            - If information is not explicitly stated, set the field to null
            - Do NOT make up salary ranges, benefits, or requirements
            - Do NOT infer experience levels unless clearly stated
            - Do NOT add generic job descriptions
            - Only extract what is actually written in the posting

            If any field cannot be determined from the text, set it to null.

            Job posting text:
            {text_content}

            Return only valid JSON without any additional text or formatting.
            """
            
            # Call OpenAI API with better parameters
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a precise job posting analyzer that extracts only factual information explicitly stated in job postings. You never infer, assume, or generate information that isn't directly mentioned. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.0,  # Zero temperature for maximum factual accuracy
                presence_penalty=0.0,  # No creativity encouraged
                frequency_penalty=0.0   # No repetition penalty needed
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
                
                # Log what we extracted for debugging
                logger.info(f"AI extracted data: job_title='{result.get('job_title')}', company='{result.get('company')}'")
                
                # Validate that we got at least one essential piece of information
                if not result.get('job_title') and not result.get('company'):
                    logger.warning(f"AI failed to extract basic job info. Full response: {job_data}")
                    result['success'] = False
                    result['error'] = 'Could not extract basic job information from posting. The job posting might be too short, blocked, or in an unsupported format.'
                
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


def enhance_job_description_with_ai(job_description: str, job_title: str = None, company: str = None) -> Dict[str, Any]:
    """
    Use AI to enhance and organize a job description into structured sections.
    
    Args:
        job_description (str): The original job description text
        job_title (str): Optional job title for context
        company (str): Optional company name for context
        
    Returns:
        Dict[str, Any]: Enhanced job description with structured sections
    """
    try:
        from openai import OpenAI
        
        # Get API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {
                'success': False,
                'error': 'OpenAI API key not found. Please set OPENAI_API_KEY environment variable.'
            }
        
        # Set up OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Build context for better enhancement
        context = ""
        if job_title:
            context += f"Job Title: {job_title}\n"
        if company:
            context += f"Company: {company}\n"
        
        # Create prompt for job description enhancement
        prompt = f"""
        {context}
        Please analyze and enhance the following job description by organizing it into clear, structured sections. Extract and present the information in a clean, professional format.

        Return the information in JSON format with the following fields:
        - enhanced_description: A clean, well-organized summary of the role (2-3 paragraphs, max 800 characters)
        - key_requirements: Essential qualifications, skills, and experience needed (as a single string with bullet points using • symbols, max 600 characters)
        - key_responsibilities: Main duties and tasks (as a single string with bullet points using • symbols, max 600 characters)  
        - benefits: Compensation, perks, and benefits mentioned (as a single string with bullet points using • symbols, max 400 characters)

        Guidelines:
        - Use clear, professional language
        - Remove fluff and marketing speak
        - Focus on factual, actionable information
        - Format lists as single strings with • bullet points
        - If a section has no relevant information, set it to null
        - Keep content concise but informative

        Original job description:
        {job_description}

        Return only valid JSON without any additional text or formatting.
        """
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert HR professional who excels at organizing and enhancing job descriptions. You extract key information and present it in a clear, structured format. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.1,  # Low temperature for consistent formatting
            presence_penalty=0.0,
            frequency_penalty=0.0
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
            
            enhanced_data = json.loads(ai_response)
            
            # Structure the response
            result = {
                'success': True,
                'enhanced_description': enhanced_data.get('enhanced_description'),
                'key_requirements': enhanced_data.get('key_requirements'),
                'key_responsibilities': enhanced_data.get('key_responsibilities'),
                'benefits': enhanced_data.get('benefits')
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI enhancement response as JSON: {str(e)}")
            logger.error(f"AI Response: {ai_response}")
            return {
                'success': False,
                'error': 'Failed to parse AI response'
            }
            
    except Exception as e:
        logger.error(f"Job description enhancement failed: {str(e)}")
        return {
            'success': False,
            'error': f'Enhancement failed: {str(e)}'
        } 