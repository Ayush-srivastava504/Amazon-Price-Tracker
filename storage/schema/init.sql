-- Core schema for Amazon price tracker
-- Run this once when setting up

-- Raw scraped data (keep for debugging)
CREATE TABLE raw_scrapes (
    scrape_id UUID DEFAULT gen_random_uuid(),
    product_id VARCHAR NOT NULL,
    scraped_data JSON NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT
);

-- Products table - current state
CREATE TABLE products (
    product_id VARCHAR PRIMARY KEY,
    title VARCHAR,
    current_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'INR',
    availability VARCHAR,
    rating DECIMAL(3,2),
    seller VARCHAR,
    url VARCHAR,
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Price history - every price we see
CREATE TABLE price_history (
    price_id UUID DEFAULT gen_random_uuid(),
    product_id VARCHAR NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    availability VARCHAR,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Daily summary for fast queries
CREATE TABLE daily_price_summary (
    date DATE NOT NULL,
    product_id VARCHAR NOT NULL,
    avg_price DECIMAL(10,2),
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    in_stock BOOLEAN,
    PRIMARY KEY (date, product_id)
);

CREATE TABLE IF NOT EXISTS pipeline_state (
    pipeline_name VARCHAR PRIMARY KEY,
    last_run_timestamp TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
