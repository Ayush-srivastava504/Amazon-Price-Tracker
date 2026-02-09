#!/usr/bin/env python3

# Main script to run the scraper.


import argparse
import json
import yaml
from datetime import datetime
import os

# Our modules
from amazon_scraper import AmazonScraper
from parser import AmazonParser
from validator import validate_batch, clean_product_data


def load_config(config_path: str) -> dict:
    if not os.path.exists(config_path):
        print(f"No config.yaml found at '{config_path}', using defaults")
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Failed to load config file: {e}")
        return {}


def main():
    arg_parser = argparse.ArgumentParser(description="Scrape Amazon product prices")

    arg_parser.add_argument(
        "--asins",
        type=str,
        help="Comma-separated ASINs to scrape"
    )

    arg_parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config.yaml"
    )

    args = arg_parser.parse_args()

    # Load config (FIXED)
    config = load_config(args.config)
    amazon_config = config.get("amazon", {})

    # Resolve ASINs
    if args.asins:
        asins = [asin.strip() for asin in args.asins.split(",") if asin.strip()]
    else:
        asins = config.get("products", {}).get("asins", [])

    if not asins:
        print("No ASINs to scrape. Use --asins or config.yaml")
        return

    print(f"Scraping {len(asins)} products...")

    # Initialize components
    scraper = AmazonScraper(amazon_config)
    parser = AmazonParser()

    # Scrape
    html_results = scraper.scrape_multiple(asins)

    # Parse
    parsed_results = []
    for asin, html in html_results.items():
        if not html:
            continue

        product_data = parser.parse_product(html, asin)
        if product_data:
            parsed_results.append(product_data)

    # Validate & clean
    valid_products, invalid_products = validate_batch(parsed_results)
    valid_products = [clean_product_data(p) for p in valid_products]

    # Save results
    if valid_products:
     output_dir = config.get("storage", {}).get("output_dir", "./data")
     os.makedirs(output_dir, exist_ok=True)

     output_file = os.path.join(output_dir, "scraper_output.json")

     with open(output_file, "w", encoding="utf-8") as f:
        json.dump(valid_products, f, indent=2, default=str)

        print(f"✓ Saved {len(valid_products)} products to {output_file}")


        for product in valid_products:
            price = f"₹{product['price']}" if product.get("price") else "No price"
            title = product.get("title", "")[:50]
            print(f"  {product['product_id']}: {price} - {title}...")

    if invalid_products:
        print(f"✗ {len(invalid_products)} products failed validation")
        for product in invalid_products:
            print(f"  {product.get('product_id')}")


if __name__ == "__main__":
    main()
