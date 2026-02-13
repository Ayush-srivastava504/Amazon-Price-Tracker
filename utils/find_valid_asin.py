import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import List, Dict, Tuple
from urllib.parse import quote_plus
from pathlib import Path
from datetime import datetime

class ASINValidator:
    
    @staticmethod
    def is_valid(asin: str) -> Tuple[bool, str]:
        if not asin:
            return False, "Empty ASIN"
        
        asin = str(asin).strip()
        
        # Check length
        if len(asin) != 10:
            return False, f"Invalid length: {len(asin)} (must be 10)"
        
        # Check alphanumeric only
        if not asin.isalnum():
            return False, "Contains non-alphanumeric characters"
        
        # Check for common patterns that suggest invalid ASINs
        if asin.isdigit():
            return False, "All digits (should have letters)"
        
        if asin.isalpha():
            return False, "All letters (should have digits)"
        
        # Check for repeated characters (sometimes indicates parsing error)
        if len(set(asin)) <= 2:
            return False, "Too few unique characters"
        
        return True, "Valid"
    
    @staticmethod
    def validate_batch(asins: List[str]) -> Dict:
        """Validate multiple ASINs and return summary"""
        results = {
            'valid': [],
            'invalid': [],
            'valid_count': 0,
            'invalid_count': 0
        }
        
        for asin in asins:
            is_valid, reason = ASINValidator.is_valid(asin)
            if is_valid:
                results['valid'].append(asin)
                results['valid_count'] += 1
            else:
                results['invalid'].append({'asin': asin, 'reason': reason})
                results['invalid_count'] += 1
        
        return results


class VolatileProductFinder:
    
    def __init__(self):
        self.base_url = "https://www.amazon.in"
        self.session = self._create_session()
        self.request_count = 0
        self.max_requests = 25
        self.utils_dir = Path("utils")
        self.utils_dir.mkdir(exist_ok=True)
        self.asin_validator = ASINValidator()
        self.validation_stats = {
            'total_parsed': 0,
            'valid_asins': 0,
            'invalid_asins': 0
        }
        
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        ]
        return session
    
    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.amazon.in/",
        }
    
    def _wait(self):
        if self.request_count <= 5:
            base = 7.0
        elif self.request_count <= 10:
            base = 9.0
        elif self.request_count <= 15:
            base = 11.0
        else:
            base = 13.0
        
        delay = random.uniform(base, base + 4.0)
        print(f"  waiting {delay:.1f}s... ({self.request_count + 1}/{self.max_requests})")
        time.sleep(delay)
    
    def search(self, term: str, max_results: int = 4) -> List[Dict]:
        if self.request_count >= self.max_requests:
            print(f"  reached limit")
            return []
        
        print(f"searching: {term}")
        url = f"{self.base_url}/s?k={quote_plus(term)}"
        
        for attempt in range(1, 3):
            try:
                self._wait()
                self.request_count += 1
                
                headers = self._get_headers()
                response = self.session.get(url, headers=headers, timeout=20)
                
                if response.status_code == 200:
                    products = self._parse_products(response.text, term, max_results)
                    if products:
                        print(f"  found {len(products)} items")
                    else:
                        print(f"  no items found")
                    return products
                
                elif response.status_code == 503:
                    print(f"  got 503, stopping")
                    self.request_count = self.max_requests
                    return []
                
                elif response.status_code == 429:
                    print(f"  rate limited")
                    self.request_count = self.max_requests
                    return []
                
                else:
                    print(f"  status {response.status_code}")
                    if attempt < 2:
                        time.sleep(25)
                    return []
                    
            except requests.exceptions.Timeout:
                print(f"  timeout (attempt {attempt})")
                if attempt < 2:
                    time.sleep(15)
                continue
            
            except Exception as e:
                print(f"  error: {str(e)[:50]}")
                return []
        
        return []
    
    def _parse_products(self, html: str, search_term: str, max_results: int) -> List[Dict]:
        
        html_lower = html.lower()
        if any(x in html_lower for x in ["robot check", "enter the characters", "captcha"]):
            print(f"  bot detection - stopping all")
            self.request_count = self.max_requests
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        for item in soup.find_all('div', {'data-asin': True}):
            asin = item.get('data-asin')
            self.validation_stats['total_parsed'] += 1
            
            # Validate ASIN
            is_valid, reason = self.asin_validator.is_valid(asin)
            
            if not is_valid:
                self.validation_stats['invalid_asins'] += 1
                continue
            
            self.validation_stats['valid_asins'] += 1
            
            title_elem = item.find('span', class_='a-text-normal')
            if not title_elem:
                title_elem = item.find('h2')
            
            title = "product"
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            products.append({
                'asin': asin,
                'title': title[:90],
                'url': f"{self.base_url}/dp/{asin}",
                'search': search_term,
                'valid': True
            })
            
            if len(products) >= max_results:
                break
        
        return products
    
    def save_results(self, all_products: List[Dict]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = self.utils_dir / f"volatile_asins_{timestamp}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("VOLATILE PRODUCTS - AMAZON INDIA\n")
            f.write(f"generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n")
            f.write(f"Total ASIN Candidates Parsed: {self.validation_stats['total_parsed']}\n")
            f.write(f"Valid ASINs: {self.validation_stats['valid_asins']}\n")
            f.write(f"Invalid ASINs (filtered): {self.validation_stats['invalid_asins']}\n")
            f.write("=" * 70 + "\n\n")
            
            by_category = {}
            for p in all_products:
                cat = p.get('search', 'other')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(p)
            
            for cat, items in by_category.items():
                f.write(f"\n{cat}\n")
                f.write("-" * 70 + "\n")
                for p in items:
                    f.write(f"ASIN: {p['asin']}\n")
                    f.write(f"Title: {p['title']}\n")
                    f.write(f"URL: {p['url']}\n")
                    f.write(f"Valid: {p['valid']}\n\n")
        
        print(f"\nsaved to: {output_file}")
        
        # simple list for quick reference
        simple_file = self.utils_dir / "asins_list.txt"
        with open(simple_file, 'w', encoding='utf-8') as f:
            for p in all_products:
                f.write(f"{p['asin']} - {p['title'][:60]}\n")
        
        print(f"saved list to: {simple_file}")
        
        # validation report
        validation_file = self.utils_dir / f"validation_report_{timestamp}.txt"
        with open(validation_file, 'w', encoding='utf-8') as f:
            f.write("ASIN VALIDATION REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Total Parsed: {self.validation_stats['total_parsed']}\n")
            f.write(f"Valid: {self.validation_stats['valid_asins']}\n")
            f.write(f"Invalid: {self.validation_stats['invalid_asins']}\n")
            if self.validation_stats['total_parsed'] > 0:
                validity_rate = (self.validation_stats['valid_asins'] / self.validation_stats['total_parsed']) * 100
                f.write(f"Validity Rate: {validity_rate:.1f}%\n")
        
        print(f"saved validation report to: {validation_file}")


# VOLATILE / TRENDING PRODUCTS - daily price changes, deals, tech
VOLATILE_PRODUCTS = {
    'Budget Phones': [
        'realme 12 pro plus',
        'redmi note 13',
        'samsung galaxy m33',
    ],
    'Earbuds & Audio': [
        'boAt Airdopes 131',
        'noise earbuds under 2000',
        'JBL earphones budget',
    ],
    'Power Banks': [
        'Mi 20000mah power bank',
        'realme 30000 power bank',
        'OnePlus power bank fast charging',
    ],
    'Smartwatches': [
        'noise smartwatch',
        'fire boltt smartwatch',
        'amazfit band',
    ],
    'Chargers & Cables': [
        '65W fast charger',
        'type c cable bundle',
        '20W USB charger',
    ],
    'Memory Cards': [
        'sandisk 256gb sd card',
        'Kingston 128gb microsd',
        'WD memory card',
    ],
    'Wireless Routers': [
        'TP-Link wifi router',
        'realme mesh router',
        'tenda wifi extender',
    ],
    'Camera Accessories': [
        'ring light stand',
        'tripod camera',
        'phone gimbal stabilizer',
    ],
    'Gaming Gear': [
        'gaming mouse under 1000',
        'mechanical keyboard budget',
        'gamepad wireless',
    ],
    'Air Purifiers': [
        'MI air purifier 3',
        'coway air purifier',
        'honeywell air purifier',
    ],
    'Fitness Trackers': [
        'fitness band under 1500',
        'smart activity tracker',
        'heart rate monitor band',
    ],
    'Laptop Accessories': [
        'laptop cooling pad',
        'USB hub type c',
        'laptop stand adjustable',
    ],
}


def main():
    print("\n" + "=" * 70)
    print("VOLATILE PRODUCT FINDER - Amazon India (with ASIN Validation)")
    print("=" * 70)
    print("\nthis finds trending/volatile products with daily price changes")
    print("will check 12 categories across 24+ searches")
    print("includes ASIN validation to filter invalid entries")
    print("takes about 5-8 minutes")
    print("\n" + "=" * 70 + "\n")
    
    input("press enter to start...")
    
    finder = VolatileProductFinder()
    all_products = []
    
    print("\n" + "=" * 70)
    print("PHASE 1: COLLECTING ASINS (with validation)")
    print("=" * 70 + "\n")
    
    categories_done = 0
    max_cats = 10
    
    for category, terms in VOLATILE_PRODUCTS.items():
        if categories_done >= max_cats:
            print(f"reached category limit ({max_cats})")
            break
        
        if finder.request_count >= finder.max_requests:
            print("reached request limit")
            break
        
        print(f"\n{category}")
        print("-" * 70)
        
        cat_products = []
        
        for term in terms[:2]:
            if finder.request_count >= finder.max_requests:
                break
            
            products = finder.search(term, max_results=4)
            
            if products:
                cat_products.extend(products)
            
            if finder.request_count >= finder.max_requests:
                break
        
        if cat_products:
            all_products.extend(cat_products)
            categories_done += 1
        
        if finder.request_count >= finder.max_requests:
            break
    
    # dedupe
    unique = {p['asin']: p for p in all_products}
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"total asins: {len(unique)}")
    print(f"requests used: {finder.request_count}/{finder.max_requests}")
    print(f"categories: {categories_done}")
    print(f"\nValidation Stats:")
    print(f"  Total Parsed: {finder.validation_stats['total_parsed']}")
    print(f"  Valid: {finder.validation_stats['valid_asins']}")
    print(f"  Invalid (filtered): {finder.validation_stats['invalid_asins']}")
    
    if finder.validation_stats['total_parsed'] > 0:
        validity_rate = (finder.validation_stats['valid_asins'] / finder.validation_stats['total_parsed']) * 100
        print(f"  Validity Rate: {validity_rate:.1f}%")
    
    if not unique:
        print("\nno items found")
        print("\ntry again later if you got blocked")
        return
    
    finder.save_results(list(unique.values()))
    
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    
    print(f"\nfound {len(unique)} validated products")
    print("check utils/ folder for results")
    
    print("\nfirst 10 asins:")
    for p in list(unique.values())[:10]:
        print(f"  {p['asin']} - {p['title'][:50]}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nstopped")
    except Exception as e:
        print(f"\nerror: {e}")
        import traceback
        traceback.print_exc()