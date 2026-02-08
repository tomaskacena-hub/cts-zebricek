import re
import time
from datetime import date, datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup

DATE_FROM = date(2025, 4, 1)
DATE_TO = date.today()

ALLOWED_YEARS = {2014, 2015}
TOP_N = 200

OUT_XLSX = "zebricek_TOP200_2014_2015.xlsx"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

RANKING_URL = "https://www.cztenis.cz/mladsi-zactvo/zebricky"


def get_html(url):
    return session.get(url, timeout=30).text


def parse_date(text):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", text)
    if not m:
        return None
    d, mth, y = map(int, m.groups())
    return date(y, mth, d)


def get_players():
    html = get_html(RANKING_URL)
    soup = BeautifulSoup(html, "lxml")

    players = []
    for a in soup.select('a[href^="/hrac/"]'):
        name = a.get_text(strip=True)
        url = "https://www.cztenis.cz" + a["href"]
        players.append((name, url))
        if len(players) >= TOP_N:
            break
    return players


def extract_points(player_url):
    html = get_html(player_url)
    soup = BeautifulSoup(html, "lxml")

    text = soup.get_text("\n", strip=True)

    year = None
    m = re.search(r"Rok narození:\s*(\d{4})", text)
    if m:
        year = int(m.group(1))

    if year not in ALLOWED_YEARS:
        return None

    tables = soup.find_all("table")
    points = []

    for tbl in tables:
        rows = tbl.find_all("tr")
        for r in rows:
            txt = r.get_text(" ", strip=True)
            dt = parse_date(txt)
            if not dt:
                continue
            if not (DATE_FROM <= dt <= DATE_TO):
                continue
            nums = re.findall(r"\b\d+\b", txt)
            if nums:
                points.append(int(nums[-1]))

    if not points:
        return (year, 1)

    best8 = sorted(points, reverse=True)[:8]
    return (year, sum(best8))


def main():
    players = get_players()
    rows = []

    for i, (name, url) in enumerate(players, start=1):
        try:
            res = extract_points(url)
            if not res:
                continue
            year, pts = res
            rows.append({
                "poradi": i,
                "jmeno": name,
                "rocnik": year,
                "body": pts,
                "url": url
            })
        except:
            continue
        time.sleep(0.2)

    df = pd.DataFrame(rows)
    df = df.sort_values("body", ascending=False).reset_index(drop=True)
    df.insert(0, "poradi_nove", range(1, len(df) + 1))

    df.to_excel(OUT_XLSX, index=False)
    print("Hotovo:", OUT_XLSX)


if __name__ == "__main__":
    main()
