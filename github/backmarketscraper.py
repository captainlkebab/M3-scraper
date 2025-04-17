# Install selenium and download chromedriver for you browser version.
# Make sure that you put the chromedriver.exe in your PATH or provide the full path to it.
# I use it quite ofthen in my projects, so I have it in Windows PAth... otherwise you can set path to the location here in the code

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path
import json
import time
import random

def load_progress():
    progress_file = Path(__file__).parent / "scraping_progress.json"
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {"last_index": 0}

def save_progress(index):
    progress_file = Path(__file__).parent / "scraping_progress.json"
    with open(progress_file, 'w') as f:
        json.dump({"last_index": index}, f)

def get_links():
    links_file = Path(__file__).parent / "Sitemaps" / "backmarket_urls.txt"
    with open(links_file, 'r', encoding='utf-8') as f:
        # Only return the first 5 URLs
        return [line.strip() for line in f if line.strip()][:5]

def extract_product_info():
    """Extracts comprehensive product information from the current page."""
    products = driver.find_elements(By.CSS_SELECTOR, 'div[data-spec="main"]')
    product_list = []
    
    for product in products:
        try:
            # Basic product info
            name_element = product.find_element(By.CSS_SELECTOR, 'h2 a span')
            product_name = name_element.text.strip() if name_element else 'N/A'
            
            # Get product URL for detailed page
            link_element = product.find_element(By.CSS_SELECTOR, 'h2 a')
            product_url = link_element.get_attribute('href') if link_element else None
            
            # Price information
            price_element = product.find_element(By.CSS_SELECTOR, 'div[data-spec="price-information"] div.body-2-bold')
            product_price = price_element.text.strip() if price_element else 'N/A'
            
            # Try to get additional information
            try:
                condition_element = product.find_element(By.CSS_SELECTOR, 'div[data-test="condition-badge"]')
                condition = condition_element.text.strip() if condition_element else 'N/A'
            except:
                condition = 'N/A'
                
            try:
                rating_element = product.find_element(By.CSS_SELECTOR, 'div[data-test="rating"]')
                rating = rating_element.text.strip() if rating_element else 'N/A'
            except:
                rating = 'N/A'
                
            try:
                specs_elements = product.find_elements(By.CSS_SELECTOR, 'ul[data-test="specs"] li')
                specs = [spec.text.strip() for spec in specs_elements] if specs_elements else []
            except:
                specs = []
            
            # Create comprehensive product data
            product_data = {
                'name': product_name,
                'price': product_price,
                'url': product_url,
                'condition': condition,
                'rating': rating,
                'specifications': specs,
                'timestamp': time.strftime('%Y-%m-%d %H:%M')
            }
            
            # If we have a product URL, try to get more detailed info
            if product_url and random.random() < 0.3:  # Only do this for 30% of products to avoid detection
                try:
                    # Open product page in a new tab
                    driver.execute_script("window.open('');")
                    driver.switch_to.window(driver.window_handles[1])
                    driver.get(product_url)
                    
                    # Add random human-like delay
                    time.sleep(random.uniform(3, 7))
                    
                    # Extract detailed information
                    try:
                        description_element = driver.find_element(By.CSS_SELECTOR, 'div[data-test="product-description"]')
                        product_data['description'] = description_element.text.strip() if description_element else 'N/A'
                    except:
                        product_data['description'] = 'N/A'
                    
                    try:
                        detailed_specs = driver.find_elements(By.CSS_SELECTOR, 'div[data-test="product-specs"] div')
                        product_data['detailed_specs'] = [spec.text.strip() for spec in detailed_specs] if detailed_specs else []
                    except:
                        product_data['detailed_specs'] = []
                    
                    # Close tab and switch back
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    
                    # Add random delay to appear more human-like
                    time.sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    print(f"Error getting detailed info: {e}")
                    # Make sure we're back on the main tab
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
            
            product_list.append(product_data)
            print(f'Product Name: {product_name}')
            print(f'Price: {product_price}')
            print(f'Condition: {condition}')
            print('-' * 40)
            
        except Exception as e:
            print(f"Error processing product: {e}")
            continue
    
    return product_list

def save_products(products, url):
    # Get current date for filenames
    date_str = time.strftime('%y%m%d')
    
    # Prepare paths
    output_dir = Path(__file__).parent / "Scraped"
    output_dir.mkdir(exist_ok=True)
    
    # Also save to docs folder for web interface
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    json_file = output_dir / f"backmarket_{date_str}.json"
    docs_json_file = docs_dir / f"backmarket_{date_str}.json"
    products_csv = output_dir / f"backmarket_products_{date_str}.csv"
    prices_csv = output_dir / f"backmarket_prices_{date_str}.csv"
    
    # Load existing JSON data
    existing_data = []
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    # Prepare new entry
    new_entry = {
        'url': url,
        'products': products,
        'scrape_date': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    existing_data.append(new_entry)
    
    # Save JSON to both locations
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    with open(docs_json_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    # Save products CSV
    import csv
    if not products_csv.exists():
        with open(products_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['product_id', 'name', 'category', 'url', 'condition', 'rating'])
    
    with open(products_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for product in products:
            product_id = hash(product['name'] + url)
            category = url.split('/l/')[-1].split('/')[0] if '/l/' in url else 'unknown'
            writer.writerow([
                product_id, 
                product['name'], 
                category, 
                product.get('url', url),
                product.get('condition', 'N/A'),
                product.get('rating', 'N/A')
            ])
    
    # Save prices CSV
    if not prices_csv.exists():
        with open(prices_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['product_id', 'price', 'timestamp'])
    
    with open(prices_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for product in products:
            product_id = hash(product['name'] + url)
            price = product['price'].replace('€', '').replace(',', '.').strip()
            writer.writerow([product_id, price, time.strftime('%Y-%m-%d %H:%M:%S')])

try:
    # Initialize the undetected ChromeDriver
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument('--disable-gpu')
    options.add_argument("--start-maximized")
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = uc.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # Load only the first 5 links
    all_links = get_links()
    progress = load_progress()
    start_index = progress["last_index"]
    
    # Make sure we don't go beyond the 5 links we have
    if start_index >= len(all_links):
        start_index = 0
    
    print(f"Starting from index {start_index}")
    
    # Process remaining links from the 5
    batch_links = all_links[start_index:]
    batch_size = 10

    print(f"Starting from index {start_index}")
    
    batch_links = all_links[start_index:start_index + batch_size]
    
    for link in batch_links:
        try:
            print(f"Processing link {start_index + batch_links.index(link) + 1} of {len(all_links)}: {link}")
            
            page_number = 0
            all_products = []
            while True:
                current_url = f'{link}?p={page_number}'
                driver.get(current_url)
                time.sleep(random.uniform(5, 10))

                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-spec="main"]'))
                )

                products = extract_product_info()
                all_products.extend(products)

                next_button = driver.find_elements(By.CSS_SELECTOR, 'a[aria-label="Next"]')
                if not next_button:
                    break

                page_number += 1
                time.sleep(random.uniform(3, 7))

            # Save products immediately after processing all pages for this link
            save_products(all_products, link)
            print(f"Saved data for: {link}")
            time.sleep(random.uniform(4, 8))  # Random delay between links

        except Exception as e:
            print(f'Error processing link {link}: {e}')
            time.sleep(random.uniform(10, 15))  # Longer delay after error
            continue

    # Save progress after the batch
    save_progress(start_index + batch_size)
    print(f"Completed batch. Progress saved at index {start_index + batch_size}")
    time.sleep(random.uniform(5, 10))  # Random delay between batches

except Exception as e:
    print(f'An error occurred: {e}')

finally:
    driver.quit()
