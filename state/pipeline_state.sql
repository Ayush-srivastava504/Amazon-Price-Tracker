-- Pipeline state table - tracks when we last ran each pipeline
-- Simple table for cron-based scheduling, not a full workflow engine

CREATE TABLE IF NOT EXISTS pipeline_state (
    -- Pipeline identifier (e.g., 'amazon_scraper', 'daily_summary')
    pipeline_name VARCHAR PRIMARY KEY,
    
    -- When the pipeline last ran successfully (UTC)
    last_run_timestamp TIMESTAMP,
    
    -- When this record was created/updated (for debugging)
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);