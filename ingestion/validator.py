
# Simple validation for scraped product data.

import re
from typing import Dict, Any, Tuple
import structlog

logger = structlog.get_logger()

def validate_product(data: Dict[str, Any]) -> Tuple[bool, str]:   #  Quick sanity checks

    if not data:
        return False, "Empty data"
    
    # Must have product ID
    pid = data.get('product_id')
    if not pid:
        return False, "Missing product_id"
    
    # Basic ASIN format check (Amazon Standard Identification Number)
    if not re.match(r'^[A-Z0-9]{10}$', str(pid)):
        return False, f"Invalid ASIN format: {pid}"
    
    # Price validation (if present)
    price = data.get('price')
    if price is not None:
        try:
            price_float = float(price)
            if price_float <= 0:
                return False, f"Price must be positive: {price}"
            if price_float > 10000000:  # 10 million INR - sanity check
                return False, f"Suspiciously high price: {price}"
        except (ValueError, TypeError):
            return False, f"Invalid price: {price}"
    
    # Title validation
    title = data.get('title')
    if not title or len(str(title).strip()) < 3:
        return False, f"Title too short: {title}"
    
    # If product is in stock, should have a price
    if data.get('availability') == 'in_stock' and price is None:
        return False, "In-stock item missing price"
    
    # Rating validation if present
    rating = data.get('rating')
    if rating is not None:
        try:
            rating_float = float(rating)
            if not 0 <= rating_float <= 5:
                return False, f"Rating out of range: {rating}"
        except (ValueError, TypeError):
            return False, f"Invalid rating: {rating}"
    
    return True, "OK"

def clean_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
    cleaned = data.copy()
    
    # Clean title
    if 'title' in cleaned and cleaned['title']:
        cleaned['title'] = str(cleaned['title']).strip()
        if len(cleaned['title']) > 500:
            cleaned['title'] = cleaned['title'][:497] + "..."
    
    # Clean seller
    if 'seller' in cleaned and cleaned['seller']:
        cleaned['seller'] = str(cleaned['seller']).strip()
    
    # Uppercase product ID
    if 'product_id' in cleaned:
        cleaned['product_id'] = str(cleaned['product_id']).upper().strip()
    
    # Round price to 2 decimal places
    if 'price' in cleaned and cleaned['price']:
        try:
            cleaned['price'] = round(float(cleaned['price']), 2)
        except (ValueError, TypeError):
            cleaned['price'] = None
    
    return cleaned

# Simple helper for batch validation
def validate_batch(products: list) -> Tuple[list, list]:
    valid = []
    invalid = []
    
    for product in products:
        is_ok, msg = validate_product(product)
        if is_ok:
            valid.append(product)
        else:
            logger.warning(f"Invalid product {product.get('product_id')}: {msg}")
            invalid.append(product)
    
    logger.info(f"Validation: {len(valid)} valid, {len(invalid)} invalid")
    return valid, invalid