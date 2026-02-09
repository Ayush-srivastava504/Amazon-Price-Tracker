-- Analytics tables - clean, query-ready data

-- Price history index for faster queries
CREATE INDEX IF NOT EXISTS idx_price_history_product ON price_history(product_id);
CREATE INDEX IF NOT EXISTS idx_price_history_time ON price_history(scraped_at);

-- Products index (DuckDB does not support partial indexes)
CREATE INDEX IF NOT EXISTS idx_products_active ON products(product_id);

-- Daily summary index  
CREATE INDEX IF NOT EXISTS idx_daily_summary_date ON daily_price_summary(date);

-- Optional: Track monitored products with targets
CREATE TABLE IF NOT EXISTS product_targets (
    product_id VARCHAR PRIMARY KEY,
    target_price DECIMAL(10,2),
    alert_on_drop BOOLEAN DEFAULT true,
    notes TEXT
);

-- Price alerts table (stores alerts we've sent)
CREATE TABLE IF NOT EXISTS price_alerts (
    alert_id UUID DEFAULT gen_random_uuid(),
    product_id VARCHAR NOT NULL,
    old_price DECIMAL(10,2),
    new_price DECIMAL(10,2),
    change_pct DECIMAL(5,2),
    alerted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent BOOLEAN DEFAULT false
);
