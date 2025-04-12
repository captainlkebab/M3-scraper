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
        return [line.strip() for line in f if line.strip()]

def extract_product_info():
    """Extracts product information from the current page."""
    products = driver.find_elements(By.CSS_SELECTOR, 'div[data-spec="main"]')
    product_list = []
    for product in products:
        try:
            # Title
            name_element = product.find_element(By.CSS_SELECTOR, 'h2 a span')
            product_name = name_element.text.strip() if name_element else 'N/A'

            # Price
            price_element = product.find_element(By.CSS_SELECTOR, 'div[data-spec="price-information"] div.body-2-bold')
            product_price = price_element.text.strip() if price_element else 'N/A'

            # Grade (looking for the grade label and value)
            grade_element = product.find_element(By.CSS_SELECTOR, '[data-test="condition-label"]')
            grade_label = grade_element.text.strip() if grade_element else 'N/A'

            # Additional information
            product_data = {
                'title': product_name,
                'price_with_currency': product_price,
                'backbox_grade_label': grade_label,
                'category_3': 'Laptop',  # This is usually fixed for laptop category
                'brand': product_name.split()[0] if product_name else 'N/A',
                'model': ' '.join(product_name.split()[1:3]) if product_name else 'N/A',
                'timestamp': time.strftime('%Y-%m-%d %H:%M')
            }
            product_list.append(product_data)

            print(f'Title: {product_data["title"]}')
            print(f'Price: {product_data["price_with_currency"]}')
            print(f'Grade: {product_data["backbox_grade_label"]}')
            print(f'Brand: {product_data["brand"]}')
            print(f'Model: {product_data["model"]}')
            print('-' * 40)

        except Exception as e:
            print(f"Error extracting product info: {e}")
            continue
    
    return product_list

def save_products(products, url):
    # Get current date for filenames
    date_str = time.strftime('%y%m%d')
    
    # Prepare paths
    output_dir = Path(__file__).parent / "Scraped"
    output_dir.mkdir(exist_ok=True)
    
    json_file = output_dir / f"backmarket_{date_str}.json"
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
    
    # Save JSON
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    # Save products CSV
    import csv
    if not products_csv.exists():
        with open(products_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['product_id', 'name', 'category', 'url'])
    
    with open(products_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for product in products:
            product_id = hash(product['name'] + url)
            category = url.split('/l/')[-1].split('/')[0] if '/l/' in url else 'unknown'
            writer.writerow([product_id, product['name'], category, url])
    
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

    # Test URL
    test_url = "https://www.backmarket.de/de-de/l/top-angebote-laptops/c8a1ab5c-5ec5-4475-981f-c4990f834d3b"
    
    try:
        print(f"Processing test URL: {test_url}")
        
        page_number = 0
        all_products = []
        while True:
            current_url = f'{test_url}?p={page_number}'
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

        # Save products for this test URL
        save_products(all_products, test_url)
        print(f"Saved data for test URL. Total products: {len(all_products)}")

    except Exception as e:
        print(f'Error processing test URL: {e}')

except Exception as e:
    print(f'An error occurred: {e}')

finally:
    driver.quit()
