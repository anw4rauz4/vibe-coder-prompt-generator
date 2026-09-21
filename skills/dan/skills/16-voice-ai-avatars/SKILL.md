---
name: dan-voice-ai-avatars
description: >-
  Produksi suara & avatar: penyiapan naskah TTS (pacing, jeda, pelafalan angka),
  pemilihan suara konsisten lintas klip, brief avatar digital (penampilan, pakaian,
  latar, gesture, etika keterbukaan), serta checklist QC audio (loudness, kecepatan,
  artefak). Gunakan saat pengguna meminta voice-over, narasi video, podcast ringkas,
  avatar presenter, atau konten berbicara tanpa merekam manusia.
---

# 16 · Voice AI & Avatars

## Prinsip
1. **Konsistensi suara > variasi**: kunci atribut (gender, use_case, index) agar semua
   klip satu proyek terdengar satu orang.
2. Avatar sintetis yang menyerupai orang nyata wajib izin tertulis; avatar fiktif
   wajib ditandai sintetis pada publikasi.
3. Audio buruk membunuh kredibilitas lebih cepat daripada visual biasa.

## Alur kerja
```
naskah (storyboard.py / weekly summary)
  -> rapikan utk TTS (kalimat ≤18 kata, angka dilafalkan, jeda ditandai)
  -> generate_speech per blok (atribut suara identik)
  -> QC (loudness −16 LUFS mobile, kecepatan, artefak)
  -> gabung ke video (cut-list dari storyboard) + subtitle (.srt sudah tersedia)
```

## Penyiapan naskah TTS (aturan konkret)
- Pecah kalimat >18 kata; hindari tanda baca ganda.
- Angka & satuan: "Rp1,47 miliar" → "satu koma empat tujuh miliar rupiah".
- Istilah asing beri ejaan fonetik bila perlu: "ROAS" → "ar-oh-ah-es".
- Satu paragraf = satu napas ide; beri jeda 0,8 dtk antar paragraf.
- Hindari akronim internal tanpa penjelasan pertama kali.

## Brief avatar (isi sebelum generate)
```
Identitas   : fiktif / berbasis orang berizin (lampirkan izin)
Penampilan  : usia perkiraan, gaya rambut, pakaian (warna merek?), aksesori
Latar       : studio netral / kantor / green-screen utk compositing
Gesture     : tenang / ekspresif; kontak mata ke lensa
Batas       : tanpa klaim tanpa bukti; tanpa meniru tokoh publik; tandai sintetis
```

## Checklist QC audio
- [ ] loudness konsisten antar klip (±1 LUFS)
- [ ] kecepatan 0,95–1,1×; tidak terpotong di akhir kalimat
- [ ] tanpa artefak klik/pop; napas sintetis tidak berulang aneh
- [ ] pelafalan merek/istilah benar (cek daftar ejaan fonetik)
- [ ] subtitle sinkron ±0,2 dtk dengan audio

## Integrasi
- Naskah: sub-skill 04 (storyboard VO) & 07 (ringkasan mingguan untuk audio briefing).
- Video: sub-skill 18. Multimodal QC: sub-skill 14.
