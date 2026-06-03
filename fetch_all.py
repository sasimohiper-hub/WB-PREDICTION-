#!/usr/bin/env python3
"""
WongBagus Prediction - Auto Fetcher
Ambil data hasil, paito, rekap dari angkanet18.com
Simpan ke data/result.json
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime, date, timedelta
import time

# ── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL = "https://angkanet18.com"
PAITO_HARIAN_URL = f"{BASE_URL}/paito-harian"
OUTPUT_FILE = "data/result.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
    "Referer": BASE_URL,
}

# Semua pasaran yang didukung
PASARAN_LIST = [
    {"id": "ncd",  "nama": "North Carolina Day",     "kode": "NCD",  "negara": "🇺🇸"},
    {"id": "ncn",  "nama": "North Carolina Night",   "kode": "NCN",  "negara": "🇺🇸"},
    {"id": "sgp",  "nama": "Singapore",               "kode": "SGP",  "negara": "🇸🇬"},
    {"id": "hkg",  "nama": "Hongkong Pools",          "kode": "HKG",  "negara": "🇭🇰"},
    {"id": "syd",  "nama": "Sydneypools",             "kode": "SYD",  "negara": "🇦🇺"},
    {"id": "jpn",  "nama": "Japan",                   "kode": "JPN",  "negara": "🇯🇵"},
    {"id": "twn",  "nama": "Taiwan",                  "kode": "TWN",  "negara": "🇹🇼"},
    {"id": "chn",  "nama": "Chinapools",              "kode": "CHN",  "negara": "🇨🇳"},
    {"id": "cmb2", "nama": "Magnum Cambodia",         "kode": "CMB2", "negara": "🇰🇭"},
    {"id": "be",   "nama": "Bullseye",                "kode": "BE",   "negara": "🇳🇿"},
    {"id": "sp",   "nama": "Sao Paulo",               "kode": "SP",   "negara": "🇧🇷"},
    {"id": "wim",  "nama": "Wisconsin Midday",        "kode": "WIM",  "negara": "🇺🇸"},
    {"id": "macau","nama": "Macau",                   "kode": "MAC",  "negara": "🇲🇴"},
    {"id": "bkk",  "nama": "Bangkok",                 "kode": "BKK",  "negara": "🇹🇭"},
    {"id": "kl",   "nama": "Kuala Lumpur",            "kode": "KL",   "negara": "🇲🇾"},
]

# Jadwal buka tiap pasaran (WIB)
DRAW_SCHEDULE = {
    "ncd":  "13:30", "ncn":  "23:00", "sgp":  "17:45",
    "hkg":  "23:00", "syd":  "13:55", "jpn":  "13:00",
    "twn":  "21:00", "chn":  "21:30", "cmb2": "18:30",
    "be":   "16:00", "sp":   "03:00", "wim":  "13:30",
    "macau":"21:05", "bkk":  "21:00", "kl":   "19:00",
}

MIN_VALID_DATE = date(2020, 1, 1)
MAX_FUTURE_DAYS = 2

# ── HELPERS ─────────────────────────────────────────────────────────────────
session = requests.Session()
session.headers.update(HEADERS)

def is_plausible_date(d: date) -> bool:
    today = date.today()
    return MIN_VALID_DATE <= d <= today + timedelta(days=MAX_FUTURE_DAYS)

def parse_date_safe(s: str):
    """Coba berbagai format tanggal, return date atau None."""
    s = s.strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            d = datetime.strptime(s, fmt).date()
            if is_plausible_date(d):
                return d
        except ValueError:
            pass
    return None

def fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(retries):
        try:
            r = session.get(url, timeout=20)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            print(f"  [retry {attempt+1}] {url}: {e}")
            time.sleep(3 * (attempt + 1))
    return None

# ── FUNGSI SCRAPE ────────────────────────────────────────────────────────────
def scrape_paito_harian() -> dict:
    """
    Ambil data multi-kolom dari halaman paito-harian.
    Return dict: { pasaran_id: [ {tanggal, result}, ... ] }
    """
    print(f"[paito-harian] Fetching {PAITO_HARIAN_URL} ...")
    soup = fetch(PAITO_HARIAN_URL)
    if not soup:
        print("[paito-harian] GAGAL fetch")
        return {}

    data = {}
    # Cari semua tabel/section per pasaran
    tables = soup.find_all("table")
    print(f"[paito-harian] Ditemukan {len(tables)} tabel")

    for table in tables:
        # Identifikasi pasaran dari heading terdekat
        heading = None
        parent = table.find_parent()
        while parent and not heading:
            h = parent.find(["h1","h2","h3","h4","h5"])
            if h:
                heading = h.get_text(strip=True)
            parent = parent.find_parent()

        # Cari juga dari data-attribute
        pasaran_id = table.get("data-pasaran") or table.get("id") or ""
        if not pasaran_id and heading:
            # Cocokkan dengan nama pasaran
            for p in PASARAN_LIST:
                if p["kode"].lower() in (heading or "").lower() or \
                   p["id"] in (heading or "").lower():
                    pasaran_id = p["id"]
                    break

        rows = []
        for tr in table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
            if len(cols) < 2:
                continue
            # Cari kolom tanggal dan result
            tgl = None
            result = None
            for col in cols:
                if re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', col):
                    d = parse_date_safe(col)
                    if d:
                        tgl = str(d)
                elif re.match(r'^\d{4}$', col):
                    result = col

            if tgl and result:
                rows.append({"tanggal": tgl, "result": result})

        if pasaran_id and rows:
            if pasaran_id not in data:
                data[pasaran_id] = []
            data[pasaran_id].extend(rows)

    return data


def scrape_single_pasaran(pasaran_id: str) -> list:
    """
    Fallback: ambil data dari halaman individu tiap pasaran.
    Return list of {tanggal, result}
    """
    url = f"{BASE_URL}/paito-warna-{pasaran_id}/"
    print(f"  [{pasaran_id}] Fetching {url}")
    soup = fetch(url)
    if not soup:
        return []

    rows = []
    # Cari tabel hasil
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
            tgl = None
            result = None
            for col in cols:
                if not tgl and re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', col):
                    d = parse_date_safe(col)
                    if d:
                        tgl = str(d)
                if not result and re.match(r'^\d{4}$', col):
                    result = col
            if tgl and result:
                rows.append({"tanggal": tgl, "result": result})

    # Deduplicate
    seen = set()
    clean = []
    for r in rows:
        key = (r["tanggal"], r["result"])
        if key not in seen:
            seen.add(key)
            clean.append(r)

    return sorted(clean, key=lambda x: x["tanggal"], reverse=True)[:90]


def scrape_rekap(pasaran_id: str) -> dict:
    """
    Ambil data rekap 2D, 3D, 4D untuk satu pasaran.
    """
    rekap = {"2d": {}, "3d": {}, "4d": {}}
    url = f"{BASE_URL}/rekap-{pasaran_id}/"
    soup = fetch(url)
    if not soup:
        return rekap

    for tipe in ["2d", "3d", "4d"]:
        section = soup.find(id=f"rekap-{tipe}") or soup.find(attrs={"data-type": tipe})
        if not section:
            continue
        for tr in section.find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all(["td","th"])]
            if len(cols) >= 2:
                angka = cols[0].zfill(len(tipe.replace("d",""))+1 if tipe != "4d" else 4)
                try:
                    count = int(re.sub(r'\D', '', cols[1]))
                    rekap[tipe][angka] = count
                except:
                    pass

    return rekap


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    os.makedirs("data", exist_ok=True)
    today_str = str(date.today())
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*50}")
    print(f" WongBagus Prediction - Fetch All")
    print(f" {now_str}")
    print(f"{'='*50}\n")

    # Load existing data
    existing = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                existing = json.load(f)
            print(f"[load] Loaded existing data: {len(existing.get('pasaran', {}))} pasaran\n")
        except:
            print("[load] File rusak, mulai fresh\n")

    result = {
        "meta": {
            "updated_at": now_str,
            "updated_date": today_str,
            "source": "angkanet18.com",
            "by": "WongBagus Prediction"
        },
        "pasaran": existing.get("pasaran", {}),
    }

    # Step 1: Ambil dari paito-harian (bulk, semua pasaran)
    paito_data = scrape_paito_harian()

    # Step 2: Merge/fallback per pasaran
    for p in PASARAN_LIST:
        pid = p["id"]
        print(f"\n[{pid}] Processing {p['nama']} ...")

        # Data dari paito-harian
        bulk_rows = paito_data.get(pid, [])

        # Fallback: ambil dari halaman individu jika bulk kosong
        if not bulk_rows:
            print(f"  [{pid}] Bulk kosong, fallback ke halaman individu...")
            bulk_rows = scrape_single_pasaran(pid)

        # Merge dengan data existing
        existing_rows = existing.get("pasaran", {}).get(pid, {}).get("hasil", [])
        existing_map = {r["tanggal"]: r["result"] for r in existing_rows}

        for row in bulk_rows:
            tgl = row.get("tanggal")
            res = row.get("result")
            if tgl and res and re.match(r'^\d{4}$', res):
                existing_map[tgl] = res

        # Sort desc, ambil 90 hari terakhir
        merged = sorted(
            [{"tanggal": k, "result": v} for k,v in existing_map.items()],
            key=lambda x: x["tanggal"],
            reverse=True
        )[:90]

        print(f"  [{pid}] {len(merged)} hasil tersimpan")

        # Rekap (ambil dari existing dulu, update periodik)
        rekap_existing = existing.get("pasaran", {}).get(pid, {}).get("rekap", {})
        # Update rekap hanya jika data baru atau belum ada
        rekap = rekap_existing if rekap_existing else scrape_rekap(pid)

        result["pasaran"][pid] = {
            "info": p,
            "jadwal": DRAW_SCHEDULE.get(pid, ""),
            "hasil": merged,
            "rekap": rekap,
            "last_result": merged[0] if merged else {},
        }

        time.sleep(0.5)  # jangan terlalu cepat

    # AUTO-CLEAN: hapus tanggal yang tidak masuk akal
    total_cleaned = 0
    for pid in result["pasaran"]:
        before = len(result["pasaran"][pid]["hasil"])
        result["pasaran"][pid]["hasil"] = [
            r for r in result["pasaran"][pid]["hasil"]
            if parse_date_safe(r.get("tanggal","")) is not None
        ]
        after = len(result["pasaran"][pid]["hasil"])
        if before != after:
            print(f"[clean] {pid}: hapus {before-after} tanggal tidak valid")
            total_cleaned += before - after

    if total_cleaned:
        print(f"\n[clean] Total dibersihkan: {total_cleaned} entri")

    # Simpan
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Selesai! Data disimpan ke {OUTPUT_FILE}")
    print(f"   Total pasaran: {len(result['pasaran'])}")
    total_hasil = sum(len(v['hasil']) for v in result['pasaran'].values())
    print(f"   Total hasil: {total_hasil}")

if __name__ == "__main__":
    main()
