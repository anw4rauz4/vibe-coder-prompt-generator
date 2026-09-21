# Campaign Plan — {Nama Kampanye}

> Template sub-skill **02**. Satu kampanye = satu tujuan = satu penawaran.

---

## 1. Identitas Kampanye
| Field | Isi |
|---|---|
| Nama kampanye | |
| Periode | {tgl mulai} – {tgl selesai} ({n} hari) |
| Tujuan utama | {konversi / awareness / traffic / launching / retensi} |
| Target terukur | {angka} |
| Budget total | Rp {…} |
| Penawaran (offer) | {produk + harga + bonus + batas waktu} |
| CTA tunggal | {satu perintah} |
| PIC | {nama} |

## 2. Ringkasan Strategi (3 baris)
```
Siapa   : {audiens prioritas + pemicu kebutuhan}
Janji   : {big idea / manfaat utama + bukti}
Aksi    : {apa yang harus dilakukan audiens sekarang}
```

## 3. Anggaran & Target Matematis
```
Gross margin         = {…}%          → Break-even ROAS = {…}x
Target ROAS          = {…}x          → Revenue target  = budget × ROAS = Rp {…}
AOV                  = Rp {…}        → Konversi target = {…}
CVR asumsi           = {…}%          → Klik target     = {…}
CTR asumsi           = {…}%          → Impresi target  = {…}
CPA maksimum         = Rp {…}        → CPM maksimum    = Rp {…}
```

## 4. Alokasi per Channel
| Channel | Budget | % | Format | Target CPA | Target ROAS | Aset | UTM |
|---|---|---|---|---|---|---|---|
| | | | | | | | `utm_source=…&utm_medium=…&utm_campaign=…` |
| | | | | | | | |
| Cadangan (10%) | | 10% | untuk scale pemenang | — | — | — | — |

## 5. Matriks Creative × Audiens
| Audiens | Hook | Format | Aset | Copy utama | Landing |
|---|---|---|---|---|---|
| Cold | | Video 9:16 15s | | | |
| Warm (engaged 30d) | | Carousel | | | |
| Hot (ATC/visit) | | Static offer | | | |

Minimal **3 varian hook** per audiens untuk A/B test (pakai `storyboard.py`).

## 6. Timeline Produksi
| Tanggal | Aktivitas | Output | PIC |
|---|---|---|---|
| H-14 | Final offer & landing page | | |
| H-10 | Produksi creative (foto/video) | | |
| H-7 | Setup kampanye, pixel, UTM | | |
| H-5 | QA tracking + uji konversi | | |
| H-3 | Soft launch (budget kecil) | | |
| H-0 | **Go live** | | |
| H+3 | Review pertama (pause yang merugi) | | |
| H+7 | Scale pemenang ≤20% | | |
| H+{n} | Penutupan & laporan | | |

## 7. Funnel & Alur Audiens
```
Iklan → {landing page} → {ATC / form} → {checkout / follow-up} → {konfirmasi}
   ↓                                                    ↓
Retargeting (belum beli, 7 hari)            Email/WA sequence (3 pesan)
```
| Tahap | Metrik | Target | Taktik penyelamat |
|---|---|---|---|
| Klik | CTR | ≥ {…}% | ganti hook |
| Landing | bounce rate | ≤ {…}% | percepat loading, sederhanakan |
| ATC | ATC rate | ≥ {…}% | tambah proof, perjelas harga |
| Checkout | cart abandonment | ≤ {…}% | WA/email reminder 1 jam |
| Beli | CVR | ≥ {…}% | urgensi + opsi pembayaran |

## 8. Konten Pendukung (organik)
| Hari | Platform | Pilar | Format | Topik | CTA |
|---|---|---|---|---|---|
| | | edukasi | | | |
| | | hiburan | | | |
| | | bukti sosial | | | |
| | | hard sell | | | |

Rasio pilar 40% edukasi · 30% hiburan · 20% bukti sosial · 10% hard sell.

## 9. KPI Dashboard (dipantau harian)
| Metrik | Target | Aktual | Status | Ambang tindakan |
|---|---|---|---|---|
| Spend | | | 🟢/🟡/🔴 | |
| ROAS | | | | < break-even → pause |
| CPA | | | | > maks → turunkan bid |
| CTR | | | | < 1% → ganti creative |
| CVR | | | | < target → cek LP |
| Frekuensi | | | | > 4 → segarkan audiens |

Sumber data: tarik ke CSV → `dan_analytics.py` → `make_infographic.py`.

## 10. Rencana Kontinjensi
| Pemicu | Tindakan dalam 24 jam |
|---|---|
| ROAS < break-even 2 hari berturut | pause adset, periksa creative & audiens |
| CPA > 1,5× target | turunkan bid / persempit audiens |
| Stok habis | hentikan iklan berbayar, alihkan ke waitlist |
| Komentar negatif viral | siapkan pernyataan, hubungi pelanggan langsung |
| Tracking mati | hentikan keputusan berbasis data sampai diperbaiki |

## 11. Checklist Pra-Go-Live
- [ ] Pixel/konversi API terpasang & teruji (event terlihat)
- [ ] UTM di semua link, konsisten penamaan
- [ ] Landing page loading < 3 detik di HP
- [ ] Offer, harga, dan tanggal promo konsisten di semua aset
- [ ] Stok & kapasitas CS/fulfillment siap untuk lonjakan
- [ ] Legal: izin edar, syarat & ketentuan promo, kebijakan refund
- [ ] Konten berbayar ditandai `#ad` bila melibatkan KOL
- [ ] Anggaran cadangan 10% tersedia untuk scale

## 12. Post-Mortem (diisi setelah kampanye)
| Pertanyaan | Jawaban |
|---|---|
| Target tercapai? | {angka vs target} |
| Apa yang paling berhasil? | {+ bukti angka} |
| Apa yang gagal & kenapa? | {akar masalah, bukan gejala} |
| 3 pembelajaran untuk kampanye berikutnya | 1) … 2) … 3) … |
| Apa yang akan diulang persis? | |
| Apa yang akan dihentikan? | |

---
_Dibuat dengan DAN · Marketing Strategist · {tanggal}_
