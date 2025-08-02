#!/usr/bin/env python3
"""
Test script for the AI scraper
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ai_scraper import scrape_job_details_with_ai
import json

def test_scraper():
    print("Testing AI Scraper...")
    
    # Test with a well-known job site that should work
    test_urls = [
        "https://stackoverflow.com/jobs/companies/stackoverflow",  # Simple page
        "https://httpbin.org/html",  # Simple HTML test page
    ]
    
    for url in test_urls:
        print(f"\n--- Testing URL: {url} ---")
        result = scrape_job_details_with_ai(url)
        print(f"Success: {result.get('success')}")
        if result.get('success'):
            print(f"Job Title: {result.get('job_title')}")
            print(f"Company: {result.get('company')}")
            print(f"Location: {result.get('location')}")
            print(f"Salary: {result.get('salary')}")
        else:
            print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    test_scraper() 