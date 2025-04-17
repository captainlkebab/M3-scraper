import requests
from bs4 import BeautifulSoup
import json
import time
from typing import Dict, Optional
import logging
from pathlib import Path
from datetime import datetime
import uuid
import csv



class RefurbedScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.base_url = "https://www.refurbed.de"
        self.setup_logging()

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging with file in logs directory
        log_file = log_dir / f"refurbed_scraper_{datetime.now().strftime('%y%m%d')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")
            return None

    def extract_product_info(self, url: str) -> Dict:
        soup = self.get_soup(url)
        if not soup:
            return {}

        try:
            # Extract product information from JSON data
            full_data = self._extract_json_data(soup) or {}
            offer_data = full_data.get("offer") or {}
            item_data = full_data.get("item") or {}
            
            # Helper function to filter out NOT-AVAILABLE
            def filter_value(value):
                return value if value != "NOT-AVAILABLE" else None
            
            # Create offer dict with only available fields
            offer = {
                key: value for key, value in {
                    "grading": offer_data.get("grading"),
                    "price": offer_data.get("price") or "NOT-AVAILABLE",  # Keep NOT-AVAILABLE for price
                    "merchant_name": offer_data.get("merchant_name"),
                    "merchant_country": offer_data.get("merchant_country"),
                    "sku": offer_data.get("sku")
                }.items() if value and value != "NOT-AVAILABLE" or key == "price"
            }

            # Create item dict with only available fields
            item = {
                key: value for key, value in {
                    "item_name": item_data.get("item_name"),
                    "price": item_data.get("price"),
                    "price2": item_data.get("price2"),
                    "currency": item_data.get("currency"),
                    "item_brand": item_data.get("item_brand"),
                    "item_variant": item_data.get("item_variant"),
                    "quantity": item_data.get("quantity"),
                    "merchant_id": item_data.get("merchant_id"),
                    "item_category2": item_data.get("item_category2"),
                    "color": item_data.get("color"),
                    "memory_size": item_data.get("memory_size"),
                    "grade": item_data.get("grade"),
                    "color_options": item_data.get("color_options"),
                    "memory_size_options": item_data.get("memory_size_options"),
                    "grading_options": item_data.get("grading_options"),
                    "connectivity": item_data.get("connectivity"),
                    "graphic_card": item_data.get("graphic_card"),
                    "keyboard_layout": item_data.get("keyboard_layout"),
                    "number_of_cores": item_data.get("number_of_cores"),
                    "processors": item_data.get("processors"),
                    "processor_clock_speed": item_data.get("processor_clock_speed"),
                    "ram_size": item_data.get("ram_size"),
                    "os": item_data.get("os"),
                    "touchscreen": item_data.get("touchscreen"),
                    "webcam": item_data.get("webcam"),
                    "backlit_keyboard": item_data.get("backlit_keyboard")
                }.items() if value and value != "NOT-AVAILABLE"
            }

            # Create filtered data with only available fields
            filtered_data = {
                "url": url,
                "title": self._get_text(soup.find('h1'))
            }
            
            if offer:
                filtered_data["offer"] = offer
            if item:
                filtered_data["item"] = item
            
            return filtered_data
        except Exception as e:
            logging.error(f"Error extracting data from {url}: {str(e)}")
            return {}

    def _extract_json_data(self, soup) -> Dict:
        """Extract product data from JSON script tags"""
        try:
            # Look for the gtmData script
            scripts = soup.find_all('script', {'type': 'text/javascript'})
            for script in scripts:
                script_text = script.string
                if script_text and 'gtmData' in script_text:
                    # Extract the JSON data
                    start_idx = script_text.find('var gtmData = ') + len('var gtmData = ')
                    end_idx = script_text.find('};', start_idx) + 1
                    if start_idx > 0 and end_idx > 0:
                        json_str = script_text[start_idx:end_idx]
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError:
                            logging.warning("Failed to parse JSON data from script")
            
            # Look for structured data in ld+json scripts
            ld_json_scripts = soup.find_all('script', {'type': 'application/ld+json'})
            for script in ld_json_scripts:
                try:
                    return json.loads(script.string)
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            return {}
        except Exception as e:
            logging.error(f"Error extracting JSON data: {str(e)}")
            return {}

    def _parse_section(self, section) -> Dict:
        """Parse a section into a structured format"""
        if not section:
            return {}
        
        result = {
            'id': section.get('id', ''),
            'class': section.get('class', ''),
            'heading': self._get_section_heading(section),
            'text_content': self._get_text(section),
            'paragraphs': [self._get_text(p) for p in section.find_all('p')],
            'lists': self._get_lists(section),
            'tables': self._get_tables(section)
        }
        
        # Extract subsections if any
        subsections = section.find_all(['section', 'div'], recursive=False)
        if subsections:
            result['subsections'] = [self._parse_section(subsection) for subsection in subsections]
        
        return result

    def _get_section_heading(self, section) -> Optional[str]:
        """Extract the heading from a section"""
        for i in range(1, 7):
            heading = section.find(f'h{i}')
            if heading:
                return self._get_text(heading)
        return None

    def _get_lists(self, section) -> list:
        """Extract lists from a section"""
        lists = []
        for list_tag in section.find_all(['ul', 'ol']):
            items = [self._get_text(li) for li in list_tag.find_all('li')]
            if items:
                lists.append({
                    'type': list_tag.name,
                    'items': items
                })
        return lists

    def _get_tables(self, section) -> list:
        """Extract tables from a section"""
        tables = []
        for table in section.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [self._get_text(cell) for cell in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)
        return tables

    def _get_text(self, element) -> Optional[str]:
        return element.get_text(strip=True) if element else None

    def scrape_urls_from_file(self, file_path: str, output_file: str):
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]

            results = []
            for i, url in enumerate(urls, 1):
                logging.info(f"Scraping {i}/{len(urls)}: {url}")
                product_info = self.extract_product_info(url)
                if product_info:
                    results.append(product_info)
                time.sleep(1)  # Polite delay between requests

            # Save results
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

            logging.info(f"Scraping completed. Saved {len(results)} products to {output_file}")

        except Exception as e:
            logging.error(f"Error in scrape_urls_from_file: {str(e)}")

    def save_to_structured_files(self, results: list, output_dir: Path):
        timestamp = datetime.now().strftime("%y%m%d")
        
        # Create products file
        products_file = output_dir / f"refurbed_{timestamp}_products.csv"

        with open(products_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Price', 'CurrencyIso', 'Url', 'Refurbished', 'Model', 'MPN', 'Brand', 'UpdateTime', 'Category', 'Source', 'Grade'])
            
            for result in results:
                item_data = result.get('item', {})
                offer_data = result.get('offer', {})
                price = offer_data.get('price')
                
                if price and price != 'NOT-AVAILABLE':
                    try:
                        price_float = float(str(price).replace(',', '.'))
                        
                        writer.writerow([
                            item_data.get('item_name') or None,  # Use item_name for Title
                            price_float,
                            'EUR',
                            result['url'],
                            True,
                            item_data.get('item_variant') or None,  # Use item_variant for Model
                            offer_data.get('sku') or None,
                            item_data.get('item_brand') or None,
                            datetime.now().isoformat(),
                            item_data.get('item_category2') or None,
                            50,
                            offer_data.get('grading') or None
                        ])
                    except (ValueError, TypeError):
                        continue
        
        # Create price entries file
        prices_file = output_dir / f"refurbed_{timestamp}_prices.csv"
        with open(prices_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Price', 'CurrencyIso', 'TimeOfChange', 'Url'])
            
            for result in results:
                offer_data = result.get('offer', {})
                price = offer_data.get('price')
                
                if price and price != 'NOT-AVAILABLE':
                    try:
                        price_float = float(str(price).replace(',', '.'))
                        writer.writerow([
                            price_float,
                            'EUR',
                            datetime.now().isoformat(),
                            result['url']
                        ])
                    except (ValueError, TypeError):
                        continue

# Modify main execution code
if __name__ == "__main__":
    scraper = RefurbedScraper()
    
    # Create Scraped directory if it doesn't exist
    output_dir = Path(__file__).parent / "Scraped"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run on all URLs - updated to use Sitemaps folder
    urls_file = Path(__file__).parent / "Sitemaps" / "refurbed_urls.txt"
    print(f"Starting to scrape URLs from: {urls_file}")
    
    try:
        with open(urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        total_urls = len(urls)
        results = []
        for i, url in enumerate(urls, 1):
            logging.info(f"Scraping {i}/{total_urls}: {url}")
            product_info = scraper.extract_product_info(url)
            if product_info:
                results.append(product_info)
            time.sleep(1)

        # Save both JSON and structured files
        json_output_file = output_dir / f"Refurbed_{datetime.now().strftime('%y%m%d')}.json"
        with open(json_output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Also save to docs folder for the web interface
        docs_dir = Path(__file__).parent.parent / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        docs_json_file = docs_dir / f"Refurbed_{datetime.now().strftime('%y%m%d')}.json"
        with open(docs_json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        scraper.save_to_structured_files(results, output_dir)
        logging.info(f"Scraping completed. Saved {len(results)} products in {json_output_file} and {docs_json_file}")
    except FileNotFoundError:
        logging.error(f"URL file not found: {urls_file}. Make sure the sitemap_fetcher has been run first.")
    except Exception as e:
        logging.error(f"Error during scraping process: {str(e)}")