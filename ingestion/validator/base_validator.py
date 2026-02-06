import logging
from typing import Dict, List, Tuple, Optional, Any

from .field_validators import (
    validate_asin, validate_url, validate_title, validate_price,
    validate_discount, validate_rating, validate_review_count,
    validate_timestamp, validate_availability
)
from .business_rules import validate_business_logic
from .sanitizers import sanitize_product_data

logger = logging.getLogger(__name__)

class DataValidator:
    """Validates scraped product data"""

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict:
        """Load validation rules from config or use defaults"""
        default_rules = {
            'price': {
                'min': 0.01,
                'max': 1000000.0,
                'required': True
            },
            'title': {
                'min_length': 3,
                'max_length': 500,
                'required': True
            },
            'asin': {
                'pattern': r'^[A-Z0-9]{10}$',
                'required': True
            },
            'url': {
                'pattern': r'^https?://(www\.)?amazon\.(com|co\.uk|de|fr|it|es|ca|co\.jp)/',
                'required': True
            },
            'rating': {
                'min': 0.0,
                'max': 5.0
            },
            'review_count': {
                'min': 0,
                'max': 10000000
            },
            'discount_percentage': {
                'min': 0.0,
                'max': 100.0
            }
        }

        # Merge with config if provided
        if self.config.get('validation'):
            config_rules = self.config['validation']
            for key in default_rules:
                if key in config_rules:
                    default_rules[key].update(config_rules[key])

        return default_rules

    def validate_product_data(self, product_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate complete product data.

        Args:
            product_data: Dictionary containing product data

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        required_fields = ['asin', 'url', 'timestamp']
        for field in required_fields:
            if field not in product_data or not product_data[field]:
                errors.append(f"Missing required field: {field}")

        # Validate individual fields
        if 'asin' in product_data:
            asin_valid, asin_error = validate_asin(product_data['asin'], self.validation_rules['asin'])
            if not asin_valid:
                errors.append(asin_error)

        if 'url' in product_data:
            url_valid, url_error = validate_url(product_data['url'], self.validation_rules['url'])
            if not url_valid:
                errors.append(url_error)

        if 'title' in product_data:
            title_valid, title_error = validate_title(product_data['title'], self.validation_rules['title'])
            if not title_valid:
                errors.append(title_error)

        # Validate price data
        if 'current_price' in product_data:
            price_valid, price_error = validate_price(product_data['current_price'], self.validation_rules['price'])
            if not price_valid:
                errors.append(price_error)

        if 'original_price' in product_data and product_data['original_price']:
            price_valid, price_error = validate_price(product_data['original_price'], self.validation_rules['price'])
            if not price_valid:
                errors.append(price_error)

        # Validate discount percentage
        if 'discount_percentage' in product_data and product_data['discount_percentage'] is not None:
            discount_valid, discount_error = validate_discount(product_data['discount_percentage'], self.validation_rules['discount_percentage'])
            if not discount_valid:
                errors.append(discount_error)

        # Validate rating
        if 'rating' in product_data and product_data['rating'] is not None:
            rating_valid, rating_error = validate_rating(product_data['rating'], self.validation_rules['rating'])
            if not rating_valid:
                errors.append(rating_error)

        # Validate review count
        if 'review_count' in product_data and product_data['review_count'] is not None:
            review_valid, review_error = validate_review_count(product_data['review_count'], self.validation_rules['review_count'])
            if not review_valid:
                errors.append(review_error)

        # Validate timestamp
        if 'timestamp' in product_data:
            ts_valid, ts_error = validate_timestamp(product_data['timestamp'])
            if not ts_valid:
                errors.append(ts_error)

        # Validate availability
        if 'availability' in product_data:
            avail_valid, avail_error = validate_availability(product_data['availability'])
            if not avail_valid:
                errors.append(avail_error)

        # Additional business logic validations
        business_errors = validate_business_logic(product_data)
        errors.extend(business_errors)

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(f"Validation failed for ASIN {product_data.get('asin', 'UNKNOWN')}: {errors}")

        return is_valid, errors

    def sanitize_product_data(self, product_data: Dict) -> Dict:
        """
        Sanitize product data by trimming strings, converting types, etc.

        Args:
            product_data: Raw product data

        Returns:
            Sanitized product data
        """
        return sanitize_product_data(product_data, self.validation_rules)