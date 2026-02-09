import logging
import json
from typing import List, Dict, Any
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

def load_to_raw_table(data: List[Dict[str, Any]], db_conn) -> int:
    if not data:
        logger.warning("No data to load to raw table")
        return 0

    records_inserted = 0

    for record in data:
        try:
            raw_id = str(uuid.uuid4())

            record["_raw_id"] = raw_id
            record["_loaded_at"] = datetime.utcnow().isoformat()

            query = """
              INSERT INTO raw_scrapes (scrape_id, product_id, scraped_data, success)
                VALUES (?, ?, ?, ?)
            """

            params = (
                raw_id,
                record.get('product_id'),
                json.dumps(record),
                True
            )

            db_conn.execute(query, params)
            records_inserted += 1

        except Exception as e:
            logger.error(
                f"Failed to load record {record.get('product_id')}: {e}"
            )

    logger.info(f"Loaded {records_inserted}/{len(data)} records to raw table")
    return records_inserted

from storage.duckdb_setup import get_connection, update_product

def load_to_clean_tables(data):     #Load validated product data into clean DuckDB tables.
    if not data:
        logger.warning("No data to load to clean tables")
        return 0

    conn = get_connection()
    records_loaded = 0

    for record in data:
        try:
            update_product(record)
            records_loaded += 1
        except Exception as e:
            logger.error(
                f"Failed to load clean record {record.get('product_id')}: {e}"
            )

    logger.info(f"Loaded {records_loaded}/{len(data)} records to clean tables")
    return records_loaded
