---
name: dan-ai-video-content
description: >-
  Produksi konten video berbantuan AI ujung-ke-ujung: storyboard bertiming (shot,
  kamera, transisi, teks layar, VO, SFX), cut-list/edit list, subtitle .srt, prompt
  video-generation per shot, caption+hashtag, dan kalender pilar konten. Melengkapi
  sub-skill 04 dengan fokus pipeline produksi & QC pasca-generate. Gunakan saat
  pengguna meminta video TikTok/Reels/Shorts/YouTube, edit list, auto-caption, atau
  seri konten berulang.
---

# 18 · AI Video Content Generation

## Prinsip
1. **3 detik pertama = anggaran seluruh video**: hook diuji terpisah sebelum produksi.
2. Satu video = satu pesan = satu CTA; durasi mengikuti platform, bukan ego kreator.
3. Generatif untuk *draft & B-roll*; keputusan cerita tetap manusia (retensi & brand).

## Pipeline
```
brief (produk, audiens, goal, tone)
  -> storyboard.py  : shot list bertiming + VO + prompt image/video + SRT
  -> generate gambar first-frame per shot (konsistensi produk)
  -> generate video per shot 2-4 dtk (satu aksi per shot)
  -> edit: cut-list + subtitle .srt + musik
  -> QC (sub-skill 14) -> publish + UTM -> ukur (sub-skill 01)
```

## Perintah
```bash
cd skills/dan/scripts
python3 storyboard.py --brief ../templates/storyboard-brief.example.json
python3 storyboard.py --product "X" --audience "Y" --platform reels --duration 30 \
    --structure hook_story_offer --goal konversi
```

## Cut-list & edit (aturan praktis)
- Potong pada aksi, bukan pada detik genap; buang napas kosong >0,4 dtk.
- Teks layar muncul ≤0,5 dtk setelah hook visual; aman di safe-area platform.
- Subtitle wajib (80%+ menonton tanpa suara); gunakan .srt dari storyboard.
- Transisi maksimal 2 jenis per video; whip-pan hanya untuk pergantian poin.

## Seri konten berulang (template mingguan)
| Hari | Pilar | Format | Sumber bahan |
|---|---|---|---|
| Sen | edukasi | listicle 3 poin | insight analysis.json |
| Rab | bukti sosial | testimoni + angka | review/UGC |
| Jum | hard-sell ringan | offer + urgensi | campaign plan |
| Sab | hiburan/relatable | POV | kalender konten |

## Integrasi & QC
- Prompt video: `references/prompt-library-image-video.md`.
- QC aset: sub-skill 14; performa pasca-tayang: sub-skill 01; voice-over: sub-skill 16.
