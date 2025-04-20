from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import time
import random

urls = [
    "https://www.backmarket.de/de-de/p/iphone-8-128-gb-space-grau-ohne-vertrag/32e68609-2d7d-4581-a2fa-62918ee1ef45",
    "https://www.backmarket.de/de-de/p/iphone-8-256-gb-gold-ohne-vertrag/e95f1314-66c4-4caf-b41b-f47b25a2b259",
    "https://www.backmarket.de/de-de/p/iphone-8-256-gb-productred-ohne-vertrag/3d389f72-3acb-4f8c-b24c-4d99077772c9"
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0",
            viewport={"width": 1280, "height": 800},
            storage_state="auth.json"
        )

        # Stealth-Modus aktivieren
        page = context.new_page()
        stealth_sync(page)

        # Mausbewegung und zufällige Verzögerung simulieren
        for _ in range(random.randint(5, 10)):
            page.mouse.move(random.randint(0, 1280), random.randint(0, 800))
            time.sleep(random.uniform(0.1, 0.5))

        # Cookies manuell akzeptieren
        print("⏳ Bitte akzeptiere Cookies manuell, dann ENTER drücken...")
        input()

        # Speicher den auth-Zustand für spätere Läufe
        context.storage_state(path="auth.json")

        for i, url in enumerate(urls, start=1):
            page = context.new_page()
            print(f"[{i}] Öffne {url}")
            page.goto(url, timeout=random.randint(30000, 60000))

            # Mausbewegungen und zufällige Verzögerungen zwischen den Aktionen
            time.sleep(random.randint(5, 10))  # Warte vor Seitenaufruf

            # Speichern der HTML-Seite
            with open(f"page_{i}.html", "w", encoding="utf-8") as f:
                f.write(page.content())

            print(f"[{i}] HTML gespeichert\n")

        browser.close()

main()
