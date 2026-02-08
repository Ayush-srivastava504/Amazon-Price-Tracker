"""HTTP scraper for Amazon product pages."""
import time
import requests
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import structlog

from .header import HeaderManager
from .validator import product_validator

logger = structlog.get_logger()

class AmazonScraper:
    """Production-grade Amazon scraper with retry logic and rate limiting."""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("base_url", "https://www.amazon.com")
        self.timeout = config.get("timeout", 10)
        self.max_retries = config.get("max_retries", 3)
        self.request_delay = config.get("request_delay", 2)
        
        self.session = self._create_session()
        self.header_manager = HeaderManager()
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def scrape_product(self, product_id: str) -> Optional[str]:
        """
        Scrape Amazon product page.
        
        Args:
            product_id: Amazon product ID (ASIN)
            
        Returns:
            HTML content if successful, None otherwise
        """
        url = f"{self.base_url}/dp/{product_id}"
        
        try:
            # Add delay between requests
            time.sleep(self.request_delay)
            
            headers = self.header_manager.get_headers()
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            response.raise_for_status()
            
            # Check if we got a valid product page
            if "robot check" in response.text.lower():
                logger.warning("Bot detection triggered", product_id=product_id)
                self.header_manager.rotate_user_agent()
                return None
                
            logger.info("Successfully scraped product", 
                       product_id=product_id, 
                       status=response.status_code)
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error("Failed to scrape product", 
                        product_id=product_id, 
                        error=str(e))
            return None
    
    def scrape_multiple_products(self, product_ids: list) -> Dict[str, Optional[str]]:
        """Scrape multiple products with rate limiting."""
        results = {}
        
        for idx, product_id in enumerate(product_ids):
            logger.info(f"Scraping product {idx+1}/{len(product_ids)}", product_id=product_id)
            
            html = self.scrape_product(product_id)
            results[product_id] = html
            
            # Be respectful with delays
            if idx < len(product_ids) - 1:
                time.sleep(self.request_delay)
                
        return results