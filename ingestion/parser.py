# Parses Amazon product pages. Extracts price, title, etc.

from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import re
import json
import time
import structlog

logger = structlog.get_logger()

class AmazonParser:      # Turns Amazon HTML into structured data
    
    def parse_product(self, html: str, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Main parsing function. Returns None if parsing fails.
        Output is a plain dict ready for JSON.dumps().
        """
        if not html or not html.strip():
            logger.warning(f"No HTML for {product_id}")
            return None
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Product title - critical field
            title_elem = soup.find("span", id="productTitle")
            title = title_elem.get_text(strip=True) if title_elem else None
            
            # Price - the main thing we care about
            price = self._extract_price(soup)
            
            # Availability
            availability = self._check_availability(soup)
            
            # Rating (optional)
            rating = self._extract_rating(soup)
            
            # Seller (optional)
            seller_elem = soup.find("a", id="sellerProfileTriggerId")
            seller = seller_elem.get_text(strip=True) if seller_elem else None
            
            # Build result - plain dict only, no custom objects
            result = {
                "product_id": product_id,
                "title": title,
                "price": price,
                "currency": "INR",  # Hardcoded for Amazon.in
                "availability": availability,
                "rating": rating,
                "seller": seller,
                "scraped_at": time.time(),
                "url": f"https://www.amazon.in/dp/{product_id}"
            }
            
            # Clean up None values for better JSON
            result = {k: v for k, v in result.items() if v is not None}
            
            logger.debug(f"Parsed {product_id}, price={price}")
            return result
            
        except Exception as e:
            logger.error(f"Parse failed for {product_id}: {e}")
            return None
    
    def _extract_price(self, soup) -> Optional[float]:
        """Try different ways to find the price. Amazon changes this often."""
        
        # Method 1: Modern price element
        price_elem = soup.find("span", class_="a-price-whole")
        if price_elem:
            price_text = price_elem.get_text(strip=True).replace(',', '')
            try:
                return float(price_text)
            except:
                pass
        
        # Method 2: JSON-LD data (often more reliable)
        script = soup.find("script", type="application/ld+json")
        if script:
            try:
                data = json.loads(script.string)
                # Navigate the JSON structure
                if isinstance(data, dict):
                    offers = data.get('offers')
                    if isinstance(offers, dict):
                        price = offers.get('price')
                        if price:
                            return float(price)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # Method 3: Old-style price block
        price_selectors = [
            "span#priceblock_ourprice",
            "span#priceblock_dealprice",
            "span.a-price",
            "span.a-color-price"
        ]
        
        for selector in price_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # Extract numbers from text like "₹1,234.56"
                numbers = re.findall(r'[\d,]+\.?\d*', text)
                if numbers:
                    try:
                        return float(numbers[0].replace(',', ''))
                    except:
                        continue
        
        return None
    
    def _check_availability(self, soup) -> str:
        """Check if product is in stock."""
        # Look for availability message
        availability_elem = soup.find("div", id="availability")
        if availability_elem:
            text = availability_elem.get_text(strip=True).lower()
            if "out of stock" in text or "currently unavailable" in text:
                return "out_of_stock"
            if "in stock" in text:
                return "in_stock"
        
        # Check add to cart button as fallback
        cart_button = soup.find("input", id="add-to-cart-button")
        if cart_button:
            return "in_stock"
        
        return "unknown"
    
    def _extract_rating(self, soup) -> Optional[float]:
        """Extract star rating if available."""
        rating_elem = soup.find("span", class_="a-icon-alt")
        if rating_elem:
            text = rating_elem.get_text(strip=True)
            # Looks like "4.3 out of 5 stars"
            match = re.search(r'(\d\.\d)', text)
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass
        return None