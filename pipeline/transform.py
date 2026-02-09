import logging
import json
from typing import List, Dict, Any, Optional
import re
from decimal import Decimal
from datetime import datetime


logger = logging.getLogger(__name__)

def parse_price(price_text: str) -> Optional[float]:     #Extract numeric price from text. Handles ₹1,234.56, $99.99, etc.
    if not price_text:
        return None
    
    try:
        # Remove everything except digits and decimal point
        clean = re.sub(r'[^\d\.]', '', price_text)
        if clean:
            # Convert to float, but be careful with precision
            return float(Decimal(clean))
    except (ValueError, TypeError) as e:
        logger.debug(f"Could not parse price '{price_text}': {e}")
    
    return None

def transform_product_record(raw_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:     # Transform raw JSON into clean, structured product data.
     # Sometimes raw_record is a string (from DB), sometimes dict
    if isinstance(raw_record, str):
        try:
            data = json.loads(raw_record)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {raw_record[:100]}...")
            return None
    else:
        data = raw_record
    
    # Extract product ID - critical field
    product_id = data.get('product_id') or data.get('asin')
    if not product_id:
        logger.warning("Record missing product_id, skipping")
        return None
    
    # Parse price - this is the most important field for us
    price = None
    price_raw = data.get('price')
    
    if isinstance(price_raw, (int, float)):
        price = float(price_raw)
    elif isinstance(price_raw, str):
        price = parse_price(price_raw)
    elif 'price_text' in data:  # Alternative field name
        price = parse_price(data.get('price_text'))
    
    # Basic validation - price should be reasonable if present
    if price is not None:
        if price <= 0:
            logger.warning(f"Product {product_id} has non-positive price: {price}")
            price = None
        elif price > 10000000:  # 10 million INR - sanity check
            logger.warning(f"Product {product_id} has suspiciously high price: {price}")
            price = None
    
    # Clean title
    title = data.get('title', '').strip()
    if title and len(title) > 500:
        title = title[:497] + "..."  # Truncate
    
    # Determine availability
    availability_raw = data.get('availability', '').lower()
    if 'out of stock' in availability_raw or 'unavailable' in availability_raw:
        availability = 'out_of_stock'
    elif 'in stock' in availability_raw:
        availability = 'in_stock'
    else:
        availability = 'unknown'
    
    # If out of stock, price might be null - that's OK
    if availability == 'out_of_stock':
        price = None
    
    # Build transformed record
    transformed = {
        'product_id': str(product_id).upper().strip(),
        'title': title,
        'price': price,
        'currency': data.get('currency', 'INR'),
        'availability': availability,
        'seller': data.get('seller', '').strip()[:100],
        'rating': data.get('rating'),  # Keep as is, will validate in quality checks
        'source_url': data.get('url', f"https://amazon.in/dp/{product_id}"),
        'scraped_at': data.get('timestamp') or data.get('_extracted_at'),
        'transformed_at': datetime.utcnow().isoformat(),
        '_raw_id': data.get('_raw_id')  # Keep link to raw data
    }
    
    return transformed

def transform_batch(raw_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:      #Transform a batch of raw record
    transformed = []
    failed = 0
    
    for raw in raw_records:
        result = transform_product_record(raw)
        if result:
            transformed.append(result)
        else:
            failed += 1
    
    if failed > 0:
        logger.warning(f"Failed to transform {failed}/{len(raw_records)} records")
    
    logger.info(f"Transformed {len(transformed)} records successfully")
    return transformed