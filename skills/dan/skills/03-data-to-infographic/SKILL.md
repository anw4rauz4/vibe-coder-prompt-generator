---
name: dan-data-to-infographic
description: >-
  Mengubah data menjadi infografik lengkap dan dashboard siap presentasi, sekaligus
  melakukan analisa graph/network. Menyediakan 16 tipe chart SVG tanpa dependensi
  (bar, hbar, stacked bar, line, area, donut/pie, funnel, radar, scatter/bubble,
  heatmap, waterfall, gauge, sparkline, network) dan merakitnya menjadi HTML
  self-contained atau poster SVG. Termasuk graph analyst: PageRank, betweenness,
  closeness, eigenvector, HITS, deteksi komunitas, untuk memetakan jaringan KOL,
  referral, ko-okurensi kata kunci, atau topik konten. Gunakan saat pengguna meminta
  infografik, visualisasi data, dashboard, laporan bergambar, chart/grafik tertentu,
  poster data, atau analisa jaringan/relasi.
---

# 03 · Data → Infographic + Graph Analyst

## A. Membuat infografik dari hasil analisa (mode AUTO)

```bash
cd skills/dan/scripts
python3 dan_analytics.py ../../../data/<file>.csv               # langkah 1
python3 make_infographic.py ../../../deliverables/analysis.json \
  --theme dan --paper a3 \
  --svg deliverables/infographic_poster.svg                     # langkah 2
```

Hasil: `deliverables/infographic.html` (self-contained, bisa di-preview & di-print)
dan `infographic_poster.svg`.

**Tema:** `dan` (gelap, default) · `light` (terang, untuk print) · `neon` · `mono`
**Ukuran kertas:** `a4` (1180px) · `a3` (1580px) · `poster` (1980px) · `wide` (2400px)

### Yang otomatis muncul di infografik AUTO
KPI cards + sparkline · tren revenue & proyeksi · health gauge · donut kontribusi channel ·
hbar ROAS & CPA · funnel konversi · top kampanye · scatter spend-vs-ROAS · pola hari/jam ·
radar profil channel · kurva Pareto · tabel korelasi · tabel detail · kartu insight · rekomendasi.

---

## B. Infografik dari data bebas (mode SPEC)

Bila datanya bukan hasil `dan_analytics.py`, buat JSON spesifikasi
(lihat `templates/data-spec.example.json`):

```json
{
  "title": "Laporan Q3 2026", "subtitle": "Ringkasan performa",
  "theme": "light", "locale": "id", "currency": "Rp", "paper": "a3",
  "badge": {"value": "82", "label": "health score"},
  "chips": ["Periode Jul–Sep", "6 channel"],
  "sections": [
    {"type": "kpi", "items": [
      {"label": "Revenue", "value": 1250000000, "format": "currency", "delta": 12.4,
       "spark": [80, 92, 88, 101, 118, 130]}
    ]},
    {"type": "chart", "chart": "bar", "span": 6, "title": "Klik per Channel",
     "data": [["IG", 4200], ["TT", 3100], ["YT", 1800]]},
    {"type": "chart", "chart": "line", "span": 6, "title": "Tren",
     "data": {"labels": ["Jul", "Agu", "Sep"], "series": {"2025": [10, 14, 13], "2026": [16, 21, 27]}}},
    {"type": "chart", "chart": "funnel", "span": 4, "title": "Funnel",
     "data": [["Impresi", 1200000], ["Klik", 84000], ["Beli", 3240]]},
    {"type": "insights", "items": [
      {"title": "TikTok tumbuh 42%", "detail": "…", "severity": "good", "action": "…"}]},
    {"type": "recommendations", "items": ["Geser 20% budget ke TikTok"]}
  ]
}
```

```bash
python3 make_infographic.py spec.json --out ../../../deliverables/q3.html
```

**Tipe chart yang tersedia** (`svg_charts.REGISTRY`):
`bar` `hbar` `stacked_bar` `line` `area` `donut` `pie` `funnel` `radar` `scatter`
`heatmap` `waterfall` `gauge` `network` `sparkline`

Galeri contoh: `python3 -m svg_charts` → `deliverables/chart_gallery.html`

---

## C. Memakai mesin chart secara langsung (Python)

```python
import sys; sys.path.insert(0, "skills/dan/scripts")
import svg_charts as sc

svg = sc.bar([("IG", 4200), ("TT", 3100)], title="Klik", th="light", loc="id")
open("chart.svg", "w").write(svg)

sc.line(compare={"Aktual": [10, 20, 30, None], "Proyeksi": [None, None, 30, 41]},
        x_labels=["Q1","Q2","Q3","Q4"], area=True)     # None = garis putus-putus
sc.donut(data, center_value="Rp1,2M", center_label="total")
sc.radar({"Kita":[8,6,9], "Rival":[6,9,5]}, ["Harga","Kualitas","Brand"])
sc.network(nodes=[{"id":"A","group":0,"value":9}], edges=[("A","B",3)], weighted=True)
```

Parameter umum semua chart: `title, subtitle, width, height, th (tema), loc ("id"/"en"),
transparent, value_fmt (fungsi format angka)`.

---

## D. Graph / Network Analyst

Untuk data **relasi**, bukan data tabel: jaringan KOL, referral pelanggan, ko-okurensi
kata kunci, peta topik, ekosistem kompetitor.

```bash
python3 graph_analyst.py --demo                       # contoh bawaan
python3 graph_analyst.py --edges relasi.csv           # source,target[,weight]
python3 graph_analyst.py --graph jaringan.json        # {"nodes":[...],"edges":[[a,b,w]]}
```
Output: `graph.json` (metrik), `graph.svg` (visual), `graph.md` (laporan).

| Metrik | Menjawab pertanyaan | Pakai untuk |
|---|---|---|
| Degree / strength | siapa paling banyak koneksi | ukuran popularitas |
| **PageRank** | siapa paling berpengaruh | memilih KOL, bukan sekadar follower |
| **Betweenness** | siapa jembatan antar kelompok | cari broker & single point of failure |
| Closeness | siapa paling cepat menyebarkan info | seeding kampanye viral |
| Eigenvector | siapa terhubung ke node penting lain | kualitas koneksi |
| HITS (hub/authority) | siapa penghubung vs sumber otoritas | memisahkan aggregator dari pakar |
| Komunitas (label prop.) | ada cluster apa saja | personalisasi pesan per cluster |
| Density / komponen | seberapa rapat & terpecah | risiko echo chamber |

Validasi: metrik pure-python sudah dicocokkan dengan **networkx** — deviasi 0,0000
(`python3 _test_graph.py`).

---

## E. Memilih chart yang benar

Ringkasan (lengkap: `references/chart-selection-guide.md`):

| Ingin menunjukkan | Pakai |
|---|---|
| Perbandingan antar kategori | `bar` / `hbar` (label panjang → hbar) |
| Perubahan sepanjang waktu | `line` (banyak titik) / `area` (volume) |
| Komposisi/porsi | `donut` (≤6 kategori) / `stacked_bar` (porsi per waktu) |
| Tahapan & drop-off | `funnel` |
| Hubungan 2 variabel | `scatter` (+ trend line, ukuran = variabel ke-3) |
| Pola 2 dimensi (hari × jam) | `heatmap` |
| Dekomposisi kenaikan/penurunan | `waterfall` |
| Skor vs target | `gauge` |
| Profil multi-dimensi | `radar` (maks 3 subjek, 4–8 sumbu) |
| Relasi antar entitas | `network` |
| Jadwal/linimasa tugas | `gantt` (warna RAG, % aktual, garis hari ini) |
| Progres vs target per item | `progress` (bullet bar + garis target) |
| Tren mini di dalam kartu | `sparkline` |

---

## F. Aturan desain infografik (wajib)

1. **Satu pesan utama** di judul; sisanya pendukung.
2. **Maks 8–12 chart** per halaman. Lebih dari itu → pecah jadi 2 halaman.
3. **Urutkan** bar berdasarkan nilai (descending), kecuali sumbu waktu/kategori baku.
4. **Sumbu dimulai dari 0** untuk bar. Bila line terpaksa dipotong, beri label jelas.
5. **Label nilai langsung di chart** agar tidak perlu membaca sumbu.
6. **Warna = makna**, bukan hiasan: hijau baik, kuning waspada, merah buruk; sisanya netral.
7. **Kontras & keterbacaan**: teks ≥ 11px pada lebar 640px; jangan pakai merah-hijau saja
   (buta warna) — tambah ikon/label.
8. **Sumber & tanggal** selalu di footer, plus catatan metodologi.
9. **Self-contained**: tanpa CDN/font eksternal (SVG + CSS inline).
10. **QA sebelum serahkan**:
```bash
python3 _validate_svg.py  ../../../deliverables/infographic.html   # XML valid
python3 _check_layout.py  ../../../deliverables/infographic.html   # 0 elemen keluar kanvas
```

## G. Etika visualisasi
Jangan: memotong sumbu bar untuk membesar-besarkan, cherry-pick rentang waktu,
dual-axis yang menyesatkan, 3D pie, atau warna yang menyamarkan kategori penting.
Bila data tidak lengkap, tulis di footer: *"Data tidak mencakup …"*.
