-- Useful views for analysis

-- Current prices view (active products only)
CREATE VIEW current_prices AS
SELECT 
    product_id,
    title,
    current_price,
    currency,
    availability,
    last_seen_at
FROM products 
WHERE is_active = true;

-- Price changes in last 24h (for alerts)
CREATE VIEW recent_price_changes AS
WITH latest AS (
    SELECT 
        product_id,
        price as current_price,
        scraped_at
    FROM price_history 
    WHERE scraped_at >= CURRENT_TIMESTAMP - INTERVAL '1 day'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY scraped_at DESC) = 1
),
previous AS (
    SELECT 
        product_id,
        AVG(price) as previous_avg_price
    FROM price_history 
    WHERE scraped_at >= CURRENT_TIMESTAMP - INTERVAL '2 days'
      AND scraped_at < CURRENT_TIMESTAMP - INTERVAL '1 day'
    GROUP BY product_id
)
SELECT 
    l.product_id,
    p.title,
    l.current_price,
    pr.previous_avg_price,
    ROUND(((l.current_price - pr.previous_avg_price) / pr.previous_avg_price) * 100, 1) as change_pct
FROM latest l
JOIN previous pr ON l.product_id = pr.product_id
JOIN products p ON l.product_id = p.product_id
WHERE ABS(l.current_price - pr.previous_avg_price) / pr.previous_avg_price > 0.05;  -- 5% change

-- Products out of stock
CREATE VIEW out_of_stock_products AS
SELECT 
    product_id,
    title,
    current_price,
    last_seen_at,
    DATE_DIFF('day', last_seen_at, CURRENT_TIMESTAMP) as days_out_of_stock
FROM products 
WHERE availability = 'out_of_stock' 
  AND is_active = true
  AND last_seen_at >= CURRENT_TIMESTAMP - INTERVAL '7 days';

-- Weekly price trends
CREATE VIEW weekly_trends AS
SELECT 
    product_id,
    DATE_TRUNC('day', scraped_at) as date,
    MIN(price) as low,
    MAX(price) as high,
    AVG(price) as avg_price,
    COUNT(*) as readings
FROM price_history 
WHERE scraped_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY product_id, DATE_TRUNC('day', scraped_at);