import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# URL der Korean Film Council Seite
URL = "https://www.koreanfilm.or.kr/eng/news/boxOffice_Daily.jsp?mode=BOXOFFICE_DAILY"

def get_data():
    # Wir tun so, als wären wir ein normaler Chrome Browser, damit die Seite uns nicht blockiert
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    print(f"Versuche Verbindung zu {URL} (Timeout: 60s)...")
    
    try:
        # TIMEOUT auf 60 Sekunden erhöht wegen langsamer Seite
        response = requests.get(URL, headers=headers, timeout=60)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"Fehler: Server antwortete mit Status Code {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Versuche die Tabelle zu finden
        # Die Seite nutzt oft verschachtelte Tabellen, wir suchen generisch nach der Struktur
        movies = []
        
        # Suche alle Zeilen in allen Tabellen, die Daten enthalten könnten
        all_rows = soup.find_all('tr')
        
        count = 0
        for row in all_rows:
            if count >= 5: break # Nur Top 5
            
            cols = row.find_all('td')
            # Eine gültige Zeile hat meistens Rank, Title, Date, Money, Admissions (ca 8 Spalten)
            if len(cols) < 5: continue
            
            # Prüfen ob die erste Spalte eine Zahl ist (der Rang)
            try:
                rank_text = cols[0].text.strip()
                int(rank_text) # Test ob Zahl
            except:
                continue # Überspringen, war wohl ein Header
            
            # Daten extrahieren
            rank = rank_text
            
            # Titel
            title_raw = cols[1].text.strip()
            title = title_raw.split('\n')[0].strip() # Erste Zeile ist der Titel
            
            # Datum & Tage
            try:
                date_str = cols[2].text.strip()
                # Format meist "Nov 26, 2025"
                release_date = datetime.strptime(date_str, '%b %d, %Y')
                days_run = (datetime.now() - release_date).days
                if days_run < 0: days_run = 0
            except:
                days_run = "-"

            # Admissions (Spalte 5, Index 4)
            adm_text = cols[4].text.replace('\n', '').strip()
            if '(' in adm_text:
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
            count += 1
            
        print(f"Erfolgreich {len(movies)} Filme gefunden.")
        return movies

    except requests.exceptions.Timeout:
        print("FEHLER: Zeitüberschreitung! Die koreanische Seite hat zu lange gebraucht.")
        return []
    except Exception as e:
        print(f"Allgemeiner Fehler: {e}")
        return []

def generate_html(movies):
    date_str = datetime.now().strftime("%d.%m.%Y")
    
    # CSS & Grundgerüst
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
        .header {{ font-size: 2.5rem; font-weight: 900; text-transform: uppercase; margin-bottom: 30px; letter-spacing: 2px; text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; width: 100%; max-width: 1200px; }}
        .grid-wrapper {{ display: flex; flex-direction: column; gap: 15px; width: 100%; max-width: 1200px; }}
        .row-container {{ display: grid; grid-template-columns: 80px 1.5fr 120px 1fr 1fr; gap: 15px; height: 100px; }}
        .box {{ border: 2px solid #fff; border-radius: 8px; display: flex; flex-direction: column; justify-content: center; padding: 0 15px; background: #0a0a0a; }}
        .rank-box {{ border-color: #FFD700; align-items: center; }}
        .rank-val {{ color: #FFD700; font-size: 3.5rem; font-weight: 900; line-height: 1; }}
        .title-box {{ border-color: #ffffff; justify-content: center; }}
        .movie-title {{ font-size: 1.5rem; font-weight: 800; text-transform: uppercase; line-height: 1.1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .days-box {{ border-color: #666; align-items: center; }}
        .days-val {{ font-size: 2rem; font-weight: 800; }}
        .days-label {{ font-size: 0.6rem; color: #888; text-transform: uppercase; margin-top: 5px; }}
        .daily-box {{ border-color: #39FF14; align-items: flex-end; }}
        .label-green {{ color: #39FF14; font-size: 0.7rem; font-weight: 800; margin-bottom: 2px; }}
        .val-big {{ font-size: 2rem; font-weight: 800; line-height: 1; }}
        .total-box {{ border-color: #00F0FF; align-items: flex-end; }}
        .label-blue {{ color: #00F0FF; font-size: 0.7rem; font-weight: 800; margin-bottom: 2px; }}
        
        .error-msg {{ text-align: center; margin-top: 50px; color: #ff3333; border: 1px solid #ff3333; padding: 20px; border-radius: 10px; }}

        @media (max-width: 800px) {{
            .row-container {{ grid-template-columns: 50px 1fr; grid-template-rows: auto auto; height: auto; border-bottom: 1px solid #333; padding-bottom: 20px; }}
            .rank-box {{ grid-row: 1 / 3; }}
            .days-box, .daily-box, .total-box {{ height: 70px; }}
        }}
    </style>
</head>
<body>
    <div class="header">SÜDKOREA KINOCHARTS | {date_str}</div>
    <div class="grid-wrapper">
    """

    if not movies:
        # Fallback-Anzeige, falls die Seite zu langsam war
        html += """
        <div class="error-msg">
            <h2>DATEN NICHT VERFÜGBAR</h2>
            <p>Die koreanische Quellseite antwortet zu langsam.</p>
            <p>Nächster Versuch morgen um 06:01 Uhr.</p>
        </div>
        """
    else:
        for m in movies:
            html += f"""
            <div class="row-container">
                <div class="box rank-box"><div class="rank-val">{m['rank']}</div></div>
                <div class="box title-box"><div class="movie-title">{m['title']}</div></div>
                <div class="box days-box"><div class="days-val">{m['days']}</div><div class="days-label">TAGE</div></div>
                <div class="box daily-box"><div class="label-green">HEUTE</div><div class="val-big">{m['daily']}</div></div>
                <div class="box total-box"><div class="label-blue">GESAMT</div><div class="val-big">{m['total']}</div></div>
            </div>
            """

    html += """
    </div>
</body>
</html>
    """
    
    # WICHTIG: Datei schreiben, egal was passiert ist
    try:
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Datei index.html wurde erfolgreich geschrieben.")
    except Exception as e:
        print(f"Fehler beim Schreiben der Datei: {e}")

if __name__ == "__main__":
    print("Script gestartet...")
    data = get_data()
    generate_html(data)
    print("Script beendet.")
