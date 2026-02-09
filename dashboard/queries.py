# Dashboard queries - simple data fetching for UI

from storage.queries import get_connection


def get_dashboard_data(days=30, product_id=None):
    conn = get_connection()
    
    # Base query
    if product_id:
        # Single product detail
        product_data = conn.execute("""
            SELECT 
                product_id,
                title,
                current_price,
                availability,
                rating,
                seller,
                last_seen_at
            FROM products 
            WHERE product_id = ? AND is_active = true
        """, (product_id,)).fetchone()
        
        query = f"""
            SELECT 
                scraped_at,
                price,
                availability
            FROM price_history 
            WHERE product_id = ? 
              AND scraped_at >= CURRENT_DATE - INTERVAL {int(days)} DAY
            ORDER BY scraped_at
        """
        
        price_history = conn.execute(query, (product_id,)).fetchall()
        
        return {
            'product': dict(
                zip(
                    ['product_id', 'title', 'current_price', 'availability', 'rating', 'seller', 'last_seen_at'],
                    product_data
                )
            ) if product_data else None,
            'history': [
                dict(zip(['scraped_at', 'price', 'availability'], row))
                for row in price_history
            ]
        }
    
    else:
        # Overview - all active products
        products = conn.execute("""
            SELECT 
                product_id,
                title,
                current_price,
                availability,
                rating,
                seller,
                last_seen_at
            FROM products 
            WHERE is_active = true
            ORDER BY last_seen_at DESC
            LIMIT 50
        """).fetchall()
        
        # Convert to list of dicts
        products_list = []
        for row in products:
            products_list.append({
                'product_id': row[0],
                'title': row[1],
                'current_price': row[2],
                'availability': row[3],
                'rating': row[4],
                'seller': row[5],
                'last_seen_at': row[6]
            })
        
        # Recent price changes for alerts
        alerts = conn.execute("""
            SELECT * FROM recent_price_changes 
            WHERE change_pct >= 10 OR change_pct <= -10
            LIMIT 20
        """).fetchall()
        
        # Basic stats
        stats = conn.execute("""
            SELECT 
                COUNT(*) as total_products,
                COUNT(CASE WHEN availability = 'in_stock' THEN 1 END) as in_stock,
                COUNT(CASE WHEN availability = 'out_of_stock' THEN 1 END) as out_of_stock,
                AVG(current_price) as avg_price
            FROM products 
            WHERE is_active = true
        """).fetchone()
        
        return {
            'products': products_list,
            'alerts': [
                dict(zip(
                    ['product_id', 'title', 'current_price', 'previous_avg_price', 'change_pct'],
                    row
                ))
                for row in alerts
            ],
            'stats': dict(
                zip(['total_products', 'in_stock', 'out_of_stock', 'avg_price'], stats)
            ) if stats else {}
        }


def get_price_trends(product_ids, days=30):       #Get price trends for multiple products
    conn = get_connection()
    
    if not product_ids:
        return []
    
    trends = []
    
    for pid in product_ids[:5]:  # Limit to 5 for chart readability
        query = f"""
            SELECT 
                DATE(scraped_at) AS date,
                AVG(price) AS avg_price
            FROM price_history
            WHERE product_id = ?
              AND scraped_at >= CURRENT_DATE - INTERVAL {int(days)} DAY
              AND price IS NOT NULL
            GROUP BY DATE(scraped_at)
            ORDER BY date
        """
        
        data = conn.execute(query, (pid,)).fetchall()
        
        if data:
            dates = [row[0] for row in data]
            prices = [float(row[1]) for row in data]
            trends.append({
                'product_id': pid,
                'title': get_product_title(pid),
                'dates': dates,
                'prices': prices
            })
    
    return trends


def get_product_title(product_id):      #Get product title - simple helper
    conn = get_connection()
    result = conn.execute(
        "SELECT title FROM products WHERE product_id = ?",
        (product_id,)
    ).fetchone()
    return result[0] if result else product_id


# Simple search
def search_products(query, limit=20):      #Search products by title
    conn = get_connection()
    
    results = conn.execute("""
        SELECT 
            product_id,
            title,
            current_price,
            availability
        FROM products 
        WHERE is_active = true 
          AND LOWER(title) LIKE LOWER(?)
        ORDER BY last_seen_at DESC
        LIMIT ?
    """, (f'%{query}%', limit)).fetchall()
    
    return [
        dict(zip(['product_id', 'title', 'current_price', 'availability'], row))
        for row in results
    ]
