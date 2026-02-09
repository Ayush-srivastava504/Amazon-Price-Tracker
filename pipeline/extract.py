import logging
from typing import List, Dict, Any
import json
from datetime import datetime

# Simple extractor - reads from scraper output or API
logger = logging.getLogger(__name__)

def extract_product_data(source_file: str = "data/scraper_output.json") -> List[Dict[str, Any]]:
    try:
        with open(source_file, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Extracted {len(data)} products from {source_file}")
        
        for item in data:
            item['_extracted_at'] = datetime.utcnow().isoformat()
        
        return data
    
    except FileNotFoundError:
        logger.warning(f"Source file {source_file} not found. Returning empty dataset.")
        return []
    
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {source_file}: {e}")
        return []

# Helper for live scraping if we want to bypass file storage
def extract_live(product_ids: List[str], scraper_instance) -> List[Dict[str, Any]]:
    results = []
    
    for pid in product_ids:
        try:
            product_data = scraper_instance.scrape_product(pid)
            if product_data:
                product_data['product_id'] = pid
                product_data['_extracted_at'] = datetime.utcnow().isoformat()
                results.append(product_data)
                
                import time
                time.sleep(1.5)
                
        except Exception as e:
            logger.error(f"Failed to extract product {pid}: {e}")
            continue
    
    logger.info(f"Live extraction complete: {len(results)}/{len(product_ids)} successful")
    return results