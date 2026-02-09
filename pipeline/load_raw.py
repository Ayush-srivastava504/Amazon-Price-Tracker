import logging
from typing import List, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

def load_to_raw_table(data: List[Dict[str, Any]], db_conn) -> int:
    if not data:
        logger.warning("No data to load to raw table")
        return 0
    
    # Raw table schema is simple: json blob + metadata
    # We're not transforming or validating here - that's for transform step
    records_inserted = 0
    
    for record in data:
        try:
            # Generate a unique ID for this raw record
            raw_id = str(uuid.uuid4())
            
            # Basic metadata
            record['_raw_id'] = raw_id
            record['_loaded_at'] = datetime.utcnow().isoformat()
            
            # For Snowflake: would use COPY or INSERT
            # For Postgres/SQLite: simple INSERT
            query = """
            INSERT INTO raw_product_data 
            (raw_id, product_id, raw_json, loaded_at)
            VALUES (%s, %s, %s, %s)
            """
            
            params = (
                raw_id,
                record.get('product_id', 'unknown'),
                json.dumps(record),  # Store entire record as JSON
                datetime.utcnow()
            )
            
            db_conn.execute(query, params)
            records_inserted += 1
            
        except Exception as e:
            logger.error(f"Failed to load record {record.get('product_id')}: {e}")
            continue
    
    logger.info(f"Loaded {records_inserted}/{len(data)} records to raw table")
    return records_inserted

# Alternative: Load to file system (good for debugging)
def load_to_raw_file(data: List[Dict[str, Any]], output_dir: str = "data/raw") -> str:
    import os
    import json
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/raw_products_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved raw data to {filename}")
    return filename