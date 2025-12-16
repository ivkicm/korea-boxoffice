import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# URL der Seite
URL = "https://www.koreanfilm.or.kr/eng/news/boxOffice_Daily.jsp?mode=BOXOFFICE_DAILY"

def parse_english_date(date_str):
    """Wandelt 'Nov 26, 2025' in ein Datum um."""
    try:
        date_str = date_str.strip()
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        # Entferne Kommas und splitte
        parts = date_str.replace(',', '').split()
        if len(parts) != 3: return None
        
        m_str, d_str, y_str = parts
        month = months.get(m_str)
        
        if month:
            return datetime(int(y_str), month, int(d_str))
        return None
    except:
        return None

def get_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Lade Daten von {URL}...")
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Laut deinem Quelltext nutzt die Seite TBODYs mit IDs wie 'listTable_0_1', 'listTable_0_2' usw.
        # Wir suchen genau diese Struktur.
        tbodies = soup.find_all('tbody', id=re.compile(r'listTable_0_\d+'))
        
        movies = []
        
        # Nur die ersten 5 Ergebnisse
        for tbody in tbodies[:5]:
            row = tbody.find('tr')
            cols = row.find_all('td')
            
            # --- 1. RANG (Spalte 0) ---
            rank = cols[0].text.strip()
            
            # --- 2. TITEL (Spalte 2 - Index 2) ---
            # Im Quelltext ist Spalte 1 das Bild, Spalte 2 der Text.
            # Der Titel steht im ersten <p> Tag.
            title_cell = cols[2]
            p_tags = title_cell.find_all('p')
            if p_tags:
                # Der Titel ist im ersten Paragraph, manchmal ist ein Link <a> drin, manchmal nur Text
                title = p_tags[0].text.strip()
            else:
                title = title_cell.text.strip()

            # --- 3. TAGE SEIT RELEASE (Spalte 3 - Index 3) ---
            days_run = "-"
            date_text = cols[3].text.strip() # z.B. "Nov 26, 2025"
            
            release_date = parse_english_date(date_text)
            if release_date:
                # Differenz zu heute berechnen
                delta = datetime.now() - release_date
                days_run = delta.days
                if days_run < 0: days_run = 0

            # --- 4. ADMISSIONS (Spalte 5 - Index 5) ---
            # Spalte 4 ist Geld ($). Spalte 5 ist Admissions (Besucher).
            # Inhalt z.B.: "81,924<br/>(5,452,511)"
            # Wir nutzen get_text mit Separator, um das <br> sauber zu trennen
            adm_text = cols[5].get_text(separator='|').strip()
            
            if '|' in adm_text:
                parts = adm_text.split('|')
                daily = parts[0].strip()
                # Total ist oft in Klammern (5,452,511)
                total = parts[1].replace('(', '').replace(')', '').strip()
            elif '(' in adm_text:
                parts = adm_text.split('(')
                daily = parts[0].strip()
                total = parts[1].replace(')', '').strip()
            else:
                daily = adm_text
                total = adm_text

            movies.append({
                'rank': rank,
                'title': title,
                'days': days_run,
                'daily': daily,
                'total': total
            })
            
        print(f"Erfolgreich {len(movies)} Filme verarbeitet.")
        return movies

    except Exception as e:
        print(f"Fehler beim Scrapen: {e}")
        return []

def generate_html(movies):
    date_str = datetime.now().strftime("%d.%m.%Y")
    
    html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Korea Box Office</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;800;900&display=swap" rel="stylesheet">
    <style>
        body {{ background-color: #000000; color: #ffffff; font-family: 'JetBrains Mono', monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }}
        
        .header {{ 
            font-size: 2.5rem; font-weight: 900; text-transform: uppercase; 
            margin-bottom: 30px; letter-spacing: 2px; text-align: center; 
            border-bottom: 2px solid #333; padding-bottom: 10px; width: 100%; max-width: 1200px; 
        }}
        
        .grid-wrapper {{ width: 100%; max-width: 1200px; display:flex; flex-direction:column; gap:15px; }}

        .row-container {{ 
            display: grid; 
            grid-template-columns: 80px 1.5fr 100px 1fr 1fr; 
            gap: 15px; 
            height: 100px; 
        }}
        
        .box {{ 
            border: 2px solid #fff; border-radius: 8px; 
            display: flex; flex-direction: column; justify-content: center; 
            padding: 0 15px; background: #0a0a0a; 
        }}
        
        .rank-box {{ border-color: #FFD700; align-items: center; }}
        .rank-val {{ color: #FFD700; font-size: 3.5rem; font-weight: 900; line-height: 1; }}
        
        .title-box {{ border-color: #ffffff; justify-content: center; }}
        .movie-title {{ 
            font-size: 1.5rem; font-weight: 800; text-transform: uppercase; 
            line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        }}
        
        .days-box {{ border-color: #666; align-items: center; }}
        .days-val {{ font-size: 2rem; font-weight: 800; }}
        .days-label {{ font-size: 0.6rem; color: #888; text-transform: uppercase; margin-top: 5px; }}
        
        .daily-box {{ border-color: #39FF14; align-items: flex-end; }}
        .label-green {{ color: #39FF14; font-size: 0.7rem; font-weight: 800; margin-bottom: 2px; }}
        .val-big {{ font-size: 2rem; font-weight: 800; line-height: 1; }}
        
        .total-box {{ border-color: #00F0FF; align-items: flex-end; }}
        .label-blue {{ color: #00F0FF; font-size: 0.7rem; font-weight: 800; margin-bottom: 2px; }}
        
        @media (max-width: 800px) {{
            .row-container {{ grid-template-columns: 60px 1fr; height: auto; padding-bottom: 20px; border-bottom:1px solid #333; }}
            .rank-box {{ grid-row: 1 / 3; height: 100%; }}
            .title-box {{ height: 60px; }}
            .days-box, .daily-box, .total-box {{ height: 70px; }}
        }}
    </style>
</head>
<body>
    <div class="header">SÜDKOREA KINOCHARTS | {date_str}</div>
    <div class="grid-wrapper">
    """

    if not movies:
        html += """
        <div style="border:1px solid red; padding:20px; text-align:center;">
            <h2 style="color:red">DATEN NICHT ERREICHBAR</h2>
            <p>Konnte die Tabelle nicht parsen.</p>
        </div>
        """
    else:
        for m in movies:
            html += f"""
            <div class="row-container">
                <div class="box rank-box"><div class="rank-val">{m['rank']}</div></div>
                <div class="box title-box"><div class="movie-title">{m['title']}</div></div>
                <div class="box days-box"><div class="days-val">{m['days']}</div><div class="days-label">TAGE</div></div>
                <div class="box daily-box"><div class="label-green">BESUCHER HEUTE</div><div class="val-big">{m['daily']}</div></div>
                <div class="box total-box"><div class="label-blue">GESAMT</div><div class="val-big">{m['total']}</div></div>
            </div>
            """

    html += """
    </div>
</body>
</html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML Datei geschrieben.")

if __name__ == "__main__":
    data = get_data()
    generate_html(data)
