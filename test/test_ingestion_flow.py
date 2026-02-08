# test_scraper.py
import yaml
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.amazon_scraper import AmazonScraper

# Test configuration
config = {
    "base_url": "https://www.amazon.com",
    "timeout": 10,
    "max_retries": 3,
    "request_delay": 2,
    "max_html_size_mb": 5
}

# Test with a valid ASIN
scraper = AmazonScraper(config)
html = scraper.scrape_product("B08N5WRWNW")  # Example ASIN

if html:
    print(f"Success! Retrieved {len(html)} characters")
    # Save for debugging
    with open("test_page.html", "w", encoding="utf-8") as f:
        f.write(html)
else:
    print("Failed to retrieve page")