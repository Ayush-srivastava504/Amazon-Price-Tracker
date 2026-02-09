-- Raw tables for ingestion
-- Raw scrapes table (already in init.sql, but kept separate for clarity)
-- Note: Using COPY to create table if it doesn't exist yet

CREATE TABLE IF NOT EXISTS raw_scrapes (
    scrape_id UUID DEFAULT gen_random_uuid(),
    product_id VARCHAR NOT NULL,
    scraped_data JSON NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    error_message TEXT
);

-- Raw HTML storage (optional, for debugging)
CREATE TABLE IF NOT EXISTS raw_html (
    html_id UUID DEFAULT gen_random_uuid(),
    product_id VARCHAR NOT NULL,
    html TEXT,  -- Can be large, only enable when debugging
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url VARCHAR
);

-- Scrape logs (simple logging)
CREATE TABLE IF NOT EXISTS scrape_logs (
    log_id UUID DEFAULT gen_random_uuid(),
    product_id VARCHAR,
    status_code INTEGER,
    response_time_ms INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    error TEXT
);