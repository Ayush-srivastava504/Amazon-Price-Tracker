# System Architecture

The Amazon Price Tracker is built using a layered ETL architecture focused on reliability, maintainability, and analytics-first data access.  
Each layer has a clearly defined responsibility and minimal coupling with other layers.

---

## High-Level Layers

### 1. Orchestration

The orchestration layer controls when and how the pipeline is executed.

- Triggered manually, via cron, or GitHub Actions
- Uses a single, consistent entry point
- Entry point: `pipeline/pipeline_runner.py`
- Ensures the pipeline runs end-to-end in a deterministic order

This layer is responsible only for execution flow, not business logic.

---

### 2. Ingestion

The ingestion layer is responsible for collecting raw data from Amazon.

- Scrapes Amazon product pages using HTTP requests
- Applies anti-bot headers and retry logic
- Parses HTML and extracts relevant product fields
- Validates basic field presence at scrape time
- Handles failures on a per-product basis

Failures in this layer do not stop the entire pipeline unless no data is collected.

---

### 3. ETL Pipeline

The ETL pipeline processes ingested data into analytics-ready formats.

- Extracts raw data from files or live scraping output
- Loads raw JSON data into DuckDB for auditing
- Transforms raw records into a normalized schema
- Runs data quality checks to filter invalid records
- Loads validated data into clean and historical tables

This layer enforces data correctness and prevents corrupt data from reaching analytics tables.

---

### 4. Storage

The storage layer uses DuckDB as an embedded analytical database.

- Stores raw JSON data for debugging and reprocessing
- Maintains a current snapshot of product data
- Preserves historical price data for trend analysis
- Optimized for read-heavy analytical workloads

DuckDB acts as the single source of truth for both the pipeline and the dashboard.

---

### 5. Presentation

The presentation layer provides a read-only analytics interface.

- Implemented using Streamlit
- Queries DuckDB directly using SQL
- Displays price trends, comparisons, and summaries
- Handles empty or partial datasets gracefully

No data modification occurs in this layer.

---

## Design Principles

- Clear separation of responsibilities across layers
- Raw and clean data layers to prevent data loss
- Fail-fast behavior with safe degradation
- Analytics-first design optimized for querying and visualization
