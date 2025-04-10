import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import os
import glob

class DatabaseUploader:
    def __init__(self, db_path=None):
        """Initialize the database uploader with an optional database path."""
        if db_path is None:
            # Default database path in the same directory as this script
            db_path = Path(__file__).parent / "products.db"
        
        self.db_path = db_path
        self.setup_logging()
        self.setup_database()
    
    def setup_logging(self):
        """Set up logging configuration."""
        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Set up logging with file in logs directory
        log_file = log_dir / "db_uploader.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def setup_database(self):
        """Create database tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create products table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                price REAL,
                currency_iso TEXT,
                url TEXT UNIQUE,
                refurbished BOOLEAN,
                model TEXT,
                mpn TEXT,
                brand TEXT,
                update_time TEXT,
                category TEXT,
                source INTEGER,
                grade TEXT
            )
            ''')
            
            # Create price_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price REAL,
                currency_iso TEXT,
                time_of_change TEXT,
                url TEXT,
                FOREIGN KEY (url) REFERENCES products(url)
            )
            ''')
            
            conn.commit()
            logging.info(f"Database setup complete at {self.db_path}")
        except Exception as e:
            logging.error(f"Error setting up database: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def upload_products(self, csv_file):
        """Upload product data from CSV to the database."""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # For each row in the dataframe
            for _, row in df.iterrows():
                try:
                    # Check if product with this URL already exists
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM products WHERE url = ?", (row['Url'],))
                    existing_product = cursor.fetchone()
                    
                    if existing_product:
                        # Update existing product
                        cursor.execute('''
                        UPDATE products 
                        SET title = ?, price = ?, currency_iso = ?, refurbished = ?,
                            model = ?, mpn = ?, brand = ?, update_time = ?,
                            category = ?, source = ?, grade = ?
                        WHERE url = ?
                        ''', (
                            row['Title'], row['Price'], row['CurrencyIso'], row['Refurbished'],
                            row['Model'], row['MPN'], row['Brand'], row['UpdateTime'],
                            row['Category'], row['Source'], row['Grade'], row['Url']
                        ))
                    else:
                        # Insert new product
                        cursor.execute('''
                        INSERT INTO products (
                            title, price, currency_iso, url, refurbished,
                            model, mpn, brand, update_time, category, source, grade
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            row['Title'], row['Price'], row['CurrencyIso'], row['Url'], row['Refurbished'],
                            row['Model'], row['MPN'], row['Brand'], row['UpdateTime'],
                            row['Category'], row['Source'], row['Grade']
                        ))
                    
                    conn.commit()
                except Exception as e:
                    logging.error(f"Error processing product {row['Url']}: {str(e)}")
                    conn.rollback()
            
            logging.info(f"Successfully uploaded products from {csv_file}")
        except Exception as e:
            logging.error(f"Error uploading products from {csv_file}: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def upload_price_history(self, csv_file):
        """Upload price history data from CSV to the database."""
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            
            # For each row in the dataframe
            for _, row in df.iterrows():
                try:
                    # Insert price history entry
                    cursor = conn.cursor()
                    cursor.execute('''
                    INSERT INTO price_history (
                        price, currency_iso, time_of_change, url
                    ) VALUES (?, ?, ?, ?)
                    ''', (
                        row['Price'], row['CurrencyIso'], row['TimeOfChange'], row['Url']
                    ))
                    
                    conn.commit()
                except Exception as e:
                    logging.error(f"Error processing price history for {row['Url']}: {str(e)}")
                    conn.rollback()
            
            logging.info(f"Successfully uploaded price history from {csv_file}")
        except Exception as e:
            logging.error(f"Error uploading price history from {csv_file}: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def process_latest_files(self):
        """Process the latest product and price files."""
        try:
            scraped_dir = Path(__file__).parent / "Scraped"
            
            # Find the latest products file
            product_files = list(scraped_dir.glob("refurbed_*_products.csv"))
            if product_files:
                latest_product_file = max(product_files, key=os.path.getmtime)
                self.upload_products(latest_product_file)
                logging.info(f"Processed latest product file: {latest_product_file}")
            else:
                logging.warning("No product files found")
            
            # Find the latest prices file
            price_files = list(scraped_dir.glob("refurbed_*_prices.csv"))
            if price_files:
                latest_price_file = max(price_files, key=os.path.getmtime)
                self.upload_price_history(latest_price_file)
                logging.info(f"Processed latest price file: {latest_price_file}")
            else:
                logging.warning("No price files found")
                
        except Exception as e:
            logging.error(f"Error processing latest files: {str(e)}")

if __name__ == "__main__":
    uploader = DatabaseUploader()
    uploader.process_latest_files()