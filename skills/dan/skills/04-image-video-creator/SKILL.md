---
name: dan-image-video-creator
description: >-
  Kreator konten image dan video: menyusun konsep kreatif, storyboard bertiming lengkap
  (tipe shot, gerakan kamera, transisi, teks layar, naskah voice-over, SFX, B-roll),
  prompt image-generation dan video-generation per shot, caption & hashtag, file subtitle
  .SRT, checklist produksi, serta kalender konten. Mendukung struktur naratif
  hook-story-offer, AIDA, PAS, before-after-bridge, listicle, testimonial, demo produk,
  dan platform TikTok, Reels, Shorts, YouTube ad, long-form, carousel. Gunakan saat
  pengguna meminta ide konten, script video, storyboard, prompt gambar/AI image,
  prompt AI video, caption, atau rencana produksi konten.
---

# 04 · Image & Video Creator

## Prinsip kreatif
1. **3 detik pertama menentukan segalanya.** Hook dulu, brand belakangan.
2. **Dibuat untuk ditonton tanpa suara**: teks layar + subtitle wajib.
3. **Satu video = satu pesan = satu CTA.**
4. **Spesifik mengalahkan indah**: prompt yang menyebut lensa, cahaya, aksi, dan mood
   menghasilkan gambar lebih konsisten daripada prompt panjang yang abstrak.
5. **Data mengarahkan kreatif**: bila ada hasil analisa (sub-skill 01), pakai angle yang
   terbukti, bukan yang paling disukai pembuatnya.

---

## A. Storyboard video (script otomatis)

```bash
cd skills/dan/scripts
python3 storyboard.py \
  --product   "Serum Vitamin C GlowLab" \
  --audience  "wanita 25-34, kulit kusam & bekas jerawat" \
  --platform  tiktok \
  --duration  30 \
  --structure hook_story_offer \
  --goal      konversi \
  --tone      friendly \
  --problem   "kulit kusam dan bekas jerawat susah hilang" \
  --result    "kulit cerah dalam 14 hari" \
  --usp       "Vitamin C 10% + Niacinamide, non-sticky" \
  --offer     "Diskon 40% + gratis ongkir sampai Minggu" \
  --cta       "Klik keranjang kuning sekarang" \
  --proof     "4,9★ dari 12.000 review"
```

Output: `deliverables/storyboard_<produk>.md` + `.json` + `.srt`

Isi paket: **5 varian hook · shot list bertiming · teks layar · naskah VO (kalimat utuh,
dihitung 145 kata/menit) · SFX/musik · B-roll · prompt image & video per shot · caption
2 versi · hashtag · checklist produksi · catatan sutradara.**

Untuk brief kompleks, pakai file JSON: `--brief storyboard-brief.json`
(contoh: `templates/storyboard-brief.example.json`).

### Platform preset
| Platform | Rasio | Durasi default | Catatan kunci |
|---|---|---|---|
| `tiktok` | 9:16 | 30s | hook ≤1,5 dtk, raw & cepat, sound trending |
| `reels` | 9:16 | 30s | estetik, transisi halus, hindari 20% bawah |
| `shorts` | 9:16 | 45s | padat, loop-friendly |
| `youtube_ad` | 16:9 | 30s | brand+CTA sebelum detik ke-5 (skip button) |
| `longform` | 16:9 | 240s | chapter tiap 60–90 dtk, B-roll kaya |
| `carousel` | 4:5 | — | slide 1 hook, slide terakhir CTA, 6–10 slide |

### Struktur naratif
`hook_story_offer` · `aida` · `pas` · `before_after_bridge` · `listicle` ·
`testimonial` · `demo_produk`

Pilih berdasarkan goal: konversi → `hook_story_offer`/`pas`; edukasi → `listicle`;
trust → `testimonial`; produk fisik → `demo_produk`/`before_after_bridge`.

---

## B. Prompt image (rumus 6 lapis)

```
[1 SUBJEK]      apa yang difoto, kondisi/aksi spesifik
[2 KOMPOSISI]   tipe shot + lensa + sudut  (Close-Up, 85mm, eye-level, rule of thirds)
[3 LINGKUNGAN]  latar, properti, waktu     (meja marmer, jendela timur, pagi)
[4 CAHAYA]      sumber, arah, kualitas     (softbox 45°, rim light hangat, soft shadow)
[5 WARNA/MOOD]  palet, tone, gaya          (palet hangat, muted pastel, editorial)
[6 TEKNIS]      rasio, resolusi, larangan  (9:16, 1080x1920, no text, no watermark)
```

**Template siap pakai** (lengkap di `references/prompt-library-image-video.md`):

```
Product hero    : "{produk} berdiri tegak di {permukaan}, {proporsi} sebagai latar,
                   hero shot, 85mm f/2.8, tiga titik cahaya (key 45°, fill lembut,
                   rim hangat), palet {warna brand}, ruang negatif untuk teks di
                   {posisi}, fotorealistik, 8K, rasio {rasio}, tanpa teks, tanpa watermark"

Lifestyle/UGC   : "kandid {talent} sedang {aksi} dengan {produk} di {lokasi},
                   cahaya alami jendela, handheld, sedikit motion blur, tone hangat,
                   terasa seperti konten UGC asli bukan iklan, rasio {rasio}"

Before–After    : "split frame vertikal, kiri: {kondisi awal, tone dingin desaturasi},
                   kanan: {kondisi akhir, tone hangat saturasi naik}, pencahayaan
                   identik agar adil, garis pembatas tipis, rasio {rasio}"

Flatlay         : "top-down flatlay {produk} dikelilingi {prop pendukung} di atas
                   {tekstur latar}, grid rapi, cahaya merata tanpa bayangan keras,
                   ruang kosong untuk headline, rasio 4:5"

Infografis      : "latar polos {warna} dengan ruang besar untuk grafik, tanpa objek
                   mengganggu, subtle gradient, rasio {rasio}"
```

**Negative prompt standar:** `text, captions, subtitles, watermark, logo, extra fingers,
deformed hands, blurry, oversaturated, plastic skin, cartoonish`

> Tambahkan teks **di tahap editing**, bukan di dalam generasi gambar — hasil lebih rapi
> dan bisa dilokalkan.

---

## C. Prompt video

```
Durasi & rasio : "Shot 2.5s, 9:16"
Subjek & aksi  : satu aksi jelas, kata kerja spesifik ("menuangkan", "membuka kemasan")
Kamera         : gerakan + kecepatan ("slow push-in", "orbit 180°", "handheld subtle")
Lensa & fokus  : "85mm, rack focus dari tangan ke produk"
Cahaya         : "cahaya jendela pagi dari kiri, rim light hangat"
Transisi keluar: "match cut ke shot berikutnya"
Konsistensi    : "pertahankan identitas & warna produk, jangan ubah bentuk kemasan"
Larangan       : "tanpa teks dalam frame, tanpa perubahan logo"
```

Untuk **AI video generator**: pecah jadi shot 2–4 detik; satu shot = satu aksi.
Untuk **first-frame/last-frame**: gunakan hasil image prompt sebagai frame awal agar
identitas produk konsisten antar shot.

---

## C·2. Rasio aset (wajib dicek — masalah paling umum di produksi nyata)

Generator gambar AI **sering mengabaikan rasio** yang diminta di dalam prompt:
storyboard minta 9:16, hasilnya 1:1. Mengunggah asset rasio salah = platform memotong
otomatis dan merusak komposisi.

Solusi: `fit_asset.py` (butuh Pillow) — crop cerdas atau pad, lalu resize ke ukuran
standar platform.

```bash
cd skills/dan/scripts
python3 fit_asset.py ../../../deliverables/gambar.png --ratio 9:16 --focus center
python3 fit_asset.py asset.png --ratio 4:5  --mode pad  --bg "#F5F1E8"   # tanpa memotong
python3 fit_asset.py asset.png --ratio 16:9 --size 1920x1080             # ukuran eksplisit
```

| Rasio | Ukuran standar | Dipakai untuk |
|---|---|---|
| 9:16 | 1080×1920 | TikTok, Reels, Shorts, Story |
| 4:5 | 1080×1350 | feed IG portrait, carousel |
| 1:1 | 1080×1080 | feed square |
| 16:9 | 1920×1080 | YouTube, thumbnail, presentasi |
| 3:4 | 1080×1440 | Pinterest |
| 1.91:1 | 1200×628 | OG image / link preview |

**Aturan memilih mode:**
- `--mode crop` bila subjek berada di tengah dan tepi tidak penting (hero shot).
- `--mode pad` bila tidak boleh ada yang terpotong (kemasan dengan teks legal/label).
- `--focus top|center|bottom` menggeser area yang dipertahankan saat crop vertikal.
- Selalu sediakan **negative space** di posisi teks layar akan ditaruh (safe area, §A).
- Sebutkan rasio & ukuran di dalam prompt sebagai petunjuk, tapi jangan menganggapnya
  dijamin — verifikasi & perbaiki dengan `fit_asset.py` sebelum tayang.

---

## D. Copywriting pendukung

| Butuh | Pola | Contoh |
|---|---|---|
| Hook | pertanyaan menusuk | "Pernah ngerasa {masalah} padahal udah coba semuanya?" |
| Hook | klaim berani + batas waktu | "Aku bebas dari {masalah} dalam {waktu} — ini caranya." |
| Hook | angka | "{n} kesalahan yang bikin {audiens} gagal {hasil}." |
| Hook | kontras | "Ini {hasil} — dan ini kondisi aku sebelumnya." |
| Hook | insider | "Yang nggak diceritakan brand soal {kategori}…" |
| CTA konversi | perintah + urgensi | "{cta} — sebelum kehabisan." |
| CTA engagement | pertanyaan | "Kamu tim {A} atau {B}? Komen ya." |
| CTA awareness | ajakan follow/save | "Save dulu biar nggak hilang." |

Caption: gunakan `caption.short` untuk feed yang padat, `caption.long` untuk storytelling.
Hashtag: 3–5 spesifik + 2–3 kategori + 1 brand (jangan >18).

---

## E. Kalender konten

Salin `templates/content-calendar.csv`, isi:
`tanggal, platform, pilar_konten, format, hook, cta, produk, owner, status, utm, kpi_target`

Pilar konten yang disarankan (rasio 4-3-2-1):
**40% edukasi · 30% hiburan/relatable · 20% bukti sosial · 10% hard selling.**

---

## F. Checklist mutu sebelum tayang
- [ ] Hook muncul ≤ batas platform (TikTok 1,5s / YT 5s)
- [ ] Dipahami **tanpa suara** (subtitle + teks layar)
- [ ] Satu CTA saja, disebut 2× (tengah & akhir)
- [ ] Teks berada di safe area platform
- [ ] Klaim produk bisa dibuktikan (izin edar/BPOM/halal bila relevan)
- [ ] Tidak memakai musik berhak cipta untuk konten komersial
- [ ] Link CTA memakai **UTM** agar terbaca oleh sub-skill 01
- [ ] Minimal 3 varian hook untuk A/B test
- [ ] Export ≥1080p, bitrate ≥8 Mbps

## G. Etika
Jangan meniru wajah/suara orang nyata tanpa izin, jangan membuat before-after palsu,
jangan klaim hasil yang tidak tipikal tanpa disclaimer, jangan menyembunyikan
konten berbayar (`#ad`/`#sponsored`).
