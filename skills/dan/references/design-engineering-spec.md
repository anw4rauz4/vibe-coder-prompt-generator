# Design Engineering Spec — Standar Brief 2D/3D & Sketsa

Rujukan teknis untuk sub-skill **05**. Prinsip: **spesifikasi yang bisa diproduksi**,
bukan sekadar deskripsi estetika. Setiap angka harus punya satuan dan toleransi.

---

## 1. Template brief desain 2D (lengkap)

```markdown
# Brief Desain 2D — {nama proyek}

## 1. Konteks
- Tujuan          : {apa yang harus dicapai desain ini}
- Pemakaian       : {feed IG / billboard / label kemasan / presentasi}
- Metrik sukses   : {CTR, recall, keterbacaan pada jarak X}
- Batas waktu     : {tanggal}
- Budget produksi : {bila cetak}

## 2. Audiens & kondisi lihat
- Siapa           : {demografis + psikografis}
- Perangkat/ukuran: {HP 6,1" / A3 / 4×6 m}
- Jarak pandang   : {30 cm / 2 m / 50 m}   ← menentukan ukuran font minimum
- Durasi pandang  : {1,5 detik / 10 detik / 1 menit}

## 3. Pesan
- Pesan tunggal   : {satu kalimat}
- Hirarki         : 1 headline · 2 produk/visual · 3 proof · 4 CTA · 5 legal
- Wajib ada       : {logo, izin edar, halal, tanggal promo, QR}
- Dilarang        : {klaim tertentu, kata tertentu}

## 4. Spesifikasi kanvas
| Item | Nilai |
|---|---|
| Ukuran akhir | {W} × {H} {mm/px} |
| Bleed | 3 mm tiap sisi |
| Safe margin | 4 mm dari trim |
| Resolusi | 300 dpi (150 dpi bila >3 m) |
| Color mode | CMYK (cetak) / sRGB (layar) |
| Orientasi | portrait / landscape |

## 5. Grid & spacing
- Kolom: {12} · gutter {24px} · margin {32px}
- Baseline grid: {8px}
- Skala spacing: 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64

## 6. Tipografi
| Peran | Font | Ukuran | Weight | Tracking | Line-height |
|---|---|---|---|---|---|
| Headline | {} | {} | 800 | −0,7 | 1,1 |
| Subhead | {} | {} | 600 | 0 | 1,3 |
| Body | {} | {} | 400 | 0 | 1,5 |
| CTA | {} | {} | 700 | +0,5 | 1,2 |
| Legal | {} | {} | 400 | 0 | 1,4 |

Ukuran font minimum: cetak 6 pt · layar 11 px · billboard 1 pt per 3 m jarak.

## 7. Warna
| Peran | HEX | CMYK | Pantone | Rasio pemakaian |
|---|---|---|---|---|
| Primer | | | | 60% |
| Sekunder | | | | 30% |
| Aksen | | | | 10% |
| Netral | | | | — |
Kontras minimum: teks 4,5:1 · teks besar 3:1.

## 8. Aset
| Aset | Sumber | Lisensi | Status |
|---|---|---|---|
| Foto produk | {shoot/AI/stok} | {} | {} |
| Logo | {file vektor} | milik brand | {} |
| Ikon | {} | {} | {} |

## 9. Referensi
- Ikuti gaya: {3 referensi + apa yang diambil}
- Hindari: {3 anti-referensi + alasannya}

## 10. Deliverable & penamaan
| File | Format | Ukuran | Penamaan |
|---|---|---|---|
| Master | .ai / .fig | — | {proyek}_{item}_master_v{n} |
| Web | .svg / .webp | ≤200 KB | {proyek}_{item}_web |
| Cetak | .pdf (PDF/X-1a) | 300 dpi | {proyek}_{item}_print_v{n} |
| Sosmed | .png | 1080×1350 | {proyek}_{item}_{platform} |

## 11. Kriteria terima (definition of done)
- [ ] Pesan tunggal terbaca dalam {durasi pandang}
- [ ] Hirarki visual jelas pada tampilan 100% (bukan thumbnail)
- [ ] Kontras ≥ 4,5:1 untuk semua teks
- [ ] Tidak ada teks dalam zona bleed/safe area
- [ ] Font di-outline/embed
- [ ] Warna sesuai spesifikasi (CMYK untuk cetak)
- [ ] Semua elemen wajib (legal/logo) ada
- [ ] File sesuai format & penamaan
- [ ] Sudah disetujui pemilik merek

## 12. Catatan produksi (bila cetak)
- Bahan : {art carton 260 gsm / albatros / vinyl}
- Finishing: {lam doff / spot UV / foil emas / emboss / die-cut}
- Jumlah : {oplah}
- Vendor : {} + kontak
- Proof : digital proof wajib + dummy cetak sebelum oplah
```

---

## 2. Spesifikasi produk & kemasan 3D

```markdown
# Spec Produk 3D — {nama item}

| Field | Nilai |
|---|---|
| Fungsi utama | |
| Dimensi luar | P {…} × L {…} × T {…} mm |
| Toleransi | ± {…} mm (lihat tabel di bawah) |
| Berat target | {…} g |
| Dinding | {…} mm |
| Material | {jenis + grade} |
| Finishing | {tekstur, warna Pantone/HEX, gloss %} |
| Mekanisme | {engsel/ulir/snap-fit} — tahan {…} siklus |
| Regulasi | {BPOM/halal/food-grade/SNI/label wajib} |
| Uji | jatuh {…} cm · tekan {…} kg · suhu {…}°C |
| Target biaya | Rp {…}/unit pada volume {…} |
| Assembly | {jumlah bagian, metode rakit, waktu rakit} |
```

### Toleransi acuan (konfirmasi ke vendor sebelum final)
| Proses | Toleransi umum |
|---|---|
| Injeksi plastik | ±0,10 mm |
| CNC aluminium | ±0,05 mm |
| CNC plastik | ±0,10 mm |
| 3D print FDM | ±0,20 mm |
| 3D print resin | ±0,10 mm |
| Sheet metal | ±0,15 mm |
| Karton lipat | ±0,50 mm |
| Kaca | ±0,30 mm |
| Sablon | ±0,20 mm |
| Sticker die-cut | ±0,30 mm |

### Draft angle & ketebalan (injeksi plastik)
- Draft minimum 1° (2–3° untuk tekstur).
- Ketebalan dinding seragam; rasio rib ≤ 0,6× dinding utama.
- Radius sudut dalam ≥ 0,5× tebal dinding.
- Hindari sink mark pada bagian tebal → coring.

---

## 3. Dieline kemasan (karton)

```
Jenis kotak   : {reverse tuck / straight tuck / mailer / sleeve / tray}
Ukuran dalam  : P × L × T mm  (produk + clearance 1–2 mm)
Ukuran datar  : hitung dari pola buka
Bahan         : {duplex 350 gsm / ivory 310 / corrugated E-flute}
Lipatan       : garis putus-putus (score) — pisau lipat
Potongan      : garis penuh (cut) — pisau pon
Lem           : area lem ≥ 15 mm, tanpa finishing di area lem
Zona aman cetak: 3 mm dari semua garis potong
File          : AI/PDF vektor, layer terpisah: CUT / FOLD / ART / GLUE
```
Selalu minta **dummy fisik** sebelum produksi massal — layar tidak menunjukkan
ketegangan bahan, arah serat, dan kekuatan lem.

---

## 4. Sketsa 3D — enam tipe keluaran

| Tipe | Fungsi | Komposisi wajib |
|---|---|---|
| Turntable 360° | evaluasi bentuk menyeluruh | 8 sudut @45°, latar & cahaya identik |
| Exploded view | menjelaskan rakitan/komponen | komponen terpisah searah sumbu + garis pemandu + nomor bagian |
| Wireframe / clay | fokus proporsi tanpa distraksi | material clay abu, tanpa warna/tekstur |
| Orthographic 3-view | gambar teknik | depan/atas/samping sejajar + dimensi + garis sumbu |
| Isometric | presentasi & ikon | sudut 30°, tanpa perspektif, tepi bersih |
| Contextual render | pemasaran | produk di lingkungan nyata + pembanding skala manusia |

**Template prompt sketsa:**
```
Industrial design sketch of {objek}, {tipe view}, kamera {sudut},
material {material} finishing {finishing}, proporsi realistis sesuai dimensi
{P×L×T} mm, studio lighting tiga titik, latar {netral/konteks},
{garis konstruksi tipis terlihat / anotasi dimensi dalam mm},
gaya {concept art / technical illustration / clay render}, rasio 16:9,
tanpa teks marketing, tanpa watermark
```

**Template render final:**
```
Photorealistic product render of {objek}, material {…} warna {HEX/Pantone},
dimensi {P×L×T} mm, diletakkan di {latar}, kamera {lensa} mm pada sudut {…},
pencahayaan {HDRI studio / softbox 45°}, depth of field {dangkal/dalam},
refleksi halus pada permukaan {…}, 8K, rasio {…}, tanpa teks
```

---

## 5. Gambar teknik (technical drawing)

Isi minimum satu set gambar:
1. **3-view orthographic** dengan dimensi keseluruhan & kritis.
2. **Detail view** untuk fitur kecil (skala diperbesar).
3. **Tabel toleransi** umum + toleransi khusus per dimensi (GD&T bila perlu).
4. **Bill of material** (nomor bagian, nama, material, jumlah, finishing).
5. **Catatan produksi**: satuan (mm), proyeksi (first-angle/ third-angle), kekasaran permukaan.
6. **Title block**: nama bagian, versi, tanggal, pembuat, pemeriksa, skala.

Simbol GD&T yang sering dipakai: ⌀ diameter · Ⓜ maximum material condition ·
⊕ posisi · ∥ paralel · ⊥ tegak lurus · ⌖ posisi titik.

---

## 6. Pipeline & tooling

```
Konsep    → sketsa tangan / AI image (sub-skill 04)
Modeling  → Blender (gratis) · Fusion 360 · SketchUp · Rhino · SolidWorks
Layout 2D → Figma · Illustrator · Inkscape · Canva (untuk non-desainer)
Dieline   → Illustrator + plugin dieline / PDF vektor dari vendor
Render    → Blender Cycles (realistis) / Eevee (cepat) · Keyshot · AI image
Prototipe → 3D print PLA/PETG · mockup karton · dummy skala 1:1
Produksi  → spec + proof → sample pra-oplah → approval → oplah
```

**Ekspor model:**
| Tujuan | Format |
|---|---|
| CNC / engineering | `.step` / `.iges` |
| Render / game | `.fbx` / `.glb` / `.obj` |
| 3D print | `.stl` / `.3mf` |
| Native (arsip) | `.blend` / `.f3d` / `.sldprt` |
| Web AR | `.glb` (Draco-compressed, <5 MB) |

**Penamaan file:**
```
{proyek}_{item}_{versi}_{status}.{ext}
glowlab_serum-botol_v3_render.png
glowlab_kotak_v2_dieline.pdf
glowlab_tutup_v1_model.step
```

---

## 7. Checklist serah terima desain 3D
- [ ] Semua dimensi + toleransi tercantum
- [ ] Material & finishing spesifik (bukan "plastik")
- [ ] Warna punya nilai pasti (HEX + CMYK/Pantone)
- [ ] Model manifold/watertight (untuk cetak 3D)
- [ ] Ketebalan dinding minimum terpenuhi (≥1,2 mm plastik, ≥0,8 mm resin)
- [ ] Draft angle cukup untuk injeksi
- [ ] Assembly sequence jelas
- [ ] File native + ekspor netral disertakan
- [ ] Versi & changelog tercatat
- [ ] Biaya produksi masih dalam target

## 8. Kolaborasi antar sub-skill
- Positioning & pesan → **02**
- Visual pemasaran/konten → **04**
- Infografik design system / laporan → **03**
- Data performa creative (A/B) → **01**
