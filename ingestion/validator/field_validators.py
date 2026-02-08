"""Field-level validators for specific data types."""
import re
from typing import Dict, Any, Tuple, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()

class FieldValidator:
    """Validators for individual fields."""
    
    # Amazon ASIN pattern: 10 characters, starting with B, 0-9 or A-Z
    ASIN_PATTERN = r'^[A-Z0-9]{10}$'
    
    @staticmethod
    def validate_asin(product_id: str) -> Tuple[bool, Optional[str]]:
        """Validate Amazon Standard Identification Number."""
        if not product_id:
            return False, "ASIN cannot be empty"
        
        if not re.match(FieldValidator.ASIN_PATTERN, product_id):
            return False, f"Invalid ASIN format: {product_id}"
        
        return True, None
    
    @staticmethod
    def validate_price(price: Any) -> Tuple[bool, Optional[str]]:
        """Validate price field."""
        if price is None:
            return True, None  # Price can be null for out-of-stock items
        
        try:
            price_float = float(price)
            
            # Basic sanity checks
            if price_float < 0:
                return False, "Price cannot be negative"
            
            if price_float == 0:
                logger.warning("Price is zero", price=price_float)
                return True, "Price is zero"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, f"Invalid price format: {price}"
    
    @staticmethod
    def validate_title(title: str) -> Tuple[bool, Optional[str]]:
        """Validate product title."""
        if not title or not title.strip():
            return False, "Title cannot be empty"
        
        title_str = str(title).strip()
        
        if len(title_str) > 500:
            return False, f"Title too long: {len(title_str)} characters"
        
        if len(title_str) < 2:
            return False, "Title too short"
        
        # Check for suspicious patterns (e.g., only special characters)
        if re.match(r'^[^a-zA-Z0-9]+$', title_str):
            return False, "Title contains only special characters"
        
        return True, None
    
    @staticmethod
    def validate_timestamp(timestamp: Any) -> Tuple[bool, Optional[str]]:
        """Validate timestamp."""
        if timestamp is None:
            return False, "Timestamp cannot be null"
        
        try:
            ts = float(timestamp)
            
            # Check if timestamp is reasonable (not in future and not before 2000)
            current_ts = datetime.now().timestamp()
            
            if ts > current_ts + 3600:  # 1 hour in future (allow some clock skew)
                return False, f"Timestamp is in future: {timestamp}"
            
            if ts < 946684800:  # Before 2000-01-01
                return False, f"Timestamp is too old: {timestamp}"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, f"Invalid timestamp: {timestamp}"
    
    @staticmethod
    def validate_rating(rating: Any) -> Tuple[bool, Optional[str]]:
        """Validate product rating."""
        if rating is None:
            return True, None  # Rating can be null
        
        try:
            rating_float = float(rating)
            
            if rating_float < 0 or rating_float > 5:
                return False, f"Rating out of bounds (0-5): {rating_float}"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, f"Invalid rating format: {rating}"