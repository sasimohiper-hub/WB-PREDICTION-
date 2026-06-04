#!/usr/bin/env python3
"""
WongBagus Prediction - Auto Fetcher v4
Source  : rumusangkanet.com/paito-harian-{slug}/
Format  : scrape tabel tanggal + 4 digit result
Output  : data/result.json
  { pid: { name, flag, slug, updated, results: [{date, result}] } }
  results[0] = TERBARU (desc)

Jalankan sekali sehari via GitHub Actions / cron.
"""

import requests
from bs4 import BeautifulSoup
import json, os, re
from datetime import datetime, date
import time

BASE_URL    = "https://rumusangkanet.com"
OUTPUT_FILE = "data/result.json"
MAX_HASIL   = 365   # simpan max 1 tahun per pasaran

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

# Hanya pasaran UTAMA (10 pasaran)
# Tambah/kurangi sesuai kebutuhan
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

session = requests.Session()
session.headers.update(HEADERS)

def fetch_html(url, retries=3):
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=25)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"    [retry {attempt+1}] {e}")
            time.sleep(5 * (attempt + 1))
    return None

def parse_tanggal(raw):
    """
    Konversi DD-MM-YYYY → YYYY-MM-DD
    """
    m = re.match(r'(\d{2})-(\d{2})-(\d{4})', raw.strip())
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return ""

def scrape_paito_harian(p):
    """
    Scrape dari /paito-harian-{slug}/
    Tabel format:
      tanggal | d1 | d2 | d3 | d4 | J | Ts1...
    Result 4D = d1 d2 d3 d4

    Return: list of {date:"YYYY-MM-DD", result:"XXXX"} urut LAMA→BARU
    """
    pid  = p["id"]
    url  = f"{BASE_URL}/paito-harian-{p['slug']}/"
    print(f"  [{pid}] GET {url}")

    html = fetch_html(url)
    if not html:
        print(f"  [{pid}] ❌ Gagal fetch")
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Cari tabel yang mengandung kolom tanggal
    hasil = []
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 5:
                continue

            # Kolom pertama = tanggal DD-MM-YYYY
            cell0 = cells[0].get_text(strip=True)
            if not re.match(r'\d{2}-\d{2}-\d{4}', cell0):
                continue

            tgl = parse_tanggal(cell0)
            if not tgl:
                continue

            # Kolom 1,2,3,4 = 4 digit result
            digits = []
            for i in range(1, 5):
                if i < len(cells):
                    d = cells[i].get_text(strip=True)
                    if re.match(r'^\d$', d):
                        digits.append(d)

            if len(digits) == 4:
                result = "".join(digits)
                hasil.append({"date": tgl, "result": result})

    # Kalau tidak ada tabel dengan format itu, coba parse dari teks
    if not hasil:
        print(f"  [{pid}] ⚠️  Tabel tidak ditemukan, coba parse teks")
        text = soup.get_text(separator="\n")
        for line in text.split("\n"):
            line = line.strip()
            # Cari pola: "04-05-2026 ... 4 digit berurutan"
            date_m = re.search(r'(\d{2}-\d{2}-\d{4})', line)
            if not date_m:
                continue
            tgl = parse_tanggal(date_m.group(1))
            nums = re.findall(r'\b\d{4}\b', line)
            # Filter tahun
            nums = [n for n in nums if not (2020 <= int(n) <= 2030)]
            if nums:
                hasil.append({"date": tgl, "result": nums[0]})

    # Deduplikasi berdasarkan tanggal (ambil yang pertama)
    seen_dates = set()
    deduped = []
    for item in hasil:
        if item["date"] not in seen_dates:
            seen_dates.add(item["date"])
            deduped.append(item)

    # Urutkan lama→baru
    deduped.sort(key=lambda x: x["date"])

    print(f"  [{pid}] ✅ {len(deduped)} hasil ditemukan")
    return deduped

def main():
    os.makedirs("data", exist_ok=True)
    now_str   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = str(date.today())

    print(f"\n{'='*55}")
    print(f"  WongBagus Prediction — Fetch All v4")
    print(f"  {now_str}  |  {len(PASARAN_LIST)} pasaran")
    print(f"{'='*55}\n")

    # Load existing data (untuk merge/fallback)
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

        new_results = scrape_paito_harian(p)   # lama→baru

        # Ambil existing results (urut terbaru di index 0 → balik dulu)
        old_results_desc = existing.get(pid, {}).get("results", [])
        old_results_asc  = list(reversed(old_results_desc))   # lama→baru

        if not new_results:
            print(f"  [{pid}] Fallback existing: {len(old_results_asc)} entri")
            merged_asc = old_results_asc
        else:
            # Merge: gabung old + new, deduplikasi by date, urut lama→baru
            date_map = {}
            for item in old_results_asc:
                if item["date"]:
                    date_map[item["date"]] = item["result"]
            for item in new_results:
                if item["date"]:
                    date_map[item["date"]] = item["result"]  # new override old

            # Tambah yg tidak punya tanggal dari old (pertahankan)
            no_date_old = [i for i in old_results_asc if not i["date"]]

            merged_asc = [{"date": d, "result": r} for d, r in sorted(date_map.items())]
            # Angka tanpa tanggal taruh di awal (paling lama)
            merged_asc = no_date_old + merged_asc
            merged_asc = merged_asc[-MAX_HASIL:]

        # Output: index 0 = TERBARU
        results_desc = list(reversed(merged_asc))

        last = results_desc[0] if results_desc else {}
        print(f"  [{pid}] Tersimpan: {len(results_desc)} | Last: {last.get('date','?')} → {last.get('result','?')}")

        output[pid] = {
            "name":    p["nama"],
            "flag":    p["flag"],
            "slug":    p["slug"],
            "updated": now_str,
            "results": results_desc,   # index 0 = TERBARU
        }

        time.sleep(2)   # jeda agar tidak kena rate limit

    # Simpan
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["results"]) for v in output.values())
    print(f"\n✅ Done! → {OUTPUT_FILE}")
    print(f"   Pasaran: {len(output)} | Total hasil: {total}\n")

if __name__ == "__main__":
    main()
