# test_ingestion_flow.py
import sys
import os
import yaml
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ingestion.amazon_scraper import AmazonScraper
from ingestion.parser import AmazonParser
from ingestion.validator.product_validator import ProductValidator

def test_ingestion_flow():
    """Test the complete ingestion flow for Amazon India."""
    
    # Load configuration
    config_path = project_root / "ingestion" / "ingestion_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Use environment-specific settings
    env = config.get("environment", "development")
    env_config = config.get(env, {})
    
    # Merge configs (environment-specific overrides)
    scraper_config = {**config.get("scraper", {}), **env_config.get("scraper", {})}
    
    # Initialize components
    scraper = AmazonScraper(scraper_config)
    parser = AmazonParser()
    validator = ProductValidator()
    
    # Test with a sample product
    sample_asins = config["products"]["sample_asins"][:2]  # Use first 2 for testing
    
    print(f"Testing ingestion flow for {len(sample_asins)} products...")
    print(f"Environment: {env}")
    print(f"Base URL: {scraper_config.get('base_url')}")
    print("-" * 50)
    
    for idx, asin in enumerate(sample_asins, 1):
        print(f"\n[{idx}/{len(sample_asins)}] Testing ASIN: {asin}")
        
        # Step 1: Scrape
        print("  Step 1: Scraping product page...")
        html = scraper.scrape_with_retry(asin, max_attempts=3)
        
        if not html:
            print("  ❌ Failed to scrape product (page might not exist or blocked)")
            continue
        
        print(f"  ✓ Scraped {len(html)} characters")
        
        # Optional: Save HTML for debugging
        if env == "development":
            debug_dir = project_root / "data" / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            html_path = debug_dir / f"{asin}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  Saved HTML to: {html_path}")
        
        # Step 2: Parse
        print("  Step 2: Parsing HTML...")
        product_data = parser.parse_product_page(html, asin)
        
        if not product_data:
            print(" Failed to parse product data")
            continue
        
        print(f" Parsed data: {product_data.get('title', 'N/A')[:50]}...")
        
        # Step 3: Validate
        print("  Step 3: Validating data...")
        is_valid, error = validator.validate(product_data)
        
        if not is_valid:
            print(f" Validation failed: {error}")
            continue
        
        print(f" Data validation passed")
        
        # Step 4: Sanitize
        print("  Step 4: Sanitizing data...")
        sanitized_data = validator.sanitize(product_data)
        
        # Display results
        print("\n  Results:")
        print(f"     Title: {sanitized_data.get('title', 'N/A')[:70]}...")
        print(f"     Price: ₹{sanitized_data.get('price', 'N/A')}")
        print(f"     Availability: {sanitized_data.get('availability', 'N/A')}")
        print(f"     Rating: {sanitized_data.get('rating', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    try:
        test_ingestion_flow()
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()