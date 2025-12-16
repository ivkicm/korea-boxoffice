import requests
from bs4 import BeautifulSoup
from datetime import datetime

# URL der Korean Film Council Seite (Tägliche Box Office)
URL = "https://www.koreanfilm.or.kr/eng/news/boxOffice_Daily.jsp?mode=BOXOFFICE_DAILY"

def get_data():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(URL, headers=headers)
        response.encoding = 'utf-8' # Encoding sicherstellen
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tabelle finden (die Klasse ist meist board_list)
        table = soup.find('table', {'class': 'board_list'})
        if not table:
            print("Keine Tabelle gefunden!")
            return []

        rows = table.find_all('tr')[1:] # Header überspringen
        
        movies = []
        
        # Nur Top 5 verarbeiten
        for row in rows[:5]:
            cols = row.find_all('td')
            if len(cols) < 5: continue
            
            # 1. Rang
            rank = cols[0].text.strip()
            
            # 2. Titel (oft mit Zeilenumbrüchen, wir säubern das)
            title_text = cols[1].text.strip()
            # Manchmal steht das Land oder Jahr dabei, wir nehmen alles vor dem ersten Zeilenumbruch
            title = title_text.split('\n')[0].strip()
            
            # 3. Release Datum & Tage seit Release
            try:
                # Das Datum steht in Spalte 3 (Index 2)
                # Format auf der Seite ist meist "Nov 26, 2025" oder "2025-11-26"
                date_str = cols[2].text.strip()
                # Versuchen wir das Standardformat der Seite
                release_date = datetime.strptime(date_str, '%b %d, %Y')
                days_run = (datetime.now() - release_date).days
                if days_run < 0: days_run = 0 # Pre-Release
            except:
                days_run = "-"

            # 4. Admissions (Besucher)
            # Spalte 5 (Index 4) enthält: "Daily (Total)" -> z.B. "81,924 (5,452,511)"
            # Manchmal sind da Zeilenumbrüche drin
            adm_text = cols[4].text.replace('\n', '').replace('\r', '').strip()
            
            # Wir trennen Daily und Total anhand der Klammer
            if '(' in adm_text:
                daily = adm_text.split('(')[0].strip()
                total = adm_text.split('(')[1].replace(')', '').strip()
            else:
                daily = adm_text
                total = adm_text # Fallback
            
            movies.append({
                'rank': rank,
                'title': title,
                'days': days_run,
                'daily': daily,
                'total': total
            })
            
        return movies
    except Exception as e:
        print(f"Fehler beim Scrapen: {e}")
        return []

def generate_html(movies):
    date_str = datetime.now().strftime("%d.%m.%Y")
    
    # CSS Style basierend auf deinem "Deutsche Kinocharts" Screenshot
    html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Korea Box Office</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;800;900&display=swap" rel="stylesheet">
    <style>
        body {{
            background-color: #000000;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
            overflow: hidden;
        }}
        
        .header {{
            font-size: 3rem;
            font-weight: 900;
            text-transform: uppercase;
            margin-bottom: 40px;
            letter-spacing: 4px;
            text-align: center;
            background: #000;
            border-bottom: 4px solid #333;
            padding-bottom: 10px;
            width: 95vw;
        }}

        .grid-wrapper {{
            display: flex;
            flex-direction: column;
            gap: 20px;
            width: 95vw;
        }}

        .row-container {{
            display: grid;
            grid-template-columns: 80px 1.5fr 150px 1fr 1fr; /* Rank, Title, Days, Daily, Total */
            gap: 20px;
            height: 110px;
        }}

        .box {{
            border: 2px solid #fff;
            border-radius: 12px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 0 20px;
            background: #0a0a0a;
            position: relative;
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }}

        /* RANK */
        .rank-box {{
            border-color: #FFD700;
            align-items: center;
        }}
        .rank-val {{
            color: #FFD700; 
            font-size: 4.5rem;
            font-weight: 900;
            line-height: 1;
            text-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
        }}

        /* TITEL */
        .title-box {{
            border-color: #ffffff;
            justify-content: center;
        }}
        .movie-title {{
            font-size: 2rem;
            font-weight: 800;
            text-transform: uppercase;
            line-height: 1.1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        /* LAUFZEIT (TAGE) */
        .days-box {{
            border-color: #666;
            align-items: center;
        }}
        .days-val {{ font-size: 2.5rem; font-weight: 800; color: #fff; line-height:1; }}
        .days-label {{ font-size: 0.8rem; color: #888; font-weight: 700; margin-top: 5px; }}
        .days-sub {{ font-size: 0.7rem; color: #555; text-transform:uppercase; }}

        /* DAILY ADMISSIONS (NEON GRÜN) */
        .daily-box {{
            border-color: #39FF14;
            align-items: flex-end;
            box-shadow: inset 0 0 20px rgba(57, 255, 20, 0.05);
        }}
        .label-green {{ color: #39FF14; font-size: 0.9rem; font-weight: 800; margin-bottom: 2px; }}
        .val-big {{ font-size: 3rem; font-weight: 800; line-height: 1; }}

        /* TOTAL ADMISSIONS (NEON BLAU) */
        .total-box {{
            border-color: #00F0FF; 
            align-items: flex-end;
            box-shadow: inset 0 0 20px rgba(0, 240, 255, 0.05);
        }}
        .label-blue {{ color: #00F0FF; font-size: 0.9rem; font-weight: 800; margin-bottom: 2px; }}

    </style>
</head>
<body>

    <div class="header">
        SÜDKOREA KINOCHARTS <span style="color:#666">|</span> {date_str}
    </div>

    <div class="grid-wrapper">
    """

    for m in movies:
        html += f"""
        <div class="row-container">
            <!-- Rank -->
            <div class="box rank-box">
                <div class="rank-val">{m['rank']}</div>
            </div>

            <!-- Title -->
            <div class="box title-box">
                <div class="movie-title">{m['title']}</div>
            </div>

            <!-- Tage -->
            <div class="box days-box">
                <div class="days-val">{m['days']}</div>
                <div class="days-label">TAGE</div>
                <div class="days-sub">im Kino</div>
            </div>

            <!-- Daily -->
            <div class="box daily-box">
                <div class="label-green">BESUCHER HEUTE</div>
                <div class="val-big">{m['daily']}</div>
            </div>

            <!-- Total -->
            <div class="box total-box">
                <div class="label-blue">GESAMT</div>
                <div class="val-big">{m['total']}</div>
            </div>
        </div>
        """

    html += """
    </div>
    <!-- Footer Timestamp -->
    <div style="margin-top:20px; color:#333; font-size:0.8rem; font-family:sans-serif;">
        Datenquelle: KOBIZ (Korean Film Council)
    </div>
</body>
</html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    print("Starte Scraping...")
    data = get_data()
    if data:
        generate_html(data)
        print(f"Erfolg! {len(data)} Filme gefunden und HTML erstellt.")
    else:
        print("Keine Daten gefunden.")
