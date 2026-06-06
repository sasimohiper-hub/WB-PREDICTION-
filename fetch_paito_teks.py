"""
fetch_paito_teks.py — Scrape paito teks dari rumusangkanet.com
Simpan ke paito-data.json sebagai database permanen.

Format paito-data.json:
{
  "slug": {
    "name": "Hongkong Pools",
    "start_date": "2025-01-01",   ← tanggal result[0] (paling lama)
    "results": ["1234", "5678"],  ← urut lama→baru
    "updated": "2026-06-06 10:00 WIB"
  }
}

Logic:
- Baca paito-data.json lama (jika ada)
- Scrape halaman → dapat list result terbaru (urut lama→baru)
- Merge: result baru di-append ke akhir, tanpa duplikat
- start_date TIDAK pernah berubah (anchor tanggal awal)
- Simpan kembali
"""

import json
import re
import time
import os
import asyncio
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)

BASE_URL = "https://rumusangkanet.com"
OUTPUT_FILE = "paito-data.json"

# Semua slug dari wongbagus-pasaran.html
ALL_SLUGS = [
    ("hongkong-pools",     "Hongkong Pools"),
    ("hklotto",            "Hongkong Lotto"),
    ("singapore",          "Singapore"),
    ("sydney-pools",       "Sydney Pools"),
    ("sdlotto",            "Sydney Lotto"),
    ("magnum-cambodia",    "Kamboja"),
    ("bullseye",           "Bullseye NZ"),
    ("chinapools",         "China Pools"),
    ("japan",              "Japan"),
    ("taiwan",             "Taiwan"),
    ("pcso",               "PCSO"),
    ("toto-macau-1",       "Toto Macau 13"),
    ("toto-macau-2",       "Toto Macau 16"),
    ("toto-macau-3",       "Toto Macau 19"),
    ("toto-macau-4",       "Toto Macau 22"),
    ("toto-macau-5",       "Toto Macau 00"),
    ("toto-macau-6",       "Toto Macau 23"),
    ("morocco-quatro-03-00-wib", "Morocco 03:00"),
    ("morocco-quatro-18-00-wib", "Morocco 18:00"),
    ("morocco-quatro-21-00-wib", "Morocco 21:00"),
    ("morocco-quatro-23-59-wib", "Morocco 23:59"),
    ("germany-plus5",      "Germany Plus5"),
    ("oregon-04-00-wib",   "Oregon 04:00"),
    ("oregon-07-00-wib",   "Oregon 07:00"),
    ("oregon-10-00-wib",   "Oregon 10:00"),
    ("oregon-13-00-wib",   "Oregon 13:00"),
    ("north-carolina-day",     "NC Day"),
    ("north-carolina-evening", "NC Evening"),
    ("georgia-midday",     "Georgia Midday"),
    ("georgia-evening",    "Georgia Evening"),
    ("georgia-night",      "Georgia Night"),
    ("texas-day",          "Texas Day"),
    ("texas-morning",      "Texas Morning"),
    ("texas-evening",      "Texas Evening"),
    ("texas-night",        "Texas Night"),
    ("new-york-midday",    "New York Midday"),
    ("new-york-evening",   "New York Evening"),
    ("new-jersey-midday",  "NJ Midday"),
    ("new-jersey-evening", "NJ Evening"),
    ("florida-midday",     "Florida Midday"),
    ("florida-evening",    "Florida Evening"),
    ("illinois-midday",    "Illinois Midday"),
    ("illinois-evening",   "Illinois Evening"),
    ("indiana-midday",     "Indiana Midday"),
    ("indiana-evening",    "Indiana Evening"),
    ("kentucky-midday",    "Kentucky Midday"),
    ("kentucky-evening",   "Kentucky Evening"),
    ("maryland-midday",    "Maryland Midday"),
    ("maryland-evening",   "Maryland Evening"),
    ("michigan-midday",    "Michigan Midday"),
    ("michigan-evening",   "Michigan Evening"),
    ("missouri-midday",    "Missouri Midday"),
    ("missouri-evening",   "Missouri Evening"),
    ("washington-dc-midday",  "WDC Midday"),
    ("washington-dc-evening", "WDC Evening"),
    ("connecticut-day",    "Connecticut Day"),
    ("connecticut-night",  "Connecticut Night"),
    ("virginia-day",       "Virginia Day"),
    ("virginia-night",     "Virginia Night"),
    ("tennesse-midday",    "Tennessee Midday"),
    ("tennesse-evening",   "Tennessee Evening"),
    ("tennesse-morning",   "Tennessee Morning"),
    ("california",         "California"),
    ("wisconsin-evening",  "Wisconsin Evening"),
]

# Pasaran mingguan — tidak tiap hari ada result
PASARAN_MINGGUAN = {
    "hongkong-pools", "hklotto", "singapore", "bullseye", "pcso"
}

# Hari LIBUR per pasaran (0=Sen,1=Sel,2=Rab,3=Kam,4=Jum,5=Sab,6=Min Python weekday)
# Disimpan ke paito-data.json → dipakai HTML untuk hitung tanggal tiap result
# Hari LIBUR per pasaran (Python weekday: 0=Sen,1=Sel,2=Rab,3=Kam,4=Jum,5=Sab,6=Min)
# Diverifikasi dari data paito harian aktual
SKIP_WEEKDAYS = {
    "singapore":      [1, 4],  # VERIFIED: Libur Selasa & Jumat (5x seminggu)
    "hongkong-pools": [0],     # Estimasi: Libur Senin
    "hklotto":        [0],     # Estimasi: Libur Senin
    "bullseye":       [0,1,2,3,4],  # Estimasi: hanya Sabtu & Minggu
    "pcso":           [0,3],   # Estimasi: Libur Senin & Kamis
}


def parse_html_paito(html):
    """
    Parse HTML → list result urut LAMA→BARU.
    Baca: kiri→kanan, atas→bawah (7 kolom per baris).
    result[-1] = terbaru.
    """
    soup = BeautifulSoup(html, 'html.parser')
    current_year = NOW.year

    FAKE_PAT = re.compile(r'^(1234|2345|3456|4567|5678|6789|7890|8901|9012|0123|(\d){3})$')

    def valid_angka(s):
        if not re.match(r'^\d{4}$', s):
            return False
        n = int(s)
        if (current_year - 1) <= n <= (current_year + 1):
            return False
        if FAKE_PAT.match(s):
            return False
        return True

    # Cari blok dengan paling banyak angka 4 digit
    best_block = None
    best_score = 0
    for tag in soup.find_all(['pre', 'div', 'p', 'section', 'article', 'main']):
        raw = tag.get_text(separator=' ', strip=True)
        tokens = raw.split()
        digits = [t for t in tokens if re.match(r'^\d{4}$', t) and valid_angka(t)]
        if len(digits) > best_score and len(digits) >= 10:
            best_score = len(digits)
            best_block = raw

    if not best_block:
        best_block = soup.get_text(separator=' ', strip=True)

    # Parse baris → kiri→kanan, atas→bawah
    lines_raw = best_block.replace('\r', '\n').split('\n')
    all_lines = []
    for line in lines_raw:
        row = [t for t in line.split() if re.match(r'^\d{4}$', t) and valid_angka(t)]
        if row:
            all_lines.append(row)

    if len(all_lines) <= 1:
        all_tokens = [t for t in best_block.split() if re.match(r'^\d{4}$', t) and valid_angka(t)]
        all_lines = [all_tokens[i:i+7] for i in range(0, len(all_tokens), 7)]

    if not all_lines:
        return None

    results = []
    seen = set()
    for row in all_lines:
        for angka in row:
            if angka not in seen:
                seen.add(angka)
                results.append(angka)

    return results if len(results) >= 5 else None


async def scrape_with_playwright(slug, browser):
    """
    Intercept network request dari halaman paito-teks.
    Data angka di-load via API/AJAX terpisah — tangkap response-nya.
    """
    url = f"{BASE_URL}/paito-teks-{slug}/"
    page = None
    try:
        page = await browser.new_page()

        # Simpan semua response yang mengandung angka paito
        api_data = []

        async def handle_response(response):
            try:
                rurl = response.url
                # Filter: cari response yang kemungkinan berisi data paito
                # Biasanya JSON atau text/plain dari endpoint API
                ctype = response.headers.get('content-type', '')
                if any(x in rurl for x in ['paito', 'data', 'result', 'teks', 'angka']):
                    body = await response.body()
                    text = body.decode('utf-8', errors='ignore')
                    # Cek apakah ada banyak angka 4 digit
                    found = re.findall(r'\b\d{4}\b', text)
                    if len(found) >= 10:
                        api_data.append({
                            'url': rurl,
                            'text': text,
                            'count': len(found),
                        })
                        print(f"\n  [API HIT] {rurl[:80]} → {len(found)} angka", flush=True)
                elif 'json' in ctype or 'text/plain' in ctype:
                    body = await response.body()
                    text = body.decode('utf-8', errors='ignore')
                    found = re.findall(r'\b\d{4}\b', text)
                    if len(found) >= 10:
                        api_data.append({
                            'url': rurl,
                            'text': text,
                            'count': len(found),
                        })
                        print(f"\n  [JSON HIT] {rurl[:80]} → {len(found)} angka", flush=True)
            except Exception:
                pass

        page.on('response', handle_response)

        await page.goto(url, wait_until='domcontentloaded', timeout=45000)
        # Tunggu API calls selesai
        await page.wait_for_timeout(8000)

        # Kalau dapat dari API → parse teks API, bukan HTML
        if api_data:
            # Pakai yang paling banyak angkanya
            best = max(api_data, key=lambda x: x['count'])
            print(f"  [API] Pakai: {best['url'][:60]} ({best['count']} angka)")
            return best['text']  # return teks API langsung

        # Fallback: coba ambil HTML biasa
        html = await page.content()

        # DEBUG
        import os as _os
        if _os.environ.get('DEBUG_HTML') or '--test' in __import__('sys').argv:
            # Log semua URL yang diakses halaman
            print(f"\n  [DEBUG] HTML: {len(html)} chars | API hits: {len(api_data)}")
            print(f"  [DEBUG] Body: {page and (await page.evaluate("document.body.innerText.slice(0,200)"))!r}")

        return html if len(html) > 1000 else None

    except Exception as e:
        print(f" [pw_err: {e}]", end='')
        return None
    finally:
        if page:
            await page.close()


async def scrape_all_async(slugs):
    """
    Jalankan semua scrape secara async dengan 1 browser instance.
    Return: dict {slug: html_or_None}
    """
    results_html = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        # Batasi concurrency: 3 tab sekaligus agar tidak overload
        semaphore = asyncio.Semaphore(3)

        async def fetch_one(slug):
            async with semaphore:
                print(f"  [{slug[:20]:20s}] Fetching...", end=' ', flush=True)
                html = await scrape_with_playwright(slug, browser)
                if html and len(html) > 500:
                    results = parse_html_paito(html)
                    if results:
                        print(f"OK {len(results)} result")
                        results_html[slug] = results
                    else:
                        print("PARSE FAIL")
                        results_html[slug] = None
                else:
                    print("NO HTML")
                    results_html[slug] = None
                await asyncio.sleep(0.5)  # gentle rate limit

        tasks = [fetch_one(slug) for slug, _ in slugs]
        await asyncio.gather(*tasks)
        await browser.close()

    return results_html


def load_existing():
    """Load paito-data.json yang ada."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def merge_results(old_results, new_results):
    """
    Merge dua list result.
    old_results : tersimpan, urut LAMA→BARU
    new_results : hasil scrape, urut LAMA→BARU
                  new_results[-1] = result paling baru

    Strategy:
    1. Cari overlap: tail old == tail new (keduanya diakhiri result yg sama)
       Ambil semua elemen new yang posisinya LEBIH BARU dari tail old.
    2. Kalau tidak ada overlap: new_results sudah punya semua data lama +
       mungkin ada yang lebih baru → cukup pakai new_results jika lebih panjang,
       atau append yang benar-benar baru ke old.
    """
    if not old_results:
        return new_results
    if not new_results:
        return old_results

    # Cari elemen terbaru dari old di dalam new
    # Cek N elemen terakhir old, cari posisinya di new
    check_tail = min(len(old_results), 30)
    old_tail = old_results[-check_tail:]  # N result terbaru yang tersimpan

    # Cari index di new dimana old_tail terakhir muncul
    # Cari dari belakang new (karena new urut lama→baru juga)
    match_pos = -1  # posisi di new[] dari result terbaru old
    for n in range(check_tail, 0, -1):
        # Coba match n elemen terakhir old dengan n elemen di new
        segment = old_results[-n:]
        # Cari segment ini di new
        seg_len = len(segment)
        for i in range(len(new_results) - seg_len, -1, -1):
            if new_results[i:i+seg_len] == segment:
                match_pos = i + seg_len  # posisi setelah match = mulai append
                break
        if match_pos >= 0:
            break

    if match_pos >= 0:
        # Ada overlap → append new_results[match_pos:] ke old
        appended = new_results[match_pos:]
        return old_results + appended
    else:
        # Tidak ada overlap:
        # Kalau new lebih panjang dari old → new punya lebih banyak data historis
        # Kalau sama panjang → mungkin ada 1-2 result baru di akhir new
        if len(new_results) >= len(old_results):
            # Pakai new sebagai base, tapi pertahankan data old yang mungkin lebih jadul
            # Cek apakah old[-1] ada di new → kalau tidak, append old[-N:] yang tidak ada
            old_set = set(old_results)
            new_set = set(new_results)
            # Result di new tapi tidak di old = benar-benar baru
            extra_new = [r for r in new_results if r not in old_set]
            if extra_new:
                return old_results + extra_new
            return old_results
        else:
            # old lebih panjang, new mungkin cuma update terbaru
            # Append result new yang belum ada di old
            old_set = set(old_results[-300:])
            truly_new = [r for r in new_results if r not in old_set]
            if truly_new:
                return old_results + truly_new
            return old_results


def calc_start_date(existing_entry, results_count):
    """
    Hitung start_date:
    - Kalau sudah ada di entry lama → pakai yang lama (JANGAN ubah!)
    - Kalau belum ada → hitung mundur dari hari ini
      Untuk pasaran harian: hari_ini - (count-1) hari
      Untuk pasaran mingguan: estimasi kasar ÷ 5 hari/minggu
    """
    if existing_entry and existing_entry.get('start_date'):
        return existing_entry['start_date']
    # Estimasi awal (akan semakin akurat setelah beberapa run)
    today = NOW.date()
    days_back = results_count - 1
    start = today - timedelta(days=days_back)
    return start.isoformat()


async def main_async(test_mode=False):
    SEP = '='*60
    print(f"\n{SEP}")
    print(f"fetch_paito_teks.py — {NOW.strftime('%A, %d %B %Y %H:%M WIB')}")
    print(f"Total slug: {len(ALL_SLUGS)}")
    print(f"{SEP}\n")

    db = load_existing()
    print(f"Data lama: {len([k for k in db if not k.startswith('_')])} pasaran\n")

    # ── Scrape semua via Playwright ──
    slugs_to_run = [ALL_SLUGS[2]] if test_mode else ALL_SLUGS  # test=sgp saja
    if test_mode:
        print("=== TEST MODE: hanya singapore ===\n")
    scraped = await scrape_all_async(slugs_to_run)

    ok_count   = 0
    fail_count = 0

    for slug, name in slugs_to_run:
        old_entry   = db.get(slug, {})
        old_results = old_entry.get('results', [])
        new_results = scraped.get(slug)

        if not new_results:
            fail_count += 1
            if old_entry:
                db[slug] = old_entry  # pertahankan data lama
            continue

        merged     = merge_results(old_results, new_results)
        start_date = calc_start_date(old_entry, len(merged))
        added      = len(merged) - len(old_results)

        db[slug] = {
            'name':          name,
            'start_date':    start_date,
            'skip_weekdays': SKIP_WEEKDAYS.get(slug, []),
            'results':       merged,
            'count':         len(merged),
            'updated':       NOW.strftime('%Y-%m-%d %H:%M WIB'),
        }
        ok_count += 1
        if added > 0:
            print(f"  [{slug[:20]:20s}] +{added} baru → {len(merged)} total")

    db['_meta'] = {
        'updated':     NOW.strftime('%Y-%m-%d %H:%M WIB'),
        'total_slugs': len(ALL_SLUGS),
        'ok':          ok_count,
        'fail':        fail_count,
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, separators=(',', ':'), ensure_ascii=False)

    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"\n{SEP}")
    print(f"paito-data.json tersimpan  ({size_kb:.1f} KB)")
    print(f"OK: {ok_count}  |  GAGAL: {fail_count}  |  Total: {len(ALL_SLUGS)}")
    print(f"{SEP}\n")


def main():
    import sys
    # Mode test: python fetch_paito_teks.py --test
    # Hanya scrape 1 slug (singapore) untuk verifikasi cepat
    test_mode = '--test' in sys.argv
    asyncio.run(main_async(test_mode=test_mode))

if __name__ == '__main__':
    main()
