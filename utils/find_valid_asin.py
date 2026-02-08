"""
Simple script to test if ASINs are valid on Amazon India
This will help you find working ASINs before using them in your scraper
"""

import requests
import time

def test_asin(asin):
    """Test if an ASIN exists on Amazon India"""
    url = f"https://www.amazon.in/dp/{asin}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8,hi;q=0.7",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            # Check if it's not a "Product not found" page
            if "page you are looking for cannot be found" in response.text.lower():
                return False, "Product not found page"
            elif "robot check" in response.text.lower():
                return None, "Bot detection triggered"
            else:
                # Try to find product title
                if '<span id="productTitle"' in response.text:
                    return True, "Valid product found"
                else:
                    return False, "No product title found"
        elif response.status_code == 404:
            return False, "404 Not Found"
        else:
            return False, f"Status code: {response.status_code}"
    
    except Exception as e:
        return None, f"Error: {str(e)}"


# List of ASINs to test on Amazon India
# Add your own ASINs here to test them
test_asins = [
    # CONFIRMED WORKING (tested 2026-02-08)
    "8129116758",  # Rich Dad Poor Dad - ✓ WORKING
    
    # Popular books to test (likely to work)
    # Search these on amazon.in and replace with actual ASINs
    "0143442295",  # Atomic Habits (if available)
    "8172234996",  # The Alchemist (if available)
    "819351749X",  # Ikigai (Indian Edition)
    "8129135736",  # The Power of Your Subconscious Mind
    
    # To find more ASINs:
    # 1. Go to https://www.amazon.in
    # 2. Search for popular products
    # 3. Click on a product
    # 4. Copy ASIN from URL (after /dp/)
    # 5. Add below:
    
    # Add your own ASINs to test:
    # "YOUR_ASIN_HERE",
]

print("Testing ASINs on Amazon India...")
print("=" * 60)

valid_asins = []

for asin in test_asins:
    print(f"\nTesting ASIN: {asin}")
    is_valid, message = test_asin(asin)
    
    if is_valid:
        print(f"  ✓ VALID - {message}")
        valid_asins.append(asin)
    elif is_valid is None:
        print(f"  ⚠ UNCLEAR - {message}")
    else:
        print(f"  ✗ INVALID - {message}")
    
    # Be respectful with rate limiting
    time.sleep(3)

print("\n" + "=" * 60)
print(f"\nValid ASINs found: {len(valid_asins)}")
if valid_asins:
    print("Working ASINs:")
    for asin in valid_asins:
        print(f"  - {asin}")
    print("\nYou can use these ASINs in your ingestion_config.yaml file.")
else:
    print("No valid ASINs found. You may need to:")
    print("1. Manually browse Amazon.in and copy ASINs from product URLs")
    print("2. Look for the ASIN in the 'Product Details' section on product pages")
    print("3. Use generic products like books (ISBNs) which are more stable")