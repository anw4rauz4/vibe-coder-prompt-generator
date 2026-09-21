# ADR-004: Pecah `svg_charts.py` menjadi paket `svg_charts/`

Status: accepted · **supersedes sebagian ADR-001** (keputusan "satu file")
Tanggal: 2026-09-16 · Pengambil keputusan: DAN + pengguna

## Konteks
ADR-001 memilih satu file agar portabel, dengan trigger pemecahan: >25 tipe chart atau
QA mulai sering gagal. Pada 18 tipe chart trigger belum terpenuhi, namun pengguna
meminta pemecahan demi navigasi & kepemilikan kode yang lebih jelas saat paket tumbuh.

## Pilihan yang dipertimbangkan
1. **Paket dengan submodul per keluarga chart** — core/bars/lines/parts/stats/net/project.
2. Tetap satu file (status quo).
3. Satu file per chart (17 file) — terlalu granular, import berisik.

## Keputusan
Kami memilih **opsi 1**, dengan syarat kompatibilitas:
- `import svg_charts as sc` dan `sc.<chart>(...)` **tidak berubah** (`__init__.py`
  mengekspor ulang semua nama publik + `REGISTRY` + helper `_` yang dipakai modul lain).
- Helper bersama masuk `core.py`; tidak ada impor sirkular (semua modul → core).
- Galeri demo jadi `python3 -m svg_charts` (`__main__.py`).
- Pemecahan dikerjakan lewat splitter deterministik + verifikasi `_test_all.py`,
  bukan salin-tempel manual, untuk menghindari regressi halus.

## Konsekuensi
- Positif: file ≤ ~400 baris, kepemilikan per keluarga chart jelas, module-map tidak
  lagi dibutuhkan untuk navigasi.
- Negatif: satu tingkat indireksi tambahan; dokumentasi & CI diperbarui
  (`python3 -m svg_charts`, referensi paket).
- Dipantau: `_test_all.py` wajib tetap 0 gagal; bila submodul mulai saling bergantung
  (selain ke core), itu sinyal batas keluarga chart salah → refactor ulang.
