"""HTTP scraper for Amazon India product pages"""

import time
import random
import requests
from typing import Optional, Dict, Any, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import structlog

from .header import HeaderManager  # correct relative import

logger = structlog.get_logger()


class AmazonScraper:
    """
    Amazon India product page scraper with:
    - retry logic
    - rate limiting
    - header rotation
    - bot detection handling
    """

    def __init__(self, config: Dict[str, Any]):
        # Core config - Amazon India specific
        self.base_url: str = config.get(
            "base_url", "https://www.amazon.in"
        )
        self.timeout: int = config.get("timeout", 10)
        self.max_retries: int = config.get("max_retries", 3)
        self.request_delay: float = float(config.get("request_delay", 2.0))
        self.max_html_size_mb: int = config.get("max_html_size_mb", 5)

        # Retry config (must live on self)
        self.retry_backoff_factor: float = config.get(
            "retry_backoff_factor", 1.0
        )
        self.retry_status_codes: List[int] = config.get(
            "retry_status_codes", [429, 500, 502, 503, 504]
        )

        # Delay randomization
        self.randomize_delay = config.get("randomize_delay", False)
        self.min_delay = config.get("min_delay", 1.0)
        self.max_delay = config.get("max_delay", 3.0)

        # Bot indicators (Amazon India specific)
        self.bot_indicators = [
            "robot check",
            "captcha",
            "enter the characters you see below",
            "sorry, we just need to make sure you're not a robot",
            "to discuss automated access to amazon data",
            "/errors/validatecaptcha",
            "api-services-support@amazon.com",  # India-specific
        ]

        self.session = self._create_session()
        self.header_manager = HeaderManager()

        logger.debug(
            "Scraper initialized for Amazon India",
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )

    # --------------------------------------------------
    # Session setup
    # --------------------------------------------------
    def _create_session(self) -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.retry_backoff_factor,
            status_forcelist=self.retry_status_codes,
            allowed_methods=["GET"],
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10,
        )

        session.mount("https://", adapter)
        session.mount("http://", adapter)

        # India-specific headers
        session.headers.update({
            "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8,hi;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
        })

        return session

    # --------------------------------------------------
    # Delay helper
    # --------------------------------------------------
    def _get_delay(self) -> float:
        if self.randomize_delay:
            return random.uniform(self.min_delay, self.max_delay)
        return self.request_delay

    # --------------------------------------------------
    # Scrape single product
    # --------------------------------------------------
    def scrape_product(self, product_id: str) -> Optional[str]:
        """
        Scrape a single product page from Amazon India.
        
        Args:
            product_id: ASIN of the product
            
        Returns:
            HTML content as string or None if failed
        """
        # Construct URL for Amazon India
        url = f"{self.base_url}/dp/{product_id}"

        try:
            time.sleep(self._get_delay())

            headers = self.header_manager.get_headers()

            logger.debug("Sending request to Amazon India", product_id=product_id, url=url)

            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=True,
            )

            if response.status_code != 200:
                logger.error(
                    "Non-200 response received",
                    product_id=product_id,
                    status_code=response.status_code,
                    url=url,
                )
                return None

            content = response.text
            content_lower = content.lower()

            # Check for bot detection
            for indicator in self.bot_indicators:
                if indicator in content_lower:
                    logger.warning(
                        "Bot detection triggered on Amazon India",
                        product_id=product_id,
                        indicator=indicator,
                    )
                    self.header_manager.rotate_user_agent()
                    return None

            logger.info(
                "Successfully scraped product from Amazon India",
                product_id=product_id,
                status_code=response.status_code,
                content_kb=len(content) / 1024,
            )

            return content

        except requests.RequestException as e:
            logger.error(
                "Request failed for Amazon India",
                product_id=product_id,
                url=url,
                error=str(e),
            )
            return None

    # --------------------------------------------------
    # ✅ Application-level retry logic
    # --------------------------------------------------
    def scrape_with_retry(
        self,
        product_id: str,
        max_attempts: int = 3
    ) -> Optional[str]:
        """
        Scrape product page with application-level retry logic.
        
        Args:
            product_id: ASIN of the product
            max_attempts: Maximum number of retry attempts
            
        Returns:
            HTML content as string or None if all attempts failed
        """
        for attempt in range(1, max_attempts + 1):
            logger.info(
                "Scrape attempt for Amazon India",
                attempt=attempt,
                max_attempts=max_attempts,
                product_id=product_id,
            )

            html = self.scrape_product(product_id)

            if html:
                logger.info(
                    "Scrape succeeded",
                    attempt=attempt,
                    product_id=product_id,
                )
                return html

            if attempt < max_attempts:
                self.header_manager.rotate_user_agent()

                backoff_seconds = self.request_delay * (2 ** (attempt - 1))
                logger.warning(
                    "Scrape failed, retrying",
                    attempt=attempt,
                    backoff_seconds=backoff_seconds,
                    product_id=product_id,
                )
                time.sleep(backoff_seconds)

        logger.error(
            "All scrape attempts failed for Amazon India",
            product_id=product_id,
            attempts=max_attempts,
        )
        return None

    # --------------------------------------------------
    # Scrape multiple products
    # --------------------------------------------------
    def scrape_multiple_products(
        self, product_ids: List[str]
    ) -> Dict[str, Optional[str]]:
        """
        Scrape multiple product pages from Amazon India.
        
        Args:
            product_ids: List of ASINs to scrape
            
        Returns:
            Dictionary mapping ASIN to HTML content (or None if failed)
        """
        results: Dict[str, Optional[str]] = {}

        for idx, product_id in enumerate(product_ids, start=1):
            logger.info(
                "Scraping product from Amazon India",
                current=idx,
                total=len(product_ids),
                product_id=product_id,
            )

            results[product_id] = self.scrape_with_retry(
                product_id, max_attempts=3
            )

            if idx < len(product_ids):
                time.sleep(self._get_delay() * 1.5)

        return results