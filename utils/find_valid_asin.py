import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import List, Dict
from urllib.parse import quote_plus
from pathlib import Path
from datetime import datetime

class VolatileProductFinder:
    
    def __init__(self):
        self.base_url = "https://www.amazon.in"
        self.session = self._create_session()
        self.request_count = 0
        self.max_requests = 25
        self.utils_dir = Path("utils")
        self.utils_dir.mkdir(exist_ok=True)
        
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
            
            if not asin or len(asin) != 10:
                continue
            
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
                'search': search_term
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
                    f.write(f"URL: {p['url']}\n\n")
        
        print(f"\nsaved to: {output_file}")
        
        # simple list for quick reference
        simple_file = self.utils_dir / "asins_list.txt"
        with open(simple_file, 'w', encoding='utf-8') as f:
            for p in all_products:
                f.write(f"{p['asin']} - {p['title'][:60]}\n")
        
        print(f"saved list to: {simple_file}")


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
    print("VOLATILE PRODUCT FINDER - Amazon India")
    print("=" * 70)
    print("\nthis finds trending/volatile products with daily price changes")
    print("will check 12 categories across 24+ searches")
    print("takes about 5-8 minutes")
    print("\n" + "=" * 70 + "\n")
    
    input("press enter to start...")
    
    finder = VolatileProductFinder()
    all_products = []
    
    print("\n" + "=" * 70)
    print("PHASE 1: COLLECTING ASINS")
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
    
    if not unique:
        print("\nno items found")
        print("\ntry again later if you got blocked")
        return
    
    finder.save_results(list(unique.values()))
    
    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    
    print(f"\nfound {len(unique)} products")
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