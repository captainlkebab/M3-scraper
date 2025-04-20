import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
import json
import re

def fetch_sitemap(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching sitemap: {e}")
        return None

def parse_and_group_urls(xml_content):
    xml_content = re.sub(' xmlns="[^"]+"', '', xml_content, count=1)
    root = ET.fromstring(xml_content)
    
    # Group URLs by their path component after de-de/
    url_groups = defaultdict(list)
    
    for url_elem in root.findall('.//loc'):
        url = url_elem.text.strip()
        # Extract path after de-de/
        match = re.search(r'backmarket\.de/de-de/([^/]+)', url)
        if match:
            group = match.group(1)
            url_groups[group].append(url)
    
    return url_groups

def save_grouped_urls(url_groups):
    output_dir = Path(__file__).parent / "Sitemaps"
    output_dir.mkdir(exist_ok=True)
    
    # Save detailed JSON with all groups
    json_file = output_dir / "backmarket_grouped_urls.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(dict(url_groups), f, ensure_ascii=False, indent=2)
    
    # Save summary
    summary_file = output_dir / "backmarket_url_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("BackMarket URL Groups Summary (grouped by path after de-de/):\n")
        f.write("=" * 50 + "\n\n")
        for group, urls in url_groups.items():
            f.write(f"Group '{group}': {len(urls)} URLs\n")
            f.write("Example URLs:\n")
            for url in urls[:3]:  # Show first 3 examples
                f.write(f"  {url}\n")
            f.write("\n")

def main():
    sitemap_url = "https://www.backmarket.de/sitemap_1.xml"
    print("Fetching sitemap...")
    
    xml_content = fetch_sitemap(sitemap_url)
    if not xml_content:
        return
    
    print("Parsing and grouping URLs...")
    url_groups = parse_and_group_urls(xml_content)
    
    print("\nURL Groups Summary:")
    for group, urls in url_groups.items():
        print(f"Group '{group}': {len(urls)} URLs")
    
    save_grouped_urls(url_groups)
    print("\nDetailed results saved in Sitemaps/backmarket_grouped_urls.json")
    print("Summary saved in Sitemaps/backmarket_url_summary.txt")

if __name__ == "__main__":
    main()