import random
import time
import os
import json
import logging
import pandas as pd
from seleniumbase import Driver
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime

# Define the path variables first
current_dir = Path(__file__).parent
root_dir = current_dir.parent

# Setup logging
logs_dir = current_dir / "logs"
logs_dir.mkdir(exist_ok=True)
log_file = logs_dir / "backmarketscraper.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# === Setup ===
url_file_path = current_dir / "Sitemaps" / "backmarket_urls.txt"

# Create new folder structure
json_output_dir = current_dir / "scraped"
json_output_dir.mkdir(parents=True, exist_ok=True)

# Generate filename with date format YYMMDD
date_str = datetime.now().strftime("%y%m%d")
output_json_path = json_output_dir / f"Backmarket_{date_str}.json"
output_products_csv = json_output_dir / f"backmarket_{date_str}_products.csv"
output_prices_csv = json_output_dir / f"backmarket_{date_str}_prices.csv"

# === Load URLs ===
with open(url_file_path, "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

# === Init Output ===
# Load existing data if file exists
all_products = []
if output_json_path.exists():
    try:
        with open(output_json_path, "r", encoding="utf-8") as f:
            all_products = json.load(f)
        logging.info(f"Loaded {len(all_products)} existing products from {output_json_path}")
    except Exception as e:
        logging.error(f"Error loading existing JSON: {str(e)}")

# === Start Browser ===
driver = Driver(uc=True, undetectable=True, incognito=True, headless=False)

def is_blocked(html):
    return "thunk.js" in html or len(html.strip()) < 1000

# Function to save current data to JSON
def save_current_data():
    try:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(all_products, f, indent=2, ensure_ascii=False)
        logging.info(f"Updated JSON with {len(all_products)} products at {output_json_path}")
        
        # Create dataframes for CSV export
        products_data = []
        prices_data = []
        
        for product in all_products:
            # Map grade codes
            grade_mapping = {"Gut": "C", "Sehr gut": "B", "Hervorragend": "A"}
            
            # Get price value without the euro symbol
            price_value = ""
            if product.get("main_price"):
                price_value = product.get("main_price", "").replace(" €", "")
                
                # Only include products with valid prices in both CSVs
                if price_value and price_value != "Ausverkauft":
                    # Add to prices CSV
                    price_entry = {
                        "Price": price_value,
                        "CurrencyIso": "EUR",
                        "TimeOfChange": product["scraped_at"],
                        "Url": product["url"]              
                        }
                    prices_data.append(price_entry)
                    
                    # Determine the grade code based on price_by_grade
                    grade_code = ""
                    for grade, price in product.get("price_by_grade", {}).items():
                        if price == product["main_price"]:
                            grade_code = grade_mapping.get(grade, "")
                            break
                    
                    # Add to products CSV
                    base_product = {
                        "Title": product["name"],
                        "Price": price_value,
                        "CurrencyIso": "EUR",
                        "Url": product["url"],
                        "Refurbished": True,
                        "Model": "",  # Leave model field empty
                        "MPN": "",
                        "Brand": product.get("brand", ""),  # Use the brand from the product data
                        "UpdateTime": product["scraped_at"],
                        "Category": product.get("category", ""),
                        "Source": "25",
                        "Grade": grade_code  # Set the grade code
                    }
                    products_data.append(base_product)
        
        # Save to CSV
        products_df = pd.DataFrame(products_data)
        prices_df = pd.DataFrame(prices_data)
        
        products_df.to_csv(output_products_csv, index=False, encoding="utf-8")
        prices_df.to_csv(output_prices_csv, index=False, encoding="utf-8")
        
        logging.info(f"Saved {len(products_data)} products to {output_products_csv}")
        logging.info(f"Saved {len(prices_data)} prices to {output_prices_csv}")
        
    except Exception as e:
        logging.error(f"Error saving data: {str(e)}")

# === Loop over URLs ===
for idx, url in enumerate(urls, start=1):
    try:
        logging.info(f"[{idx}] Visiting: {url}")
        driver.uc_open_with_reconnect(url, reconnect_time=4)
        time.sleep(random.uniform(5, 9))

        try:
            driver.uc_gui_click_captcha()
            time.sleep(3)
        except Exception:
            pass

        html = driver.get_page_source()

        # === Parse HTML ===
        if is_blocked(html):
            logging.warning(f"[{idx}] Page blocked or empty.")
            continue

        soup = BeautifulSoup(html, "html.parser")

        # === Extract Content ===
        product_name = soup.find("h1", class_="heading-1")

        # Extract category using the provided selector
        category_element = soup.select_one('li.text-action-default-hi:nth-child(2) > a:nth-child(1) > span:nth-child(2)')
        category = category_element.get_text(strip=True) if category_element else None
        
        # find all condition labels
        grade_spans = soup.find_all("span", class_="body-1") + soup.find_all("span", class_="body-1-bold")
        price_by_grade = {}
        valid_grades = {"Gut", "Sehr gut", "Hervorragend"}

        for grade in grade_spans:
            grade_text = grade.get_text(strip=True)
            if grade_text in valid_grades:
                next_price = grade.find_next_sibling("span", class_="body-2")
                if next_price:
                    price_text = next_price.get_text(strip=True).replace("\xa0€", " €")
                    price_by_grade[grade_text] = price_text

        # fallback main price (e.g. top of page)
        main_price = soup.find("span", {"data-qa": "productpage-product-price"})
        main_price_text = main_price.get_text(strip=True).replace("\xa0€", " €") if main_price else None

        # Extract brand from title
        brand = None
        if product_name:
            product_name_text = product_name.get_text(strip=True)
            # Get the first word which is typically the brand
            brand = product_name_text.split()[0] if product_name_text else None

        product_data = {
            "url": url,
            "name": product_name.get_text(strip=True) if product_name else None,
            "main_price": main_price_text,
            "price_by_grade": price_by_grade,
            "category": category,
            "brand": brand,
            "scraped_at": datetime.now().isoformat()
        }
        all_products.append(product_data)
        logging.info(f"[{idx}] Extracted: {product_data['name']} - {product_data['main_price']} - Category: {category}")
        
        # Save after each successful scrape
        save_current_data()

    except Exception as e:
        logging.error(f"[{idx}] Failed: {e}")

# Final save (though it should already be saved)
save_current_data()
logging.info(f"Scraping completed. Total products: {len(all_products)}")
driver.quit()