# Data Flow

This document describes how data flows through the Amazon Price Tracker system, from ingestion to visualization.

---

## High-Level Flow

```

Trigger
↓
Ingestion
↓
ETL Pipeline
↓
DuckDB Storage
↓
Streamlit Dashboard

```

Each stage has a clearly defined responsibility and failure boundaries.

---

## 1. Pipeline Trigger

The pipeline can be triggered in multiple ways:

- Manual execution from the terminal
- Scheduled execution using cron
- Automated execution via GitHub Actions

All triggers execute the same entry point:

```

python -m pipeline.pipeline_runner

```

---

## 2. Ingestion Layer

**Source**
- Amazon product pages (India)
- Optional intermediate JSON file (`scraper_output.json`)

**Flow**
```

Product ASINs
→ HTTP Request
→ HTML Response
→ Parsing & Extraction
→ Raw Product Records

```

Failures at this stage are handled per product and logged without stopping the entire run.

---

## 3. Extract Phase

- Reads raw scraped data (file or live)
- Attaches metadata such as timestamps
- Produces a list of raw product records

If no data is extracted, the pipeline stops early.

---

## 4. Load Raw Phase

- Raw product records are stored as JSON
- Data is written to the `raw_scrapes` table in DuckDB
- Each record is tagged with a unique identifier

This layer acts as an audit and replay mechanism.

---

## 5. Transform Phase

- Raw fields are cleaned and normalized
- Prices are converted to numeric values
- Availability and metadata are standardized
- Records are shaped into analytics-ready format

Invalid records are filtered out during this stage.

---

## 6. Quality Checks

Before updating clean tables, the data is validated:

- Required fields must be present
- Prices must be within expected ranges
- Duplicate or malformed records are detected

Failures here are logged and may skip affected records.

---

## 7. Load Clean Phase

Validated data is written to analytics tables:

- `products` is updated with the latest snapshot
- `price_history` stores time-series price data

This ensures historical tracking without overwriting past observations.

---

## 8. Storage Layer (DuckDB)

DuckDB serves as the single source of truth:

- Raw data for debugging
- Clean snapshot for fast reads
- Historical data for trend analysis

All dashboard queries read directly from DuckDB.

---

## 9. Presentation Layer

```

User
→ Streamlit UI
→ SQL Queries
→ DuckDB
→ Charts & Tables

```

The dashboard is read-only and does not modify stored data.

---

## Failure Handling in Data Flow

- Empty extract → pipeline stops
- Partial scrape failure → remaining products continue
- Invalid data → excluded from clean tables
- Dashboard queries with no results → render empty views safely

---

## Summary

The data flow is designed to be:

- Linear and easy to reason about
- Resilient to partial failures
- Auditable through raw data storage
- Optimized for analytical queries

This structure balances simplicity with real-world data engineering practices.

```