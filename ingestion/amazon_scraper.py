import requests
import time
import random
import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import json

from .headers import get_random_header
from .validators import validate_product_data
from .parser import parse_product_page

logger = logging.getLogger(__name__)

class AmazonScraper:
    def __init__(self, config_path: str = "ingestion/ingestion_config.yaml"):
        self.session = requests.Session()
        self.session.headers.update(get_random_header())
        
        # Configuration
        self.max_retries = 3
        self.delay_range = (1, 3)  # seconds between requests
        self.timeout = 30
        
    def fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Fetch HTML content from Amazon product page with retry logic"""
        if retry_count >= self.max_retries:
            logger.error(f"Max retries exceeded for {url}")
            return None
            
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(*self.delay_range))
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Check if we got blocked
            if "robot check" in response.text.lower():
                logger.warning("Detected bot check page")
                return None
                
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed (attempt {retry_count + 1}): {e}")
            # Rotate user agent and retry
            self.session.headers.update(get_random_header())
            return self.fetch_page(url, retry_count + 1)
            
    def get_product_data(self, url: str) -> Optional[Dict]:
        """Main method to get product data from URL"""
        try:
            # Extract ASIN from URL
            asin = self.extract_asin(url)
            if not asin:
                logger.error(f"Could not extract ASIN from URL: {url}")
                return None
                
            # Fetch page content
            html = self.fetch_page(url)
            if not html:
                return None
                
            # Parse product data
            product_data = parse_product_page(html, asin, url)
            
            # Validate data
            if validate_product_data(product_data):
                return product_data
            else:
                logger.error(f"Validation failed for product: {asin}")
                return None
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
            
    @staticmethod
    def extract_asin(url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL"""
        parsed = urlparse(url)
        
        # Try to get ASIN from path
        path_parts = parsed.path.split('/')
        for i, part in enumerate(path_parts):
            if part == 'dp' and i + 1 < len(path_parts):
                return path_parts[i + 1].split('?')[0]
                
        # Try from query parameters
        query_params = parse_qs(parsed.query)
        if 'asin' in query_params:
            return query_params['asin'][0]
            
        return None
        
    def scrape_multiple(self, urls: list) -> list:
        """Scrape multiple product URLs"""
        results = []
        for url in urls:
            data = self.get_product_data(url)
            if data:
                results.append(data)
        return results