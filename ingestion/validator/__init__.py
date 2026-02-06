from .base_validator import DataValidator
from .sanitizers import sanitize_product_data

__all__ = ['DataValidator', 'validate_product_data', 'sanitize_data', 'validate_and_sanitize']

# Convenience functions
def validate_product_data(product_data: dict, config: dict = None) -> bool:
    validator = DataValidator(config)
    is_valid, _ = validator.validate_product_data(product_data)
    return is_valid

def sanitize_data(product_data: dict, config: dict = None) -> dict:
    validator = DataValidator(config)
    return validator.sanitize_product_data(product_data)

def validate_and_sanitize(product_data: dict, config: dict = None) -> tuple:
    validator = DataValidator(config)
    is_valid, errors = validator.validate_product_data(product_data)
    if is_valid:
        sanitized = validator.sanitize_product_data(product_data)
    else:
        sanitized = product_data.copy()
    return is_valid, sanitized, errors