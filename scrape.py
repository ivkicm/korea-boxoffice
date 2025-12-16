import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# URL der Korean Film Council Seite
URL = "https://www.koreanfilm.or.kr/eng/news/boxOffice_Daily.jsp?mode=BOXOFFICE_DAILY"

def parse_english_date(date_str):
    """Wandelt 'Nov 26, 2025' manuell in ein Datum um."""
    try:
        # Bereinigen
        date_str = date_str.strip()
        
        # Mapping für englische Monate
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        # Split: "Nov 26, 2025" -> ["Nov", "26,", "2025"]
        parts = date_str.replace(',', '').split()
        if len(parts) != 3: return None
        
        m_str, d_str, y_str = parts
        
        month = months.get(m_str)
        day = int(d_str)
        year = int(y_str)
        
        if month:
            return datetime(year, month, day)
        return None
    except:
        return None

def get_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    print(f"Verbinde zu {URL}...")
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Suche alle Zeilen
        all_rows = soup.find_all('tr')
        
        movies = []
        count = 0
        
        for row in all_rows:
            if count >= 5: break
            
            cols = row.find_all('td')
            # Wir brauchen mindestens 5 Spalten (Rank, Title, Date, Money, Admissions)
            if len(cols) < 5: continue
            
            # Prüfen ob Rank eine Zahl ist
            rank_text = cols[0].text.strip()
            if not rank_text.isdigit(): continue 
            
            # 1. TITEL FINDEN
            # Meistens im <a> Tag, sonst erster Text
            a_tag = cols[1].find('a')
            if a_tag:
                title = a_tag.text.strip()
            else:
                # Fallback: Alles Text holen, splitten, erste nicht-leere Zeile
                lines = [line.strip() for line in cols[1].text.split('\n') if line.strip()]
                title = lines[0] if lines else "Unbekannt"

            # 2. DATUM & TAGE FINDEN
            days_run = "-"
            date_text = cols[2].text.strip() # Spalte 3 ist Release Date
            
            release_date = parse_english_date(date_text)
            if release_date:
                diff = (datetime.now() - release_date).days
                days_run = diff if diff >= 0 else 0 # Keine negativen Tage
            
            # 3. ADMISSIONS FINDEN (Spalte 5 / Index 4)
            # Format: "81,924 (5,452,511)" oder mit Zeilenumbruch
            adm_text = cols[4].text.strip()
            
            # Bereinigen von Zeilenumbrüchen
            adm_text = " ".join(adm_text.split())
            
            if '(' in adm_text:
                parts = adm_text.split('(')
                daily = parts[0].strip()
                total = parts[1].replace(')', '').strip()
            else:
                daily = adm_text
                total = adm_text

            movies.append({
                'rank': rank_text,
                'title': title,
                'days': days_run,
                'daily': daily,
                'total': total
            })
            count += 1
            
        print(f"Daten gefunden für: {[m['title'] for m in movies]}")
        return movies

    except Exception as e:
        print(f"Fehler: {e}")
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
        body {{ background-color: #000000; color: #ffffff; font-family: 'JetBrains Mono', monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; height: 100vh; overflow: hidden; }}
        
        .header {{ 
            font-size: 2.5rem; font-weight: 900; text-transform: uppercase; 
            margin-bottom: 30px; letter-spacing: 2px; text-align: center; 
            border-bottom: 2px solid #333; padding-bottom: 10px; width: 100%; max-width: 1200px; 
        }}
        
        .row-container {{ 
            display: grid; 
            grid-template-columns: 80px 1.5fr 100px 1fr 1fr; /* Spaltenbreiten */
            gap: 15px; 
            width: 100%; max-width: 1200px; 
            margin-bottom: 15px; 
            height: 100px; 
        }}
        
        .box {{ 
            border: 2px solid #fff; border-radius: 8px; 
            display: flex; flex-direction: column; justify-content: center; 
            padding: 0 15px; background: #0a0a0a; 
        }}
        
        /* Rank */
        .rank-box {{ border-color: #FFD700; align-items: center; }}
        .rank-val {{ color: #FFD700; font-size: 3.5rem; font-weight: 900; line-height: 1; }}
        
        /* Title */
        .title-box {{ border-color: #ffffff; justify-content: center; }}
        .movie-title {{ 
            font-size: 1.6rem; font-weight: 800; text-transform: uppercase; 
            line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; 
        }}
        
        /* Days */
        .days-box {{ border-color: #666; align-items: center; }}
        .days-val {{ font-size: 2.2rem; font-weight: 800; }}
        .days-label {{ font-size: 0.6rem; color: #888; text-transform: uppercase; margin-top: 5px; }}
        
        /* Daily (Besucher) */
        .daily-box {{ border-color: #39FF14; align-items: flex-end; }}
        .label-green {{ color: #39FF14; font-size: 0.7rem; font-weight: 800; margin-bottom: 2px; }}
        .val-big {{ font-size: 2.2rem; font-weight: 800; line-height: 1; }}
        
        /* Total (Besucher) */
        .total-box {{ border-color: #00F0FF; align-items: flex-end; }}
        .label-blue {{ color: #00F0FF; font-size: 0.7rem; font-weight: 800; margin-bottom: 2px; }}
        
        @media (max-width: 800px) {{
            .row-container {{ grid-template-columns: 1fr; height: auto; padding-bottom: 20px; }}
        }}
    </style>
</head>
<body>
    <div class="header">SÜDKOREA KINOCHARTS | {date_str}</div>
    """

    if not movies:
        html += "<div style='color:red; margin-top:50px;'>Keine Daten gefunden.</div>"
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
    <div style="margin-top:20px; font-size:0.7rem; color:#444;">Quelle: KOBIZ Data</div>
</body>
</html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    data = get_data()
    generate_html(data)
