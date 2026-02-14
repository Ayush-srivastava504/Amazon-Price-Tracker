# DuckDB setup for Amazon price tracker

import duckdb
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def init_db(db_path="data/amazon_prices.duckdb"):       #Setup DuckDB
    # Create data directory if missing
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = duckdb.connect(db_path)
    
    # Check if we already have tables
    tables = conn.execute("SHOW TABLES").fetchall()
    if tables:
        logger.info(f"Found existing tables: {[t[0] for t in tables]}")
        return conn
    
    # Load and run schema files
    schema_dir = Path(__file__).parent / "schema"
    
    # Run init.sql first
    init_sql = schema_dir / "init.sql"
    if init_sql.exists():
        sql = init_sql.read_text()
        conn.execute(sql)
        logger.info("Created core schema")
    
    # Run raw tables
    raw_sql = schema_dir / "raw_tables.sql"
    if raw_sql.exists():
        conn.execute(raw_sql.read_text())
        logger.info("Created raw tables")
    
    # Run analytics tables  
    analytics_sql = schema_dir / "analytics_tables.sql"
    if analytics_sql.exists():
        conn.execute(analytics_sql.read_text())
        logger.info("Created analytics tables")
    
    # Run views
    views_sql = schema_dir / "views.sql"
    if views_sql.exists():
        conn.execute(views_sql.read_text())
        logger.info("Created views")
    
    logger.info(f"DuckDB initialized at {db_path}")
    return conn

# Simple singleton pattern - one connection per process
_db_conn = None

def get_connection(db_path="data/amazon_prices+.duckdb"):     #Get database connection
    global _db_conn
    if _db_conn is None:
        _db_conn = init_db(db_path)
    return _db_conn

def save_raw_scrape(product_id, scraped_data, success=True, error=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO raw_scrapes (product_id, scraped_data, success, error_message)
        VALUES (?, ?, ?, ?)
    """, (product_id, scraped_data, success, error))

def update_product(product_data):      #Update product and price history. This is the main write operation after scraping.
    
   
    conn = get_connection()
    
    # Extract fields
    pid = product_data['product_id']
    price = product_data.get('price')
    availability = product_data.get('availability', 'unknown')
    
    # Check current price
    current = conn.execute("""
        SELECT current_price FROM products WHERE product_id = ?
    """, (pid,)).fetchone()
    
    # Update products table
    conn.execute("""
        INSERT INTO products (product_id, title, current_price, availability, rating, seller, url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (product_id) DO UPDATE SET
            title = excluded.title,
            current_price = excluded.current_price,
            availability = excluded.availability,
            rating = excluded.rating,
            seller = excluded.seller,
            last_seen_at = now(),
            is_active = true
    """, (
        pid,
        product_data.get('title'),
        price,
        availability,
        product_data.get('rating'),
        product_data.get('seller'),
        product_data.get('url')
    ))
    
    # Add to price history if price changed
    old_price = current[0] if current else None
    if price is not None:
        conn.execute("""
            INSERT INTO price_history (product_id, price, availability)
            VALUES (?, ?, ?)
        """, (pid, price, availability))
    
    conn.commit()
    logger.debug(f"Updated product {pid}")