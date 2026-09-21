# Laporan Analisa Marketing — {Nama Bisnis / Kampanye}

> Template sub-skill **01**. Dihasilkan dari `analysis.json`; isi narasi dengan tangan
> pada bagian "Interpretasi" agar tidak sekadar menempel angka.

---

**Periode** : {tgl mulai} – {tgl selesai} ({n} hari)
**Sumber data** : {file / platform} · {jumlah baris}
**Disusun oleh** : DAN · Marketing Data Analyst
**Tanggal laporan** : {tanggal}

---

## 1. Ringkasan Eksekutif (maks 5 baris)
- **Kabar utama** : {satu kalimat + angka paling penting}
- **Masalah terbesar** : {…}
- **Peluang terbesar** : {…}
- **Rekomendasi #1** : {aksi + dampak yang diharapkan + tenggat}
- **Keputusan yang diminta** : {apa yang harus diputuskan pembaca}

**Marketing Health Score: {…}/100** — {interpretasi singkat}

## 2. KPI Utama
| Metrik | Periode ini | Periode lalu | Δ | Target | Status |
|---|---|---|---|---|---|
| Revenue | | | | | 🟢/🟡/🔴 |
| Ad Spend | | | | | |
| ROAS | | | | ≥ {…}x | |
| CTR | | | | ≥ {…}% | |
| CVR | | | | ≥ {…}% | |
| CPA | | | | ≤ Rp {…} | |
| AOV | | | | | |
| Konversi | | | | | |
| Profit | | | | | |
| Margin | | | | | |

**Interpretasi:** {2–3 kalimat: apa arti angka-angka ini untuk bisnis}

## 3. Performa per Channel
| Channel | Spend | Revenue | ROAS | CTR | CVR | CPA | Share Rev | Keputusan |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | scale / hold / pause |

**Interpretasi:** {channel mana yang menahan performa, mana yang menutupi}

**Realokasi yang disarankan:**
```
Dari {channel A}  : −Rp {…} ({…}%)
Ke   {channel B}  : +Rp {…}
Ke   {channel C}  : +Rp {…}
Proyeksi ROAS     : {…}x → {…}x  (asumsi CPA channel tujuan bertahan)
```

## 4. Performa per Kampanye
| Kampanye | Spend | Revenue | ROAS | Konversi | CPA | Status |
|---|---|---|---|---|---|---|
| | | | | | | |

**Top 3 pemenang** : {…} — alasan menang: {…}
**Bottom 3** : {…} — diagnosis: {…}

## 5. Tren & Proyeksi
- Arah tren : {naik/turun} (slope {…}/hari, R² {…})
- Perubahan periode : {±…%}
- Proyeksi {n} hari : {angka per hari} — metode {linear regression}
- **Tingkat keyakinan** : {tinggi bila R² > 0,6; rendah bila < 0,3}

**Interpretasi:** {apakah tren ini struktural atau musiman? apa pemicunya?}

## 6. Anomali
| Tanggal | Metrik | Nilai | Deviasi | z | Kemungkinan penyebab | Sudah diverifikasi? |
|---|---|---|---|---|---|---|
| | | | | | | ya / belum |

> Anomali yang belum diverifikasi **tidak boleh** dipakai sebagai dasar keputusan.

## 7. Funnel
| Tahap | Volume | Konversi tahap | Drop-off |
|---|---|---|---|
| Impresi | | — | — |
| Klik | | CTR {…}% | {…}% |
| Konversi | | CVR {…}% | {…}% |

**Titik bocor terbesar:** {tahap} → **perbaikan yang disarankan:** {…}

## 8. Analisa Pareto
{top n} dari {total} {channel/kampanye} menyumbang 80% {metrik}: {daftar}
**Implikasi:** {fokus optimasi vs evaluasi sisanya}

## 9. Pola Waktu
- Hari terbaik : {…} ({…}% revenue)
- Hari terlemah : {…}
- Jam terbaik : {…}
- **Tindakan penjadwalan:** {…}

## 10. Korelasi
| A | B | r | Kekuatan | Catatan |
|---|---|---|---|---|
| | | | | |

> Korelasi ≠ kausalitas. Untuk membuktikan, lakukan uji terkontrol (§12).

## 11. Insight & Rekomendasi
Format tiap insight: **Judul (angka) → Bukti → Sebab → Aksi terukur**

1. **{judul}** — {bukti + periode}. Sebab: {hipotesis, tandai bila asumsi}.
   → **Aksi:** {langkah + ukuran + tenggat + PIC}
2. …
3. …

| Prioritas | Aksi | Dampak diharapkan | Biaya | Tenggat | PIC |
|---|---|---|---|---|---|
| 1 (segera) | | | | | |
| 2 | | | | | |
| 3 | | | | | |

## 12. Uji yang Disarankan
| Uji | Hipotesis | Variabel | Sampel min | Durasi | Metrik menang |
|---|---|---|---|---|---|
| | | | 50 konversi/varian | ≥7 hari | |

## 13. Keterbatasan Data
- Cakupan : {periode, channel yang termasuk/tidak}
- Kualitas : {baris kosong, duplikasi, tracking gap}
- Atribusi : {model yang dipakai platform, risiko double-count}
- Ukuran sampel : {apakah cukup untuk simpulan}
- Yang tidak bisa dijawab data ini : {…}

## 14. Langkah Berikutnya
1. {…}
2. {…}
3. {…}

---

### Lampiran
- `analysis.json` — data mentah hasil hitungan
- `summary_channel.csv` — tabel agregat per channel
- `infographic.html` — versi visual laporan ini

**Metodologi:** CTR = klik÷impresi · CVR = konversi÷klik · CPA = spend÷konversi ·
ROAS = revenue÷spend · AOV = revenue÷konversi · Tren = regresi linear least-square ·
Anomali = z-score ≥ 2σ · Pareto = kumulatif menurun 80%.

_Dibuat dengan DAN · Marketing Data Analyst_
