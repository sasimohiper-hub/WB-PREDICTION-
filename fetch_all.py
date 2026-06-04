#!/usr/bin/env python3
"""
WongBagus Prediction - Auto Fetcher v6
Source  : angkanet22.com/paito-harian-{slug}/
Output  : data/result.json
"""

import requests
from bs4 import BeautifulSoup
import json, os, re
from datetime import datetime, date
import time

OUTPUT_FILE = "data/result.json"
MAX_HASIL   = 365

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Referer":         "https://angkanet22.com/",
}

PASARAN_LIST = [
    {"id":"hkg",  "nama":"Hongkong Pools",     "flag":"🇭🇰", "slug":"hongkong-pools"},
    {"id":"sgp",  "nama":"Singapore",          "flag":"🇸🇬", "slug":"singapore"},
    {"id":"syd",  "nama":"Sydneypools",        "flag":"🇦🇺", "slug":"sydney-pools"},
    {"id":"jpn",  "nama":"Japan",              "flag":"🇯🇵", "slug":"japan"},
    {"id":"twn",  "nama":"Taiwan",             "flag":"🇹🇼", "slug":"taiwan"},
    {"id":"ncd",  "nama":"North Carolina Day", "flag":"🇺🇸", "slug":"north-carolina-day"},
    {"id":"cmb2", "nama":"Magnum Cambodia",    "flag":"🇰🇭", "slug":"magnum-cambodia"},
    {"id":"be",   "nama":"Bullseye",           "flag":"🇳🇿", "slug":"bullseye"},
    {"id":"chn",  "nama":"Chinapools",         "flag":"🇨🇳", "slug":"chinapools"},
    {"id":"sp",   "nama":"Sao Paulo",          "flag":"🇧🇷", "slug":"sao-paulo"},
]

# Coba beberapa domain mirror angkanet
DOMAINS = [
    "https://angkanet22.com",
    "https://angkanet18.com",
    "https://angkanet20.com",
    "https://rumusangkanet.com",
]

session = requests.Session()
session.headers.update(HEADERS)

def fetch_html(slug, retries=2):
    for domain in DOMAINS:
        url = f"{domain}/paito-harian-{slug}/"
        for attempt in range(retries):
            try:
                r = session.get(url, timeout=20)
                if r.status_code == 200:
                    print(f"    ✅ OK: {url}")
                    return r.text
                print(f"    [{attempt+1}] HTTP {r.status_code} - {domain}")
            except Exception as e:
                print(f"    [{attempt+1}] Error: {e}")
            time.sleep(3)
    return None

def parse_tanggal(raw):
    m = re.match(r'(\d{2})-(\d{2})-(\d{4})', raw.strip())
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return ""

def scrape(p):
    pid  = p["id"]
    html = fetch_html(p["slug"])
    if not html:
        print(f"  [{pid}] ❌ Semua domain gagal")
        return []

    soup  = BeautifulSoup(html, "html.parser")
    hasil = []

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td","th"])
            if len(cells) < 5:
                continue
            cell0 = cells[0].get_text(strip=True)
            if not re.match(r'\d{2}-\d{2}-\d{4}', cell0):
                continue
            tgl = parse_tanggal(cell0)
            if not tgl:
                continue
            digits = []
            for i in range(1, 5):
                if i < len(cells):
                    d = cells[i].get_text(strip=True)
                    if re.match(r'^\d$', d):
                        digits.append(d)
            if len(digits) == 4:
                hasil.append({"date": tgl, "result": "".join(digits)})

    # Fallback: parse teks
    if not hasil:
        text = soup.get_text(separator="\n")
        for line in text.split("\n"):
            line = line.strip()
            date_m = re.search(r'(\d{2}-\d{2}-\d{4})', line)
            if not date_m:
                continue
            tgl = parse_tanggal(date_m.group(1))
            nums = re.findall(r'\b(\d{4})\b', line)
            nums = [n for n in nums if not (2020 <= int(n) <= 2030)]
            if nums:
                hasil.append({"date": tgl, "result": nums[0]})

    # Deduplikasi & sort
    seen = set()
    deduped = []
    for item in hasil:
        if item["date"] not in seen:
            seen.add(item["date"])
            deduped.append(item)
    deduped.sort(key=lambda x: x["date"])
    print(f"  [{pid}] ✅ {len(deduped)} hasil")
    return deduped

def main():
    os.makedirs("data", exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*55}")
    print(f"  WongBagus Prediction — Fetch All v6")
    print(f"  {now_str}  |  {len(PASARAN_LIST)} pasaran")
    print(f"{'='*55}\n")

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
        pid = p["id"]
        print(f"\n▶ [{pid.upper()}] {p['nama']}")

        new_results  = scrape(p)
        old_desc     = existing.get(pid, {}).get("results", [])
        old_asc      = list(reversed(old_desc))

        if not new_results:
            merged_asc = old_asc
        else:
            date_map = {}
            for item in old_asc:
                if item.get("date"):
                    date_map[item["date"]] = item["result"]
            for item in new_results:
                if item.get("date"):
                    date_map[item["date"]] = item["result"]
            merged_asc = [{"date":d,"result":r} for d,r in sorted(date_map.items())]
            merged_asc = merged_asc[-MAX_HASIL:]

        results_desc = list(reversed(merged_asc))
        last = results_desc[0] if results_desc else {}
        print(f"  [{pid}] Total: {len(results_desc)} | Last: {last.get('date','?')} → {last.get('result','?')}")

        output[pid] = {
            "name":    p["nama"],
            "flag":    p["flag"],
            "slug":    p["slug"],
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
