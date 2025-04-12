from datetime import datetime

# Kalenderwoche bestimmen
kw = datetime.today().isocalendar().week

# Beispiel: Dynamischer Inhalt basierend auf der KW
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Weekly Update KW {kw}</title>
</head>
<body>
    <h1>Wöchentlicher Content – KW {kw}</h1>
    <p>Dies ist der automatisch generierte Inhalt für Kalenderwoche {kw}.</p>
</body>
</html>
"""

# In docs/index.html schreiben
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
