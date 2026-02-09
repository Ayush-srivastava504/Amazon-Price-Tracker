#!/usr/bin/env python3
# Main pipeline orchestrator.

import logging
import argparse
from datetime import datetime
import sys
from typing import Optional
from pathlib import Path
import duckdb   
from storage.duckdb_setup import get_connection


# Make project root importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import our pipeline steps
from pipeline.extract import extract_product_data, extract_live
from pipeline.load_raw import load_to_raw_table, load_to_clean_tables
from pipeline.transform import transform_batch
from pipeline.quality_checks import run_quality_checks

# Configure logging - simple and practical
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PipelineRunner:         # Orchestrates the ETL pipeline

    def __init__(self, db_conn=None, use_live_scraping=False):
        self.db_conn = db_conn
        self.use_live_scraping = use_live_scraping
        self.results = {
            'start_time': None,
            'end_time': None,
            'records_processed': 0,
            'errors': []
        }

    def run(self, product_ids: Optional[list] = None):           # Main pipeline execution
        self.results['start_time'] = datetime.utcnow()
        logger.info(f"Starting pipeline run at {self.results['start_time']}")

        try:
            # STEP 1: EXTRACT
            logger.info("=== EXTRACT PHASE ===")
            if self.use_live_scraping and product_ids:
                from ingestion.amazon_scraper import AmazonScraper  # Lazy import
                scraper = AmazonScraper(config={})
                raw_data = extract_live(product_ids, scraper)
            else:
                raw_data = extract_product_data()

            if not raw_data:
                logger.error("No data extracted. Pipeline stopping.")
                self.results['errors'].append("No data extracted")
                return False

            logger.info(f"Extracted {len(raw_data)} raw records")

            # STEP 2: LOAD RAW
            logger.info("=== LOAD RAW PHASE ===")
            if self.db_conn:
                loaded_count = load_to_raw_table(raw_data, self.db_conn)
                logger.info(f"Loaded {loaded_count} records to raw storage")
            else:
                logger.warning("No DB connection, skipping raw load")

            # STEP 3: TRANSFORM
            logger.info("=== TRANSFORM PHASE ===")
            transformed_data = transform_batch(raw_data)

            if not transformed_data:
                logger.error("No data transformed. Pipeline stopping.")
                self.results['errors'].append("No data transformed")
                return False

            # STEP 4: QUALITY CHECKS
            logger.info("=== QUALITY CHECK PHASE ===")
            quality_passed, quality_stats = run_quality_checks(transformed_data)

            if not quality_passed:
                logger.warning("Quality checks failed, but continuing...")

            # STEP 5: LOAD TRANSFORMED (to final table)
            logger.info("=== LOAD TRANSFORMED PHASE ===")
            if self.db_conn and transformed_data:
                loaded_clean = load_to_clean_tables(transformed_data)  
                logger.info(
                    f"Loaded {loaded_clean} transformed records to clean tables"
                )
            else:
                logger.warning("No DB connection, skipping clean load")

            # Update results
            self.results['records_processed'] = len(transformed_data)
            self.results['quality_stats'] = quality_stats
            self.results['end_time'] = datetime.utcnow()

            runtime = (
                self.results['end_time'] - self.results['start_time']
            ).total_seconds()
            logger.info(
                f"Pipeline completed in {runtime:.1f}s. "
                f"Processed {len(transformed_data)} records."
            )

            return quality_passed

        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}", exc_info=True)
            self.results['errors'].append(str(e))
            self.results['end_time'] = datetime.utcnow()
            return False

    def get_summary(self):
        if self.results['end_time'] and self.results['start_time']:
            runtime = (
                self.results['end_time'] - self.results['start_time']
            ).total_seconds()
            self.results['runtime_seconds'] = runtime

        return self.results


def main():          # Command line entry point
    parser = argparse.ArgumentParser(description='Run Amazon price tracker ETL pipeline')
    parser.add_argument('--products', type=str, help='Comma-separated product IDs')
    parser.add_argument('--live', action='store_true', help='Use live scraping instead of file')
    parser.add_argument('--config', type=str, default='configs/dev.yaml', help='Config file path')

    args = parser.parse_args()

    # Parse product IDs if provided
    product_ids = None
    if args.products:
        product_ids = [pid.strip() for pid in args.products.split(',')]
        logger.info(f"Running pipeline for {len(product_ids)} products")

    # Initialize DuckDB connection (FIXED)
    db_conn = get_connection("data/amazon_prices.duckdb")
    logger.info("Connected to DuckDB at data/amazon_prices.duckdb")

    # Initialize pipeline
    runner = PipelineRunner(
        db_conn=db_conn,          
        use_live_scraping=args.live
    )

    # Run it
    success = runner.run(product_ids)

    # Print summary
    summary = runner.get_summary()
    print("\n" + "=" * 50)
    print("PIPELINE SUMMARY")
    print("=" * 50)
    print(f"Status: {'SUCCESS' if success else 'FAILED'}")
    print(f"Records: {summary.get('records_processed', 0)}")
    print(f"Runtime: {summary.get('runtime_seconds', 0):.1f}s")

    if summary.get('errors'):
        print(f"Errors: {summary['errors']}")

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
