# Design Decisions

This document explains the key technical decisions made while building the Amazon Price Tracker and the reasoning behind them.

---

## DuckDB

DuckDB was chosen as the primary database because it fits the project’s analytical nature.

- Embedded and serverless, requiring no separate database setup
- Optimized for analytical and time-series queries
- Supports standard SQL and window functions
- Integrates directly with Python and Streamlit
- Easy to version and manage for a portfolio project

This makes DuckDB a strong choice for local analytics and dashboards without operational overhead.

---

## ETL Pipeline Structure

The project uses a clear Extract → Transform → Load pipeline to maintain separation of concerns.

- Extraction handles data sourcing only
- Transformation normalizes and cleans data
- Loading is responsible for persistence
- Quality checks run before updating clean tables

This structure makes the pipeline easier to debug, extend, and reason about.

---

## Raw and Clean Data Model

Data is stored in multiple layers instead of a single table.

- Raw JSON data is preserved for auditing and debugging
- Clean tables store validated, structured data
- Historical tables capture price changes over time

This approach prevents data loss and allows reprocessing without re-scraping.

---

## Streamlit for the Dashboard

Streamlit was selected for the presentation layer due to its simplicity and tight Python integration.

- Minimal setup and fast iteration
- Direct access to DuckDB from Python
- Suitable for read-only analytical dashboards
- Easy deployment using Streamlit Cloud

It allows focus on analytics rather than frontend complexity.

---

## Minimal Infrastructure

The system avoids external services unless necessary.

- No separate database server
- No message queues or distributed systems
- All components run locally or via simple automation

This keeps the project easy to understand, run, and maintain while still reflecting real-world design patterns.

---

## Trade-offs

- Not designed for very high write throughput
- Single-node database limits scale
- Git-based storage is not ideal for very large datasets

These trade-offs are acceptable for the current scope and can be addressed in future iterations.

---
