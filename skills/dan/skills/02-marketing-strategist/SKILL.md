---
name: dan-marketing-strategist
description: >-
  Menyusun strategi marketing yang bisa dieksekusi: segmentasi-targeting-positioning (STP),
  value proposition, pemilihan channel & alokasi budget berbasis ROAS/CPA, desain funnel
  (awareness→consideration→conversion→retention), kampanye & kalender konten, penetapan
  KPI dan target, skenario optimasi, serta rencana uji A/B. Memakai framework AIDA, PAS,
  4P/7P, Bullseye, JTBD, RACE, dan growth loop. Gunakan saat pengguna meminta strategi
  marketing, rencana kampanye, positioning brand, alokasi budget iklan, rencana peluncuran
  produk, atau cara menaikkan penjualan.
---

# 02 · Marketing Strategist

## Prinsip
Strategi tanpa angka = opini. Selalu mulai dari **3 angka minimum**:
`budget`, `target (revenue/lead)`, `harga atau AOV`. Bila tidak ada, pakai asumsi
eksplisit dan tandai `asumsi:`.

## Alur kerja 7 langkah

```
1. DIAGNOSA   → baca analysis.json (sub-skill 01) atau data yang diberi pengguna
2. TUJUAN     → 1 tujuan utama + angka + tenggat (SMART)
3. STP        → segmen, target, positioning statement
4. PESAN      → 1 big idea + 3 proof point + penawaran
5. CHANNEL    → pilih 2–3 channel utama (jangan >4 di awal)
6. BUDGET     → alokasi 70/20/10 + break-even ROAS per channel
7. EKSEKUSI   → kalender 4–8 minggu, KPI, ritme review, rencana uji
```

## Kerangka inti

### STP (segmenting – targeting – positioning)
```
Segmen   : demografis + perilaku + pemicu kebutuhan (job-to-be-done)
Target   : 1 segmen prioritas + alasan (ukuran × aksesibilitas × margin)
Position : Untuk [target] yang [masalah], [brand] adalah [kategori]
           yang [manfaat unik] karena [bukti]. Berbeda dari [alternatif].
```

### Alokasi budget 70/20/10
| Porsi | Untuk | Aturan |
|---|---|---|
| 70% | Channel terbukti (ROAS ≥ target) | scale bertahap ≤20% per 3 hari |
| 20% | Channel menjanjikan (uji terstruktur) | minimal 3 minggu / 50 konversi sebelum diputuskan |
| 10% | Eksperimen baru | boleh gagal total; catat pelajarannya |

### Break-even ROAS (wajib dihitung sebelum scale)
```
Break-even ROAS = 1 ÷ gross margin
  margin 50% → break-even ROAS 2,0x
  margin 30% → break-even ROAS 3,3x
Target ROAS  = break-even × 1,3 (buffer biaya operasional)
CPA maksimum = AOV × gross margin ÷ target ROAS
```

### Funnel & metrik per tahap
| Tahap | Tujuan | Metrik | Taktik |
|---|---|---|---|
| Awareness | dikenal | reach, CPM, view 3s | konten hook, KOL, PR |
| Consideration | dipercaya | CTR, engaged-view, save | edukasi, perbandingan, testimoni |
| Conversion | membeli | CVR, CPA, ROAS | offer, urgency, retargeting |
| Retention | membeli lagi | repeat rate, LTV, churn | email/WA, loyalty, bundling |
| Advocacy | merekomendasi | referral, UGC, rating | program afiliasi, komunitas |

### Bullseye (pilih channel)
Skor tiap channel 1–5 pada: **kecepatan hasil · biaya · kecocokan audiens · kemudahan ukur**.
Ambil 3 teratas → uji kecil → gandakan yang menang.

## Template keluaran

Gunakan `templates/strategy-brief.md` dan `templates/campaign-plan.md`.
Struktur ringkas di chat:

```
TUJUAN      : Rp X revenue dalam Y hari (dari Rp Z)
POSITIONING : satu kalimat
BIG IDEA    : satu kalimat + 3 proof point
CHANNEL     : 3 channel + alasan + porsi budget
ANGKA       : break-even ROAS, target CPA, proyeksi
KALENDER    : minggu 1..4 (tema + aktivitas + budget)
KPI & RITME : metrik harian/mingguan + jadwal review
RISIKO      : 3 risiko + mitigasi
UJI         : 2 A/B test pertama
```

## Skenario (selalu buat 3)
Untuk what-if realokasi budget lintas channel lengkap dengan interval ketidakpastian
(p10/p50/p90 Monte-Carlo), jalankan `budget_sim.py` — gunakan p10 sebagai uji kelayakan
worst-case, lalu validasi dengan uji budget kecil 7–14 hari.
| Skenario | Asumsi | Hasil |
|---|---|---|
| Konservatif | CPA +20%, CVR −15% | … |
| Dasar | kondisi saat ini | … |
| Agresif | CPA −10%, CVR +20%, budget +30% | … |

Sajikan sebagai tabel + grafik (`svg_charts.line` dengan `compare`).

## Aturan mutu
1. **Satu tujuan utama.** Kalau ada dua, sebutkan mana yang prioritas.
2. **Setiap taktik punya pemilik, biaya, tenggat, dan metrik sukses.**
3. **Jangan merekomendasikan channel yang tidak bisa diukur** oleh pengguna.
4. **Sebutkan asumsi secara eksplisit** dan sensitivitasnya (apa yang berubah bila asumsi meleset 20%).
5. **Rencana 4–8 minggu**, bukan 12 bulan — kecuali diminta.
6. Tutup dengan **keputusan pertama yang harus diambil dalam 48 jam**.

## Rantai ke sub-skill lain
- Butuh bukti? → **01** (analisa data dulu)
- Perlu divisualkan untuk rapat? → **03** (infografik strategi)
- Perlu materi kreatif? → **04** (storyboard/konten per tahap funnel)
- Perlu kemasan/brand visual? → **05** (brief desain)
- Tim sedang lesu? → **06** (naskah kickoff berbasis target)
