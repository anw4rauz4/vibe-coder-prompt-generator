# Brand Style Guide — Token Desain & Layout Infografik

Token ini **sinkron dengan paket `svg_charts`**, jadi infografik, chart, dan mockup
mempunyai tampilan yang sama. Rujukan untuk sub-skill **03** dan **05**.

---

## 1. Palet tema (siap pakai)

### `dan` — gelap (default; bagus untuk layar & presentasi)
| Token | HEX | Pakai untuk |
|---|---|---|
| bg | `#0F172A` | latar halaman |
| panel | `#111C33` | header / panel |
| card | `#16233F` | kartu & chart |
| text | `#F1F5F9` | teks utama |
| muted | `#94A3B8` | label, sumbu, catatan |
| grid | `#24344F` | garis grid & border |
| accent | `#38BDF8` | sorotan utama |
| good | `#34D399` | positif / di atas target |
| warn | `#FBBF24` | waspada |
| bad | `#FB7185` | negatif / di bawah target |

Seri chart: `#38BDF8 · #A78BFA · #34D399 · #FBBF24 · #FB7185 · #22D3EE · #F472B6 · #84CC16 · #F97316 · #818CF8`

### `light` — terang (untuk cetak & dokumen resmi)
bg `#FFFFFF` · panel `#F8FAFC` · card `#FFFFFF` · text `#0F172A` · muted `#64748B` ·
grid `#E2E8F0` · accent `#2563EB` · good `#059669` · warn `#D97706` · bad `#DC2626`

Seri: `#2563EB · #7C3AED · #059669 · #D97706 · #DC2626 · #0891B2 · #DB2777 · #65A30D · #EA580C · #4F46E5`

### `neon` — untuk konten sosial/layar besar
bg `#07070F` · panel `#0D0D1A` · card `#12122A` · text `#EAF6FF` · muted `#7C86A8` ·
grid `#1E2140` · accent `#00E5FF` · good `#00FF9C` · warn `#FFD400` · bad `#FF3D71`

### `mono` — laporan formal / fotokopi aman
bg `#FFFFFF` · panel `#F4F4F5` · text `#18181B` · muted `#71717A` · grid `#E4E4E7`
Seri grayscale: `#18181B → #D4D4D8` (10 tingkat)

> Cara pakai: `python3 make_infographic.py data.json --theme light`
> atau di Python: `sc.bar(data, th="neon")`.

---

## 2. Aturan warna semantik
| Makna | Warna | Jangan |
|---|---|---|
| Baik / di atas target | `good` | pakai hijau untuk sekadar hiasan |
| Waspada | `warn` | pakai kuning untuk teks kecil (kontras rendah) |
| Buruk / di bawah target | `bad` | pakai merah untuk kategori netral |
| Netral / data | seri berurutan | campur semantik & kategori dalam satu chart |

**Rasio 60-30-10:** 60% latar/netral · 30% warna pendukung · 10% aksen.
**Kontras minimum:** teks 4,5:1 · teks besar 3:1 · elemen grafik penting 3:1.
**Buta warna:** jangan andalkan merah-hijau saja; tambah ikon (▲▼), pola, atau label.

---

## 3. Tipografi

```
Font stack : -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
             'Helvetica Neue', Arial, 'Noto Sans', sans-serif
```
> **Penting:** font eksternal/CDN tidak dimuat di viewer offline — selalu pakai stack sistem.
> Alternatif open-source yang aman untuk cetak: Inter, Noto Sans, Source Sans.

### Skala modular (rasio 1,25)
| Peran | px | weight | tracking | line-height |
|---|---|---|---|---|
| Display / judul infografik | 34 | 800 | −0,7 | 1,15 |
| H1 judul section | 22 | 700 | −0,4 | 1,2 |
| H2 sub-judul | 17 | 700 | −0,2 | 1,3 |
| Angka KPI | 24 | 800 | −0,6 | 1,0 |
| Body | 13,5 | 400 | 0 | 1,55 |
| Label / sumbu chart | 11 | 400–600 | 0 | 1,2 |
| Caption / footer | 11 | 400 | 0 | 1,6 |
| Eyebrow (huruf kapital kecil) | 13 | 700 | +1,6 | 1,2 |

Aturan: maksimum **2 keluarga font**; gunakan weight untuk hierarki, bukan ukuran saja.
Angka selalu `font-variant-numeric: tabular-nums` di tabel.

---

## 4. Grid, spacing, radius, elevasi

```
Grid      : 12 kolom · gutter 14px · margin 24–30px
Lebar max : a4 1180 · a3 1580 · poster 1980 · wide 2400  (PAPER_W di make_infographic.py)
Spacing   : kelipatan 4 → 4, 8, 12, 14, 16, 18, 24, 26, 32
Radius    : kartu 16–18 · chip/pill 999 · elemen kecil 4–10
Elevasi   : pakai border 1px (--grid), bukan shadow berat (lebih bersih untuk print)
```

Breakpoint: `>1280` desktop · `900–1280` laptop · `<900` mobile → semua kartu jadi span 12.

---

## 5. Anatomi infografik DAN

```
┌───────────────────────────────────────────────┐
│ HEADER  judul · subjudul 1–2 baris · chips ·   │  ← badge skor di kanan
│         badge health score                     │
├───────────────────────────────────────────────┤
│ RINGKASAN KPI   8–10 kartu + sparkline         │
├───────────────────────────────────────────────┤
│ VISUALISASI     grid 12 kolom, span 4/6/8      │  ← chart utama dulu, detail belakangan
├───────────────────────────────────────────────┤
│ TABEL DETAIL    angka pasti untuk dicek        │
├───────────────────────────────────────────────┤
│ INSIGHT         kartu ber-aksen kiri (severity)│
├───────────────────────────────────────────────┤
│ REKOMENDASI     daftar bernomor, 2 kolom       │
├───────────────────────────────────────────────┤
│ FOOTER          metodologi · sumber · tanggal  │
└───────────────────────────────────────────────┘
```

**Urutan baca (F-pattern):** pesan utama kiri-atas → KPI → chart pendukung → detail → aksi.

---

## 6. Standar komponen

### Kartu KPI
```
label (kapital kecil, muted) → angka besar (800) → delta (▲ hijau / ▼ merah) → sparkline
```
Delta wajib menyebut basis: "vs periode sebelumnya".

### Kartu insight
Border kiri 4px sesuai severity (`good`/`warn`/`bad`/`accent`).
Isi: **Judul (angka) → detail (bukti) → blok "Aksi"** dengan latar berbeda.

### Chart card
Judul chart di dalam SVG (`title` + `subtitle`), catatan metodologi di bawah SVG
(class `.note`, 11px, muted). Jangan menaruh catatan penting hanya di catatan kaki.

---

## 7. Gaya bahasa visual
| Konteks | Gaya |
|---|---|
| Laporan manajemen | `light`/`mono`, tabel lengkap, minim dekorasi |
| Presentasi layar | `dan`, chart besar, angka menonjol |
| Konten sosial | `neon`, kontras tinggi, tipografi besar |
| Cetak A3/A4 | `light`, hindari latar gelap penuh (boros tinta) |

---

## 8. Checklist aksesibilitas & mutu
- [ ] Kontras teks ≥ 4,5:1 (uji `text` vs `card`)
- [ ] Ukuran teks minimum 11px pada lebar 640px
- [ ] Setiap chart punya judul + satuan
- [ ] Warna bukan satu-satunya pembeda
- [ ] Tidak ada elemen keluar kanvas (`_check_layout.py` = 0 masalah)
- [ ] XML/SVG valid (`_validate_svg.py`)
- [ ] Tidak ada referensi eksternal (CDN/font/gambar http)
- [ ] Footer memuat sumber data, periode, dan tanggal pembuatan
- [ ] Versi tabel tersedia untuk angka penting
