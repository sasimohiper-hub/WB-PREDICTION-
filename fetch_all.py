#!/usr/bin/env python3
"""
WongBagus Prediction - Auto Fetcher v2
Source: rumusangkanet.com/paito-teks-{slug}/
Output result.json: hasil[] urut lama→baru (index 0 = paling lama)
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, date
import time

# ── CONFIG ───────────────────────────────────────────────────────────────────
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

PASARAN_LIST = [
    {"id":"ncd",   "nama":"North Carolina Day",  "kode":"NCD",  "negara":"🇺🇸", "slug":"north-carolina-day"},
    {"id":"ncn",   "nama":"North Carolina Night", "kode":"NCN",  "negara":"🇺🇸", "slug":"north-carolina-evening"},
    {"id":"sgp",   "nama":"Singapore",            "kode":"SGP",  "negara":"🇸🇬", "slug":"singapore"},
    {"id":"hkg",   "nama":"Hongkong Pools",       "kode":"HKG",  "negara":"🇭🇰", "slug":"hongkong-pools"},
    {"id":"syd",   "nama":"Sydneypools",          "kode":"SYD",  "negara":"🇦🇺", "slug":"sydney-pools"},
    {"id":"jpn",   "nama":"Japan",                "kode":"JPN",  "negara":"🇯🇵", "slug":"japan"},
    {"id":"twn",   "nama":"Taiwan",               "kode":"TWN",  "negara":"🇹🇼", "slug":"taiwan"},
    {"id":"chn",   "nama":"Chinapools",           "kode":"CHN",  "negara":"🇨🇳", "slug":"chinapools"},
    {"id":"cmb2",  "nama":"Magnum Cambodia",      "kode":"CMB2", "negara":"🇰🇭", "slug":"magnum-cambodia"},
    {"id":"be",    "nama":"Bullseye",             "kode":"BE",   "negara":"🇳🇿", "slug":"bullseye"},
    {"id":"sp",    "nama":"Sao Paulo",            "kode":"SP",   "negara":"🇧🇷", "slug":"sao-paulo"},
    {"id":"wim",   "nama":"Wisconsin Midday",     "kode":"WIM",  "negara":"🇺🇸", "slug":"wisconsin-evening"},
    {"id":"macau", "nama":"Macau",                "kode":"MAC",  "negara":"🇲🇴", "slug":"macau"},
    {"id":"bkk",   "nama":"Bangkok",              "kode":"BKK",  "negara":"🇹🇭", "slug":"bangkok"},
    {"id":"kl",    "nama":"Kuala Lumpur",         "kode":"KL",   "negara":"🇲🇾", "slug":"johor"},
]

DRAW_SCHEDULE = {
    "ncd":"13:30","ncn":"23:00","sgp":"17:45","hkg":"23:00",
    "syd":"13:55","jpn":"13:00","twn":"21:00","chn":"21:30",
    "cmb2":"18:30","be":"16:00","sp":"03:00","wim":"13:30",
    "macau":"21:05","bkk":"21:00","kl":"19:00",
}

session = requests.Session()
session.headers.update(HEADERS)

def fetch_html(url: str, retries=3):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=25)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"    [retry {attempt+1}] {e}")
            time.sleep(4 * (attempt + 1))
    return None

def scrape_paito_teks(p: dict) -> list:
    pid  = p["id"]
    url  = f"{BASE_URL}/paito-teks-{p['slug']}/"
    print(f"  [{pid}] GET {url}")

    soup = fetch_html(url)
    if not soup:
        print(f"  [{pid}] ❌ Gagal fetch")
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
    print(f"  [{pid}] ✅ {len(hasil)} angka (lama→baru)")
    return hasil

def main():
    os.makedirs("data", exist_ok=True)
    now_str   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = str(date.today())

    print(f"\n{'='*55}")
    print(f"  WongBagus Prediction — Fetch All v2")
    print(f"  {now_str}")
    print(f"{'='*55}\n")

    existing = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE) as f:
                existing = json.load(f)
            print(f"[load] Existing: {len(existing.get('pasaran', {}))} pasaran\n")
        except Exception as e:
            print(f"[load] File rusak ({e}), mulai fresh\n")

    output = {
        "meta": {
            "updated_at":   now_str,
            "updated_date": today_str,
            "source":       "rumusangkanet.com/paito-teks",
            "by":           "WongBagus Prediction",
        },
        "pasaran": {}
    }

    for p in PASARAN_LIST:
        pid = p["id"]
        print(f"\n▶ [{pid.upper()}] {p['nama']}")

        angka_list = scrape_paito_teks(p)

        old_hasil = existing.get("pasaran", {}).get(pid, {}).get("hasil", [])
        old_nums  = [r["result"] for r in old_hasil]

        if not angka_list:
            print(f"  [{pid}] Fallback existing: {len(old_nums)} entri")
            combined = old_nums
        else:
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

        hasil_final = [{"urutan": i+1, "result": r} for i, r in enumerate(combined)]
        last = hasil_final[-1] if hasil_final else {}

        print(f"  [{pid}] Tersimpan: {len(hasil_final)} | Last: {last.get('result','?')}")

        output["pasaran"][pid] = {
            "info":        p,
            "jadwal":      DRAW_SCHEDULE.get(pid, ""),
            "hasil":       hasil_final,
            "last_result": last,
        }

        time.sleep(1.5)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["hasil"]) for v in output["pasaran"].values())
    print(f"\n✅ Done! → {OUTPUT_FILE}")
    print(f"   Pasaran: {len(output['pasaran'])} | Total hasil: {total}\n")

if __name__ == "__main__":
    main()
