---
name: dan-marketing-data-analyst
description: >-
  Menganalisa data marketing/iklan dari CSV atau XLSX (Meta Ads, Google Ads, TikTok Ads,
  Shopee/Tokopedia, GA4, CRM): menghitung KPI (CTR, CPC, CPM, CVR, CPA, ROAS, AOV, margin),
  agregasi per channel/kampanye/waktu, deteksi tren & regresi, forecasting, deteksi anomali
  (z-score), analisa funnel, Pareto, korelasi antar metrik, dan health score. Menghasilkan
  laporan Markdown, JSON siap-visualisasi, dan CSV ringkasan. Gunakan saat pengguna mengirim
  data kampanye/penjualan dan minta analisa, evaluasi performa, diagnosis penurunan,
  atau laporan KPI.
---

# 01 · Marketing Data Analyst

## Kapan dipakai
Pengguna mengirim file data (CSV/XLSX) atau tabel angka, dan menanyakan:
performa, efisiensi, penyebab naik/turun, perbandingan channel, proyeksi, atau laporan.

## Alur kerja

```
1. INSPEKSI   → baca header, jumlah baris, rentang tanggal, kolom yang kosong
2. NORMALISASI→ petakan nama kolom (ID/EN) & parse angka lintas format
3. HITUNG KPI → CTR, CPC, CPM, CVR, CPA, ROAS, AOV, profit, margin
4. PECAH      → per channel, per kampanye, per hari/jam/hari-dalam-pekan
5. DIAGNOSA   → tren (regresi), anomali (z-score), Pareto, korelasi, funnel
6. SIMPULKAN  → 3–7 insight, masing-masing 1 aksi terukur
7. SERAHKAN   → analysis.md + analysis.json + summary CSV
```

## Perintah

```bash
cd skills/dan/scripts

# analisa
python3 dan_analytics.py <file.csv|xlsx> \
  --currency Rp --forecast 7 \
  --out       ../../../deliverables/analysis.json \
  --report    ../../../deliverables/analysis.md \
  --summary-csv ../../../deliverables/summary_channel.csv

# self-test parser angka (jalankan bila format data tidak lazim)
python3 dan_analytics.py x --test

# bila angka memakai format EN (1,234.56) dan terbaca salah:
python3 dan_analytics.py <file.csv> --num-locale en

# business plan / laporan omset divisi (xlsx multi-sheet, ada target & tahun lalu)
python3 plan_analyst.py --file "<business plan>.xlsx" \
  --outdir ../../../deliverables/<klien> --nama "PT Contoh"
python3 make_infographic.py ../../../deliverables/<klien>/spec_infografik.json \
  --out ../../../deliverables/<klien>/infografik.html --paper a3
python3 project_monitor.py report ../../../deliverables/<klien>/projects.json \
  --out-dir ../../../deliverables/<klien>/pmo

# intip isi xlsx tanpa dependensi (sheet, dimensi, rentang, formula)
python3 xlsx_lite.py --file "<file>.xlsx" --list
python3 xlsx_lite.py --file "<file>.xlsx" --sheet "Omset All" --range A5:I20
```

**Kapan pakai `plan_analyst` (bukan `dan_analytics`):** workbook berisi omset per divisi
per bulan + target + tahun lalu + stok + pencapaian salesman. Keluarannya: pencapaian vs
target, YoY, gap per divisi, akar masalah (EA/CB/IPT), kanal & produk, stock cover days,
proyeksi 3 skenario, rekonsiliasi tim↔divisi, temuan kualitas data (DQ), rekomendasi
berprioritas dengan dampak Rp — plus `projects.json` siap dipantau mingguan.
**Kapan pakai `dan_analytics`:** data mentah baris-per-transaksi/kampanye (CSV/XLSX iklan).

## Rumus wajib (jangan salah)

| Metrik | Rumus | Sehat bila |
|---|---|---|
| CTR | klik ÷ impresi × 100% | ≥ 1% (paid social), ≥ 3% (search/brand) |
| CPC | spend ÷ klik | turun trennya |
| CPM | spend ÷ impresi × 1000 | stabil, naik = lelang makin ketat |
| CVR | konversi ÷ klik × 100% | ≥ 2% e-commerce, ≥ 10% lead form |
| CPA | spend ÷ konversi | < AOV ÷ 3 |
| ROAS | revenue ÷ spend | ≥ 3x (umum), ≥ 4x untuk scale |
| AOV | revenue ÷ konversi | naik = upsell/bundling berhasil |
| Margin | (revenue − spend) ÷ revenue | ≥ 30% setelah HPP lebih baik |
| Impresi→Konversi | konversi ÷ impresi | bandingkan antar channel sejenis |

Detail + 30 metrik lain: `references/metric-library.md`.

## Diagnosis cepat (decision tree)

| Gejala | Kemungkinan penyebab | Cek pertama |
|---|---|---|
| CTR turun, CPC naik | creative fatigue / frekuensi tinggi | frekuensi & umur creative |
| CTR bagus, CVR jelek | mismatch janji iklan vs landing page | kecepatan LP, kesesuaian offer |
| CVR bagus, ROAS jelek | AOV terlalu kecil / CPA mahal | bundling, bid strategy, audiens |
| ROAS turun padahal spend naik | skala melewati audiens optimal | naikkan budget bertahap ≤20%/3 hari |
| Revenue naik, profit turun | diskon/ongkos memakan margin | margin per unit, bukan omzet |
| Data bolong/spike | tracking error atau pixel ganda | validasi event & deduplikasi |

## Standar insight

Setiap insight **wajib** punya 4 bagian:

```
JUDUL      : metrik + angka + arah      → "ROAS TikTok 1,46x, terendah kedua"
BUKTI      : pembanding & periode       → "vs Marketplace 8,60x, 90 hari"
SEBAB      : hipotesis (tandai bila tebakan) → "asumsi: audiens broad, CVR 1,9%"
AKSI       : langkah + ukuran + tenggat → "persempit ke interest skincare, uji 14 hari, target ROAS ≥ 2x"
```

## Jebakan yang harus dihindari
1. **Rata-rata menipu** — selalu lihat median & sebaran; rata-rata CPA bisa ditutupi 1 kampanye ekstrem.
2. **Attribution ganda** — jumlah ROAS per channel ≠ ROAS total bila ada overlap jendela atribusi.
3. **Simpson's paradox** — agregat bisa berlawanan dengan per-segmen. Cek minimal 2 dimensi.
4. **Survivorship** — kampanye yang sudah dimatikan tidak ada di data; tanyakan pada pengguna.
5. **Periode pendek** — < 14 hari belum cukup menyimpulkan; sebutkan di keterbatasan.
6. **Korelasi ≠ kausalitas** — validasi dengan eksperimen/A-B test sebelum klaim sebab-akibat.

## Bila data tidak lengkap
Minta maksimal 3 hal ini (jangan lebih, agar tidak menghambat):
1. **Spend & revenue** per periode (untuk ROAS),
2. **Klik & konversi** (untuk CVR/CPA),
3. **Tujuan** kampanye (konversi / awareness / traffic).

Jika tidak tersedia, buat **skenario** dengan asumsi eksplisit:
`asumsi: CTR 1,5%, CVR 2,5%, AOV Rp180.000 → break-even ROAS = ...`

## Serah terima
Selalu sertakan di chat: **1) angka kunci, 2) 3 insight teratas, 3) 1 rekomendasi terbesar,
4) tawaran lanjut ke infografik (sub-skill 03) atau strategi (sub-skill 02).**
