# Amazon India ASIN Finder - ALL CATEGORIES


import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from pathlib import Path
from datetime import datetime


class UltraSafeASINFinder:
    
    def __init__(self):
        self.base_url = "https://www.amazon.in"
        self.session = self._create_session()
        self.request_count = 0
        self.max_requests = 25  # Increased but still safe
        
        # Create utils directory if it doesn't exist
        self.utils_dir = Path("utils")
        self.utils_dir.mkdir(exist_ok=True)
        
    def _create_session(self) -> requests.Session:
        """Create session with rotating user agents"""
        session = requests.Session()
        
        # Multiple realistic user agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
        ]
        
        return session
    
    def _get_headers(self) -> dict:
        """Get randomized, realistic headers"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,hi;q=0.6",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "Referer": "https://www.amazon.in/",
        }
    
    def _ultra_safe_delay(self):
        """Very long delays to be extremely safe"""
        # Progressive delays - longer as we make more requests
        if self.request_count <= 5:
            base = 8.0
        elif self.request_count <= 10:
            base = 10.0
        elif self.request_count <= 15:
            base = 12.0
        else:
            base = 15.0
        
        # Add randomness
        delay = random.uniform(base, base + 5.0)
        print(f"    ⏳ Waiting {delay:.1f}s before next request (#{self.request_count + 1})...")
        time.sleep(delay)
    
    def search_with_ultra_safety(self, search_term: str, max_results: int = 4) -> List[Dict]:
        """
        Ultra-safe search with extensive error handling
        
        Args:
            search_term: What to search for
            max_results: Maximum ASINs to extract (kept low)
            
        Returns:
            List of products
        """
        if self.request_count >= self.max_requests:
            print(f"  ⚠️  Reached safe request limit ({self.max_requests}). Stopping.")
            return []
        
        print(f"\n🔍 Searching: {search_term}")
        
        url = f"{self.base_url}/s?k={quote_plus(search_term)}"
        
        max_attempts = 2  # Fewer retry attempts
        for attempt in range(1, max_attempts + 1):
            try:
                # Wait before request
                self._ultra_safe_delay()
                self.request_count += 1
                
                headers = self._get_headers()
                response = self.session.get(url, headers=headers, timeout=20)
                
                # Handle response codes
                if response.status_code == 200:
                    products = self._extract_asins(response.text, search_term, max_results)
                    if products:
                        return products
                    else:
                        print(f"  ⚠️  No ASINs extracted (might be layout change)")
                        return []
                
                elif response.status_code == 503:
                    print(f"  🛑 503 Error - Amazon is blocking requests")
                    print(f"  💡 STOPPING IMMEDIATELY to prevent further blocking")
                    self.request_count = self.max_requests  # Stop all requests
                    return []
                
                elif response.status_code == 429:
                    print(f"  🛑 429 Rate Limited - Too many requests")
                    print(f"  💡 STOPPING IMMEDIATELY")
                    self.request_count = self.max_requests
                    return []
                
                elif response.status_code == 404:
                    print(f"  ⚠️  404 Not Found")
                    return []
                
                else:
                    print(f"  ⚠️  Unexpected status {response.status_code}")
                    if attempt < max_attempts:
                        print(f"    ⏸️  Waiting 30s before retry...")
                        time.sleep(30)
                        continue
                    return []
                    
            except requests.exceptions.Timeout:
                print(f"  ⚠️  Request timeout (attempt {attempt}/{max_attempts})")
                if attempt < max_attempts:
                    time.sleep(20)
                    continue
                return []
            
            except requests.exceptions.ConnectionError:
                print(f"  ⚠️  Connection error - check your internet")
                return []
            
            except Exception as e:
                print(f"  ❌ Unexpected error: {e}")
                return []
        
        return []
    
    def _extract_asins(self, html: str, search_term: str, max_results: int) -> List[Dict]:
        """Extract ASINs from HTML with bot detection"""
        
        # Critical: Check for bot detection FIRST
        html_lower = html.lower()
        if any(indicator in html_lower for indicator in [
            "robot check", 
            "enter the characters",
            "captcha",
            "automated access",
            "sorry, we just need to make sure"
        ]):
            print(f"  🤖 BOT DETECTION TRIGGERED!")
            print(f"  🛑 STOPPING ALL REQUESTS IMMEDIATELY")
            print(f"  💡 Wait 2-3 hours before trying again")
            self.request_count = self.max_requests  # Stop everything
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Method 1: Find data-asin attributes
        for item in soup.find_all('div', {'data-asin': True}):
            asin = item.get('data-asin')
            
            if not asin or len(asin) != 10:
                continue
            
            # Get title
            title_elem = item.find('span', class_='a-text-normal')
            if not title_elem:
                title_elem = item.find('h2', class_='a-size-mini')
            if not title_elem:
                title_elem = item.find('h2')
            
            title = "Unknown Product"
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            products.append({
                'asin': asin,
                'title': title[:100],
                'url': f"{self.base_url}/dp/{asin}",
                'source': search_term
            })
            
            if len(products) >= max_results:
                break
        
        if products:
            print(f"  ✓ Found {len(products)} ASINs")
        else:
            print(f"  ⚠️  No ASINs found (HTML structure may have changed)")
        
        return products
    
    def save_results(self, all_products: List[Dict], validated: List[Dict]):
        """Save results to utils folder"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all found ASINs
        all_asins_file = self.utils_dir / f"all_asins_{timestamp}.txt"
        with open(all_asins_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("All ASINs Found on Amazon India\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            # Group by category
            by_source = {}
            for p in all_products:
                source = p.get('source', 'Unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(p)
            
            for source, products in by_source.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"Search: {source}\n")
                f.write(f"{'='*80}\n\n")
                for p in products:
                    f.write(f"ASIN: {p['asin']}\n")
                    f.write(f"Title: {p['title']}\n")
                    f.write(f"URL: {p['url']}\n")
                    f.write("-" * 80 + "\n")
        
        print(f"\n💾 Saved all ASINs to: {all_asins_file}")
        
        # Save validated ASINs (ready for config)
        if validated:
            validated_file = self.utils_dir / f"validated_asins_{timestamp}.txt"
            with open(validated_file, 'w', encoding='utf-8') as f:
                f.write("# Validated Amazon India ASINs\n")
                f.write("# Copy these to your ingestion_config.yaml\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("#\n")
                f.write("# Total validated: {}\n".format(len(validated)))
                f.write("\n" + "="*80 + "\n\n")
                f.write("sample_asins:\n")
                
                for p in validated:
                    title = p.get('validated_title', p.get('title', 'Unknown'))
                    f.write(f'  - "{p["asin"]}"  # {title[:70]}\n')
                
                f.write("\n" + "="*80 + "\n")
                f.write("# End of validated ASINs\n")
            
            print(f"💾 Saved validated ASINs to: {validated_file}")
            
            # Also save a simple list
            simple_file = self.utils_dir / "latest_validated_asins.txt"
            with open(simple_file, 'w', encoding='utf-8') as f:
                f.write("# Latest Validated ASINs (simple format)\n\n")
                for p in validated:
                    f.write(f"{p['asin']}\n")
            
            print(f"💾 Saved simple list to: {simple_file}")


# ALL PRODUCT CATEGORIES - Diverse searches across all types
ALL_CATEGORIES = {
    'Books': [
        'Rich Dad Poor Dad',
        'Ikigai book',
        'Atomic Habits',
    ],
    'Electronics - Audio': [
        'boAt Airdopes 131',
        'JBL earphones',
        'Sony headphones',
    ],
    'Electronics - Mobile': [
        'Mi power bank 10000mah',
        'realme smartphone',
        'Samsung Galaxy phone',
    ],
    'Electronics - Smart Home': [
        'Fire TV Stick',
        'Echo Dot',
        'Mi Smart Band',
    ],
    'Home & Kitchen - Cookware': [
        'Prestige pressure cooker',
        'Hawkins pressure cooker',
        'Pigeon cookware set',
    ],
    'Home & Kitchen - Storage': [
        'Milton water bottle',
        'Cello water bottle',
        'Tupperware container',
    ],
    'Home & Kitchen - Appliances': [
        'Pigeon electric kettle',
        'Philips air fryer',
        'Bajaj mixer grinder',
    ],
    'Personal Care - Skin': [
        'Mamaearth face wash',
        'Nivea body lotion',
        'Lakme lipstick',
    ],
    'Personal Care - Hair': [
        'Mamaearth onion oil',
        'Pantene shampoo',
        'Himalaya hair oil',
    ],
    'Personal Care - Grooming': [
        'Gillette razor blades',
        'Philips trimmer',
        'Beardo beard oil',
    ],
    'Fashion - Mens': [
        'Levi jeans',
        'Allen Solly shirt',
        'Van Heusen formal shirt',
    ],
    'Fashion - Womens': [
        'Biba kurti',
        'W for Woman dress',
        'Jaipur Kurti',
    ],
    'Fashion - Footwear': [
        'Nike running shoes',
        'Puma sneakers',
        'Bata shoes',
    ],
    'Sports & Fitness': [
        'yoga mat',
        'dumbbells set',
        'resistance bands',
    ],
    'Baby Products': [
        'Pampers diapers',
        'Johnson baby lotion',
        'Himalaya baby cream',
    ],
}


def main():
    """Main function with ultra-safe approach"""
    print("=" * 80)
    print("Ultra-Safe Amazon India ASIN Finder - ALL CATEGORIES")
    print("=" * 80)
    print("\n📋 Features:")
    print("  ✓ Searches 15 product categories")
    print("  ✓ Ultra-long delays (8-20 seconds)")
    print("  ✓ Maximum 25 total requests")
    print("  ✓ Instant stop on any blocking")
    print("  ✓ Saves results to utils/ folder")
    print("\n⏱️  Estimated time: 5-8 minutes")
    print("⚠️  If you see 503 errors, the script will stop immediately")
    print("=" * 80)
    
    input("\n👉 Press ENTER to start (or Ctrl+C to cancel)...")
    
    finder = UltraSafeASINFinder()
    all_products = []
    
    # Search categories
    print("\n\n" + "=" * 80)
    print("PHASE 1: Finding ASINs Across All Categories")
    print("=" * 80)
    
    category_count = 0
    max_categories = 8  # Limit number of categories to stay safe
    
    for category, searches in ALL_CATEGORIES.items():
        if category_count >= max_categories:
            print(f"\n⚠️  Reached category limit ({max_categories}). Stopping search phase.")
            break
        
        if finder.request_count >= finder.max_requests:
            print(f"\n⚠️  Reached request limit. Stopping search phase.")
            break
        
        print(f"\n{'='*80}")
        print(f"📦 Category: {category}")
        print('='*80)
        
        category_products = []
        
        # Only search first 2 terms per category to save requests
        for search_term in searches[:2]:
            if finder.request_count >= finder.max_requests:
                break
            
            products = finder.search_with_ultra_safety(search_term, max_results=4)
            
            if products:
                category_products.extend(products)
            
            # Check if we were blocked
            if finder.request_count >= finder.max_requests:
                print("\n🛑 Stopping due to errors or limits")
                break
        
        if category_products:
            all_products.extend(category_products)
            category_count += 1
        
        if finder.request_count >= finder.max_requests:
            break
    
    # Remove duplicates
    unique_products = {p['asin']: p for p in all_products}
    
    print("\n\n" + "=" * 80)
    print("PHASE 1 RESULTS")
    print("=" * 80)
    print(f"Total unique ASINs found: {len(unique_products)}")
    print(f"Requests made: {finder.request_count}/{finder.max_requests}")
    
    if not unique_products:
        print("\n❌ No ASINs found!")
        print("\nPossible reasons:")
        print("  1. Got blocked/rate limited (503 or 429 error)")
        print("  2. Network issues")
        print("  3. Amazon HTML structure changed")
        print("\n💡 What to do:")
        print("  1. Wait 2-3 hours")
        print("  2. Try again")
        print("  3. Or collect ASINs manually from browser")
        return
    
    # Save all found ASINs
    finder.save_results(list(unique_products.values()), [])
    
    # Validation phase (only if we have request budget)
    remaining = finder.max_requests - finder.request_count
    
    if remaining < 5:
        print(f"\n⚠️  Only {remaining} requests remaining - skipping validation")
        print(f"💡 Found ASINs saved to utils/ folder")
        print(f"💡 You can manually test these ASINs later")
    else:
        print("\n\n" + "=" * 80)
        print("PHASE 2: Validating ASINs")
        print("=" * 80)
        
        to_validate = min(len(unique_products), remaining - 1, 10)
        print(f"Validating {to_validate} ASINs...")
        
        validated = []
        for idx, (asin, product) in enumerate(list(unique_products.items())[:to_validate], 1):
            if finder.request_count >= finder.max_requests - 1:
                print(f"\n⚠️  Approaching request limit, stopping validation")
                break
            
            print(f"\n[{idx}/{to_validate}] Validating {asin}...", end=" ")
            
            # Validate with same safety
            url = f"{finder.base_url}/dp/{asin}"
            
            try:
                finder._ultra_safe_delay()
                finder.request_count += 1
                
                headers = finder._get_headers()
                response = finder.session.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    if "robot check" in response.text.lower():
                        print("🤖 Bot detected - stopping")
                        break
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    title_elem = soup.find('span', id='productTitle')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        print(f"✓ VALID")
                        print(f"    {title[:70]}")
                        product['validated_title'] = title
                        validated.append(product)
                    else:
                        print(f"✗ No title found")
                else:
                    print(f"✗ Status {response.status_code}")
                    
            except Exception as e:
                print(f"✗ Error: {e}")
        
        # Final save with validated ASINs
        if validated:
            finder.save_results(list(unique_products.values()), validated)
    
    # Final summary
    print("\n\n" + "=" * 80)
    print("✅ FINAL RESULTS")
    print("=" * 80)
    print(f"Total ASINs found: {len(unique_products)}")
    print(f"Categories searched: {min(category_count, len(ALL_CATEGORIES))}")
    print(f"Requests made: {finder.request_count}/{finder.max_requests}")
    
    if 'validated' in locals() and validated:
        print(f"Validated ASINs: {len(validated)}")
        print("\n📦 Validated ASINs:")
        for p in validated[:10]:  # Show first 10
            print(f"  • {p['asin']} - {p.get('validated_title', p['title'])[:60]}")
    
    print("\n📁 Results saved in utils/ folder:")
    print(f"   • all_asins_*.txt (all found ASINs)")
    if 'validated' in locals() and validated:
        print(f"   • validated_asins_*.txt (ready for config)")
        print(f"   • latest_validated_asins.txt (simple list)")
    
    print("\n" + "=" * 80)
    print("✅ Done!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Stopped by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        
        traceback.print_exc()
        