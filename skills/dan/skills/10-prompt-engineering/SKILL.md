---
name: dan-prompt-engineering
description: >-
  Memperlakukan prompt sebagai artekal yang bisa di-QA: lint elemen prompt (peran,
  konteks, tugas, kendala, format keluaran, contoh, pembatas, kriteria sukses,
  larangan, bahasa), memberi skor 0-100 + grade, saran perbaikan berprioritas,
  kerangka ulang otomatis, dan varian pembingkaian (role-first, constraint-first,
  few-shot, chain-of-thought, audience-first, counterfactual). Gunakan saat pengguna
  meminta "perbaiki prompt saya", "kenapa jawaban AI tidak sesuai", "buatkan prompt
  untuk X", atau ingin prompt yang konsisten untuk tim/produksi.
---

# 10 · Prompt Engineering

## Prinsip
1. Prompt adalah **spesifikasi**, bukan permintaan lisan: tiap elemen yang hilang
   adalah kebebasan yang Anda berikan ke model untuk menebak.
2. Ukur dulu, baru perbaiki: skor & elemen hilang memberi bahasa bersama untuk tim.
3. Simpan prompt produksi ber-versi (git/ADR) beserta eval-nya (lihat sub-skill 15/20).

## Perintah
```bash
cd skills/dan/scripts
python3 prompt_lab.py lint     --text "..."        # skor + elemen hilang + saran
python3 prompt_lab.py improve  --file p.txt --out p_baru.md
python3 prompt_lab.py variants --text "..." --n 4  # varian pembingkaian
```

## Checklist 12 elemen (bobot)
tugas 12 · format 12 · konteks 10 · kendala 10 · peran 10 · audiens 8 · contoh 8 ·
kriteria sukses 8 · panjang 6 · pembatas 6 · larangan 5 · bahasa 5.
Penalti: kata ambigu (dsb, etc, sekitar, kira-kira) −5 each; prompt <40 karakter −10.

## Pola yang terbukti (untuk tugas marketing/DAN)
- **Analisa data**: sebut file + periode + metrik + format tabel + "tandai `asumsi:`".
- **Infografik**: sebut pesan utama dulu, lalu daftar chart + span + tema.
- **Kreatif**: beri persona + audiens + 1 pesan + larangan (jangan klaim tanpa bukti).
- **Coaching**: beri data faktual + minta nada + langkah 15 menit.

## Varian & A/B
Jalankan 2 varian pada tugas sama, nilai dengan eval_set (sub-skill 15) atau
pass/fail manual; catat hasilnya ke `llm_obs.py` agar pilihan berbasis data.

## Integrasi
- Prompt untuk engine DAN: lihat contoh di tiap SKILL.md sub-skill.
- Prompt gambar/video: `references/prompt-library-image-video.md` (sub-skill 04).
- QA berkelanjutan: sub-skill 20 (observability) + 15 (eval set).

## Batas
Lint bersifat heuristik lexical; prompt kreatif sengaja melanggar beberapa elemen
(mis. tanpa format) bisa tetap baik — gunakan skor sebagai pemicu diskusi, bukan veto.
