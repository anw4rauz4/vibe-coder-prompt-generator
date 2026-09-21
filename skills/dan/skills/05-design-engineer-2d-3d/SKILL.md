---
name: dan-design-engineer-2d-3d
description: >-
  Design engineer untuk kebutuhan 2D dan 3D: menyusun brief desain yang presisi,
  spesifikasi teknis produk & kemasan (dimensi, material, finishing, toleransi, dieline),
  design system (warna, tipografi, grid, spacing), mockup dan render 3D, sketsa 3D
  (turntable, exploded view, wireframe, orthographic 3-view, isometric), technical
  drawing, serta prompt untuk AI 3D/image dan panduan ekspor ke Blender, Fusion 360,
  SketchUp, Figma, Illustrator, atau cetak. Gunakan saat pengguna meminta brief desain,
  spesifikasi produk/kemasan, mockup, sketsa 3D, gambar teknik, design system, atau
  panduan produksi cetak.
---

# 05 · Design Engineer 2D / 3D + Sketsa 3D

## Peran
Menerjemahkan **niat bisnis** menjadi **spesifikasi yang bisa diproduksi**:
ukuran, material, toleransi, warna bernilai pasti, format file, dan kriteria terima.
Bukan sekadar "bikin bagus" — tapi "bikin bisa dibuat".

---

## A. Brief desain 2D (poster, kemasan label, banner, feed)

Isi 12 blok ini (template: `templates/design-brief-2d.md` pola di bawah):

```
1. Tujuan & konteks     : dipakai di mana, untuk apa, mengukur apa
2. Audiens              : siapa, di perangkat apa, jarak pandang berapa
3. Pesan tunggal        : satu kalimat yang harus diingat
4. Hirarki visual       : 1) headline 2) produk 3) proof 4) CTA 5) legal
5. Kanvas & safe area   : WxH mm/px, bleed 3 mm, margin, zona bebas UI
6. Grid & spacing       : kolom, gutter, baseline grid, skala spacing (4/8 pt)
7. Tipografi            : font headline/body, ukuran, weight, tracking, line-height
8. Warna                : HEX/CMYK/Pantone, rasio 60-30-10, aturan kontras ≥ 4.5:1
9. Aset                 : foto/vektor/3D yang dipakai + lisensinya
10. Gaya & referensi    : 3 referensi + 3 anti-referensi (yang harus dihindari)
11. Deliverable & format: master, ekspor (PNG/JPG/PDF/SVG/AI), penamaan file
12. Kriteria terima     : daftar cek yang harus lulus sebelum disetujui
```

### Spesifikasi cetak (wajib bila masuk produksi)
| Item | Nilai standar |
|---|---|
| Resolusi | 300 dpi pada ukuran akhir (150 dpi untuk billboard >3 m) |
| Color mode | CMYK (bukan RGB) |
| Bleed | 3 mm tiap sisi |
| Safe margin | 4 mm dari trim |
| Hitam teks | K100 (bukan rich black) untuk teks kecil |
| Rich black | C60 M40 Y40 K100 untuk bidang besar |
| Font | outline/embed; minimum 6 pt |
| Finishing | laminasi doff/glossy, spot UV, foil, emboss, die-cut |
| Proof | digital proof + dummy cetak sebelum oplah |

---

## B. Spesifikasi produk & kemasan 3D

```
Nama item        :
Fungsi utama     :
Dimensi          : P × L × T (mm)  + toleransi (± mm)
Berat target     : g
Material         : jenis + grade + ketebalan
Finishing        : tekstur, warna (Pantone/HEX), gloss level (%)
Mekanisme        : engsel/ulir/snap-fit + jumlah siklus tahan
Regulasi         : BPOM/halal/food-grade/label wajib
Dieline          : format (AI/PDF), pisau potong, lipatan, lem
Lingkungan       : suhu penyimpanan, tahan jatuh (cm), uji tekan
Biaya target     : per unit pada volume X
```

**Toleransi umum** (acuan awal, konfirmasi ke vendor):
injeksi plastik ±0,10 mm · CNC aluminium ±0,05 mm · karton lipat ±0,5 mm ·
kaca ±0,3 mm · sablon ±0,2 mm · sticker die-cut ±0,3 mm.

---

## C. Design system (agar konsisten lintas media)

```
Warna      : primer / sekunder / aksen / netral / semantik (success, warning, danger)
             + turunan 50–900, aturan pemakaian & rasio 60-30-10
Tipografi  : skala modular (1,25 atau 1,333) → 12/14/16/20/25/31/39…
             pasangan heading–body, maksimum 2 keluarga font
Grid       : 12 kolom, gutter 24, margin 32–64, breakpoint 640/900/1280/1580
Spacing    : kelipatan 4 atau 8 (4, 8, 12, 16, 24, 32, 48, 64)
Radius     : 4 / 8 / 12 / 18 / 999 (pill)
Elevasi    : 3 tingkat shadow
Ikon       : stroke 1,5–2 px, grid 24×24, ujung rounded
```

Token siap pakai (sinkron dengan tema infografik di paket `svg_charts`):
lihat `references/brand-style-guide.md`.

---

## D. Sketsa 3D — 6 tipe keluaran

| Tipe | Untuk | Isi prompt |
|---|---|---|
| **Turntable / 360°** | evaluasi bentuk | 8 sudut @45°, latar netral, cahaya konsisten |
| **Exploded view** | menjelaskan rakitan | komponen terpisah sepanjang sumbu, garis pemandu |
| **Wireframe / clay** | fokus bentuk & proporsi | material clay abu, tanpa warna/tekstur |
| **Orthographic 3-view** | gambar teknik | tampak depan/atas/samping, sejajar, berdimensi |
| **Isometric** | presentasi & ikon | sudut 30°, tanpa perspektif, tepi bersih |
| **Contextual render** | pemasaran | produk di lingkungan nyata, skala manusia |

**Template prompt sketsa 3D:**
```
"Industrial design sketch of {objek}, {tipe view}, {sudut kamera},
 material {material} dengan finishing {finishing}, proporsi realistis,
 studio lighting tiga titik, latar {latar}, garis konstruksi tipis terlihat,
 anotasi dimensi dalam mm, gaya {concept art / technical illustration},
 rasio 16:9, tanpa teks marketing"
```

**Template prompt render final:**
```
"Photorealistic product render of {objek}, {material & warna pasti},
 dimensi {P×L×T} mm, diletakkan di {latar}, kamera {lensa} pada {sudut},
 pencahayaan {HDRI/softbox}, depth of field {dalam/dangkal},
 refleksi halus pada permukaan, 8K, rasio {rasio}, tanpa teks"
```

---

## E. Pipeline & tooling

```
Konsep   → sketsa tangan / AI image (sub-skill 04)
Model    → Blender (gratis) · Fusion 360 · SketchUp · Rhino
2D/layout→ Figma · Illustrator · Inkscape
Dieline  → Illustrator + plugin dieline, atau PDF vektor dari vendor
Render   → Blender Cycles/Eevee · Keyshot · AI image
Prototipe→ 3D print (PLA/PETG) · mockup karton · dummy skala 1:1
Produksi → kirim spec + proof, minta sample pra-oplah
```

**Format file & penamaan:**
```
{nama-proyek}_{item}_{versi}_{status}.{ext}
glowlab_serum-botol_v3_render.png
glowlab_kotak_v2_dieline.pdf
```
Sumber 3D: `.blend`/`.step`/`.obj`/`.fbx` · 2D: `.ai`/`.fig`/`.svg` ·
cetak: `.pdf` (PDF/X-1a) · web: `.svg`/`.webp`.

---

## F. Kriteria terima (definition of done)
- [ ] Semua dimensi & toleransi tercantum, bukan "kira-kira"
- [ ] Warna punya nilai pasti (HEX + CMYK/Pantone)
- [ ] Kontras teks ≥ 4,5:1 (AA), teks besar ≥ 3:1
- [ ] File vektor tersedia untuk elemen yang akan dicetak
- [ ] Bleed & safe area benar; tidak ada teks terpotong
- [ ] Font di-outline/embed
- [ ] Versi file & changelog tercatat
- [ ] Sudah dilihat di ukuran sebenarnya (100%), bukan hanya thumbnail
- [ ] Uji keterbacaan pada jarak pakai (feed HP / rak toko / billboard)
- [ ] Biaya produksi masih dalam target

## G. Kolaborasi
- Butuh visual pemasaran produk → **04** (prompt image/video, konteks pemakaian)
- Butuh data performa desain (A/B creative) → **01**
- Butuh infografik design system → **03**
- Butuh posisi brand sebelum mendesain → **02**
