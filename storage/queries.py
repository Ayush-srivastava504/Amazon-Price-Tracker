# Common read queries for the dashboard

from .duckdb_setup import get_connection

def get_active_products(limit=100):
    conn = get_connection()
    return conn.execute("""
        SELECT * FROM current_prices 
        ORDER BY last_seen_at DESC 
        LIMIT ?
    """, (limit,)).fetchall()

def get_product_history(product_id, days=30):      # Get price history for a product.
    conn = get_connection()
    return conn.execute("""
        SELECT 
            scraped_at,
            price,
            availability
        FROM price_history 
        WHERE product_id = ? 
          AND scraped_at >= CURRENT_DATE - INTERVAL ? DAY
        ORDER BY scraped_at
    """, (product_id, days)).fetchall()

def get_daily_summary(days_back=7):      # Get aggregated daily stats
    conn = get_connection()
    return conn.execute("""
        SELECT 
            date,
            COUNT(DISTINCT product_id) as products,
            AVG(avg_price) as avg_price
        FROM daily_price_summary 
        WHERE date >= CURRENT_DATE - INTERVAL ? DAY
        GROUP BY date
        ORDER BY date
    """, (days_back,)).fetchall()

def get_price_alerts(threshold_pct=10):    # Find products with significant price changes
    conn = get_connection()
    return conn.execute("""
        SELECT * FROM recent_price_changes 
        WHERE ABS(change_pct) >= ?
        ORDER BY ABS(change_pct) DESC
    """, (threshold_pct,)).fetchall()

def get_lowest_prices(limit=20):     # Find cheapest active products.
    conn = get_connection()
    return conn.execute("""
        SELECT 
            product_id,
            title,
            current_price,
            availability,
            last_seen_at
        FROM products 
        WHERE is_active = true 
          AND current_price IS NOT NULL
        ORDER BY current_price ASC
        LIMIT ?
    """, (limit,)).fetchall()

def search_products(search_term, limit=50):       #Search products by title
    conn = get_connection()
    # Simple LIKE search - good enough for now
    return conn.execute("""
        SELECT 
            product_id,
            title,
            current_price,
            availability
        FROM products 
        WHERE is_active = true 
          AND LOWER(title) LIKE LOWER(?)
        LIMIT ?
    """, (f'%{search_term}%', limit)).fetchall()

# Helper for dashboard charts
def get_price_chart_data(product_id, days=30):
    """Get data ready for charting."""
    conn = get_connection()
    data = conn.execute("""
        SELECT 
            DATE(scraped_at) as date,
            AVG(price) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM price_history 
        WHERE product_id = ?
          AND scraped_at >= CURRENT_DATE - INTERVAL ? DAY
        GROUP BY DATE(scraped_at)
        ORDER BY date
    """, (product_id, days)).fetchall()
    
    # Convert to lists for chart libraries
    dates = [row[0] for row in data]
    prices = [float(row[1]) if row[1] else None for row in data]
    return dates, prices

# Simple stats
def get_db_stats():
    conn = get_connection()
    stats = {}
    
    # Counts
    stats['total_products'] = conn.execute(
        "SELECT COUNT(*) FROM products WHERE is_active = true"
    ).fetchone()[0]
    
    stats['price_history_count'] = conn.execute(
        "SELECT COUNT(*) FROM price_history"
    ).fetchone()[0]
    
    stats['in_stock'] = conn.execute("""
        SELECT COUNT(*) FROM products 
        WHERE availability = 'in_stock' AND is_active = true
    """).fetchone()[0]
    
    # Recent activity
    stats['scrapes_today'] = conn.execute("""
        SELECT COUNT(*) FROM price_history 
        WHERE DATE(scraped_at) = CURRENT_DATE
    """).fetchone()[0]
    
    return stats