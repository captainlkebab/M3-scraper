import json
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import pickle
import logging
from pathlib import Path

# Setup logging
def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set up logging with file in logs directory
    log_file = log_dir / f"price_predictor_{datetime.now().strftime('%y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

# Call setup_logging at the beginning of your script
logger = setup_logging()


def extract_date_from_filename(filename):
    """Extract date from filename format Refurbed_YYMMDD.json"""
    date_part = filename.split('_')[1].split('.')[0]
    year = int('20' + date_part[:2])
    month = int(date_part[2:4])
    day = int(date_part[4:6])
    return datetime(year, month, day)

def load_data_files(data_dir="github/Scraped"):
    """Load all available data files and return them sorted by date"""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_path, data_dir)
    
    data_files = []
    
    for filename in os.listdir(data_path):
        if filename.startswith("Refurbed_") and filename.endswith(".json"):
            file_path = os.path.join(data_path, filename)
            file_date = extract_date_from_filename(filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data_files.append({
                        'filename': filename,
                        'date': file_date,
                        'data': data
                    })
                logger.info(f"Loaded {filename} with {len(data)} products")
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
    
    # Sort by date
    data_files.sort(key=lambda x: x['date'])
    return data_files

def prepare_price_history(data_files):
    """Create a price history dataframe from all data files"""
    price_history = {}
    
    for file_info in data_files:
        date = file_info['date']
        data = file_info['data']
        
        for product in data:
            # Skip products with no price or "NOT-AVAILABLE"
            if product.get('offer', {}).get('price') == "NOT-AVAILABLE" or not product.get('offer', {}).get('price'):
                continue
            
            # Use URL as unique identifier
            product_id = product['url']
            
            # Get price as float
            try:
                price = float(product['offer']['price'])
            except (ValueError, TypeError):
                continue
            
            # Initialize product entry if not exists
            if product_id not in price_history:
                price_history[product_id] = {
                    'title': product.get('title', ''),
                    'brand': product.get('item', {}).get('item_brand', ''),
                    'model': product.get('item', {}).get('item_name', ''),
                    'category': product.get('item', {}).get('item_category2', ''),
                    'grade': product.get('offer', {}).get('grading', ''),
                    'prices': {}
                }
            
            # Add price for this date
            price_history[product_id]['prices'][date.strftime('%Y-%m-%d')] = price
    
    return price_history

def build_prediction_models(price_history, min_data_points=2):
    """Build linear regression models for products with enough data points"""
    prediction_models = {}
    
    for product_id, product_data in price_history.items():
        prices = product_data['prices']
        
        # Skip if not enough data points
        if len(prices) < min_data_points:
            continue
        
        # Convert to dataframe for modeling
        dates = [datetime.strptime(date, '%Y-%m-%d') for date in prices.keys()]
        price_values = list(prices.values())
        
        # Convert dates to numeric (days since first date)
        first_date = min(dates)
        days_since_first = [(date - first_date).days for date in dates]
        
        # Create and fit model
        X = np.array(days_since_first).reshape(-1, 1)
        y = np.array(price_values)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Calculate R-squared to measure model quality
        r_squared = model.score(X, y)
        
        # Store model and metadata
        prediction_models[product_id] = {
            'model': model,
            'first_date': first_date,
            'last_date': max(dates),
            'last_price': price_values[-1],
            'r_squared': r_squared,
            'title': product_data['title'],
            'brand': product_data['brand'],
            'model_name': product_data['model'],
            'category': product_data['category'],
            'grade': product_data['grade'],
            'price_history': prices
        }
    
    return prediction_models

def generate_predictions(prediction_models, days_ahead=30):
    """Generate price predictions for the specified number of days ahead"""
    predictions = {}
    
    today = datetime.now()
    
    for product_id, model_data in prediction_models.items():
        model = model_data['model']
        first_date = model_data['first_date']
        
        # Generate prediction dates
        prediction_dates = [today + timedelta(days=i) for i in range(1, days_ahead + 1)]
        
        # Convert to days since first date
        days_since_first = [(date - first_date).days for date in prediction_dates]
        X_pred = np.array(days_since_first).reshape(-1, 1)
        
        # Make predictions
        y_pred = model.predict(X_pred)
        
        # Apply dampening factor to reduce extreme predictions
        # The further in the future, the more we dampen the change
        last_price = model_data['last_price']
        dampened_predictions = []
        
        for i, predicted_price in enumerate(y_pred):
            # Calculate days from today
            days_from_today = i + 1
            
            # Dampening factor increases with time (stronger dampening for further predictions)
            dampening_factor = 1.0 - (days_from_today / (days_ahead * 2))
            
            # Calculate raw price change
            raw_change = predicted_price - last_price
            
            # Apply dampening to the change
            dampened_change = raw_change * dampening_factor
            
            # Limit maximum monthly change to 5% (more realistic for IT equipment)
            max_change_pct = 5.0  # 5% maximum monthly change
            max_change = last_price * (max_change_pct / 100)
            
            if abs(dampened_change) > max_change:
                dampened_change = max_change if dampened_change > 0 else -max_change
            
            # Calculate dampened price
            dampened_price = last_price + dampened_change
            
            # Ensure price is positive
            dampened_price = max(0, dampened_price)
            
            dampened_predictions.append(dampened_price)
        
        # Store predictions
        product_predictions = {}
        for i, date in enumerate(prediction_dates):
            product_predictions[date.strftime('%Y-%m-%d')] = round(dampened_predictions[i], 2)
        
        # Calculate trend percentage (compared to last known price)
        predicted_price_30d = product_predictions[prediction_dates[-1].strftime('%Y-%m-%d')]
        
        if last_price > 0:
            trend_pct = ((predicted_price_30d - last_price) / last_price) * 100
            # Cap trend percentage to a reasonable range
            trend_pct = max(min(trend_pct, 5.0), -5.0)
        else:
            trend_pct = 0
            
        # Store predictions with metadata
        predictions[product_id] = {
            'title': model_data['title'],
            'brand': model_data['brand'],
            'model': model_data['model_name'],
            'category': model_data['category'],
            'grade': model_data['grade'],
            'last_price': last_price,
            'trend_pct': round(trend_pct, 2),
            'r_squared': round(model_data['r_squared'], 4),
            'price_history': model_data['price_history'],
            'predictions': product_predictions
        }
    
    return predictions

def save_predictions(predictions, output_dir="docs"):
    """Save predictions to a JSON file"""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_path, output_dir)
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Save predictions
    output_file = os.path.join(output_path, "price_predictions.json")
    
    # Convert to serializable format
    serializable_predictions = {}
    for product_id, pred_data in predictions.items():
        serializable_predictions[product_id] = {
            'title': pred_data['title'],
            'brand': pred_data['brand'],
            'model': pred_data['model'],
            'category': pred_data['category'],
            'grade': pred_data['grade'],
            'last_price': pred_data['last_price'],
            'trend_pct': pred_data['trend_pct'],
            'r_squared': pred_data['r_squared'],
            'price_history': pred_data['price_history'],
            'predictions': pred_data['predictions']
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(serializable_predictions, f, indent=2)
    
    logger.info(f"Saved predictions to {output_file}")
    return output_file

def generate_summary_stats(predictions):
    """Generate summary statistics for predictions"""
    categories = {}
    brands = {}
    total_products = len(predictions)
    
    # Count products by category and brand
    for product_id, pred_data in predictions.items():
        category = pred_data['category']
        brand = pred_data['brand']
        
        if category:
            categories[category] = categories.get(category, 0) + 1
        
        if brand:
            brands[brand] = brands.get(brand, 0) + 1
    
    # Find trending categories and brands
    category_trends = {}
    brand_trends = {}
    
    for product_id, pred_data in predictions.items():
        category = pred_data['category']
        brand = pred_data['brand']
        trend_pct = pred_data['trend_pct']
        
        if category:
            if category not in category_trends:
                category_trends[category] = []
            category_trends[category].append(trend_pct)
        
        if brand:
            if brand not in brand_trends:
                brand_trends[brand] = []
            brand_trends[brand].append(trend_pct)
    
    # Calculate average trends
    avg_category_trends = {cat: sum(trends)/len(trends) for cat, trends in category_trends.items() if len(trends) >= 3}
    avg_brand_trends = {brand: sum(trends)/len(trends) for brand, trends in brand_trends.items() if len(trends) >= 3}
    
    # Sort by trend
    trending_categories = sorted(avg_category_trends.items(), key=lambda x: x[1], reverse=True)
    trending_brands = sorted(avg_brand_trends.items(), key=lambda x: x[1], reverse=True)
    
    # Get top 5 trending up and down
    top_trending_up_categories = [item for item in trending_categories if item[1] > 0][:5]
    top_trending_down_categories = [item for item in trending_categories if item[1] < 0][-5:]
    
    top_trending_up_brands = [item for item in trending_brands if item[1] > 0][:5]
    top_trending_down_brands = [item for item in trending_brands if item[1] < 0][-5:]
    
    summary = {
        'total_products_with_predictions': total_products,
        'categories': {cat: count for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)},
        'brands': {brand: count for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True)},
        'trending_up_categories': [{
            'name': cat,
            'trend_pct': round(trend, 2),
            'count': categories.get(cat, 0)
        } for cat, trend in top_trending_up_categories],
        'trending_down_categories': [{
            'name': cat,
            'trend_pct': round(trend, 2),
            'count': categories.get(cat, 0)
        } for cat, trend in top_trending_down_categories],
        'trending_up_brands': [{
            'name': brand,
            'trend_pct': round(trend, 2),
            'count': brands.get(brand, 0)
        } for brand, trend in top_trending_up_brands],
        'trending_down_brands': [{
            'name': brand,
            'trend_pct': round(trend, 2),
            'count': brands.get(brand, 0)
        } for brand, trend in top_trending_down_brands]
    }
    
    return summary

def save_summary(summary, output_dir="docs"):
    """Save summary statistics to a JSON file"""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_path, output_dir)
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Save summary
    output_file = os.path.join(output_path, "prediction_summary.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Saved summary to {output_file}")
    return output_file

def main():
    logger.info("Starting price prediction process")
    logger.info("Loading data files...")
    data_files = load_data_files()
    
    if len(data_files) < 2:
        logger.warning(f"Not enough data files found. Need at least 2, found {len(data_files)}")
        return
    
    logger.info(f"Found {len(data_files)} data files")
    
    logger.info("Preparing price history...")
    price_history = prepare_price_history(data_files)
    logger.info(f"Prepared price history for {len(price_history)} products")
    
    logger.info("Building prediction models...")
    prediction_models = build_prediction_models(price_history)
    logger.info(f"Built prediction models for {len(prediction_models)} products")
    
    logger.info("Generating predictions...")
    predictions = generate_predictions(prediction_models)
    logger.info(f"Generated predictions for {len(predictions)} products")
    
    logger.info("Saving predictions...")
    save_predictions(predictions)
    
    logger.info("Generating summary statistics...")
    summary = generate_summary_stats(predictions)
    save_summary(summary)
    
    logger.info("Price prediction process completed successfully")

if __name__ == "__main__":
    main()

