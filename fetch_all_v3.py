#!/usr/bin/env python3
"""
WongBagus Prediction - Auto Fetcher v3
Source: rumusangkanet.com/paito-teks-{slug}/
Output result.json: format kompatibel dengan index.html
  DB[key] = { name, flag, jadwal, results: [{date, result}] }
"""

import requests
from bs4 import BeautifulSoup
import json, os, re
from datetime import datetime, date
import time

BASE_URL    = "https://rumusangkanet.com"
OUTPUT_FILE = "data/result.json"
MAX_HASIL   = 365

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Referer":         BASE_URL,
}

# Semua 148 pasaran dari rumusangkanet.com/paito-teks
PASARAN_LIST = [
    # ── UTAMA ──
    {"id":"be",    "nama":"Bullseye",              "flag":"🇳🇿", "slug":"bullseye"},
    {"id":"chn",   "nama":"Chinapools",            "flag":"🇨🇳", "slug":"chinapools"},
    {"id":"hkg",   "nama":"Hongkong Pools",        "flag":"🇭🇰", "slug":"hongkong-pools"},
    {"id":"jpn",   "nama":"Japan",                 "flag":"🇯🇵", "slug":"japan"},
    {"id":"cmb2",  "nama":"Magnum Cambodia",       "flag":"🇰🇭", "slug":"magnum-cambodia"},
    {"id":"ncd",   "nama":"North Carolina Day",    "flag":"🇺🇸", "slug":"north-carolina-day"},
    {"id":"sp",    "nama":"Sao Paulo",             "flag":"🇧🇷", "slug":"sao-paulo"},
    {"id":"sgp",   "nama":"Singapore",             "flag":"🇸🇬", "slug":"singapore"},
    {"id":"syd",   "nama":"Sydneypools",           "flag":"🇦🇺", "slug":"sydney-pools"},
    {"id":"twn",   "nama":"Taiwan",                "flag":"🇹🇼", "slug":"taiwan"},
    # ── SEMUA ──
    {"id":"bkk",   "nama":"Bangkok",               "flag":"🇹🇭", "slug":"bangkok"},
    {"id":"beijing","nama":"Beijing",              "flag":"🇨🇳", "slug":"beijing"},
    {"id":"birmingham","nama":"Birmingham",        "flag":"🇬🇧", "slug":"birmingham"},
    {"id":"bochum","nama":"Bochum",                "flag":"🇩🇪", "slug":"bochum"},
    {"id":"bogota","nama":"Bogota",                "flag":"🇨🇴", "slug":"bogota"},
    {"id":"buenosaires","nama":"Buenos Aires",     "flag":"🇦🇷", "slug":"buenos-aires"},
    {"id":"california","nama":"California",        "flag":"🇺🇸", "slug":"california"},
    {"id":"cambodia","nama":"Cambodia",            "flag":"🇰🇭", "slug":"cambodia"},
    {"id":"ctday", "nama":"Connecticut Day",       "flag":"🇺🇸", "slug":"connecticut-day"},
    {"id":"ctnight","nama":"Connecticut Night",    "flag":"🇺🇸", "slug":"connecticut-night"},
    {"id":"darlington","nama":"Darlington",        "flag":"🇬🇧", "slug":"darlington"},
    {"id":"flevening","nama":"Florida Evening",    "flag":"🇺🇸", "slug":"florida-evening"},
    {"id":"flmidday","nama":"Florida Midday",      "flag":"🇺🇸", "slug":"florida-midday"},
    {"id":"fukuoka","nama":"Fukuoka",              "flag":"🇯🇵", "slug":"fukuoka"},
    {"id":"gaevening","nama":"Georgia Evening",    "flag":"🇺🇸", "slug":"georgia-evening"},
    {"id":"gamidday","nama":"Georgia Midday",      "flag":"🇺🇸", "slug":"georgia-midday"},
    {"id":"ganight","nama":"Georgia Night",        "flag":"🇺🇸", "slug":"georgia-night"},
    {"id":"gerplus5","nama":"Germany Plus5",       "flag":"🇩🇪", "slug":"germany-plus5"},
    {"id":"glasgow","nama":"Glasgow",              "flag":"🇬🇧", "slug":"glasgow"},
    {"id":"granada","nama":"Granada",              "flag":"🇪🇸", "slug":"granada"},
    {"id":"greenwich","nama":"Greenwich",          "flag":"🇬🇧", "slug":"greenwich"},
    {"id":"guangzhou","nama":"Guang Zhou",         "flag":"🇨🇳", "slug":"guang-zhou"},
    {"id":"gunpo", "nama":"Gunpo",                 "flag":"🇰🇷", "slug":"gunpo"},
    {"id":"hamburg","nama":"Hamburg",              "flag":"🇩🇪", "slug":"hamburg"},
    {"id":"hanoi", "nama":"Hanoi",                 "flag":"🇻🇳", "slug":"hanoi"},
    {"id":"hklottery","nama":"Hongkong Lottery",   "flag":"🇭🇰", "slug":"hongkong"},
    {"id":"hklotto","nama":"Hongkong Lotto",       "flag":"🇭🇰", "slug":"hklotto"},
    {"id":"huizhou","nama":"Huizhou",              "flag":"🇨🇳", "slug":"huizhou"},
    {"id":"ilevening","nama":"Illinois Evening",   "flag":"🇺🇸", "slug":"illinois-evening"},
    {"id":"ilmidday","nama":"Illinois Midday",     "flag":"🇺🇸", "slug":"illinois-midday"},
    {"id":"incheon","nama":"Incheon",              "flag":"🇰🇷", "slug":"incheon"},
    {"id":"inevening","nama":"Indiana Evening",    "flag":"🇺🇸", "slug":"indiana-evening"},
    {"id":"inmidday","nama":"Indiana Midday",      "flag":"🇺🇸", "slug":"indiana-midday"},
    {"id":"istanbul","nama":"Istanbul",            "flag":"🇹🇷", "slug":"istanbul"},
    {"id":"jenewa","nama":"Jenewa",                "flag":"🇨🇭", "slug":"jenewa"},
    {"id":"johor", "nama":"Johor",                 "flag":"🇲🇾", "slug":"johor"},
    {"id":"kyevening","nama":"Kentucky Evening",   "flag":"🇺🇸", "slug":"kentucky-evening"},
    {"id":"kymidday","nama":"Kentucky Midday",     "flag":"🇺🇸", "slug":"kentucky-midday"},
    {"id":"lasvegas","nama":"Las Vegas",           "flag":"🇺🇸", "slug":"las-vegas"},
    {"id":"lincoln","nama":"Lincoln",              "flag":"🇺🇸", "slug":"lincoln"},
    {"id":"lisbon","nama":"Lisbon",                "flag":"🇵🇹", "slug":"lisbon"},
    {"id":"lucerne","nama":"Lucerne",              "flag":"🇨🇭", "slug":"lucerne"},
    {"id":"luzhou","nama":"Luzhou",                "flag":"🇨🇳", "slug":"luzhou"},
    {"id":"lyon",  "nama":"Lyon",                  "flag":"🇫🇷", "slug":"lyon"},
    {"id":"macau", "nama":"Macau",                 "flag":"🇲🇴", "slug":"macau"},
    {"id":"malawi","nama":"Malawi",                "flag":"🇲🇼", "slug":"malawi"},
    {"id":"maldives","nama":"Maldives",            "flag":"🇲🇻", "slug":"maldives"},
    {"id":"marbella","nama":"Marbella",            "flag":"🇪🇸", "slug":"marbella"},
    {"id":"marseille","nama":"Marseille",          "flag":"🇫🇷", "slug":"marseille"},
    {"id":"mdevening","nama":"Maryland Evening",   "flag":"🇺🇸", "slug":"maryland-evening"},
    {"id":"mdmidday","nama":"Maryland Midday",     "flag":"🇺🇸", "slug":"maryland-midday"},
    {"id":"melbourne","nama":"Melbourne",          "flag":"🇦🇺", "slug":"melbourne"},
    {"id":"metz",  "nama":"Metz",                  "flag":"🇫🇷", "slug":"metz"},
    {"id":"mexicocity","nama":"Mexico City",       "flag":"🇲🇽", "slug":"mexico-city"},
    {"id":"mievening","nama":"Michigan Evening",   "flag":"🇺🇸", "slug":"michigan-evening"},
    {"id":"mimidday","nama":"Michigan Midday",     "flag":"🇺🇸", "slug":"michigan-midday"},
    {"id":"milan", "nama":"Milan",                 "flag":"🇮🇹", "slug":"milan"},
    {"id":"milmidday","nama":"Milwaukee Midday",   "flag":"🇺🇸", "slug":"milwaukee-midday"},
    {"id":"milmorning","nama":"Milwaukee Morning", "flag":"🇺🇸", "slug":"milwaukee-morning"},
    {"id":"msday", "nama":"Mississauga Day",       "flag":"🇨🇦", "slug":"mississauga-day"},
    {"id":"msevening","nama":"Mississauga Evening","flag":"🇨🇦", "slug":"mississauga-evening"},
    {"id":"msmidnight","nama":"Mississauga Midnight","flag":"🇨🇦","slug":"mississauga-midnight"},
    {"id":"msmorning","nama":"Mississauga Morning","flag":"🇨🇦", "slug":"mississauga-morning"},
    {"id":"msnight","nama":"Mississauga Night",    "flag":"🇨🇦", "slug":"mississauga-night"},
    {"id":"moevening","nama":"Missouri Evening",   "flag":"🇺🇸", "slug":"missouri-evening"},
    {"id":"momidday","nama":"Missouri Midday",     "flag":"🇺🇸", "slug":"missouri-midday"},
    {"id":"montreal","nama":"Montreal",            "flag":"🇨🇦", "slug":"montreal"},
    {"id":"morocco03","nama":"Morocco Quatro 03:00","flag":"🇲🇦","slug":"morocco-quatro-03-00-wib"},
    {"id":"morocco18","nama":"Morocco Quatro 18:00","flag":"🇲🇦","slug":"morocco-quatro-18-00-wib"},
    {"id":"morocco21","nama":"Morocco Quatro 21:00","flag":"🇲🇦","slug":"morocco-quatro-21-00-wib"},
    {"id":"morocco23","nama":"Morocco Quatro 23:59","flag":"🇲🇦","slug":"morocco-quatro-23-59-wib"},
    {"id":"muenchen","nama":"Muenchen",            "flag":"🇩🇪", "slug":"muenchen"},
    {"id":"mumbai","nama":"Mumbai",                "flag":"🇮🇳", "slug":"mumbai"},
    {"id":"munster","nama":"Munster",              "flag":"🇩🇪", "slug":"munster"},
    {"id":"murcia","nama":"Murcia",                "flag":"🇪🇸", "slug":"murcia"},
    {"id":"nagoya","nama":"Nagoya",                "flag":"🇯🇵", "slug":"nagoya"},
    {"id":"nanjing","nama":"Nanjing",              "flag":"🇨🇳", "slug":"nanjing"},
    {"id":"naples","nama":"Naples",                "flag":"🇮🇹", "slug":"naples"},
    {"id":"newdelhi","nama":"New Delhi",           "flag":"🇮🇳", "slug":"new-delhi"},
    {"id":"njevening","nama":"New Jersey Evening", "flag":"🇺🇸", "slug":"new-jersey-evening"},
    {"id":"njmidday","nama":"New Jersey Midday",   "flag":"🇺🇸", "slug":"new-jersey-midday"},
    {"id":"nyevening","nama":"New York Evening",   "flag":"🇺🇸", "slug":"new-york-evening"},
    {"id":"nymidday","nama":"New York Midday",     "flag":"🇺🇸", "slug":"new-york-midday"},
    {"id":"ncn",   "nama":"North Carolina Evening","flag":"🇺🇸", "slug":"north-carolina-evening"},
    {"id":"oregon04","nama":"Oregon 04:00",        "flag":"🇺🇸", "slug":"oregon-04-00-wib"},
    {"id":"oregon07","nama":"Oregon 07:00",        "flag":"🇺🇸", "slug":"oregon-07-00-wib"},
    {"id":"oregon10","nama":"Oregon 10:00",        "flag":"🇺🇸", "slug":"oregon-10-00-wib"},
    {"id":"oregon13","nama":"Oregon 13:00",        "flag":"🇺🇸", "slug":"oregon-13-00-wib"},
    {"id":"osaka", "nama":"Osaka",                 "flag":"🇯🇵", "slug":"osaka"},
    {"id":"paju",  "nama":"Paju",                  "flag":"🇰🇷", "slug":"paju"},
    {"id":"paris", "nama":"Paris",                 "flag":"🇫🇷", "slug":"paris"},
    {"id":"pcso",  "nama":"Pcso",                  "flag":"🇵🇭", "slug":"pcso"},
    {"id":"perth", "nama":"Perth",                 "flag":"🇦🇺", "slug":"perth"},
    {"id":"phoenix","nama":"Phoenix",              "flag":"🇺🇸", "slug":"phoenix"},
    {"id":"pisa",  "nama":"Pisa",                  "flag":"🇮🇹", "slug":"pisa"},
    {"id":"reims", "nama":"Reims",                 "flag":"🇫🇷", "slug":"reims"},
    {"id":"rio",   "nama":"Rio De Janeiro",        "flag":"🇧🇷", "slug":"rio-de-janeiro"},
    {"id":"rostock","nama":"Rostock",              "flag":"🇩🇪", "slug":"rostock"},
    {"id":"rotterdam","nama":"Rotterdam",          "flag":"🇳🇱", "slug":"rotterdam"},
    {"id":"saitama","nama":"Saitama",              "flag":"🇯🇵", "slug":"saitama"},
    {"id":"sandiego","nama":"San Diego",           "flag":"🇺🇸", "slug":"san-diego"},
    {"id":"santiago","nama":"Santiago",            "flag":"🇨🇱", "slug":"santiago"},
    {"id":"sapporo","nama":"Sapporo",              "flag":"🇯🇵", "slug":"sapporo"},
    {"id":"seoul", "nama":"Seoul",                 "flag":"🇰🇷", "slug":"seoul"},
    {"id":"shanghai","nama":"Shanghai",            "flag":"🇨🇳", "slug":"shanghai"},
    {"id":"siena", "nama":"Siena",                 "flag":"🇮🇹", "slug":"siena"},
    {"id":"sochi", "nama":"Sochi",                 "flag":"🇷🇺", "slug":"sochi"},
    {"id":"stpetersburg","nama":"St.Petersburg",   "flag":"🇷🇺", "slug":"st-petersburg"},
    {"id":"suwon", "nama":"Suwon",                 "flag":"🇰🇷", "slug":"suwon"},
    {"id":"sydlottery","nama":"Sydney Lottery",    "flag":"🇦🇺", "slug":"sydney"},
    {"id":"sdlotto","nama":"Sydney Lotto",         "flag":"🇦🇺", "slug":"sdlotto"},
    {"id":"taiyuan","nama":"Taiyuan",              "flag":"🇨🇳", "slug":"taiyuan"},
    {"id":"tnevening","nama":"Tennesse Evening",   "flag":"🇺🇸", "slug":"tennesse-evening"},
    {"id":"tnmidday","nama":"Tennesse Midday",     "flag":"🇺🇸", "slug":"tennesse-midday"},
    {"id":"tnmorning","nama":"Tennesse Morning",   "flag":"🇺🇸", "slug":"tennesse-morning"},
    {"id":"txday", "nama":"Texas Day",             "flag":"🇺🇸", "slug":"texas-day"},
    {"id":"txevening","nama":"Texas Evening",      "flag":"🇺🇸", "slug":"texas-evening"},
    {"id":"txmorning","nama":"Texas Morning",      "flag":"🇺🇸", "slug":"texas-morning"},
    {"id":"txnight","nama":"Texas Night",          "flag":"🇺🇸", "slug":"texas-night"},
    {"id":"tokyo", "nama":"Tokyo",                 "flag":"🇯🇵", "slug":"tokyo"},
    {"id":"tmacau00","nama":"Toto Macau 00",       "flag":"🇲🇴", "slug":"toto-macau-5"},
    {"id":"tmacau13","nama":"Toto Macau 13",       "flag":"🇲🇴", "slug":"toto-macau-1"},
    {"id":"tmacau16","nama":"Toto Macau 16",       "flag":"🇲🇴", "slug":"toto-macau-2"},
    {"id":"tmacau19","nama":"Toto Macau 19",       "flag":"🇲🇴", "slug":"toto-macau-3"},
    {"id":"tmacau22","nama":"Toto Macau 22",       "flag":"🇲🇴", "slug":"toto-macau-4"},
    {"id":"troyes","nama":"Troyes",                "flag":"🇫🇷", "slug":"troyes"},
    {"id":"venice","nama":"Venice",                "flag":"🇮🇹", "slug":"venice"},
    {"id":"versailles","nama":"Versailles",        "flag":"🇫🇷", "slug":"versailles"},
    {"id":"vaday", "nama":"Virginia Day",          "flag":"🇺🇸", "slug":"virginia-day"},
    {"id":"vanight","nama":"Virginia Night",       "flag":"🇺🇸", "slug":"virginia-night"},
    {"id":"vladimir","nama":"Vladimir",            "flag":"🇷🇺", "slug":"vladimir"},
    {"id":"warsaw","nama":"Warsaw",                "flag":"🇵🇱", "slug":"warsaw"},
    {"id":"wdcevening","nama":"Washington DC Evening","flag":"🇺🇸","slug":"washington-dc-evening"},
    {"id":"wdcmidday","nama":"Washington DC Midday","flag":"🇺🇸","slug":"washington-dc-midday"},
    {"id":"weimar","nama":"Weimar",                "flag":"🇩🇪", "slug":"weimar"},
    {"id":"wv",    "nama":"West Virginia",         "flag":"🇺🇸", "slug":"west-virginia"},
    {"id":"wim",   "nama":"Wisconsin Evening",     "flag":"🇺🇸", "slug":"wisconsin-evening"},
    {"id":"yokohama","nama":"Yokohama",            "flag":"🇯🇵", "slug":"yokohama"},
    {"id":"zurich","nama":"Zurich",                "flag":"🇨🇭", "slug":"zurich"},
]

session = requests.Session()
session.headers.update(HEADERS)

def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=25)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"    [retry {attempt+1}] {e}")
            time.sleep(4 * (attempt+1))
    return None

def scrape_paito_teks(p):
    """
    Scrape angka 4D dari halaman paito-teks.
    Return: list string 4D urut lama→baru
    """
    pid  = p["id"]
    url  = f"{BASE_URL}/paito-teks-{p['slug']}/"
    print(f"  [{pid}] GET {url}")

    soup = fetch_html(url)
    if not soup:
        print(f"  [{pid}] ❌ Gagal")
        return []

    for tag in soup(["script","style","nav","header","footer","aside","noscript","meta","link"]):
        tag.decompose()

    raw    = soup.get_text(separator=" ")
    tokens = re.findall(r'\b(\d{4})\b', raw)

    hasil = []
    seen  = set()
    for t in tokens:
        n = int(t)
        if 2015 <= n <= 2035:
            continue
        if t in seen:
            continue
        seen.add(t)
        hasil.append(t)

    hasil = hasil[-MAX_HASIL:]
    print(f"  [{pid}] ✅ {len(hasil)} angka")
    return hasil  # lama→baru

def main():
    os.makedirs("data", exist_ok=True)
    now_str   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = str(date.today())

    print(f"\n{'='*55}")
    print(f"  WongBagus Prediction — Fetch All v3")
    print(f"  {now_str}  |  {len(PASARAN_LIST)} pasaran")
    print(f"{'='*55}\n")

    # Load existing
    existing = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE) as f:
                existing = json.load(f)
            print(f"[load] Existing: {len(existing)} pasaran\n")
        except Exception as e:
            print(f"[load] File rusak ({e}), mulai fresh\n")

    output = {}

    for p in PASARAN_LIST:
        pid = p["id"]
        print(f"\n▶ [{pid.upper()}] {p['nama']}")

        angka_list = scrape_paito_teks(p)

        # Ambil existing results
        old_results = existing.get(pid, {}).get("results", [])
        old_nums    = [r["result"] for r in old_results]

        if not angka_list:
            print(f"  [{pid}] Fallback existing: {len(old_nums)} entri")
            combined = old_nums
        else:
            # Merge: existing dulu + baru, deduplikasi, urut lama→baru
            combined_seen = set()
            combined = []
            for n in old_nums:
                if n not in combined_seen:
                    combined_seen.add(n)
                    combined.append(n)
            for n in angka_list:
                if n not in combined_seen:
                    combined_seen.add(n)
                    combined.append(n)
            combined = combined[-MAX_HASIL:]

        # Format output: [{date, result}]
        # Angka dari web tidak punya tanggal → pakai placeholder
        # Kalau existing punya tanggal, pertahankan
        old_map = {r["result"]: r.get("date","") for r in old_results}
        results = []
        for num in reversed(combined):  # terbaru dulu (index 0 = terbaru)
            results.append({
                "date":   old_map.get(num, ""),
                "result": num
            })

        last = results[0] if results else {}
        print(f"  [{pid}] Tersimpan: {len(results)} | Last: {last.get('result','?')}")

        output[pid] = {
            "name":    p["nama"],
            "flag":    p["flag"],
            "slug":    p["slug"],
            "updated": now_str,
            "results": results,  # index 0 = TERBARU
        }

        time.sleep(1.5)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["results"]) for v in output.values())
    print(f"\n✅ Done! → {OUTPUT_FILE}")
    print(f"   Pasaran: {len(output)} | Total hasil: {total}\n")

if __name__ == "__main__":
    main()
