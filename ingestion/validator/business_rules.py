"""Business rule validators for domain-specific logic."""
from typing import Dict, Any, Tuple, Optional
import structlog

logger = structlog.get_logger()

class BusinessRuleValidator:
    """Validate business rules and constraints."""
    
    def __init__(self):
        self.price_thresholds = {
            'min_price': 0.01,
            'max_price': 1000000,
            'suspicious_price': 999999.99  # Often used as placeholder
        }
        
        self.required_fields = ['product_id', 'title', 'price', 'timestamp']
        
    def validate_required_fields(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Check all required fields are present."""
        missing_fields = []
        
        for field in self.required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"
        
        return True, None
    
    def validate_price_bounds(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate price is within acceptable business bounds."""
        price = data.get('price')
        
        if price is None:
            return True, None  # Price can be null for out-of-stock
        
        try:
            price_float = float(price)
            
            # Check for suspicious placeholder prices
            if price_float == self.price_thresholds['suspicious_price']:
                logger.warning("Suspicious price detected", price=price_float)
                return False, "Suspicious price (placeholder value)"
            
            # Check min/max bounds
            if price_float < self.price_thresholds['min_price']:
                return False, f"Price below minimum: {price_float}"
            
            if price_float > self.price_thresholds['max_price']:
                return False, f"Price above maximum: {price_float}"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, f"Invalid price for business validation: {price}"
    
    def validate_product_availability(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate availability rules."""
        availability = data.get('availability', '').lower()
        price = data.get('price')
        
        # If product is in stock, price should not be null
        if availability in ['in_stock', 'available'] and price is None:
            return False, "In-stock product must have a price"
        
        # If product is out of stock, price can be null
        if availability in ['out_of_stock', 'unavailable']:
            logger.info("Product out of stock", product_id=data.get('product_id'))
            return True, None
        
        return True, None
    
    def validate_data_freshness(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Ensure data is not too old."""
        from datetime import datetime
        
        timestamp = data.get('timestamp')
        
        if not timestamp:
            return False, "Timestamp missing for freshness check"
        
        try:
            data_time = datetime.fromtimestamp(float(timestamp))
            current_time = datetime.now()
            
            # Data should be less than 24 hours old
            time_diff = current_time - data_time
            if time_diff.total_seconds() > 86400:  # 24 hours
                return False, f"Data is too old: {time_diff}"
            
            return True, None
            
        except (ValueError, TypeError):
            return False, f"Invalid timestamp for freshness check: {timestamp}"