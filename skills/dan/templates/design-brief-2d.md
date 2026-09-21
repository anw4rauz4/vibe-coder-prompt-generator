# Brief Desain 2D — {Nama Proyek}

> Template sub-skill **05**. Isi semua `{…}`; hapus baris yang tidak relevan.
> Prinsip: **spesifikasi yang bisa diproduksi**, bukan sekadar deskripsi estetika.
> Acuan teknis lengkap: `references/design-engineering-spec.md`.

---

## 1. Konteks
| Field | Isi |
|---|---|
| Tujuan desain | {apa yang harus dicapai} |
| Media pemakaian | {feed IG / story / billboard / label kemasan / slide / banner web} |
| Metrik sukses | {CTR · recall · keterbacaan pada jarak X · konversi} |
| Batas waktu | {tanggal final} |
| Budget produksi | {bila cetak} |
| Pemilik keputusan | {nama approver} |

## 2. Audiens & kondisi lihat
| Field | Isi |
|---|---|
| Siapa | {demografis + psikografis} |
| Perangkat / ukuran | {HP 6,1" / A3 / 4×6 m} |
| Jarak pandang | {30 cm / 2 m / 50 m} ← menentukan ukuran font minimum |
| Durasi pandang | {1,5 detik / 10 detik / 1 menit} |
| Kebutuhan aksesibilitas | {kontras, ukuran teks, buta warna} |

## 3. Pesan
- **Pesan tunggal** : {satu kalimat yang harus diingat}
- **Hirarki visual** : 1) headline 2) produk/visual utama 3) proof 4) CTA 5) legal
- **Wajib ada** : {logo · nomor izin edar · logo halal · tanggal promo · QR · S&K}
- **Dilarang** : {klaim tertentu · kata tertentu · warna tertentu}
- **Tone of voice** : {friendly / profesional / mewah / lucu}

## 4. Spesifikasi kanvas
| Item | Nilai |
|---|---|
| Ukuran akhir | {W} × {H} {mm / px} |
| Bleed | 3 mm tiap sisi (cetak) / 0 (layar) |
| Safe margin | 4 mm dari trim |
| Resolusi | 300 dpi · 150 dpi bila luas > 3 m |
| Color mode | CMYK (cetak) / sRGB (layar) |
| Orientasi | portrait / landscape / square |
| Rasio | {9:16 · 4:5 · 1:1 · 16:9} |

## 5. Grid & spacing
```
Kolom          : {12} · gutter {24px} · margin {32px}
Baseline grid  : {8px}
Skala spacing  : 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64
Radius         : 4 / 8 / 12 / 18 / 999 (pill)
```

## 6. Tipografi
| Peran | Font | Ukuran | Weight | Tracking | Line-height |
|---|---|---|---|---|---|
| Headline | {…} | {…} | 800 | −0,7 | 1,1 |
| Subhead | {…} | {…} | 600 | 0 | 1,3 |
| Body | {…} | {…} | 400 | 0 | 1,5 |
| CTA | {…} | {…} | 700 | +0,5 | 1,2 |
| Legal | {…} | {…} | 400 | 0 | 1,4 |

**Ukuran minimum:** cetak 6 pt · layar 11 px · billboard ±1 pt tiap 3 m jarak pandang.
**Font stack aman (tanpa CDN):** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
'Helvetica Neue', Arial, 'Noto Sans', sans-serif`

## 7. Warna
| Peran | HEX | CMYK | Pantone | Porsi |
|---|---|---|---|---|
| Primer | {…} | {…} | {…} | 60% |
| Sekunder | {…} | {…} | {…} | 30% |
| Aksen | {…} | {…} | {…} | 10% |
| Netral / latar | {…} | {…} | — | — |
| Semantik (baik/waspada/buruk) | {…} | — | — | seperlunya |

Kontras minimum: teks 4,5:1 · teks besar 3:1 · elemen grafik penting 3:1.
Jangan mengandalkan warna saja sebagai pembeda (tambah ikon/label/pola).

## 8. Aset
| Aset | Sumber | Lisensi | Status |
|---|---|---|---|
| Foto produk | {shoot / AI / stok} | {…} | {siap / perlu dibuat} |
| Logo | {file vektor .ai/.svg} | milik brand | {…} |
| Ikon | {library / custom} | {…} | {…} |
| Model 3D | {Blender / Fusion / AI} | {…} | {…} |

> Untuk aset foto/render: pakai template prompt di `references/prompt-library-image-video.md`.
> Untuk aset 3D: pakai spesifikasi di `references/design-engineering-spec.md` §4.

## 9. Referensi & anti-referensi
**Ikuti gaya (3):**
1. {referensi} — yang diambil: {…}
2. {referensi} — yang diambil: {…}
3. {referensi} — yang diambil: {…}

**Hindari (3):**
1. {anti-referensi} — karena: {…}
2. {anti-referensi} — karena: {…}
3. {anti-referensi} — karena: {…}

## 10. Deliverable & penamaan
| Keluaran | Format | Ukuran | Nama file |
|---|---|---|---|
| Master | .ai / .fig | — | `{proyek}_{item}_master_v{n}` |
| Web | .svg / .webp | ≤ 200 KB | `{proyek}_{item}_web` |
| Cetak | .pdf (PDF/X-1a) | 300 dpi | `{proyek}_{item}_print_v{n}` |
| Sosmed | .png | 1080×1350 | `{proyek}_{item}_{platform}` |
| Sumber terbuka | .svg / .eps | vektor | `{proyek}_{item}_source` |

## 11. Catatan produksi (bila cetak)
```
Bahan     : {art carton 260 gsm / albatros / vinyl / HVS}
Finishing : {lam doff / lam glossy / spot UV / foil emas / emboss / die-cut}
Oplah     : {jumlah}
Vendor    : {nama + kontak}
Proof     : digital proof wajib → dummy cetak → approval → oplah
Hitam teks: K100 (jangan rich black untuk teks kecil)
Rich black: C60 M40 Y40 K100 (bidang besar saja)
```

## 12. Kriteria terima (definition of done)
- [ ] Pesan tunggal terbaca dalam {durasi pandang} pada jarak {…}
- [ ] Hirarki visual jelas pada tampilan 100% (bukan hanya thumbnail)
- [ ] Kontras semua teks ≥ 4,5:1
- [ ] Tidak ada teks/elemen penting di zona bleed atau di luar safe margin
- [ ] Font sudah di-outline atau di-embed
- [ ] Mode warna sesuai tujuan (CMYK untuk cetak, sRGB untuk layar)
- [ ] Semua elemen wajib (logo/legal/izin) ada dan terbaca
- [ ] Ukuran & resolusi sesuai spesifikasi §4
- [ ] Nama file sesuai konvensi §10
- [ ] Sudah diuji pada perangkat/ukuran sebenarnya
- [ ] Disetujui pemilik keputusan

## 13. Pertanyaan terbuka
| # | Pertanyaan | Kepada | Tenggat |
|---|---|---|---|
| 1 | {…} | {…} | {…} |

---

**Ringkasan untuk desainer (satu paragraf):**
> {Tulis 3–4 kalimat: siapa audiensnya, apa satu pesan yang harus sampai, di media apa
> desain ini akan dilihat, dan gaya apa yang diinginkan. Ini yang dibaca pertama kali.}

_Dibuat dengan DAN · Design Engineer 2D/3D · {tanggal}_
