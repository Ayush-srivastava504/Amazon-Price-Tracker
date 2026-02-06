from typing import Dict, Any
from datetime import datetime
import re

def sanitize_product_data(product_data: Dict, validation_rules: Dict) -> Dict:
    """
    Sanitize product data by trimming strings, converting types, etc.

    Args:
        product_data: Raw product data
        validation_rules: Validation rules for reference

    Returns:
        Sanitized product data
    """
    sanitized = product_data.copy()

    # Trim string fields
    string_fields = ['title', 'brand', 'category', 'category_path', 'availability']
    for field in string_fields:
        if field in sanitized and isinstance(sanitized[field], str):
            sanitized[field] = sanitized[field].strip()

    # Truncate title if too long
    if 'title' in sanitized:
        max_len = validation_rules.get('title', {}).get('max_length', 500)
        if len(sanitized['title']) > max_len:
            sanitized['title'] = sanitized['title'][:max_len-3] + '...'

    # Convert numeric fields
    numeric_fields = ['current_price', 'original_price', 'discount_percentage', 'rating', 'review_count']
    for field in numeric_fields:
        if field in sanitized and sanitized[field] is not None:
            try:
                if field == 'review_count':
                    sanitized[field] = int(float(sanitized[field]))
                else:
                    sanitized[field] = float(sanitized[field])
            except (ValueError, TypeError):
                sanitized[field] = None

    # Normalize availability
    if 'availability' in sanitized and isinstance(sanitized['availability'], str):
        avail = sanitized['availability'].lower()
        if 'in stock' in avail:
            sanitized['availability'] = 'in_stock'
        elif 'out of stock' in avail:
            sanitized['availability'] = 'out_of_stock'
        elif 'available' in avail:
            sanitized['availability'] = 'available'
        else:
            # If not matching, set to 'unknown'
            sanitized['availability'] = 'unknown'

    # Ensure timestamp is ISO format string
    if 'timestamp' in sanitized:
        if isinstance(sanitized['timestamp'], datetime):
            sanitized['timestamp'] = sanitized['timestamp'].isoformat()

    # Remove emojis from text fields if configured
    if validation_rules.get('text_fields', {}).get('remove_emojis', False):
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        text_fields = ['title', 'brand', 'category', 'category_path']
        for field in text_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = emoji_pattern.sub(r'', sanitized[field])

    return sanitized