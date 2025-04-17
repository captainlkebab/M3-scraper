# Used IT Equipment Price Tracker
This project is a comprehensive solution for tracking prices of used and refurbished IT equipment across multiple marketplaces. It includes web scrapers, data processing tools, and a web interface to visualize price trends and predictions.

## Features
- Multi-source data collection : Scrapes product information from Refurbed, BackMarket, and other refurbished equipment marketplaces
- Price tracking : Monitors price changes over time for thousands of products
- Price prediction : Uses machine learning to forecast future price trends
- Web interface : Interactive dashboard to explore the data and price predictions
## Project Structure
- github/ - Contains the scraper scripts and data processing tools
- docs/ - Web interface for visualizing the data
- Scraped/ - Storage for the collected data
## Getting Started
### Prerequisites
- Python 3.8 or higher
- Chrome browser (for selenium-based scrapers)
- Required Python packages (see requirements below)
### Installation
1. Clone this repository to your local machine
2. Install the required packages:
```bash
pip install -r requirements.txt
 ```
```

### Running the Scrapers Refurbed Scraper
```bash
python github/refurbedscraper.py
 ```
```
 BackMarket Scraper
```bash
python github/backmarketscraper.py
 ```
```

### Generating Price Predictions
After collecting data for at least two weeks, you can generate price predictions:

```bash
python github/price_predictor.py
 ```
```

### Viewing the Dashboard
Open docs/index.html in your web browser to view the dashboard. For the best experience, use a local web server:

```bash
cd docs
python -m http.server 8000
 ```

Then visit http://localhost:8000 in your browser.

## Data Update Schedule
- The scrapers are designed to run weekly (preferably on Sundays)
- Price predictions are updated after each new data collection
## Technologies Used
- Python (BeautifulSoup, Selenium, Pandas, Scikit-learn)
- JavaScript (for the web interface)
- HTML/CSS
## License
This project is for personal use only. Please respect the terms of service of the websites being scraped.