"""Data sanitization and cleaning functions."""
from typing import Dict, Any, List, Optional
import re
import structlog

logger = structlog.get_logger()

class DataSanitizer:
    """Sanitize and clean input data."""
    
    @staticmethod
    def sanitize_string(value: Any, max_length: int = 500) -> Optional[str]:
        """Sanitize string fields."""
        if value is None:
            return None
        
        # Convert to string
        string_value = str(value)
        
        # Remove excessive whitespace
        string_value = ' '.join(string_value.split())
        
        # Truncate if too long
        if len(string_value) > max_length:
            logger.warning("String truncated", 
                          original_length=len(string_value),
                          max_length=max_length)
            string_value = string_value[:max_length]
        
        return string_value
    
    @staticmethod
    def sanitize_price(price: Any) -> Optional[float]:
        """Sanitize price field."""
        if price is None:
            return None
        
        try:
            # Remove currency symbols and thousand separators
            if isinstance(price, str):
                price_clean = re.sub(r'[^\d\.]', '', price)
                return float(price_clean)
            else:
                return float(price)
        except (ValueError, TypeError):
            logger.warning("Failed to sanitize price", price=price)
            return None
    
    @staticmethod
    def sanitize_rating(rating: Any) -> Optional[float]:
        """Sanitize rating field."""
        if rating is None:
            return None
        
        try:
            rating_float = float(rating)
            
            # Ensure rating is between 0 and 5
            if rating_float < 0:
                return 0.0
            elif rating_float > 5:
                return 5.0
            else:
                return round(rating_float, 1)  # Round to 1 decimal
            
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def sanitize_product_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize entire product data dictionary."""
        sanitized = data.copy()
        
        # String fields
        string_fields = ['title', 'seller', 'availability']
        for field in string_fields:
            if field in sanitized:
                sanitized[field] = DataSanitizer.sanitize_string(sanitized[field])
        
        # Numeric fields
        if 'price' in sanitized:
            sanitized['price'] = DataSanitizer.sanitize_price(sanitized['price'])
        
        if 'rating' in sanitized:
            sanitized['rating'] = DataSanitizer.sanitize_rating(sanitized['rating'])
        
        # Ensure product_id is uppercase
        if 'product_id' in sanitized and sanitized['product_id']:
            sanitized['product_id'] = sanitized['product_id'].upper().strip()
        
        logger.debug("Data sanitized", product_id=sanitized.get('product_id'))
        return sanitized