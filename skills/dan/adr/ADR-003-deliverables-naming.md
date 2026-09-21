# ADR-003: Semua artefak di `deliverables/`; hindari nama folder yang diabaikan snapshot

Status: accepted
Tanggal: 2026-09-16 · Pengambil keputusan: DAN (arsitek paket)

## Konteks
Pada awal pengembangan, artefak ditulis ke folder `output/`. File di dalamnya **hilang**
antar sesi karena snapshot workspace mengabaikan direktori bernama `out`, `build`,
`dist`, `node_modules`, dll. (pencocokan ternyata menangkap `output/` juga).

## Pilihan yang dipertimbangkan
1. **`deliverables/`** — nama tidak bertabrakan dengan daftar abaian; makna jelas.
2. Tetap `output/` — risiko kehilangan pekerjaan berulang.
3. `artifacts/` — juga aman, tapi `deliverables` lebih eksplisit sebagai "hasil serahan".

## Keputusan
Kami memilih **`deliverables/`** dan menuliskannya sebagai aturan kerja di
`SKILL.md` (§2) serta `scripts/README.md`: semua engine menulis ke sana secara default,
dan nama `output/ build/ dist/ out/ target/` dilarang untuk artefak yang harus bertahan.

## Konsekuensi
- Positif: hasil kerja persisten & mudah ditemukan pengguna.
- Negatif: perlu disiplin; engine baru wajib memakai path default yang sama.
- Dipantau: `_check_refs.py` & `_test_all.py` (artefak contoh diregenerasi di CI).
