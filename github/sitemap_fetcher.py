import requests
import xml.etree.ElementTree as ET
import logging
from pathlib import Path
import re

class SitemapFetcher:
    def __init__(self):
        self.sitemaps = {
            'Refurbed': "https://www.refurbed.de/sitemap-marketplace.xml",
            
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.notebook_identifiers = [
            'macbook', 'thinkpad', 'ideapad', 'probook', 'elitebook', 'zenbook', 
            'vivobook', 'inspiron', 'latitude', 'xps', 'pavilion', 'envy', 'spectre',
            'chromebook', 'surface-laptop', 'surface-book', 'yoga', 'legion', 'omen',
            'alienware', 'predator', 'swift', 'aspire', 'gram', 'notebook', 'laptop'
        ]
        self.phone_identifiers = [
            'iphone', 'galaxy-s', 'galaxy-note', 'galaxy-a', 'galaxy-z', 'pixel', 
            'oneplus', 'mi-', 'redmi', 'poco', 'huawei-p', 'huawei-mate', 'honor', 
            'xperia', 'nokia', 'moto', 'oppo', 'vivo', 'realme', 'smartphone'
        ]
        self.tablet_identifiers = [
            'ipad', 'galaxy-tab', 'surface-pro', 'surface-go', 'mediapad', 'matepad',
            'mi-pad', 'tab-', 'yoga-tab', 'lenovo-tab', 'tablet'
        ]
        self.monitor_identifiers = [
            'monitor', 'display', 'ultrasharp', 'odyssey', 'predator-x', 'rog-swift',
            'viewsonic', 'benq', 'acer-', 'lg-', 'samsung-', 'dell-', 'hp-'
        ]
        self.exclusion_identifiers = [
            'watch', 'gear', 'galaxy-watch', 'apple-watch', 'smartwatch', 'band', 
            'fitbit', 'airpods', 'headphone', 'earbuds', 'speaker', 'homepod',
            'echo', 'alexa', 'google-home', 'nest', 'router', 'modem', 'printer',
            'scanner', 'keyboard', 'mouse', 'trackpad', 'webcam', 'camera', 'lens',
            'charger', 'adapter', 'cable', 'case', 'cover', 'screen-protector','docking'
        ]
        self.setup_logging()

    def setup_logging(self):
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging with file in logs directory
        log_file = log_dir / "sitemap_fetcher.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def fetch_sitemap(self, url: str) -> str:
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            logging.info(f"Successfully fetched sitemap from {url}")
            return response.text
        except requests.RequestException as e:
            logging.error(f"Error fetching sitemap: {str(e)}")
            return ""

    def filter_urls(self, xml_content: str, source: str) -> list:
        filtered_urls = []
        excluded_urls = {}
        
        try:
            xml_content = re.sub(' xmlns="[^"]+"', '', xml_content, count=1)
            root = ET.fromstring(xml_content)
            
            all_identifiers = (self.notebook_identifiers + self.phone_identifiers + 
                             self.tablet_identifiers + self.monitor_identifiers)

            # Different XML structure for each source
            url_elements = root.findall('.//url/loc') if source == 'Refurbed' else root.findall('.//loc')

            for url_elem in url_elements:
                url = url_elem.text.strip()
                
                # Changed to look for /p/ in both sources
                if "/p/" in url:
                    url_lower = url.lower()
                    
                    # Track which exclusion pattern matched
                    for excl in self.exclusion_identifiers:
                        if excl in url_lower:
                            if excl not in excluded_urls:
                                excluded_urls[excl] = []
                            excluded_urls[excl].append(url)
                            break
                    
                    if any(excl in url_lower for excl in self.exclusion_identifiers):
                        continue
                    
                    if any(ident in url_lower for ident in all_identifiers):
                        filtered_urls.append(url)

            # Log exclusion summary
            logging.info(f"Found {len(filtered_urls)} relevant product URLs for {source}")
            logging.info(f"\nExclusion Summary for {source}:")
            for category, urls in excluded_urls.items():
                logging.info(f"{category}: {len(urls)} URLs")
                for url in urls[:3]:
                    logging.info(f"  Example: {url}")
                if len(urls) > 3:
                    logging.info(f"  ... and {len(urls) - 3} more")
            
            return filtered_urls

        except ET.ParseError as e:
            logging.error(f"XML parsing error for {source}: {str(e)}")
            return []

    def run(self):
        for source, url in self.sitemaps.items():
            # Fetch sitemap
            xml_content = self.fetch_sitemap(url)
            if not xml_content:
                continue

            # Filter URLs
            filtered_urls = self.filter_urls(xml_content, source)
            
            # Save URLs to file
            # Create Sitemaps directory if it doesn't exist
            sitemaps_dir = Path(__file__).parent / "Sitemaps"
            sitemaps_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = sitemaps_dir / f"{source.lower()}_urls.txt"
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    for url in filtered_urls:
                        f.write(f"{url}\n")
                logging.info(f"Successfully saved {len(filtered_urls)} URLs to {output_path}")
            except Exception as e:
                logging.error(f"Error saving URLs to file for {source}: {str(e)}")

if __name__ == "__main__":
    fetcher = SitemapFetcher()
    fetcher.run()