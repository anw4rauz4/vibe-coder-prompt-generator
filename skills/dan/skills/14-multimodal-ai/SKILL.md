---
name: dan-multimodal-ai
description: >-
  Bekerja dengan modalitas selain teks: gambar (audit aset, rasio, metadata, prompt
  reverse-engineering), audio/TTS (penyiapan naskah & pacing), video (cut-list dari
  storyboard), dan dokumen (ekstrak tabel ke data). Menyediakan checklist QC per
  modalitas dan template prompt multimodal. Gunakan saat pengguna mengirim gambar/
  audio/video/dokumen dan meminta analisa, konversi, QC, atau prompt untuk memprosesnya.
---

# 14 · Multimodal AI

## Prinsip
1. Setiap modalitas punya **QC tersendiri** sebelum dipakai di produksi.
2. Gambar/video AI wajib ditandai sebagai sintetis bila ditampilkan ke publik.
3. Ekstraksi (tabel dari PDF, teks dari audio) selalu diverifikasi sampel manual ≥10%.

## Kemampuan & alat di paket ini
| Modalitas | Alat | Kegunaan |
|---|---|---|
| Gambar | `fit_asset.py` | rasio platform, crop/pad tanpa merusak subjek |
| Gambar | PIL (opsional) | metadata: dimensi, mode warna, ukuran file |
| Gambar | `generate_image` (runtime) | render dari prompt sub-skill 04/09 |
| Audio | `generate_speech` (runtime) | TTS naskah; siapkan lewat pedoman pacing di bawah |
| Video | `storyboard.py` | shot list + SRT + prompt per shot |
| Dokumen | `dan_analytics.py` | CSV/XLSX → metrik; tabel diesktrak manual ke CSV dulu |

## Checklist QC gambar
- [ ] rasio sesuai platform (9:16/4:5/16:9) — cek via `fit_asset.py`
- [ ] tidak ada teks terbakar (watermark/typo) bila teks akan ditambahkan di editing
- [ ] wajah/tangan tidak cacat; logo & merek fiktif atau berizin
- [ ] konsistensi produk antar shot (warna, bentuk kemasan) — kunci satu kalimat deskripsi
- [ ] berat file wajar untuk channel (web <300 KB setelah kompresi)

## Pedoman naskah TTS (voice-over)
- Kalimat ≤18 kata; satu ide per kalimat.
- Tandai jeda: baris baru = jeda 0,4 dtk; paragraf = 0,8 dtk.
- Angka ditulis sesuai pelafalan ("dua koma lima persen", bukan "2.5%").
- Uji dengar pada kecepatan 1,0 dan 1,15 sebelum produksi.

## Template prompt multimodal
```
Gambar→teks : "Desklikasikan gambar ini untuk audit: subjek utama, teks terlihat,
               merek/logo, rasio, cacat visual. Format daftar."
Teks→gambar : lihat references/prompt-library-image-video.md
Video→teks  : "Buat cut-list: timecode, aksi, teks layar, transisi. Format tabel."
```

## Integrasi
- Prompt gambar/video: sub-skill 04 & 09.
- Aset untuk kampanye: sub-skill 04 (storyboard) → 14 (QC) → 03 (masuk infografik).
