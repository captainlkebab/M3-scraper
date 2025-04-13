import sqlite3
import pandas as pd
from datetime import datetime
import os

# Datenbankpfad (anpassen, falls anders)
# Update database path
DB_PATH = "databaseproducts.db"

# Lade aktuelle Kalenderwoche
current_week = datetime.today().isocalendar().week
current_year = datetime.today().year

# Verbinde mit SQLite DB
conn = sqlite3.connect(DB_PATH)

# Preisdaten der aktuellen Kalenderwoche abrufen
# Updated query for databaseproducts.db structure
query = f"""
SELECT p.name, pr.price , pr.timestamp
FROM products p
JOIN prices pr ON p.product_id = pr.product_id
WHERE strftime('%Y', pr.timestamp) = '{current_year}'
  AND strftime('%W', pr.timestamp) = '{current_week:02d}'
ORDER BY pr.price DESC
"""
df = pd.read_sql_query(query, conn)
conn.close()

# Prüfe, ob Daten existieren
if df.empty:
    html_table = "<p>No data found for this week.</p>"
else:
    html_table = df.to_html(index=False, border=0)

# HTML-Template generieren
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Weekly Price Update – Week {current_week}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f4f4f4; }}
    </style>
</head>
<body>
    <h1>Prices for Calendar Week {current_week}, {current_year}</h1>
    <p>This data was automatically generated.</p>
    {html_table}
</body>
</html>
"""

# Stelle sicher, dass der docs/ Ordner existiert
os.makedirs("docs", exist_ok=True)

# Schreibe HTML-Datei
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
