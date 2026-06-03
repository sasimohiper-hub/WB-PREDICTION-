# ⭐ WongBagus Prediction ⭐

Platform prediksi & paito togel terlengkap — data update otomatis setiap jam dari angkanet.

## 📁 Struktur File

```
wongbagus/
├── index.html              ← Halaman utama (baca dari data/result.json)
├── fetch_all.py            ← Scraper data dari angkanet
├── data/
│   └── result.json         ← Data hasil, paito, rekap (auto-generate)
├── .github/
│   └── workflows/
│       └── update.yml      ← GitHub Actions (auto-update setiap jam)
└── README.md
```

---

## 🚀 Cara Setup di GitHub

### Langkah 1: Buat Repo Baru
1. Buka [github.com/new](https://github.com/new)
2. Nama repo: `wongbagus` (atau bebas)
3. Pilih **Public**
4. Jangan centang "Initialize with README"
5. Klik **Create repository**

### Langkah 2: Upload Semua File
Upload semua file ini ke repo:
- `index.html`
- `fetch_all.py`
- `data/result.json`
- `.github/workflows/update.yml`
- `README.md`

**Cara upload:**
- Klik **Add file → Upload files**
- Drag & drop semua file
- Klik **Commit changes**

> ⚠️ Untuk folder `.github/workflows/`, buat manual:
> Klik **Add file → Create new file** → ketik `.github/workflows/update.yml` → paste isi filenya

### Langkah 3: Aktifkan GitHub Pages
1. Buka **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / root (`/`)
4. Klik **Save**
5. Tunggu 1-2 menit → website live di `https://USERNAME.github.io/wongbagus/`

### Langkah 4: Aktifkan GitHub Actions
1. Buka tab **Actions**
2. Klik **"I understand my workflows, go ahead and enable them"**
3. Klik workflow **"WongBagus Auto Update"**
4. Klik **Run workflow** → **Run workflow** (untuk test pertama kali)

---

## ⚙️ Cara Kerja

```
GitHub Actions (tiap jam)
    ↓
fetch_all.py
    ↓ scrape
angkanet18.com/paito-harian/
    ↓ simpan
data/result.json
    ↓ commit & push
GitHub repo
    ↓ serve
index.html (GitHub Pages)
```

---

## 🔧 Kustomisasi

### Tambah/Hapus Pasaran
Edit `fetch_all.py` bagian `PASARAN_LIST`:
```python
PASARAN_LIST = [
    {"id": "sgp", "nama": "Singapore", "kode": "SGP", "negara": "🇸🇬"},
    # tambah di sini...
]
```

### Ganti Jadwal Update
Edit `.github/workflows/update.yml` bagian `cron`:
```yaml
# Setiap 30 menit:
- cron: '*/30 * * * *'

# Setiap 2 jam:
- cron: '0 */2 * * *'

# Setiap jam 12 & 18 WIB (= 05 & 11 UTC):
- cron: '0 5,11 * * *'
```

---

## ❓ Troubleshooting

| Masalah | Solusi |
|---|---|
| Data kosong | Jalankan workflow manual di tab Actions |
| GitHub Actions gagal | Cek log di tab Actions → klik workflow yang gagal |
| Halaman tidak update | Tunggu 5 menit atau hard refresh (Ctrl+Shift+R) |
| result.json tidak ada | Upload ulang file `data/result.json` |

---

## 📞 Kontak
WongBagus Prediction — Data update otomatis tiap jam 🕐
