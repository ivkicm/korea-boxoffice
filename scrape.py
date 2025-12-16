import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from datetime import datetime
import re

# URL der Seite
URL = "https://www.koreanfilm.or.kr/eng/news/boxOffice_Daily.jsp?mode=BOXOFFICE_DAILY"

def parse_english_date(date_str):
    try:
        date_str = date_str.strip()
        months = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
        parts = date_str.replace(',', '').split()
        if len(parts) != 3: return None
        m_str, d_str, y_str = parts
        month = months.get(m_str)
        if month: return datetime(int(y_str), month, int(d_str))
        return None
    except: return None

def get_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    print(f"Lade Daten von {URL}...")
    try:
        response = requests.get(URL, headers=headers, timeout=30)
        soup = BeautifulSoup(response.content, 'html.parser')
        tbodies = soup.find_all('tbody', id=re.compile(r'listTable_0_\d+'))
        movies = []
        for tbody in tbodies[:5]:
            row = tbody.find('tr')
            cols = row.find_all('td')
            rank = cols[0].text.strip()
            
            title_cell = cols[2]
            p_tags = title_cell.find_all('p')
            title = p_tags[0].text.strip() if p_tags else title_cell.text.strip()

            days_run = "-"
            date_text = cols[3].text.strip()
            release_date = parse_english_date(date_text)
            if release_date:
                delta = datetime.now() - release_date
                days_run = delta.days if delta.days >= 0 else 0

            adm_text = cols[5].get_text(separator='|').strip()
            if '|' in adm_text:
                parts = adm_text.split('|')
                daily = parts[0].strip()
                total = parts[1].replace('(', '').replace(')', '').strip()
            elif '(' in adm_text:
                parts = adm_text.split('(')
                daily = parts[0].strip()
                total = parts[1].replace(')', '').strip()
            else:
                daily = adm_text
                total = adm_text

            movies.append({'rank': rank, 'title': title, 'days': days_run, 'daily': daily, 'total': total})
        print(f"Erfolgreich {len(movies)} Filme verarbeitet.")
        return movies
    except Exception as e:
        print(f"Fehler: {e}")
        return []

def generate_html(movies):
    date_str = datetime.now().strftime("%d.%m.%Y")
    
    # CSS vom US-Script übernommen (VH/VW statt PX)
    css_style = """
        :root { 
            --bg: #000000; 
            --box-bg: #111; 
            --border: #333;
            --text-main: #ffffff;
            --text-dim: #999;
            --green: #00FF41; 
            --blue: #00C2FF;  
            --gold: #FFD700;
        }
        * { box-sizing: border-box; }
        
        body { 
            margin: 0; 
            padding: 0.5vh 2vw; 
            background-color: var(--bg); 
            color: var(--text-main); 
            font-family: 'Inter', sans-serif; 
            height: 100vh; width: 100vw; 
            overflow: hidden; 
            display: flex; flex-direction: column; 
            justify-content: flex-start; 
        }

        /* HEADER */
        .header-container {
            width: 100%;
            text-align: center;
            margin-bottom: 0.5vh;
            border-bottom: 1px solid #222;
            padding-bottom: 0.5vh;
            padding-top: 1vh;
            flex: 0 0 auto;
            display: flex; justify-content: center; align-items: center; gap: 1vw;
        }

        .flag-img { height: 5vh; width: auto; border-radius: 4px; }

        h1 { 
            font-family: 'JetBrains Mono', monospace; 
            font-size: 5.5vh; 
            font-weight: 800;
            color: #ffffff; 
            text-transform: uppercase;
            letter-spacing: 2px;
            margin: 0;
            line-height: 1;
        }

        .list-wrapper {
            display: flex;
            flex-direction: column;
            gap: 0.8vh; 
            width: 100%; 
            flex: 1 1 auto; 
            justify-content: center;
        }

        .movie-row {
            display: grid;
            /* Layout wie US: Title breit, Tage schmal */
            grid-template-columns: 3.5fr 0.5fr 3fr 3fr; 
            gap: 0.8vw; 
            height: 15.5vh; 
            width: 100%;
        }

        .box {
            background-color: var(--box-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            display: flex; flex-direction: column; justify-content: center;
            padding: 0 1vw;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            overflow: hidden;
        }

        /* 1. RANK & NAME */
        .box-title {
            display: flex; flex-direction: row; 
            align-items: center; justify-content: flex-start;
            border-left: 5px solid #fff;
        }
        .rank-1 .box-title { border-left: 5px solid var(--gold); background: linear-gradient(90deg, #1a1a00, #111); }

        .rank {
            font-family: 'JetBrains Mono', monospace;
            font-size: 5vh; font-weight: 900; color: #555;
            margin-right: 1.5vw; min-width: 40px;
        }
        .rank-1 .rank { color: var(--gold); text-shadow: 0 0 15px rgba(255,215,0,0.5); }
        
        .title {
            font-size: 2.8vh; font-weight: 800; text-transform: uppercase;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.1;
        }

        /* 2. TAGE */
        .box-days { align-items: center; border-top: 2px solid #333; }
        .days-val { 
            font-family: 'JetBrains Mono'; 
            font-size: 5vh; 
            font-weight: 900; color: #ddd; line-height: 0.9;
        }
        .label-center { font-size: 1.6vh; font-weight: 700; text-transform: uppercase; color: var(--text-dim); margin-top: 0.5vh;}

        /* 3. DAILY */
        .box-daily {
            align-items: flex-end; 
            border-bottom: 5px solid var(--green); 
            background: linear-gradient(180deg, var(--box-bg), #001a05);
        }
        .val-daily { 
            font-family: 'JetBrains Mono'; 
            font-size: 6.5vh; /* Etwas kleiner als US weil Zahlen länger sein können */
            font-weight: 900; color: #fff; 
            letter-spacing: -2px; 
            line-height: 0.8; 
            text-shadow: 0 0 20px rgba(0,255,65,0.4);
        }
        .lbl-daily { color: var(--green); font-size: 1.6vh; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5vh; }

        /* 4. TOTAL */
        .box-total {
            align-items: flex-end; 
            border-bottom: 5px solid var(--blue); 
            background: linear-gradient(180deg, var(--box-bg), #00121a);
        }
        .val-total { 
            font-family: 'JetBrains Mono'; 
            font-size: 6.5vh; /* Etwas kleiner als US */
            font-weight: 900; color: #ccc; 
            letter-spacing: -2px; 
            line-height: 0.8;
        }
        .lbl-total { color: var(--blue); font-size: 1.6vh; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5vh; }
    """

    html = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Korea Box Office</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@700;800;900&family=Inter:wght@800;900&display=swap" rel="stylesheet">
    <style>{css_style}</style>
</head>
<body>
    <div class="header-container">
        <img src="https://upload.wikimedia.org/wikipedia/commons/0/09/Flag_of_South_Korea.svg" class="flag-img" alt="Korea">
        <h1>
            <span>SÜDKOREA</span>
            <span style="color:#444; margin:0 20px;">|</span>
            <span>{date_str}</span>
        </h1>
    </div>
    
    <div class="list-wrapper">
    """

    if not movies:
        html += "<h2 style='text-align:center; color:red; margin-top:20vh;'>KEINE DATEN VERFÜGBAR</h2>"
    else:
        for m in movies:
            rank = int(m['rank'])
            row_class = "rank-1" if rank == 1 else ""
            
            html += f"""
            <div class="movie-row {row_class}">
                <div class="box box-title">
                    <div class="rank">{rank}</div>
                    <div class="title">{m['title']}</div>
                </div>

                <div class="box box-days">
                    <div class="days-val">{m['days']}</div>
                    <div class="label-center">Tage</div>
                </div>

                <div class="box box-daily">
                    <div class="lbl-daily">Besucher Heute</div>
                    <div class="val-daily">{m['daily']}</div>
                </div>

                <div class="box box-total">
                    <div class="lbl-total">Gesamt</div>
                    <div class="val-total">{m['total']}</div>
                </div>
            </div>
            """

    html += """
    </div>
</body>
</html>
    """
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html (Vollbild) geschrieben.")

if __name__ == "__main__":
    data = get_data()
    generate_html(data)
