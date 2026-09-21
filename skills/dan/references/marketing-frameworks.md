# Marketing Frameworks — Pustaka Kerangka Kerja

Rujukan untuk sub-skill **02 (Strategist)**. Pakai maksimal 2–3 framework per proyek;
framework adalah alat bantu berpikir, bukan pengganti keputusan.

---

## 1. Diagnosis & perencanaan

### STP (Segmenting – Targeting – Positioning)
```
Segmenting : bagi pasar → demografis, geografis, psikografis, perilaku, JTBD
Targeting  : skor tiap segmen (ukuran × pertumbuhan × aksesibilitas × kecocokan × margin)
Positioning: "Untuk [target] yang [masalah/kebutuhan], [brand] adalah [kategori]
             yang [manfaat unik] karena [bukti]. Berbeda dari [alternatif] yang [kekurangan]."
```
Uji posisi dengan **perceptual map**: 2 sumbu atribut penting, plot brand & kompetitor
(`svg_charts.scatter`).

### 4P / 7P
Product · Price · Place · Promotion (+ People · Process · Physical evidence untuk jasa).
Gunakan sebagai checklist, bukan sebagai strategi itu sendiri.

### JTBD (Jobs To Be Done)
```
Ketika [situasi], saya ingin [motivasi], supaya [hasil yang diharapkan].
```
Fungsi · Emosional · Sosial. Job yang sama sering punya "pesaing" yang tak terduga.

### SWOT → TOWS (agar menghasilkan aksi)
|  | Strength | Weakness |
|---|---|---|
| **Opportunity** | SO: pakai kekuatan untuk menangkap peluang | WO: perbaiki kelemahan demi peluang |
| **Threat** | ST: pakai kekuatan untuk menahan ancaman | WT: bertahan/minimalkan risiko |

### Bullseye (pemilihan channel)
Skor 1–5 tiap channel pada: kecepatan hasil · biaya · kecocokan audiens · kemudahan diukur ·
skalabilitas. Ambil 3 teratas → uji budget kecil → gandakan yang menang.
Jangan jalankan >4 channel sekaligus bila tim kecil.

---

## 2. Kerangka pesan & copy

| Framework | Urutan | Terbaik untuk |
|---|---|---|
| **AIDA** | Attention → Interest → Desire → Action | iklan pendek, landing page |
| **PAS** | Problem → Agitate → Solution | audiens sadar masalah, butuh didorong |
| **BAB** | Before → After → Bridge | transformasi/hasil nyata |
| **4U** | Useful · Urgent · Unique · Ultra-specific | menulis headline |
| **FAB** | Feature → Advantage → Benefit | produk teknis |
| **Star-Story-Solution** | tokoh → konflik → jalan keluar | video naratif, case study |
| **QUEST** | Qualify → Understand → Educate → Stimulate → Transition | konten panjang/edukasi |
| **PPPP** | Picture → Promise → Prove → Push | sales page |

**Big idea test:** bisa dijelaskan dalam 1 kalimat? Bikin orang ingin cerita ke temannya?
Bisa dipakai di 10 konten berbeda tanpa basi?

---

## 3. Funnel & pertumbuhan

### AARRR (pirate metrics)
Acquisition → Activation → Retention → Revenue → Referral.
Petakan metrik tiap tahap (lihat `metric-library.md` §6).

### RACE
Reach → Act → Convert → Engage. Cocok untuk rencana digital tahunan.

### Growth loop (lebih tahan lama daripada funnel)
```
pengguna baru → membuat sesuatu yang terlihat orang lain → menarik pengguna baru
contoh: UGC, referral, SEO programmatic, marketplace review
```
Ukur: **cycle time** (berapa lama satu putaran) dan **loop rate** (>1 = tumbuh sendiri).

### Marketing mix budgeting
| Metode | Kapan dipakai |
|---|---|
| % dari revenue | stabil, industri mapan (7–15% B2C, 3–8% B2B) |
| Objective & task | paling akurat; hitung biaya per tujuan |
| Competitor parity | hanya sebagai sanity check |
| All-you-can-afford | startup tahap awal (berisiko) |

**Aturan 70/20/10:** 70% terbukti · 20% uji terstruktur · 10% eksperimen.

---

## 4. Pricing

| Strategi | Mekanisme | Risiko |
|---|---|---|
| Cost-plus | biaya + margin target | mengabaikan nilai yang dirasakan |
| Value-based | harga dari nilai bagi pelanggan | butuh riset |
| Penetration | harga rendah untuk merebut pasar | perang harga |
| Skimming | harga tinggi di awal lalu turun | mengundang pesaing |
| Tiered (good-better-best) | 3 paket; tengah paling laku | kompleksitas |
| Bundling | menaikkan AOV | mengaburkan nilai satuan |
| Subscription | LTV tinggi, churn jadi risiko | butuh retensi kuat |

**Angka yang wajib dihitung:** gross margin · break-even ROAS · CPA maksimum ·
LTV:CAC · payback period.

---

## 5. Pengukuran & eksperimen

### OKR marketing
```
Objective : kualitatif, inspiratif, 1 kuartal
Key Results: 3–5 angka terukur (bukan daftar tugas)
```
Contoh: O = "Menjadi pilihan pertama skincare lokal untuk kulit kusam";
KR1 = ROAS ≥ 3x · KR2 = repeat rate ≥ 25% · KR3 = share of voice 15%.

### North Star Metric + input metrics
Satu metrik hasil (mis. jumlah pembelian berulang) + 3–5 metrik proses yang bisa digerakkan.

### A/B testing — aturan minimum
| Item | Aturan |
|---|---|
| Satu variabel | ubah 1 hal saja per uji |
| Ukuran sampel | minimal 50 konversi per varian (idealnya 100+) |
| Durasi | ≥7 hari penuh (menutup pola hari) |
| Signifikansi | p < 0,05; sebutkan interval kepercayaan |
| Urutan | uji hal berdampak besar dulu (offer > headline > visual > warna) |

### Attribution — kenali batasnya
`last-click` meremehkan awareness · `first-click` meremehkan closing ·
`data-driven` butuh volume. Selalu cek **MER** (revenue total ÷ spend total) sebagai
pembanding yang tidak bergantung platform.

---

## 6. Kerangka eksekusi

### Rencana kampanye 4 minggu
| Minggu | Fase | Fokus |
|---|---|---|
| 1 | Setup & baseline | tracking, UTM, creative, ukur titik awal |
| 2 | Uji | 3–5 varian hook/audiens, budget kecil |
| 3 | Scale | gandakan pemenang, tambah budget ≤20%/3 hari |
| 4 | Optimasi & panen | retargeting, bundling, upsell, evaluasi |

### RACI (agar jelas siapa melakukan apa)
Responsible · Accountable · Consulted · Informed — isi per aktivitas.

### Risk register (minimum 3 risiko)
```
Risiko | Dampak (1-5) | Kemungkinan (1-5) | Mitigasi | Pemicu (early warning) | Pemilik
```

---

## 7. Kapan memakai yang mana (pintasan)

| Situasi pengguna | Mulai dari |
|---|---|
| "Penjualan turun, nggak tahu kenapa" | AARRR + funnel diagnosis → 01 |
| "Mau launching produk baru" | STP + JTBD + Bullseye + rencana 4 minggu |
| "Budget terbatas, harus pilih channel" | Bullseye + 70/20/10 + break-even ROAS |
| "Iklan jalan tapi nggak konversi" | PAS/BAB untuk pesan + uji A/B + funnel |
| "Mau menaikkan LTV" | Growth loop + subscription/bundling + retention cohort |
| "Butuh laporan ke manajemen" | OKR + North Star + infografik (03) |
| "Perang harga dengan kompetitor" | Perceptual map + value-based pricing + diferensiasi |
