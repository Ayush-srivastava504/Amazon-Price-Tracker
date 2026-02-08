import yaml
import logging
import pandas as pd
from typing import List, Dict
from ingestion.amazon_scraper import AmazonScraper

logger = logging.getLogger(__name__)

class Extract:
    def __init__(self, config_path: str = "ingestion/ingestion_config.yaml"):
        self.config = self.load_config(config_path)
        self.scraper = AmazonScraper(config_path)
        
    def load_config(self, config_path: str) -> Dict:    #Load configuration from YAML file
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get_product_urls(self) -> List[str]:        # Get list of product URLs to scrape
        # Could be from config file, database, or external source
        urls = self.config.get('product_urls', [])
        
        # If no URLs in config, read from file
        if not urls:
            try:
                with open('data/product_urls.txt', 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                logger.warning("No product URLs found in config or file")
                
        return urls
    
    def run(self) -> pd.DataFrame:       # Run extraction process
        logger.info("Starting extraction process")
        
        # Get URLs to scrape
        urls = self.get_product_urls()
        if not urls:
            logger.error("No URLs to scrape")
            return pd.DataFrame()
        
        logger.info(f"Found {len(urls)} URLs to scrape")
        
        # Scrape data
        products_data = self.scraper.scrape_multiple(urls)
        
        # Convert to DataFrame
        if products_data:
            df = pd.DataFrame(products_data)
            logger.info(f"Successfully scraped {len(df)} products")
            return df
        else:
            logger.warning("No data scraped")
            return pd.DataFrame()
    
    def run_with_checkpoint(self, checkpoint_file: str = "data/last_run.txt") -> pd.DataFrame:      # Run extraction with checkpointing to track last run
        import os
        from datetime import datetime
        
        # Check if we should run based on schedule
        if os.path.exists(checkpoint_file):
            with open(checkpoint_file, 'r') as f:
                last_run = datetime.fromisoformat(f.read().strip())
            
            # Check if enough time has passed
            hours_since_last = (datetime.now() - last_run).total_seconds() / 3600
            min_interval = self.config.get('scrape_interval_hours', 4)
            
            if hours_since_last < min_interval:
                logger.info(f"Last run was {hours_since_last:.1f} hours ago. Skipping.")
                return pd.DataFrame()
        
        # Run extraction
        df = self.run()
        
        # Update checkpoint
        with open(checkpoint_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        return df