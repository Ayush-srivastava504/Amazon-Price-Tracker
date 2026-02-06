import re
import json
import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

def parse_product_page(html: str, asin: str, url: str) -> Dict:
    """Parse HTML to extract product information"""
    soup = BeautifulSoup(html, 'html.parser')
    
    product_data = {
        'asin': asin,
        'url': url,
        'timestamp': datetime.utcnow().isoformat(),
        'scraped_at': datetime.utcnow().isoformat()
    }
    
    # Extract title
    title = extract_title(soup)
    if title:
        product_data['title'] = title
        
    # Extract price
    price_data = extract_price(soup)
    product_data.update(price_data)
    
    # Extract other metadata
    metadata = extract_metadata(soup)
    product_data.update(metadata)
    
    # Extract availability
    availability = extract_availability(soup)
    product_data['availability'] = availability
    
    # Extract ratings
    ratings = extract_ratings(soup)
    product_data.update(ratings)
    
    # Extract product details
    details = extract_product_details(soup)
    product_data['details'] = details
    
    return product_data

def extract_title(soup: BeautifulSoup) -> Optional[str]:
    """Extract product title"""
    selectors = [
        '#productTitle',
        'h1.a-size-large',
        'span#productTitle',
        'h1.a-text-bold'
    ]
    
    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            return element.get_text(strip=True)
    return None

def extract_price(soup: BeautifulSoup) -> Dict:
    """Extract price information"""
    price_data = {
        'current_price': None,
        'original_price': None,
        'currency': 'USD',
        'discount_percentage': None
    }
    
    # Try different price selectors
    price_selectors = [
        'span.a-price-whole',
        'span#priceblock_ourprice',
        'span#priceblock_dealprice',
        'span.a-color-price',
        'span.offer-price'
    ]
    
    for selector in price_selectors:
        price_element = soup.select_one(selector)
        if price_element:
            price_text = price_element.get_text(strip=True)
            price = extract_float_from_text(price_text)
            if price:
                price_data['current_price'] = price
                break
    
    # Try to get original price for discounts
    original_selectors = [
        'span.a-text-strike',
        'span.a-price.a-text-price'
    ]
    
    for selector in original_selectors:
        original_element = soup.select_one(selector)
        if original_element:
            original_text = original_element.get_text(strip=True)
            original_price = extract_float_from_text(original_text)
            if original_price:
                price_data['original_price'] = original_price
                
                # Calculate discount
                if price_data['current_price']:
                    discount = ((original_price - price_data['current_price']) / original_price) * 100
                    price_data['discount_percentage'] = round(discount, 2)
                break
    
    return price_data

def extract_float_from_text(text: str) -> Optional[float]:
    """Extract float from text with currency symbols"""
    match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def extract_metadata(soup: BeautifulSoup) -> Dict:
    """Extract product metadata"""
    metadata = {}
    
    # Extract brand
    brand_selectors = [
        'a#bylineInfo',
        'a#brand',
        'tr.po-brand td.a-span9'
    ]
    
    for selector in brand_selectors:
        element = soup.select_one(selector)
        if element:
            metadata['brand'] = element.get_text(strip=True)
            break
    
    # Extract category
    breadcrumb = soup.select_one('#wayfinding-breadcrumbs_feature_div')
    if breadcrumb:
        categories = [a.get_text(strip=True) for a in breadcrumb.select('a')]
        metadata['category'] = categories[-1] if categories else None
        metadata['category_path'] = ' > '.join(categories)
    
    return metadata

def extract_availability(soup: BeautifulSoup) -> str:
    """Extract availability status"""
    availability_selectors = [
        '#availability span',
        '#availability .a-color-success',
        '#outOfStock'
    ]
    
    for selector in availability_selectors:
        element = soup.select_one(selector)
        if element:
            text = element.get_text(strip=True).lower()
            if 'out of stock' in text:
                return 'out_of_stock'
            elif 'in stock' in text:
                return 'in_stock'
            elif 'available' in text:
                return 'available'
    
    return 'unknown'

def extract_ratings(soup: BeautifulSoup) -> Dict:
    """Extract rating information"""
    ratings = {
        'rating': None,
        'review_count': None
    }
    
    # Rating
    rating_element = soup.select_one('span[data-hook="rating-out-of-text"]')
    if rating_element:
        rating_text = rating_element.get_text(strip=True)
        match = re.search(r'([\d.]+) out of 5', rating_text)
        if match:
            ratings['rating'] = float(match.group(1))
    
    # Review count
    count_element = soup.select_one('span[data-hook="total-review-count"]')
    if count_element:
        count_text = count_element.get_text(strip=True)
        match = re.search(r'([\d,]+)', count_text)
        if match:
            ratings['review_count'] = int(match.group(1).replace(',', ''))
    
    return ratings

def extract_product_details(soup: BeautifulSoup) -> Dict:
    """Extract additional product details"""
    details = {}
    
    # Try to get from technical details table
    tech_table = soup.select_one('#productDetails_techSpec_section_1')
    if tech_table:
        rows = tech_table.select('tr')
        for row in rows:
            th = row.select_one('th')
            td = row.select_one('td')
            if th and td:
                key = th.get_text(strip=True).lower().replace(' ', '_')
                value = td.get_text(strip=True)
                details[key] = value
    
    return details