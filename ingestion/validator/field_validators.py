import re
from typing import Tuple, Optional, Any
from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)

def validate_asin(asin: str, rules: dict) -> Tuple[bool, Optional[str]]:
    """Validate ASIN format"""
    if not asin or not isinstance(asin, str):
        return False, "ASIN must be a non-empty string"

    pattern = rules.get('pattern', r'^[A-Z0-9]{10}$')
    if not re.match(pattern, asin.strip()):
        return False, f"Invalid ASIN format: {asin}. Must be 10 alphanumeric characters."

    return True, None

def validate_url(url: str, rules: dict) -> Tuple[bool, Optional[str]]:
    """Validate Amazon URL"""
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    pattern = rules.get('pattern', r'^https?://(www\.)?amazon\.(com|co\.uk|de|fr|it|es|ca|co\.jp)/')
    if not re.search(pattern, url, re.IGNORECASE):
        return False, f"URL must be a valid Amazon URL: {url}"

    return True, None

def validate_title(title: str, rules: dict) -> Tuple[bool, Optional[str]]:
    """Validate product title"""
    if not title or not isinstance(title, str):
        return False, "Title must be a non-empty string"

    title = title.strip()
    min_len = rules.get('min_length', 3)
    max_len = rules.get('max_length', 500)

    if len(title) < min_len:
        return False, f"Title too short (min {min_len} characters): {title}"

    if len(title) > max_len:
        logger.warning(f"Title too long ({len(title)} > {max_len}), will be truncated")

    return True, None

def validate_price(price: Any, rules: dict) -> Tuple[bool, Optional[str]]:
    """Validate price value"""
    try:
        price_val = float(price)
    except (ValueError, TypeError):
        return False, f"Price must be a number: {price}"

    min_price = rules.get('min', 0.01)
    max_price = rules.get('max', 1000000.0)

    if price_val < min_price:
        return False, f"Price too low ({price_val} < {min_price})"

    if price_val > max_price:
        return False, f"Price too high ({price_val} > {max_price})"

    if math.isnan(price_val) or math.isinf(price_val):
        return False, f"Invalid price value: {price_val}"

    return True, None

def validate_discount(discount: Any, rules: dict) -> Tuple[bool, Optional[str]]:
    """Validate discount percentage"""
    try:
        discount_val = float(discount)
    except (ValueError, TypeError):
        return False, f"Discount must be a number: {discount}"

    min_discount = rules.get('min', 0.0)
    max_discount = rules.get('max', 100.0)

    if discount_val < min_discount:
        return False, f"Discount too low ({discount_val} < {min_discount})"

    if discount_val > max_discount:
        return False, f"Discount too high ({discount_val} > {max_discount})"

    return True, None

def validate_rating(rating: Any, rules: dict) -> Tuple[bool, Optional[str]]:
    """Validate product rating"""
    try:
        rating_val = float(rating)
    except (ValueError, TypeError):
        return False, f"Rating must be a number: {rating}"

    min_rating = rules.get('min', 0.0)
    max_rating = rules.get('max', 5.0)

    if rating_val < min_rating:
        return False, f"Rating too low ({rating_val} < {min_rating})"

    if rating_val > max_rating:
        return False, f"Rating too high ({rating_val} > {max_rating})"

    return True, None

def validate_review_count(review_count: Any, rules: dict) -> Tuple[bool, Optional[str]]:
    """Validate review count"""
    try:
        count_val = int(review_count)
    except (ValueError, TypeError):
        return False, f"Review count must be an integer: {review_count}"

    min_count = rules.get('min', 0)
    max_count = rules.get('max', 10000000)

    if count_val < min_count:
        return False, f"Review count too low ({count_val} < {min_count})"

    if count_val > max_count:
        logger.warning(f"Review count very high: {count_val}")
        # Still valid, just log warning

    return True, None

def validate_timestamp(timestamp: Any) -> Tuple[bool, Optional[str]]:
    """Validate timestamp format"""
    if not timestamp:
        return False, "Timestamp is required"

    try:
        # Try parsing ISO format
        if isinstance(timestamp, str):
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, datetime):
            # Already a datetime object
            pass
        else:
            return False, f"Invalid timestamp type: {type(timestamp)}"
    except (ValueError, TypeError) as e:
        return False, f"Invalid timestamp format: {timestamp}. Error: {e}"

    return True, None

def validate_availability(availability: str) -> Tuple[bool, Optional[str]]:
    """Validate availability status"""
    # This is a soft validation, just log if unknown
    valid_statuses = ['in_stock', 'out_of_stock', 'available', 'unknown', 'limited']

    if availability not in valid_statuses:
        logger.warning(f"Unknown availability status: {availability}")
        # Still valid, just not standardized

    return True, None