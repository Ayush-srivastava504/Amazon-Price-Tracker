
# Simple Amazon India scraper. Gets HTML, avoids bans, nothing fancy.

import time
import random
import requests
from typing import Optional, Dict, Any, List
import structlog

logger = structlog.get_logger()

# Real browser headers we actually use
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

class AmazonScraper:
    
    def __init__(self, config: Optional[Dict] = None):
        # Defaults that work for Amazon India
        config = config or {}
        self.base_url = config.get("base_url", "https://www.amazon.in")
        self.timeout = config.get("timeout", 15)
        self.request_delay = config.get("request_delay", 3.0)
        self.max_retries = config.get("max_retries", 3)
        
        # Bot detection patterns - if we see these, Amazon caught us
        self.bot_indicators = [
            "robot check",
            "captcha",
            "enter the characters you see below",
            "sorry, we just need to make sure you're not a robot",
        ]
        
        # Simple session with retries
        self.session = requests.Session()
        self.session.headers.update({
            "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        
        # Track which user agent we're using
        self.current_ua_index = 0
        
        logger.info(f"Scraper ready for {self.base_url}, delay={self.request_delay}s")

    def _get_headers(self) -> Dict[str, str]:        # Rotate user agents to look less bot-like.
        headers = {
            "User-Agent": USER_AGENTS[self.current_ua_index],
            "Referer": "https://www.amazon.in/",
        }
        # Move to next UA for next request
        self.current_ua_index = (self.current_ua_index + 1) % len(USER_AGENTS)
        return headers
    
    def _random_delay(self) -> float:         # Add jitter to avoid pattern detection
        return random.uniform(self.request_delay * 0.8, self.request_delay * 1.2)
    
    def scrape_product(self, product_id: str) -> Optional[str]:     #Get raw HTML for a product. Returns None if failed
        url = f"{self.base_url}/dp/{product_id}"
        
        try:
            # Be nice to Amazon
            time.sleep(self._random_delay())
            
            response = self.session.get(
                url,
                headers=self._get_headers(),
                timeout=self.timeout,
                allow_redirects=True
            )
            
            # Check for bot detection
            html = response.text.lower()
            for indicator in self.bot_indicators:
                if indicator in html:
                    logger.warning(f"Bot detection: {indicator[:30]}...")
                    return None
            
            if response.status_code != 200:
                logger.error(f"HTTP {response.status_code} for {product_id}")
                return None
            
            logger.info(f"Scraped {product_id}, {len(response.text)/1024:.1f}KB")
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {product_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error for {product_id}: {e}")
            return None
    
    def scrape_with_retry(self, product_id: str, max_attempts: int = 2) -> Optional[str]:
        for attempt in range(1, max_attempts + 1):
            html = self.scrape_product(product_id)
            if html:
                return html
            logger.info(f"Retry {attempt}/{max_attempts} for {product_id}")
            time.sleep(attempt * 2)  # Backoff
        return None
    
    def scrape_multiple(self, product_ids: List[str]) -> Dict[str, Optional[str]]:
        results = {}
        for i, pid in enumerate(product_ids):
            logger.info(f"Scraping {i+1}/{len(product_ids)}: {pid}")
            results[pid] = self.scrape_with_retry(pid)
            # Extra delay between products
            if i < len(product_ids) - 1:
                time.sleep(self.request_delay * 1.5)
        return results