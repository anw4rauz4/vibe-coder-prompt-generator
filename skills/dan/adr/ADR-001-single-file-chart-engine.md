# ADR-001: Mesin chart sebagai satu file zero-dependency (`svg_charts.py`)

Status: superseded oleh ADR-004 (file dipecah menjadi paket `svg_charts/`; alasan &
prinsip zero-dependency tetap berlaku)
Tanggal: 2026-09-16 · Pengambil keputusan: DAN (arsitek paket)

## Konteks
Infografik & dashboard harus bisa dirender di viewer offline (tanpa CDN) dan tetap
berfungsi di lingkungan tanpa paket pihak ketiga. Review statis menandai file ini
"god module" (>600 baris) — perlu keputusan eksplisit, bukan pembiaran.

## Pilihan yang dipertimbangkan
1. **Satu file `svg_charts.py`** — kelebihan: tanpa dependensi, mudah disalin ke repo
   lain, satu import; kekurangan: file panjang, navigasi butuh module-map.
2. **Paket multi-modul (`svg_charts/` per chart)** — kelebihan: file kecil;
   kekurangan: menambah kompleksitas import & packaging untuk nilai yang minim.
3. **Library eksternal (matplotlib/plotly)** — kelebihan: fitur kaya; kekurangan:
   dependensi berat, output tidak SVG-inline-friendly, gagal di lingkungan minim.

## Keputusan
Kami memilih **opsi 1**, dengan mitigasi: module-map (daftar isi section) di kepala file,
prefix `_` untuk helper internal, dan QA otomatis (`_validate_svg.py`, `_check_layout.py`)
yang menangkap regressi tata letak tanpa perlu membaca kode sumber.

## Konsekuensi
- Positif: seluruh infografik DAN bekerja di Python standar; portabel.
- Negatif/utang: file panjang; penambahan chart harus menjaga konsistensi parameter
  (`title, subtitle, width, height, th, loc, transparent`).
- Dipantau: jumlah tipe chart & hasil `_test_all.py`; bila >25 tipe atau QA mulai
  sering gagal, pecah menjadi paket (opsi 2).
