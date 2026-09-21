# ADR-002: Stdlib-first — dependensi wajib nol, dependensi kaya bersifat opsional

Status: accepted
Tanggal: 2026-09-16 · Pengambil keputusan: DAN (arsitek paket)

## Konteks
Paket harus bisa dijalankan oleh pengguna di lingkungan apa pun (termasuk sandbox tanpa
pip). Beberapa kemampuan memang lebih baik dengan pustaka (XLSX, networkx, Pillow),
tapi menjadikannya wajib akan membuat paket tidak jalan di lingkungan minim.

## Pilihan yang dipertimbangkan
1. **Stdlib-only wajib + opsional ber-fallback** — kelebihan: selalu jalan; kekurangan:
   perlu menulis fallback & menguji dua jalur.
2. **Wajibkan requirements.txt penuh** — kelebihan: kode lebih singkat; kekurangan:
   gagal instal = paket mati; berat untuk pengguna kasual.

## Keputusan
Kami memilih **opsi 1**. Aturan implementasi:
- Engine inti hanya `import` stdlib.
- Pustaka kaya diimpor dalam `try/except ImportError` dengan fallback pure-python
  (contoh: `graph_analyst.py` punya implementasi Brandes/power-iteration sendiri).
- Fallback **diverifikasi terhadap pustaka referensi** bila tersedia
  (`_test_graph.py`: deviasi 0,0000 vs networkx).
- Daftar dependensi opsional + cara instal ada di `scripts/requirements.txt`.

## Konsekuensi
- Positif: paket jalan di Python standar; verifikasi silang menjaga kebenaran fallback.
- Negatif/utang: dua jalur kode untuk beberapa fitur → beban uji ganda.
- Dipantau: `_test_all.py` harus lulus baik dengan maupun tanpa dependensi opsional.
