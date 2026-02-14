import logging
from typing import List, Dict, Any, Tuple
import statistics

logger = logging.getLogger(__name__)

def run_quality_checks(data: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:     # Run basic quality checks on transformed datapython -m pipeline.pipeline_runner --live

    if not data:
        return False, {"error": "No data to check"}
    
    checks = {
        "total_records": len(data),
        "failed_checks": []
    }
    
    # Check 1: Product IDs should be present and look like ASINs
    missing_product_ids = sum(1 for r in data if not r.get('product_id'))
    if missing_product_ids:
        checks['failed_checks'].append(f"{missing_product_ids} records missing product_id")
    
    # Check 2: Price distribution check (only for in-stock items)
    prices = [r['price'] for r in data if r.get('price') is not None]
    if prices:
        checks['price_stats'] = {
            'count': len(prices),
            'avg': statistics.mean(prices),
            'min': min(prices),
            'max': max(prices)
        }
        
        # Flag suspicious prices (too high/low relative to average)
        if len(prices) > 5:
            avg_price = statistics.mean(prices)
            suspicious = [p for p in prices if p > avg_price * 10 or p < avg_price * 0.1]
            if suspicious:
                checks['failed_checks'].append(f"{len(suspicious)} suspicious prices detected")
    
    # Check 3: Check for duplicate product IDs in this batch
    product_ids = [r['product_id'] for r in data if r.get('product_id')]
    duplicate_ids = set([pid for pid in product_ids if product_ids.count(pid) > 1])
    if duplicate_ids:
        checks['failed_checks'].append(f"Duplicate product IDs: {list(duplicate_ids)[:3]}...")
    
    # Check 4: Timestamp recency (data should be fresh)
    # This is simplified - would parse timestamps in reality
    checks['recent_records'] = len(data)  # Assume all are recent for now
    
    # Determine if checks passed
    checks['passed'] = len(checks['failed_checks']) == 0
    checks['pass_rate'] = f"{len(data) - len(checks['failed_checks'])}/{len(data)}"
    
    if not checks['passed']:
        logger.warning(f"Quality checks failed: {checks['failed_checks']}")
    else:
        logger.info(f"All quality checks passed for {len(data)} records")
    
    return checks['passed'], checks

# Simple threshold-based alert
def check_price_anomaly(current_price: float, historical_prices: List[float]) -> bool:     #Check if current price is anomalous compared to history
    if not historical_prices:
        return False
    
    avg_historical = statistics.mean(historical_prices)
    
    # More than 50% change is suspicious
    if current_price > avg_historical * 1.5:
        logger.warning(f"Price spike: {current_price} vs avg {avg_historical:.2f}")
        return True
    elif current_price < avg_historical * 0.5:
        logger.warning(f"Price drop: {current_price} vs avg {avg_historical:.2f}")
        return True
    
    return False