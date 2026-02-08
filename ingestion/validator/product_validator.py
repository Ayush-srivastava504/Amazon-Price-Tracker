"""Main product validator orchestrating all validation rules."""
from typing import Dict, Any, Tuple, Optional
import structlog

from .base_validator import BaseValidator, ValidatorChain
from .field_validators import FieldValidator
from .business_rules import BusinessRuleValidator
from .sanitizers import DataSanitizer

logger = structlog.get_logger()

class ProductValidator(BaseValidator):
    """Orchestrates all validation and sanitization for product data."""
    
    def __init__(self):
        self.field_validator = FieldValidator()
        self.business_validator = BusinessRuleValidator()
        self.sanitizer = DataSanitizer()
        
        # Create validation chain
        self.validator_chain = ValidatorChain()
        self._setup_validation_chain()
    
    def _setup_validation_chain(self):
        """Setup validation chain with specific validators."""
        # Add field validators
        self.validator_chain.add_validator(FieldValidationAdapter(self.field_validator))
        
        # Add business rule validators
        self.validator_chain.add_validator(BusinessValidationAdapter(self.business_validator))
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate product data using the validation chain.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # First, sanitize the data
        sanitized_data = self.sanitize(data)
        
        # Run validation chain
        is_valid, errors = self.validator_chain.validate(sanitized_data)
        
        if not is_valid:
            error_message = "; ".join(errors)
            logger.error("Validation failed", 
                        product_id=sanitized_data.get('product_id'),
                        errors=error_message)
            return False, error_message
        
        logger.info("Validation passed", product_id=sanitized_data.get('product_id'))
        return True, None
    
    def sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize product data."""
        return self.sanitizer.sanitize_product_data(data)

# Adapter classes to make validators compatible with BaseValidator interface
class FieldValidationAdapter(BaseValidator):
    """Adapter for FieldValidator."""
    
    def __init__(self, field_validator: FieldValidator):
        self.field_validator = field_validator
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Run field validations."""
        # Validate individual fields
        validations = [
            self.field_validator.validate_asin(data.get('product_id')),
            self.field_validator.validate_price(data.get('price')),
            self.field_validator.validate_title(data.get('title')),
            self.field_validator.validate_timestamp(data.get('timestamp')),
            self.field_validator.validate_rating(data.get('rating'))
        ]
        
        for is_valid, error in validations:
            if not is_valid:
                return False, error
        
        return True, None
    
    def sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data  # Field validator doesn't sanitize

class BusinessValidationAdapter(BaseValidator):
    """Adapter for BusinessRuleValidator."""
    
    def __init__(self, business_validator: BusinessRuleValidator):
        self.business_validator = business_validator
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Run business rule validations."""
        # Check required fields
        is_valid, error = self.business_validator.validate_required_fields(data)
        if not is_valid:
            return False, error
        
        # Check price bounds
        is_valid, error = self.business_validator.validate_price_bounds(data)
        if not is_valid:
            return False, error
        
        # Check availability rules
        is_valid, error = self.business_validator.validate_product_availability(data)
        if not is_valid:
            return False, error
        
        # Check data freshness
        is_valid, error = self.business_validator.validate_data_freshness(data)
        if not is_valid:
            return False, error
        
        return True, None
    
    def sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data  # Business validator doesn't sanitize
    