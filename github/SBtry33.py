from seleniumbase import Driver
import time

def test_bypass_bot_protection():
    # Initialize the undetected chromedriver
    driver = Driver(uc=True)
    
    try:
        # Open the target URL
        driver.get("https://www.scrapingcourse.com/antibot-challenge")
        
        # Wait for the page to load
        time.sleep(5)
        
        # If there's a captcha, you need to handle it
        # There's no built-in uc_gui_click_captcha method, so you need to implement captcha handling
        
        # Example: If the captcha is a checkbox type (like reCAPTCHA)
        try:
            # Find the captcha checkbox frame
            frames = driver.find_elements("xpath", "//iframe[contains(@src, 'recaptcha')]")
            if frames:
                # Switch to the frame containing the captcha
                driver.switch_to.frame(frames[0])
                
                # Find and click the checkbox
                checkbox = driver.find_element("xpath", "//div[@class='recaptcha-checkbox-border']")
                checkbox.click()
                
                # Switch back to the main content
                driver.switch_to.default_content()
                
                print("Captcha checkbox clicked")
                time.sleep(2)
        except Exception as e:
            print(f"Captcha handling error: {e}")
        
        # Get the page source after handling the captcha
        page_html = driver.page_source
        print(page_html)
        
    finally:
        # Always quit the driver to clean up resources
        driver.quit()

if __name__ == "__main__":
    test_bypass_bot_protection()
from seleniumbase import BaseCase
import time

class Scraper(BaseCase):
    def test_get_html(self):
        # Path to the file containing URLs
        urls_file_path = r"c:\Users\samil\Documents\PythonScripts\Scraper\M3-scraper\github\Sitemaps\backmarket_urls.txt"
        
        # Read URLs from the file
        with open(urls_file_path, 'r') as file:
            urls = file.readlines()
        
        # Process the first 10 URLs
        for i, url in enumerate(urls[:10]):
            url = url.strip()  # Remove any leading/trailing whitespace
            if url:  # Skip empty lines
                print(f"Processing URL {i+1}/10: {url}")
                try:
                    self.open(url)
                    page_html = self.get_page_source()
                    print(f"Successfully retrieved HTML for URL {i+1}")
                    
                    # Optional: Save the HTML to a file
                    # with open(f"output_{i+1}.html", "w", encoding="utf-8") as f:
                    #     f.write(page_html)
                    
                    # Add a small delay between requests to avoid being blocked
                    time.sleep(2)
                except Exception as e:
                    print(f"Error processing {url}: {e}")