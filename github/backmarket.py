from seleniumbase import SB
import os
from pathlib import Path
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re

# Path to the URLs file - with better path resolution
script_dir = Path(os.path.dirname(os.path.abspath(__file__)))
urls_file = script_dir / "Sitemaps" / "backmarket_urls.txt"

# Check if file exists, if not try alternative locations
if not urls_file.exists():
    # Try parent directory
    urls_file = script_dir.parent / "Sitemaps" / "backmarket_urls.txt"
    
    # If still not found, try another common location
    if not urls_file.exists():
        urls_file = script_dir / "github" / "Sitemaps" / "backmarket_urls.txt"

print(f"Looking for URLs file at: {urls_file}")
print(f"File exists: {urls_file.exists()}")

# Create output directory for results
output_dir = script_dir / "Scraped"
output_dir.mkdir(parents=True, exist_ok=True)

# Create a results file to store product data
results_file = output_dir / f"backmarket_products_{datetime.now().strftime('%y%m%d')}.json"
results = []

# Read all URLs from the file
if urls_file.exists():
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(urls)} URLs from {urls_file}")
    
    # Debug: Print the first few URLs to verify they're being loaded correctly
    print(f"First 5 URLs:")
    for i, url in enumerate(urls[:5]):
        print(f"URL {i+1}: {url}")
else:
    print(f"ERROR: URLs file not found at {urls_file}")
    urls = []

# Initialize the browser only once
with SB(uc=True, test=True, locale="en") as sb:
    # Process each URL
    for i, url in enumerate(urls):
        print(f"Processing URL {i+1}/{len(urls)}: {url}")
        try:
            # Navigate to the URL
            sb.activate_cdp_mode(url)
            
            # Handle captcha if present
            sb.uc_gui_click_captcha()
            
            # Wait for page to load completely
            sb.sleep(2)
            
            # Get the page HTML
            html_content = sb.get_page_source()
            
            # Use BeautifulSoup to parse the HTML directly
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract product information using BeautifulSoup
            try:
                # Extract product name - typically in the title tag
                title_tag = soup.find('title')
                product_name = title_tag.text.split('|')[0].strip() if title_tag else "Unknown Product"
                
                # Extract product title from h1
                h1_tag = soup.find('h1')
                product_title = h1_tag.text.strip() if h1_tag else product_name
                
                # Extract category - this might be in breadcrumbs or meta tags
                # For BackMarket, we might need to infer from the product name or URL
                category = "Unknown"
                if "Chromebook" in product_name:
                    category = "Chromebook"
                elif "Aspire" in product_name:
                    category = "Aspire Laptop"
                else:
                    category = "Laptop"  # Default category
                
                # Extract price - look for price elements
                price = "Unknown"
                price_elements = soup.select('[data-test="product-price"], .price, [itemprop="price"]')
                if price_elements:
                    price_text = price_elements[0].text.strip()
                    # Clean up price text (remove currency symbols, etc.)
                    price_match = re.search(r'(\d+[.,]\d+)', price_text)
                    if price_match:
                        price = price_match.group(1)
                
                # Extract brand
                brand = "Unknown"
                brand_elements = soup.select('.brand-name, [itemprop="brand"]')
                if brand_elements:
                    brand = brand_elements[0].text.strip()
                else:
                    # Try to extract brand from product name
                    common_brands = ["Acer", "Apple", "Asus", "Dell", "HP", "Lenovo", "Samsung", "Sony", "Toshiba"]
                    for b in common_brands:
                        if b.lower() in product_name.lower():
                            brand = b
                            break
                
                # Extract grading - BackMarket uses quality grades
                grading = "Unknown"
                grade_elements = soup.select('[data-test="product-condition"], .condition, [itemprop="condition"]')
                if grade_elements:
                    grading = grade_elements[0].text.strip()
                
                # Create product data dictionary
                product_data = {
                    "url": url,
                    "title": product_title,
                    "product_name": product_name,
                    "category": category,
                    "brand": brand,
                    "price": price,
                    "grading": grading,
                    "scraped_at": datetime.now().isoformat()
                }
                
                results.append(product_data)
                print(f"Extracted data: {product_data}")
                
                # Save intermediate results every 10 products
                if (i + 1) % 10 == 0:
                    with open(results_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2)
                    print(f"Saved intermediate results ({len(results)} products)")
                
            except Exception as e:
                print(f"Error extracting product data: {e}")
            
            # Add a random delay between requests to avoid being blocked
            delay = 2 + (i % 3)  # Varies between 2-4 seconds
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            # Continue with next URL instead of stopping
            continue
    
    # Save all extracted product data to a JSON file
    if results:
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"Saved {len(results)} product details to {results_file}")