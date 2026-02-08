"""HTML parser to extract structured product data from Amazon pages."""
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import re
import structlog

logger = structlog.get_logger()

class AmazonParser:
    """Parse Amazon HTML to extract product information."""
    
    def __init__(self):
        self.price_patterns = [
            r'\$(\d+\.\d{2})',
            r'(\d+\.\d{2})\s*USD',
            r'price\":\"\$\s*(\d+\.\d{2})'
        ]
        
    def parse_product_page(self, html: str, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Parse HTML and extract product data.
        
        Args:
            html: HTML content
            product_id: Amazon product ID
            
        Returns:
            Dictionary with product data or None if parsing fails
        """
        if not html:
            return None
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract product title
            title_element = soup.find("span", {"id": "productTitle"})
            title = title_element.get_text(strip=True) if title_element else None
            
            # Extract price using multiple strategies
            price = self._extract_price(soup)
            
            # Extract availability
            availability = self._extract_availability(soup)
            
            # Extract rating
            rating = self._extract_rating(soup)
            
            # Extract seller
            seller = self._extract_seller(soup)
            
            product_data = {
                "product_id": product_id,
                "title": title,
                "price": price,
                "currency": "USD",
                "availability": availability,
                "rating": rating,
                "seller": seller,
                "timestamp": time.time()
            }
            
            logger.debug("Parsed product data", product_id=product_id)
            return product_data
            
        except Exception as e:
            logger.error("Failed to parse HTML", product_id=product_id, error=str(e))
            return None
    
    def _extract_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract price using multiple fallback strategies."""
        # Strategy 1: Direct price element
        price_element = soup.find("span", {"class": "a-price-whole"})
        if price_element:
            price_text = price_element.get_text(strip=True).replace(',', '')
            try:
                return float(price_text)
            except ValueError:
                pass
        
        # Strategy 2: Search in JSON-LD
        script_tag = soup.find("script", {"type": "application/ld+json"})
        if script_tag:
            import json
            try:
                data = json.loads(script_tag.string)
                if isinstance(data, dict) and 'offers' in data:
                    price = data['offers'].get('price')
                    if price:
                        return float(price)
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Strategy 3: Regex patterns
        html_str = str(soup)
        for pattern in self.price_patterns:
            match = re.search(pattern, html_str)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        
        return None
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """Extract availability status."""
        # Simplified - expand based on actual HTML structure
        availability_elem = soup.find("div", {"id": "availability"})
        if availability_elem:
            text = availability_elem.get_text(strip=True).lower()
            if "in stock" in text:
                return "in_stock"
            elif "out of stock" in text:
                return "out_of_stock"
        return "unknown"
    
    def _extract_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract product rating."""
        rating_elem = soup.find("span", {"class": "a-icon-alt"})
        if rating_elem:
            text = rating_elem.get_text(strip=True)
            match = re.search(r'(\d\.\d)', text)
            if match:
                return float(match.group(1))
        return None
    
    def _extract_seller(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract seller information."""
        seller_elem = soup.find("a", {"id": "sellerProfileTriggerId"})
        return seller_elem.get_text(strip=True) if seller_elem else None