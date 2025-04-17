from playwright.sync_api import sync_playwright
import time

urls = [
    "https://www.backmarket.de/de-de/p/iphone-8-128-gb-space-grau-ohne-vertrag/32e68609-2d7d-4581-a2fa-62918ee1ef45",
    "https://www.backmarket.de/de-de/p/iphone-8-256-gb-gold-ohne-vertrag/e95f1314-66c4-4caf-b41b-f47b25a2b259",
    "https://www.backmarket.de/de-de/p/iphone-8-256-gb-productred-ohne-vertrag/3d389f72-3acb-4f8c-b24c-4d99077772c9"
]

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for i, url in enumerate(urls):
            try:
                page.goto(url, timeout=20000)
                time.sleep(2)  # Warten, bis Seite geladen ist

                title = page.locator("h1").first.text_content().strip()
                price = page.locator("[data-qa='main-price']").first.text_content().strip()

                print(f"\n{i+1}. {url}")
                print(f"📦 Produkt: {title}")
                print(f"💶 Preis: {price}")
            except Exception as e:
                print(f"{i+1}. {url} - ERROR: {e}")
        browser.close()

run()
