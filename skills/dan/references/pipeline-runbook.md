# Runbook Pipeline & Kontrak Output DAN

Detail operasional yang dipindah dari `SKILL.md` agar indeks tetap ramping.
**Baca file ini hanya saat akan menjalankan pipeline atau menyerahkan deliverable.**

## 1. Pipeline lengkap (perintah siap pakai)

```bash
cd skills/dan/scripts

# 0) data demo (lewati bila punya data sendiri)
python3 make_sample_data.py --days 90

# 1) ANALISA -> analysis.json/md + summary_channel.csv
python3 dan_analytics.py <data.csv> --currency Rp --forecast 7 \
    --summary-csv <out>/summary_channel.csv

# 2) INFOGRAFIK -> infographic.html + poster SVG   (--lang id|en|zh)
python3 make_infographic.py <out>/analysis.json --theme dan --paper a3 \
    --svg <out>/infographic_poster.svg

# 3) GRAPH (bila ada data relasi)
python3 graph_analyst.py --demo | --edges relasi.csv | --graph net.json

# 4) KONTEN VIDEO
python3 storyboard.py --brief ../templates/storyboard-brief.example.json

# 5) MONITORING mingguan (satu perintah, ber-gate)
python3 weekly.py --projects projects.json --updates batch.json --channel slack

# 6) KEPUTUSAN: simulator budget & krisis
python3 budget_sim.py --analysis <out>/analysis.json --shift 20
python3 crisis_sim.py  --analysis <out>/analysis.json --stok 4000

# 7) QA sebelum menyerahkan (wajib)
python3 _test_all.py && python3 _check_refs.py
python3 claim_audit.py --report <out>/analysis.md --source <out>/analysis.json
python3 narrative_check.py --file <out>/weekly_summary.md
```

Urutan wajib untuk pekerjaan berbasis data: **1 → 2 → 7**. Langkah 3–6 sesuai kebutuhan.
Rilis paket: `python3 release.py --version X.Y.Z --with-sec` (8 gate).

## 2. Struktur direktori (ringkas)

```
skills/dan/
├── SKILL.md            indeks ramping (baca dulu, ≤2 k token)
├── AGENT.md            persona + system prompt siap salin
├── skills/NN-*/SKILL.md   21 sub-skill (baca HANYA yang relevan tugas)
├── references/*.md        pustaka mendalam (baca sesuai kebutuhan)
├── scripts/*.py           60+ engine CLI zero-dependency
├── templates/             dokumen & spec siap isi
├── cases/                 3 kasus end-to-end ber-assert
└── qa_history.jsonl       riwayat QA antar-rilis (append-only)
examples/  → contoh sektor fnb/fashion/b2b · adapters/ → 12 runtime · kursus/ → latihan
```

## 3. Aturan kerja (versi lengkap)

1. Data dulu, opini kemudian; angka tertelusur atau ditandai `asumsi:`.
2. Setiap temuan = 1 aksi terukur + pemilik + tenggat.
3. Format angka Indonesia default (`1.234.567`, desimal koma) kecuali diminta lain.
4. Deliverable self-contained: SVG+CSS inline, tanpa CDN.
5. Verifikasi sebelum serahkan: `_test_all.py` 0 gagal + `_check_refs.py` 0 hilang.
6. Sebut keterbatasan: ukuran sampel, periode, korelasi ≠ kausalitas.
7. Etika: tanpa klaim menyesatkan, tanpa meniru identitas, grafik tidak memanipulasi.
8. **Disiplin konteks:** jangan cat/dump file >200 baris ke percakapan; baca per-section
   (grep/`sed -n`); pakai ulang `analysis.json` antar sub-skill, jangan hitung ulang.
9. Secret hanya di environment; tidak pernah di file/repo/chat.
10. Tutup dengan "Langkah berikutnya" berisi 2–3 opsi.

## 4. Kontrak output per jenis permintaan

| Permintaan | Deliverable minimum |
|---|---|
| Analisa data | `analysis.md` + `analysis.json` + 3 insight ber-aksi |
| Strategi | `strategy-brief.md` terisi + alokasi budget + KPI & timeline |
| Infografik | `infographic.html` + ringkasan temuan di chat |
| Video/image | `storyboard_*.md/.json/.srt` + 5 varian hook |
| Desain 2D/3D | brief spesifikasi (dimensi, material, toleransi, format) |
| Monitoring | `weekly_summary.*` + guard status + burn-up |
| Laporan klien | `laporan_klien_<lang>.md` (bahasa manusia + glosarium) |
| Motivasi | 1 pesan utama + 3 langkah kecil + 1 angka penyemangat |

## 5. Plug-and-play (ringkas)

`make_adapters.py` → claude/cursor/gemini/chatgpt/copilot/windsurf/zed/continue/n8n/vscode.
`mcp_server.py` → 10 tool untuk klien MCP apa pun. `make_bundle.py` → offline zip.
Detail langkah per platform: `PLUGPLAY.md`.
