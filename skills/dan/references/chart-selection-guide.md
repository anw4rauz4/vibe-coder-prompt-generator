# Chart Selection Guide — Memilih Visual yang Benar

Rujukan untuk sub-skill **03**. Cocokkan **pertanyaan bisnis** → chart → fungsi di paket `svg_charts`.

## 1. Tabel keputusan cepat

| Pertanyaan yang ingin dijawab | Chart | Fungsi | Catatan |
|---|---|---|---|
| Mana yang paling besar/kecil? | Bar vertikal | `bar` | ≤12 kategori; urutkan menurun |
| Label kategorinya panjang? | Bar horizontal | `hbar` | paling mudah dibaca |
| Bagaimana perubahan terhadap waktu? | Line | `line` | ≥4 titik waktu |
| Seberapa besar volumenya seiring waktu? | Area | `area` / `line(area=True)` | 1–2 seri saja |
| Bandingkan beberapa seri dalam waktu | Multi-line | `line(compare={...})` | maks 4 seri |
| Apa komposisinya? | Donut | `donut` | ≤6 kategori; selain itu pakai bar |
| Komposisi berubah antar periode? | Stacked bar | `stacked_bar` | pakai `pct=True` untuk 100% |
| Di mana bocornya? | Funnel | `funnel` | sertakan % drop tiap tahap |
| Apakah dua hal berhubungan? | Scatter | `scatter` | aktifkan `trend=True` (r ditampilkan) |
| Ada pola waktu × kategori? | Heatmap | `heatmap` | mis. hari × jam posting |
| Kenapa nilainya berubah dari A ke B? | Waterfall | `waterfall` | bridge/dekomposisi |
| Seberapa dekat dengan target? | Gauge | `gauge` | 1 metrik saja |
| Bagaimana profil multi-dimensi? | Radar | `radar` | ≤3 subjek, 4–8 sumbu |
| Siapa terhubung dengan siapa? | Network | `network` | pakai `graph_analyst.py` |
| Tren mini dalam kartu KPI | Sparkline | `sparkline` | tanpa sumbu |
| Angka pasti harus dibaca | Tabel | HTML `<table>` | jangan paksa jadi chart |

## 2. Kesalahan yang paling sering terjadi

| Kesalahan | Akibat | Perbaikan |
|---|---|---|
| Pie/donut >6 slice | tidak terbaca | grouped bar / tabel |
| Sumbu bar tidak dari 0 | membesar-besarkan | mulai dari 0, atau pakai line |
| Dual axis tanpa label | menyesatkan | hindari; pecah jadi 2 chart |
| Line terlalu banyak seri | spaghetti | maks 4, sisanya tabel |
| 3D pada pie/bar | distorsi persepsi | selalu 2D |
| Warna pelangi tanpa makna | fokus hilang | warna = kategori/semantik |
| Label nilai dilewat | pembaca menebak | `show_values=True` |
| Chart tanpa judul & satuan | ambigu | judul + subtitle + satuan |
| Menampilkan semua data | tidak ada pesan | pilih chart yang menjawab pertanyaan |

## 3. Jumlah chart per media

| Media | Maks chart | Layout |
|---|---|---|
| Kartu KPI / thumbnail | 1 | gauge atau sparkline |
| Slide presentasi | 1 (maks 2) | satu pesan per slide |
| Infografik 1 halaman | 8–12 | grid 12 kolom, span 4/6/8 |
| Dashboard | 12–20 | hierarki: KPI → tren → detail |
| Laporan PDF | bebas | tiap bab 1 chart kunci |

## 4. Ukuran & span yang dipakai `make_infographic.py`

Grid 12 kolom. Rekomendasi span:

| Chart | span | width×height saran |
|---|---|---|
| Tren utama (line/area) | 8 | 880×380 |
| Gauge health | 4 | 380×230 |
| Donut komposisi | 4 | 520×360 |
| hbar ROAS/CPA | 4 | 520×360 |
| Funnel | 4 | 520×380 |
| Top kampanye (hbar) | 6 | 620×380 |
| Scatter spend vs ROAS | 6 | 620×380 |
| Bar pola hari/jam | 6 | 620×330 |
| Radar profil | 6 | 560×400 |
| Pareto | 6 | 620×340 |
| Network graph | 12 | 1100×620 |
| Tabel detail | 12 | — |

## 5. Resep siap pakai

**"Kenapa penjualan turun?"** → waterfall (dekomposisi) + line tren + hbar per channel
+ tabel anomali.

**"Channel mana yang harus discale?"** → scatter spend vs ROAS + hbar ROAS + stacked bar
kontribusi + tabel CPA.

**"Kapan harus posting?"** → heatmap hari×jam + bar pola hari.

**"Funnel mana yang bocor?"** → funnel + bar drop-off per tahap + line CVR harian.

**"Siapa KOL paling berpengaruh?"** → network (ukuran = PageRank) + hbar betweenness
+ tabel komunitas.

**"Apakah kampanye berhasil?"** → gauge health + line aktual vs target + donut kontribusi
+ kartu insight.

## 6. Aksesibilitas
- Kontras teks ≥ 4,5:1 terhadap latar.
- Jangan andalkan warna saja → tambah label/ikon/pola.
- Hindari pasangan merah-hijau murni untuk pembeda utama.
- Ukuran teks minimum 11px pada lebar 640px; 13px untuk body infografik.
- Sertakan versi tabel untuk chart penting (sudah otomatis di mode AUTO).
