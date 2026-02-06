from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

def validate_business_logic(product_data: Dict) -> List[str]:
    """Additional business logic validations"""
    errors = []

    # Check price consistency
    current_price = product_data.get('current_price')
    original_price = product_data.get('original_price')

    if current_price and original_price:
        if current_price > original_price:
            errors.append(f"Current price ({current_price}) > original price ({original_price})")

        # Calculate expected discount
        expected_discount = ((original_price - current_price) / original_price * 100)
        provided_discount = product_data.get('discount_percentage')

        if provided_discount is not None:
            discount_diff = abs(provided_discount - expected_discount)
            if discount_diff > 5.0:  # Allow 5% difference for rounding
                errors.append(f"Discount mismatch: provided={provided_discount}%, calculated={expected_discount:.2f}%")

    # Check if rating exists but no review count
    if 'rating' in product_data and product_data['rating'] is not None:
        if 'review_count' not in product_data or product_data['review_count'] is None:
            logger.warning(f"Rating exists but no review count for ASIN {product_data.get('asin')}")

    # Check if review count exists but no rating
    if 'review_count' in product_data and product_data['review_count'] is not None:
        if 'rating' not in product_data or product_data['rating'] is None:
            logger.warning(f"Review count exists but no rating for ASIN {product_data.get('asin')}")

    # Validate currency
    if 'currency' in product_data and product_data['currency']:
        valid_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD', 'JPY']
        if product_data['currency'] not in valid_currencies:
            errors.append(f"Invalid currency: {product_data['currency']}")

    return errors