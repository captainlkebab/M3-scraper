import pandas as pd
from pathlib import Path
import glob
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
import pyodbc

load_dotenv()
 
def get_connection():
    # connection info
    server = "tcp:sql-prod-price-scraper.database.windows.net,1433"
    database = "db-prod-price-scraper"
    username = "novitio"
    password =os.getenv("DB_PASSWORD")

    connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()
        print("Successfully connected to database!")
        return conn, cursor
    except Exception as e:
        print("Connection error:", e)
        return None, None


def upload_refurbed_data():
    # Get database connection
    conn, cursor = get_connection()
    if not conn or not cursor:
        print("❌ Failed to connect to database!")
        return

    # Get the Scraped directory path
    scraped_dir = Path(__file__).parent.parent / "Scraped"
    
    # Create a directory for failed uploads if it doesn't exist
    failed_dir = Path(__file__).parent / "Failed_Uploads"
    failed_dir.mkdir(exist_ok=True)
    
    # Lists to track failed uploads
    failed_products = []
    failed_prices = []
    processed_products = []

    # Find the most recent files
    products_files = glob.glob(str(scraped_dir / "Refurbed_*_products.csv"))
    prices_files = glob.glob(str(scraped_dir / "Refurbed_*_prices.csv"))
    
    if not products_files or not prices_files:
        print("❌ No CSV files found!")
        return
    
    # Get the most recent files
    latest_products = max(products_files, key=os.path.getctime)
    latest_prices = max(prices_files, key=os.path.getctime)

    try:
        # Read CSV files with proper NA handling and encoding fix
        products_df = pd.read_csv(latest_products, encoding="utf-8", on_bad_lines="skip")
        prices_df = pd.read_csv(latest_prices, encoding="utf-8", on_bad_lines="skip")
        
        print(f"🔍 Found {len(products_df)} products and {len(prices_df)} prices.")

        # Process Products
        for index, row in products_df.iterrows():
            try:
                print(f"📦 Processing product {index + 1} / {len(products_df)}: {row['Url']}")  # Debug output

                # Process Model field to exclude grade and everything after
                model = row['Model']
                if pd.notna(model):
                    if 'grade' in model.lower():
                        model = model.lower().split('grade')[0].strip()
                    model = model.rstrip(' |')

                # Check if product exists
                cursor.execute("SELECT Id FROM Products WHERE Url = ?", (row['Url'],))
                existing_product = cursor.fetchone()
                
                if existing_product:
                    # Update existing product
                    cursor.execute("""
                        UPDATE Products 
                        SET Title = ?, Price = ?, CurrencyIso = ?, Refurbished = ?,
                            Model = ?, MPN = ?, Brand = ?, UpdateTime = ?, 
                            Category = ?, Source = ?, Grade = ?
                        WHERE Url = ?
                    """, (
                        row['Title'],
                        float(row['Price']) if pd.notna(row['Price']) else 0,
                        row['CurrencyIso'],
                        1 if row['Refurbished'] else 0,
                        model,
                        row['MPN'],
                        row['Brand'],
                        row['UpdateTime'],
                        row['Category'],
                        row['Source'],
                        row['Grade'],
                        row['Url']
                    ))
                    product_id = existing_product[0]
                else:
                    # Insert new product
                    new_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO Products (Id, Title, Price, CurrencyIso, Url, Refurbished,
                                        Model, MPN, Brand, UpdateTime, Category, Source, Grade)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_id,
                        row['Title'],
                        float(row['Price']) if pd.notna(row['Price']) else 0,
                        row['CurrencyIso'],
                        row['Url'],
                        1 if row['Refurbished'] else 0,
                        model,
                        row['MPN'],
                        row['Brand'],
                        row['UpdateTime'],
                        row['Category'],
                        row['Source'],
                        row['Grade']
                    ))
                    product_id = new_id

                processed_products.append(row)  # Track successful inserts
                
                # Commit every 100 rows
                if (index + 1) % 100 == 0:
                    conn.commit()
                    print("✅ Committed batch of 100 records.")

            except Exception as e:
                print(f"❌ Error processing product {row['Url']} at index {index}: {e}")
                failed_products.append(row)
                continue

        # Final commit
        conn.commit()

        # Process Prices
        for index, row in prices_df.iterrows():
            try:
                print(f"💰 Processing price {index + 1} / {len(prices_df)}: {row['Url']}")  # Debug output

                # Get product ID for the URL
                cursor.execute("SELECT Id FROM Products WHERE Url = ?", (row['Url'],))
                product = cursor.fetchone()
                
                if product and pd.notna(row['Price']):
                    # Insert new price entry
                    cursor.execute("""
                        INSERT INTO PriceEntries (Id, ProductId, Price, CurrencyIso, TimeOfChange)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()),
                        product[0],
                        float(row['Price']),
                        row['CurrencyIso'],
                        row['TimeOfChange']
                    ))

                # Commit every 100 rows
                if (index + 1) % 100 == 0:
                    conn.commit()

            except Exception as e:
                print(f"❌ Error processing price for {row['Url']} at index {index}: {e}")
                failed_prices.append(row)
                continue
        
        # Final commit
        conn.commit()
        
        # Save failed uploads if any
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        if failed_products:
            failed_products_df = pd.DataFrame(failed_products)
            failed_products_file = failed_dir / f"failed_products_{timestamp}.csv"
            failed_products_df.to_csv(failed_products_file, index=False)
            print(f"⚠️ Saved {len(failed_products)} failed products to {failed_products_file}")
            
        if failed_prices:
            failed_prices_df = pd.DataFrame(failed_prices)
            failed_prices_file = failed_dir / f"failed_prices_{timestamp}.csv"
            failed_prices_df.to_csv(failed_prices_file, index=False)
            print(f"⚠️ Saved {len(failed_prices)} failed prices to {failed_prices_file}")
        
        # Save successfully processed rows
        processed_products_df = pd.DataFrame(processed_products)
        processed_products_file = failed_dir / f"processed_products_{timestamp}.csv"
        processed_products_df.to_csv(processed_products_file, index=False)
        print(f"✅ Saved {len(processed_products)} successfully processed products to {processed_products_file}")

        successful_products = len(products_df) - len(failed_products)
        successful_prices = len(prices_df) - len(failed_prices)
        print(f"🎉 Successfully processed {successful_products} products and {successful_prices} price entries")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during upload: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print("🔌 Database connection closed.")

if __name__ == "__main__":
    upload_refurbed_data()
