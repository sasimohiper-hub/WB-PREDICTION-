#!/usr/bin/env python3
"""
WongBagus Prediction - Auto Fetcher v7
Source  : angkanet (paito-harian-{slug})
Output  : data/result.json
Pasaran : 65 market lengkap
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

# ── 65 PASARAN ────────────────────────────────────────────────────────────────
PASARAN_LIST = [
    # ASIA UTAMA
    {"id":"hk",    "nama":"Hongkong",          "flag":"🇭🇰", "short":"HK",    "slug":"hongkong-pools"},
    {"id":"hkl",   "nama":"HK Lotto",          "flag":"🇭🇰", "short":"HKL",   "slug":"hklotto"},
    {"id":"sgp",   "nama":"Singapore",         "flag":"🇸🇬", "short":"SGP",   "slug":"singapore"},
    {"id":"sdy",   "nama":"Sydney Pools",      "flag":"🇦🇺", "short":"SDY",   "slug":"sydney-pools"},
    {"id":"sdl",   "nama":"Sydney Lotto",      "flag":"🇦🇺", "short":"SDL",   "slug":"sdlotto"},
    {"id":"kam",   "nama":"Kamboja",           "flag":"🇰🇭", "short":"KAM",   "slug":"magnum-cambodia"},
    {"id":"bull",  "nama":"Bullseye NZ",       "flag":"🇳🇿", "short":"BULL",  "slug":"bullseye"},
    {"id":"chn",   "nama":"China Pools",       "flag":"🇨🇳", "short":"CHN",   "slug":"chinapools"},
    {"id":"jpn",   "nama":"Japan",             "flag":"🇯🇵", "short":"JPN",   "slug":"japan"},
    {"id":"twn",   "nama":"Taiwan",            "flag":"🇹🇼", "short":"TWN",   "slug":"taiwan"},
    {"id":"pcso",  "nama":"PCSO",              "flag":"🇵🇭", "short":"PCSO",  "slug":"pcso"},
    # TOTO MACAU
    {"id":"mac1",  "nama":"Toto Macau 13",     "flag":"🇲🇴", "short":"MAC13", "slug":"toto-macau-1"},
    {"id":"mac2",  "nama":"Toto Macau 16",     "flag":"🇲🇴", "short":"MAC16", "slug":"toto-macau-2"},
    {"id":"mac3",  "nama":"Toto Macau 19",     "flag":"🇲🇴", "short":"MAC19", "slug":"toto-macau-3"},
    {"id":"mac4",  "nama":"Toto Macau 22",     "flag":"🇲🇴", "short":"MAC22", "slug":"toto-macau-4"},
    {"id":"mac5",  "nama":"Toto Macau 00",     "flag":"🇲🇴", "short":"MAC00", "slug":"toto-macau-5"},
    {"id":"mac6",  "nama":"Toto Macau 23",     "flag":"🇲🇴", "short":"MAC23", "slug":"toto-macau-6"},
    # MOROCCO
    {"id":"mrq3",  "nama":"Morocco 03:00",     "flag":"🇲🇦", "short":"MRQ3",  "slug":"morocco-quatro-03-00-wib"},
    {"id":"mrq18", "nama":"Morocco 18:00",     "flag":"🇲🇦", "short":"MRQ18", "slug":"morocco-quatro-18-00-wib"},
    {"id":"mrq21", "nama":"Morocco 21:00",     "flag":"🇲🇦", "short":"MRQ21", "slug":"morocco-quatro-21-00-wib"},
    {"id":"mrq23", "nama":"Morocco 23:59",     "flag":"🇲🇦", "short":"MRQ23", "slug":"morocco-quatro-23-59-wib"},
    # GERMANY
    {"id":"ger",   "nama":"Germany Plus5",     "flag":"🇩🇪", "short":"GER",   "slug":"germany-plus5"},
    # OREGON
    {"id":"or4",   "nama":"Oregon 04:00",      "flag":"🇺🇸", "short":"OR4",   "slug":"oregon-04-00-wib"},
    {"id":"or7",   "nama":"Oregon 07:00",      "flag":"🇺🇸", "short":"OR7",   "slug":"oregon-07-00-wib"},
    {"id":"or10",  "nama":"Oregon 10:00",      "flag":"🇺🇸", "short":"OR10",  "slug":"oregon-10-00-wib"},
    {"id":"or13",  "nama":"Oregon 13:00",      "flag":"🇺🇸", "short":"OR13",  "slug":"oregon-13-00-wib"},
    # NORTH CAROLINA
    {"id":"ncd",   "nama":"NC Day",            "flag":"🇺🇸", "short":"NCD",   "slug":"north-carolina-day"},
    {"id":"nce",   "nama":"NC Evening",        "flag":"🇺🇸", "short":"NCE",   "slug":"north-carolina-evening"},
    # GEORGIA
    {"id":"geom",  "nama":"Georgia Midday",    "flag":"🇺🇸", "short":"GEOM",  "slug":"georgia-midday"},
    {"id":"geoe",  "nama":"Georgia Evening",   "flag":"🇺🇸", "short":"GEOE",  "slug":"georgia-evening"},
    {"id":"geon",  "nama":"Georgia Night",     "flag":"🇺🇸", "short":"GEON",  "slug":"georgia-night"},
    # TEXAS
    {"id":"txd",   "nama":"Texas Day",         "flag":"🇺🇸", "short":"TXD",   "slug":"texas-day"},
    {"id":"txmr",  "nama":"Texas Morning",     "flag":"🇺🇸", "short":"TXMR",  "slug":"texas-morning"},
    {"id":"txe",   "nama":"Texas Evening",     "flag":"🇺🇸", "short":"TXE",   "slug":"texas-evening"},
    {"id":"txn",   "nama":"Texas Night",       "flag":"🇺🇸", "short":"TXN",   "slug":"texas-night"},
    # NEW YORK
    {"id":"nyd",   "nama":"New York Midday",   "flag":"🇺🇸", "short":"NYD",   "slug":"new-york-midday"},
    {"id":"nye",   "nama":"New York Evening",  "flag":"🇺🇸", "short":"NYE",   "slug":"new-york-evening"},
    # NEW JERSEY
    {"id":"njm",   "nama":"NJ Midday",         "flag":"🇺🇸", "short":"NJM",   "slug":"new-jersey-midday"},
    {"id":"nje",   "nama":"NJ Evening",        "flag":"🇺🇸", "short":"NJE",   "slug":"new-jersey-evening"},
    # FLORIDA
    {"id":"flm",   "nama":"Florida Midday",    "flag":"🇺🇸", "short":"FLM",   "slug":"florida-midday"},
    {"id":"fle",   "nama":"Florida Evening",   "flag":"🇺🇸", "short":"FLE",   "slug":"florida-evening"},
    # ILLINOIS
    {"id":"ilm",   "nama":"Illinois Midday",   "flag":"🇺🇸", "short":"ILM",   "slug":"illinois-midday"},
    {"id":"ile",   "nama":"Illinois Evening",  "flag":"🇺🇸", "short":"ILE",   "slug":"illinois-evening"},
    # INDIANA
    {"id":"indm",  "nama":"Indiana Midday",    "flag":"🇺🇸", "short":"INDM",  "slug":"indiana-midday"},
    {"id":"inde",  "nama":"Indiana Evening",   "flag":"🇺🇸", "short":"INDE",  "slug":"indiana-evening"},
    # KENTUCKY
    {"id":"kym",   "nama":"Kentucky Midday",   "flag":"🇺🇸", "short":"KYM",   "slug":"kentucky-midday"},
    {"id":"kye",   "nama":"Kentucky Evening",  "flag":"🇺🇸", "short":"KYE",   "slug":"kentucky-evening"},
    # MARYLAND
    {"id":"mdm",   "nama":"Maryland Midday",   "flag":"🇺🇸", "short":"MDM",   "slug":"maryland-midday"},
    {"id":"mde",   "nama":"Maryland Evening",  "flag":"🇺🇸", "short":"MDE",   "slug":"maryland-evening"},
    # MICHIGAN
    {"id":"mim",   "nama":"Michigan Midday",   "flag":"🇺🇸", "short":"MIM",   "slug":"michigan-midday"},
    {"id":"mie",   "nama":"Michigan Evening",  "flag":"🇺🇸", "short":"MIE",   "slug":"michigan-evening"},
    # MISSOURI
    {"id":"mom",   "nama":"Missouri Midday",   "flag":"🇺🇸", "short":"MOM",   "slug":"missouri-midday"},
    {"id":"moe",   "nama":"Missouri Evening",  "flag":"🇺🇸", "short":"MOE",   "slug":"missouri-evening"},
    # WASHINGTON DC
    {"id":"wdm",   "nama":"WDC Midday",        "flag":"🇺🇸", "short":"WDM",   "slug":"washington-dc-midday"},
    {"id":"wde",   "nama":"WDC Evening",       "flag":"🇺🇸", "short":"WDE",   "slug":"washington-dc-evening"},
    # CONNECTICUT
    {"id":"ctd",   "nama":"Connecticut Day",   "flag":"🇺🇸", "short":"CTD",   "slug":"connecticut-day"},
    {"id":"ctn",   "nama":"Connecticut Night", "flag":"🇺🇸", "short":"CTN",   "slug":"connecticut-night"},
    # VIRGINIA
    {"id":"vad",   "nama":"Virginia Day",      "flag":"🇺🇸", "short":"VAD",   "slug":"virginia-day"},
    {"id":"van",   "nama":"Virginia Night",    "flag":"🇺🇸", "short":"VAN",   "slug":"virginia-night"},
    # TENNESSEE
    {"id":"tnm",   "nama":"Tennessee Midday",  "flag":"🇺🇸", "short":"TNM",   "slug":"tennesse-midday"},
    {"id":"tne",   "nama":"Tennessee Evening", "flag":"🇺🇸", "short":"TNE",   "slug":"tennesse-evening"},
    {"id":"tnmr",  "nama":"Tennessee Morning", "flag":"🇺🇸", "short":"TNMR",  "slug":"tennesse-morning"},
    # LAINNYA
    {"id":"cal",   "nama":"California",        "flag":"🇺🇸", "short":"CAL",   "slug":"california"},
    {"id":"wim",   "nama":"Wisconsin Midday",  "flag":"🇺🇸", "short":"WIM",  "slug":"wisconsin-midday"},
    {"id":"wie",   "nama":"Wisconsin Evening", "flag":"🇺🇸", "short":"WIE",   "slug":"wisconsin-evening"},
]

# ── DOMAINS (mirror angkanet, coba urut) ─────────────────────────────────────
DOMAINS = [
    "https://angkanet22.com",
    "https://angkanet18.com",
    "https://angkanet20.com",
    "https://rumusangkanet.com",
]

session = requests.Session()
session.headers.update(HEADERS)

# ── FETCH HTML ────────────────────────────────────────────────────────────────
def fetch_html(slug, retries=2):
    for domain in DOMAINS:
        url = f"{domain}/paito-harian-{slug}/"
        for attempt in range(retries):
            try:
                r = session.get(url, timeout=20)
                if r.status_code == 200:
                    print(f"    ✅ OK: {url}")
                    return r.text
                print(f"    [{attempt+1}] HTTP {r.status_code} — {domain}")
            except Exception as e:
                print(f"    [{attempt+1}] Error: {e}")
            time.sleep(2)
    return None

# ── PARSE TANGGAL ─────────────────────────────────────────────────────────────
def parse_tanggal(raw):
    # Format DD-MM-YYYY → YYYY-MM-DD
    m = re.match(r'(\d{2})-(\d{2})-(\d{4})', raw.strip())
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return ""

# ── SCRAPE PAITO HARIAN ───────────────────────────────────────────────────────
def scrape(p):
    pid  = p["id"]
    html = fetch_html(p["slug"])
    if not html:
        print(f"  [{pid}] ❌ Semua domain gagal")
        return []

    soup  = BeautifulSoup(html, "html.parser")
    hasil = []

    # Strategi 1: tabel dengan kolom tanggal + 4 digit
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
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

    # Strategi 2: fallback parse teks
    if not hasil:
        text = soup.get_text(separator="\n")
        for line in text.split("\n"):
            line = line.strip()
            date_m = re.search(r'(\d{2}-\d{2}-\d{4})', line)
            if not date_m:
                continue
            tgl = parse_tanggal(date_m.group(1))
            if not tgl:
                continue
            nums = re.findall(r'\b(\d{4})\b', line)
            nums = [n for n in nums if not (2015 <= int(n) <= 2035)]
            if nums:
                hasil.append({"date": tgl, "result": nums[0]})

    # Deduplikasi & sort ascending (lama→baru)
    seen    = set()
    deduped = []
    for item in hasil:
        if item["date"] and item["date"] not in seen:
            seen.add(item["date"])
            deduped.append(item)
    deduped.sort(key=lambda x: x["date"])

    print(f"  [{pid}] ✅ {len(deduped)} hasil")
    return deduped

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    os.makedirs("data", exist_ok=True)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*60}")
    print(f"  WongBagus Prediction — Fetch All v7")
    print(f"  {now_str}  |  {len(PASARAN_LIST)} pasaran")
    print(f"{'='*60}\n")

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
        pid = p["id"]
        print(f"\n▶ [{p['short']}] {p['nama']}")

        new_results = scrape(p)

        # Ambil existing (desc) → convert ke asc untuk merge
        old_desc = existing.get(pid, {}).get("results", [])
        old_asc  = list(reversed(old_desc))

        if not new_results:
            # Scrape gagal — pertahankan data existing
            merged_asc = old_asc
            print(f"  [{pid}] ⚠ Pakai data existing: {len(merged_asc)} entri")
        else:
            # Merge by date (new_results override existing untuk tanggal sama)
            date_map = {}
            for item in old_asc:
                if item.get("date"):
                    date_map[item["date"]] = item["result"]
            for item in new_results:
                if item.get("date"):
                    date_map[item["date"]] = item["result"]

            merged_asc = [
                {"date": d, "result": r}
                for d, r in sorted(date_map.items())
            ]
            merged_asc = merged_asc[-MAX_HASIL:]  # max 365 hari

        # Simpan desc (terbaru index 0) — kompatibel dengan WBData
        results_desc = list(reversed(merged_asc))
        last = results_desc[0] if results_desc else {}

        print(f"  [{pid}] Total: {len(results_desc)} | Last: {last.get('date','?')} → {last.get('result','?')}")

        output[pid] = {
            "name":    p["nama"],
            "flag":    p["flag"],
            "short":   p["short"],
            "slug":    p["slug"],
            "updated": now_str,
            "results": results_desc,
        }

        time.sleep(1)  # jeda antar request

    # Simpan
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["results"]) for v in output.values())
    ok    = sum(1 for v in output.values() if v["results"])
    print(f"\n✅ Done! → {OUTPUT_FILE}")
    print(f"   Pasaran: {len(output)} | Berhasil: {ok} | Total hasil: {total}\n")

if __name__ == "__main__":
    main()
