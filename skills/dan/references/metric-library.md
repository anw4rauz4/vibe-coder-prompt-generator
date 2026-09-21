# Metric Library — Kamus Metrik Marketing

Rujukan lengkap untuk sub-skill **01 (Data Analyst)** dan **02 (Strategist)**.
Semua rumus memakai nama kolom kanonik dari `dan_analytics.py`.

## 1. Metrik jangkauan (awareness)

| Metrik | Rumus | Satuan | Benchmark umum | Catatan |
|---|---|---|---|---|
| Impressions | Σ impresi | kali | — | jumlah tayangan, boleh orang sama |
| Reach | Σ unik | orang | — | butuh data unik; jangan disamakan dengan impresi |
| Frequency | impresi ÷ reach | kali | 1,5–4 (prospekting), 3–8 (retargeting) | >8 biasanya fatigue |
| CPM | spend ÷ impresi × 1000 | mata uang | Rp 8–40 rb (feed IG/TT ID) | naik = lelang makin ketat |
| CPV | spend ÷ video view | mata uang | Rp 50–400 | untuk video ads |
| View-through rate | view ≥3s ÷ impresi | % | 25–45% | indikator kekuatan hook |
| Thumb-stop rate | view ≥3s ÷ reach | % | ≥ 30% | versi reach dari VTR |

## 2. Metrik interaksi (engagement)

| Metrik | Rumus | Benchmark | Catatan |
|---|---|---|---|
| Engagement | like + comment + share + save | — | simpan sebagai satu kolom |
| Engagement Rate (ER) | engagement ÷ impresi × 100% | 1–3% IG, 3–8% TikTok | ada yang pakai ÷follower; sebutkan pembaginya |
| ER per reach | engagement ÷ reach × 100% | lebih tinggi dari ER impresi | konsisten pilih satu |
| Comment ratio | komentar ÷ engagement | >10% = diskusi hidup | sinyal kuat untuk algoritma |
| Save rate | save ÷ impresi | >1% = konten bernilai | terbaik untuk edukasi |
| Share rate | share ÷ impresi | >0,5% = viral potensial | |

## 3. Metrik lalu lintas (traffic)

| Metrik | Rumus | Benchmark | Catatan |
|---|---|---|---|
| CTR | klik ÷ impresi × 100% | 0,9–2% paid social · 3–6% search brand · 1–3% email | indikator utama kualitas creative |
| CPC | spend ÷ klik | Rp 800–8.000 (ID) | turun bila relevansi naik |
| Outbound CTR | klik keluar ÷ impresi | lebih rendah dari CTR total | |
| Bounce rate | sesi 1 halaman ÷ sesi | <60% | tinggi = mismatch intent |
| Avg. session | rata-rata durasi sesi | >60 dtk | |
| Landing CVR | konversi ÷ sesi LP | 2–5% e-comm, 10–25% lead form | |

## 4. Metrik konversi & efisiensi

| Metrik | Rumus | Sehat bila | Catatan |
|---|---|---|---|
| CVR | konversi ÷ klik × 100% | ≥2% e-comm | cek per device |
| CPA / CPL | spend ÷ konversi | < AOV × margin ÷ target ROAS | |
| Cost per ATC | spend ÷ add-to-cart | — | sinyal dini masalah checkout |
| Cart abandonment | 1 − (checkout ÷ ATC) | <70% | |
| AOV | revenue ÷ konversi | tren naik | naikkan lewat bundling/upsell |
| ROAS | revenue ÷ spend | ≥3x | lihat catatan margin di bawah |
| Break-even ROAS | 1 ÷ gross margin | — | margin 40% → 2,5x |
| Target ROAS | break-even × 1,3 | — | buffer biaya operasional |
| MER (marketing efficiency ratio) | total revenue ÷ total spend (semua channel) | ≥2x | tidak terpengaruh attribution |
| Profit | revenue − spend | >0 | sebelum HPP; sebutkan bila sesudah |
| Contribution margin | revenue − spend − HPP | >0 | angka yang sebenarnya penting |

> **Hati-hati ROAS:** ROAS 3x dengan margin 30% artinya profit kotor hanya 0,9× spend
> dikurangi HPP — bisa jadi merugi. Selalu sandingkan ROAS dengan margin.

## 5. Metrik pelanggan (retention)

| Metrik | Rumus | Catatan |
|---|---|---|
| CAC | (spend marketing + sales) ÷ pelanggan baru | bandingkan dengan LTV |
| LTV | AOV × frekuensi beli/tahun × umur pelanggan (tahun) × margin | |
| LTV:CAC | LTV ÷ CAC | sehat ≥ 3:1 |
| CAC payback | CAC ÷ (margin per bulan per pelanggan) | <12 bulan |
| Repeat purchase rate | pembeli ≥2× ÷ total pembeli | >25% bagus |
| Churn | pelanggan hilang ÷ pelanggan awal periode | |
| Retention cohort | % cohort masih aktif di bulan ke-n | gambar sebagai heatmap |
| NPS | %promotor − %detraktor | >30 baik, >50 sangat baik |

## 6. Metrik konten & funnel

| Tahap | Metrik | Cara baca |
|---|---|---|
| Hook | 3s view rate | rendah = 3 detik pertama gagal |
| Hold | average watch time / completion | rendah = alur membosankan |
| Click | CTR | rendah = penawaran tidak jelas |
| Convert | LP CVR | rendah = friksi/kepercayaan |
| Repeat | repeat rate | rendah = produk/layanan mengecewakan |

## 7. Metrik forecasting (dipakai `dan_analytics.py`)

| Metrik | Rumus/metode | Interpretasi |
|---|---|---|
| Slope | regresi linear least-square | perubahan per periode |
| R² | 1 − SSres ÷ SStot | >0,6 tren jelas; <0,3 jangan dipakai meramal |
| Moving average | rata-rata n periode berjalan | menghaluskan noise; MA-3/MA-7 |
| z-score | (x − μ) ÷ σ | \|z\| ≥ 2 = anomali |
| Growth | (akhir ÷ awal − 1) × 100% | sebutkan periode pembandingnya |
| CAGR | (akhir ÷ awal)^(1/tahun) − 1 | untuk periode >1 tahun |

## 8. Aturan presentasi angka
1. Selalu sertakan **periode** dan **satuan**.
2. Format Indonesia: `Rp1.234.567` dan `2,5%` (kecuali diminta EN).
3. Pembulatan: uang → satuan terdekat; persen → 1–2 desimal; rasio → 2 desimal.
4. Perubahan: tulis `+12,4%` / `−8,1%`, dan sebutkan basis pembandingnya.
5. Angka kecil: pakai `rb`/`jt`/`M` agar mudah dibaca di grafik.
6. Jangan menampilkan lebih dari **7 angka** dalam satu blok tanpa konteks.
