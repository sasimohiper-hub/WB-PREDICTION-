#!/usr/bin/env python3
"""
WongBagus Prediction - Auto Fetcher v5
Source  : angkanet.com (API JSON publik)
Output  : data/result.json
"""

import requests, json, os, re
from datetime import datetime
import time

OUTPUT_FILE = "data/result.json"
MAX_HASIL   = 365

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "id-ID,id;q=0.9",
    "Referer": "https://www.angkanet.com/",
}

PASARAN_LIST = [
    {"id":"hkg",  "nama":"Hongkong Pools",     "flag":"🇭🇰", "kode":"hongkong"},
    {"id":"sgp",  "nama":"Singapore",          "flag":"🇸🇬", "kode":"singapore"},
    {"id":"syd",  "nama":"Sydneypools",        "flag":"🇦🇺", "kode":"sydney"},
    {"id":"jpn",  "nama":"Japan",              "flag":"🇯🇵", "kode":"japan"},
    {"id":"twn",  "nama":"Taiwan",             "flag":"🇹🇼", "kode":"taiwan"},
    {"id":"ncd",  "nama":"North Carolina Day", "flag":"🇺🇸", "kode":"northcarolina"},
    {"id":"cmb2", "nama":"Magnum Cambodia",    "flag":"🇰🇭", "kode":"cambodia"},
    {"id":"be",   "nama":"Bullseye",           "flag":"🇳🇿", "kode":"bullseye"},
    {"id":"chn",  "nama":"Chinapools",         "flag":"🇨🇳", "kode":"china"},
    {"id":"sp",   "nama":"Sao Paulo",          "flag":"🇧🇷", "kode":"saopaulo"},
]

session = requests.Session()
session.headers.update(HEADERS)

def fetch_angkanet(kode, retries=3):
    """Coba beberapa endpoint angkanet"""
    urls = [
        f"https://www.angkanet.com/result/{kode}/",
        f"https://angkanet.com/result/{kode}/",
        f"https://www.angkanet.com/paito/{kode}/",
    ]
    for url in urls:
        for attempt in range(retries):
            try:
                r = session.get(url, timeout=20)
                if r.status_code == 200:
                    return r.text, url
                print(f"    [attempt {attempt+1}] HTTP {r.status_code} - {url}")
            except Exception as e:
                print(f"    [attempt {attempt+1}] Error: {e}")
            time.sleep(3)
    return None, None

def parse_result(html):
    """Extract tanggal + 4 digit dari HTML angkanet"""
    hasil = []
    if not html:
        return hasil

    # Cari pola tanggal YYYY-MM-DD atau DD-MM-YYYY diikuti 4 digit
    # Pattern 1: YYYY-MM-DD ... 4digit
    patterns = [
        r'(\d{4}-\d{2}-\d{2})[^0-9]*?(\d{4})\b',
        r'(\d{2}-\d{2}-\d{4})[^0-9]*?(\d{4})\b',
        r'(\d{2}/\d{2}/\d{4})[^0-9]*?(\d{4})\b',
    ]

    for pat in patterns:
        matches = re.findall(pat, html)
        if matches:
            for tgl_raw, result in matches:
                # skip tahun
                if 2020 <= int(result) <= 2030:
                    continue
                # Normalize tanggal ke YYYY-MM-DD
                if re.match(r'\d{4}-\d{2}-\d{2}', tgl_raw):
                    tgl = tgl_raw
                elif re.match(r'\d{2}-\d{2}-\d{4}', tgl_raw):
                    p = tgl_raw.split('-')
                    tgl = f"{p[2]}-{p[1]}-{p[0]}"
                elif re.match(r'\d{2}/\d{2}/\d{4}', tgl_raw):
                    p = tgl_raw.split('/')
                    tgl = f"{p[2]}-{p[1]}-{p[0]}"
                else:
                    continue
                hasil.append({"date": tgl, "result": result})
            if hasil:
                break

    # Deduplikasi
    seen = set()
    deduped = []
    for item in hasil:
        if item["date"] not in seen:
            seen.add(item["date"])
            deduped.append(item)

    deduped.sort(key=lambda x: x["date"])
    return deduped

def main():
    os.makedirs("data", exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*55}")
    print(f"  WongBagus Prediction — Fetch All v5")
    print(f"  {now_str}  |  {len(PASARAN_LIST)} pasaran")
    print(f"{'='*55}\n")

    # Load existing
    existing = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE) as f:
                existing = json.load(f)
            print(f"[load] Existing: {len(existing)} pasaran\n")
        except:
            print("[load] Mulai fresh\n")

    output = {}

    for p in PASARAN_LIST:
        pid  = p["id"]
        print(f"\n▶ [{pid.upper()}] {p['nama']}")

        html, url_used = fetch_angkanet(p["kode"])
        if html:
            print(f"  [{pid}] ✅ Fetched dari {url_used}")
        new_results = parse_result(html)
        print(f"  [{pid}] Parsed: {len(new_results)} entri")

        # Merge dengan existing
        old_desc = existing.get(pid, {}).get("results", [])
        old_asc  = list(reversed(old_desc))

        date_map = {}
        for item in old_asc:
            if item.get("date"):
                date_map[item["date"]] = item["result"]
        for item in new_results:
            if item.get("date"):
                date_map[item["date"]] = item["result"]

        merged_asc = [{"date": d, "result": r} for d, r in sorted(date_map.items())]
        merged_asc = merged_asc[-MAX_HASIL:]
        results_desc = list(reversed(merged_asc))

        last = results_desc[0] if results_desc else {}
        print(f"  [{pid}] Total: {len(results_desc)} | Last: {last.get('date','?')} → {last.get('result','?')}")

        output[pid] = {
            "name":    p["nama"],
            "flag":    p["flag"],
            "updated": now_str,
            "results": results_desc,
        }

        time.sleep(2)

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["results"]) for v in output.values())
    print(f"\n✅ Done! → {OUTPUT_FILE}")
    print(f"   Pasaran: {len(output)} | Total hasil: {total}\n")

if __name__ == "__main__":
    main()
