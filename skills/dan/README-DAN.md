# DAN — Agen Marketing Multi-Skill

Paket **Agent Skill** siap pakai: satu agen dengan sembilan sub-skill yang bisa
dipanggil terpisah atau dirangkai jadi satu pipeline — dari data mentah sampai materi
kreatif siap tayang, dimonitor & dicoach, plus advis arsitektur software dan bangunan.

```
DATA MENTAH → ANALISA → INSIGHT → STRATEGI → INFOGRAFIK → KONTEN → EKSEKUSI
                                                                    ↓
                                   MONITORING / TRACKING / PROGRESS / CONTROLLING
                                                                    ↓
                          ARSITEKTUR (software & bangunan) + COACHING BERBASIS DATA
```

---

## Isi paket

```
skills/dan/
├── SKILL.md          ← orchestrator: kapan memakai sub-skill mana + pipeline
├── AGENT.md          ← persona & system prompt siap salin ke runtime lain
├── skills/           ← 21 sub-skill (marketing 01-09 + keterampilan AI 10-21)
│   ├── 01-marketing-data-analyst/    KPI, funnel, tren, anomali, korelasi, forecast
│   ├── 02-marketing-strategist/      STP, positioning, budget, campaign plan, A/B test
│   ├── 03-data-to-infographic/       18 tipe chart + infografik + graph/network analyst
│   ├── 04-image-video-creator/       storyboard bertiming, prompt image/video, SRT
│   ├── 05-design-engineer-2d-3d/     brief desain, spec produk/kemasan, sketsa 3D
│   ├── 06-motivator-coach/           Motivator EXPERT: GROW, SDT, Progress Principle, OARS
│   ├── 07-project-monitoring-controlling/  monitoring, tracking, progress, controlling, form
│   ├── 08-software-architecture/     scaffold multi-bahasa, review pro/kon, trade-off
│   ├── 09-architectural-design/      denah 2D, massa 3D, tampak, KDB/KLB, RAB, konstruksi
│   ├── 10-prompt-engineering/        lint/skor/perbaiki/varian prompt (prompt_lab.py)
│   ├── 11-ai-workflow-automation/    workflow terdeklarasi antar-engine (workflow.py)
│   ├── 12-ai-agents/                 kartu agent, pola multi-agent, tool ber-izin
│   ├── 13-rag-retrieval/             RAG stdlib bersitasi (rag.py)
│   ├── 14-multimodal-ai/             QC & prompt gambar/audio/video/dokumen
│   ├── 15-custom-ai-assistants/      spec -> prompt+tools+evaluation (assistant_builder.py)
│   ├── 16-voice-ai-avatars/          naskah TTS, konsistensi suara, brief avatar
│   ├── 17-ai-tool-stacking/          rekomendasi stack AI + biaya (stack_advisor.py)
│   ├── 18-ai-video-content/          storyboard -> cut-list -> subtitle -> QC
│   ├── 19-ai-app-saas/               MVP spec, unit economics, launch checklist
│   ├── 20-llm-observability/         trace JSONL + pass-rate/biaya/latensi (llm_obs.py)
│   └── 21-staying-updated/           digest berjadwal + aturan adopsi-vs-tunggu
├── references/       ← 9 pustaka pengetahuan (metrik, chart, framework, brand, prompt,
│                        design spec, motivation, software-arch, architectural-design)
├── scripts/          ← 10 engine yang bisa dijalankan + 5 skrip QA
└── templates/        ← 11 dokumen siap isi (incl. 3 form, projects & building example)
```

## Engine yang bisa dijalankan

| Script | Fungsi | Dependensi |
|---|---|---|
| `dan_analytics.py` | CSV/XLSX → KPI, agregasi, tren, forecast, anomali, Pareto, korelasi, health score → JSON + Markdown + CSV | stdlib (openpyxl utk XLSX) |
| `svg_charts/` | Paket 18 tipe chart sebagai SVG murni (bar, line, donut, funnel, radar, scatter, heatmap, waterfall, gauge, network, **gantt**, **progress**, sparkline, dll.) | **tanpa dependensi** |
| `make_infographic.py` | JSON → infografik HTML self-contained + poster SVG | tanpa dependensi |
| `graph_analyst.py` | PageRank, betweenness, closeness, eigenvector, HITS, komunitas → JSON + SVG + laporan | networkx opsional |
| `storyboard.py` | Brief → shot list bertiming, naskah VO, prompt image/video per shot, caption, `.srt` | tanpa dependensi |
| `fit_asset.py` | Crop/pad aset gambar ke rasio platform (9:16, 4:5, 16:9, …) | Pillow opsional |
| `project_monitor.py` | Monitoring/tracking/progress/controlling: variance, SPI, RAG, stalled, earned value, forecast, Gantt dashboard, `coach` | tanpa dependensi |
| `make_forms.py` | Form interaktif self-contained: progress / monitoring / controlling → batch JSON | tanpa dependensi |
| `arch_advisor.py` | Scaffold proyek multi-bahasa (python/node/ts/go/php × api/cli/worker) · review kode → kelebihan/kekurangan + skor · compare trade-off pola/DB/bahasa/hosting + rekomendasi ber-konteks | tanpa dependensi |
| `arch_design.py` | Denah 2D per lantai, massa 3D isometrik, tampak depan, KDB/KLB, RAB, jadwal material, tahapan konstruksi, prompt render interior/eksterior | tanpa dependensi |
| `exec_dashboard.py` | Dashboard eksekutif GABUNGAN: marketing + proyek + portofolio bangunan dalam satu infografik | tanpa dependensi |
| `weekly_run.py` | Otomasi ritme mingguan: apply update form → report → coach → exec dashboard → ringkasan 1 halaman siap cetak | tanpa dependensi |
| `pmo_guard.py` | Policy-as-code gate: tugas kritis/stalled/terlambat & CPI buruk wajib punya tindakan/update, иначе exit≠0 untuk CI/cron | tanpa dependensi |
| `make_slides.py` | Slide deck HTML self-contained (9 slide, chart SVG inline, navigasi panah, cetak=PDF) | tanpa dependensi |
| `claim_audit.py` | Validator provenance angka: setiap klaim numerik di laporan dicocokkan ke sumber JSON; yang tak cocok ditandai untuk tinjauan; `--fail-under` utk gate CI | tanpa dependensi |
| `dan.py` | Unified CLI: `list` · `run <engine>` · `new <template> --set k=v` · `audit` · `doctor` | tanpa dependensi |
| `run_cases.py` | Runner katalog kasus end-to-end (`list` / `run <nama>` / `run all`) — demo, onboarding, sekaligus integration test | tanpa dependensi |
| `i18n.py` | Label struktural ID/EN untuk ringkasan mingguan & slide (`--lang en`); narasi tetap bahasa sumber | tanpa dependensi |
| `i18n_queue.py` | Antrean terjemahan NARASI: extract baris narasi ber-id → terjemahkan (manusia/agent) → apply; menghindari terjemahan mesin buta | tanpa dependensi |
| `export_png.py` | SVG/HTML → PNG memakai renderer opsional (cairosvg/rsvg/inkscape/chromium); tanpa renderer → exit 2 + petunjuk jelas | renderer opsional |
| `make_pyz.py` | Kemas seluruh engine + template jadi SATU file `dan.pyz` yang jalan di mesin mana pun ber-python3 (zipapp) | tanpa dependensi |
| `make_package.py` | Kemas paket: manifest sha256, `dan-skill-<v>.zip`, INSTALL.md, CHANGELOG | tanpa dependensi |
| `demo_tour.py` | Tur onboarding satu perintah (`dan.py demo`): cuplikan hidup sub-skill 01-21 | tanpa dependensi |
| `rag_eval.py` | Eval retrieval RAG terukur: recall@1/@5, MRR, laporan miss lexical vs synonym | tanpa dependensi |
| `make_digest.py` | Digest rilis 5 baris + rincian area + checklist + naskah audio briefing | tanpa dependensi |
| `make_adapters.py` | Ekspor plug-and-play: Claude/Cursor/Gemini/ChatGPT/Copilot/AGENTS.md + SYSTEM_PROMPT | tanpa dependensi |
| `mcp_server.py` | Server MCP stdio (10 tool) — pasang di Claude, Cursor, Gemini CLI, dll | tanpa dependensi |
| `mcp_smoke.py` | Uji integrasi nyata: initialize→tools/list→tools/call semua tool, verifikasi keluaran | tanpa dependensi |
| `notify.py` | Notifikasi ritme mingguan (telegram/slack/email/stdout) yang mengisi diri dari summary+guard; tanpa mengirim (curl contoh disertakan) | tanpa dependensi |
| `burnup.py` | Burn-up multi-periode (Aktual vs Rencana) dari riwayat append-only + deteksi stagnasi | tanpa dependensi |
| `budget_sim.py` | Simulator what-if realokasi budget: Monte-Carlo p10/p50/p90 + aturan kelayakan worst-case | tanpa dependensi |
| `weekly.py` | SATU perintah ritme mingguan: weekly_run→snap→burnup→guard→notify→digest→audit (+narrative); cron-ready, exit≠0 bila guard gagal | tanpa dependensi |
| `narrative_check.py` | Pemeriksa narasi: klaim kausal tanpa uji, overclaim, proyeksi tanpa penanda, superlatif, person-blame + saran perbaikan | tanpa dependensi |
| `annotate.py` | Lapisan komentar review (localStorage + ekspor/impor JSON) pada deliverable HTML — loop review tim tanpa server | tanpa dependensi |
| `client_report.py` | Laporan versi klien (ID/EN): narasi bahasa manusia + arti dalam rupiah + glosarium, angka tetap tertelusur | tanpa dependensi |
| `export_pdf.py` | HTML/SVG → PDF headless bila chromium/wkhtmltopdf/weasyprint ada; tanpa renderer → exit 2 + petunjuk jelas | renderer opsional |
| `pkg_health.py` | Dashboard kesehatan paket: scorecard rilis + tren test/refs/ukuran dari `qa_history.jsonl` | tanpa dependensi |
| `release.py` | Rilis ber-gate satu perintah: test→cases→refs→adapters→package→digest→health; gagal di gate = rilis dihentikan | tanpa dependensi |
| `print_deck.py` | Deck rapat pimpinan cetak A4 landscape (5 halaman) dari data yang sama dengan exec_dashboard | tanpa dependensi |
| `init_wizard.py` | Wizard onboarding ≤5 pertanyaan (sektor→data→keluaran pertama); interaktif atau via flag untuk CI | tanpa dependensi |
| `weekly_watch.py` | Watchdog cron mingguan: release dry-run + skor paket + PMO guard + drift QA; exit 1 bila drift | tanpa dependensi |
| `showcase.py` | Galeri satu halaman (showcase.html di root) yang mengindeks seluruh artefak contoh | tanpa dependensi |
| `narrative_trend.py` | Eval berkelanjutan kualitas tulisan: narrative_check+claim_audit per laporan → riwayat append-only + tren | tanpa dependensi |
| `make_bundle.py` | Bundle offline: `dan.pyz` + examples + adapters + docs + INSTALL-OFFLINE (tanpa pip, tanpa jaringan) | tanpa dependensi |
| `multi_client.py` | Dashboard gabungan lintas-klien: tabel perbandingan + tab per klien (filter tanpa reload) | tanpa dependensi |
| `make_sop.py` | SOP/runbook operasional: cadence harian→kuartalan, matriks RACI, aturan eskalasi, definisi selesai | tanpa dependensi |
| `crisis_sim.py` | Simulasi krisis (budget cut, channel mati, stok habis, reputasi) dengan dampak terukur + respons 0-24j/24-72j/minggu-2 | tanpa dependensi |
| `sec_audit.py` | Audit keamanan ringan: secret tertanam, pola berisiko (eval/exec/pickle/shell), http://, izin file longgar; gate rilis `--with-sec` | tanpa dependensi |
| `make_course.py` | Paket pelatihan: deck slide + naskah audio ber-timestamp (TTS-ready) + petunjuk produksi | tanpa dependensi |
| `notify.py --send` | Kirim sungguhan via Telegram/Slack/SMTP **hanya** bila kredensial ada di environment (tidak pernah disimpan) | stdlib urllib/smtplib |
| `make_sample_data.py` | Generator data demo 90 hari × 6 channel untuk uji coba | tanpa dependensi |
| `prompt_lab.py` | Lint/skor/grade prompt, saran berprioritas, kerangka ulang, varian pembingkaian | tanpa dependensi |
| `workflow.py` | Runner workflow JSON antar-engine: kondisi, retry, on_fail, audit `workflow_run.json` | tanpa dependensi |
| `rag.py` | RAG stdlib: indeks chunk ber-heading + TF-IDF cosine + jawaban bersitasi | tanpa dependensi |
| `stack_advisor.py` | Rekomendasi stack tool AI (10 kategori) + biaya bulanan + risiko | tanpa dependensi |
| `assistant_builder.py` | Spec asisten → system prompt + manifest tool + eval set + README | tanpa dependensi |
| `llm_obs.py` | Trace append-only JSONL + laporan pass-rate/biaya/latensi + alarm | tanpa dependensi |
| `weekly_diff.py` | Riwayat append-only (snap) + diff antar-minggu (delta progres/RAG/stalled) | tanpa dependensi |
| `demo_tour.py` | Tur onboarding satu perintah: cuplikan hidup tiap sub-skill 01-21 (`dan.py demo`) | tanpa dependensi |
| `rag_eval.py` | Eval retrieval RAG terukur: recall@1/@5, MRR, laporan miss (lexical vs synonym) | tanpa dependensi |
| `make_digest.py` | Digest rilis 5 baris + rincian area + checklist minggu + naskah audio briefing | tanpa dependensi |

QA: `_test_all.py` (smoke test terpadu, 125 pemeriksaan incl. property-based, pyz, & engine AI 10-21) · `run_cases.py run all` (3 kasus end-to-end) · `dan.py doctor` (sekali jalan: test+refs+parser) · `_validate_svg.py` (XML valid) ·
`_check_layout.py` (elemen keluar kanvas) · `_check_refs.py` (referensi silang dokumen) ·
`_test_graph.py` (cross-check metrik graph vs networkx) · `dan_analytics.py x --test`
(parser angka).

---

## Mulai dalam 5 perintah

```bash
cd skills/dan/scripts

# 1) data demo (lewati bila sudah punya CSV sendiri)
python3 make_sample_data.py --days 90

# 2) ANALISA → deliverables/analysis.{json,md} + summary_channel.csv
python3 dan_analytics.py ../../../data/sample_campaign.csv --currency Rp --forecast 7 \
  --summary-csv ../../../deliverables/summary_channel.csv

# 3) INFOGRAFIK → deliverables/infographic.html + poster SVG
python3 make_infographic.py ../../../deliverables/analysis.json --theme dan --paper a3 \
  --svg deliverables/infographic_poster.svg

# 4) GRAPH ANALYST → deliverables/graph.{json,svg,md}
python3 graph_analyst.py --demo

# 5) STORYBOARD VIDEO → deliverables/storyboard_*.{md,json,srt}
python3 storyboard.py --brief ../templates/storyboard-brief.example.json

# 6) MONITORING PROYEK → forms.html + report + dashboard + coach
python3 make_forms.py --projects ../templates/projects.example.json \
    --out ../../../deliverables/forms.html
python3 project_monitor.py report ../templates/projects.example.json
python3 project_monitor.py coach  ../templates/projects.example.json
```

QA (satu perintah untuk semua):

```bash
python3 _test_all.py      # 73 pemeriksaan: parser, semua chart, spec+auto mode,
                          # storyboard, graph vs networkx, layout, monitoring, forms
```

Skrip QA terpisah bila butuh detail: `_validate_svg.py` (XML valid) ·
`_check_layout.py` (elemen keluar kanvas) · `_check_refs.py` (referensi silang dokumen) ·
`_test_graph.py` (cross-check networkx) · `dan_analytics.py x --test` (parser angka).

---

## Akses dari VS Code lokal
Buka folder repo di VS Code: `.vscode/` menyediakan tasks (QA penuh, demo, kasus,
ritme mingguan, adapter, MCP smoke), launch config, snippet, dan `mcp.json` untuk
Copilot agent mode. Multi-root: buka `dan.code-workspace`. Detail: `PLUGPLAY.md` §5b.

## Contoh pemanggilan per sub-skill

**01 · Data Analyst** — "analisa data iklanku, kenapa ROAS turun?"
→ jalankan `dan_analytics.py file.csv`, serahkan `analysis.md` + 3 insight ber-aksi.

**02 · Strategist** — "buatkan strategi marketing budget Rp50 juta"
→ isi `templates/strategy-brief.md`, hitung break-even ROAS & CPA maksimum,
buat 3 skenario (konservatif/dasar/agresif).

**03 · Infographic** — "bikin infografik dari data ini"
→ `dan_analytics.py` lalu `make_infographic.py`. Untuk data bebas pakai mode SPEC
(`templates/data-spec.example.json`). Untuk data relasi (KOL/referral/keyword)
→ `graph_analyst.py --edges relasi.csv`.

**04 · Image & Video** — "buatkan konsep video TikTok 30 detik"
→ `storyboard.py --brief …`. Ambil template prompt dari
`references/prompt-library-image-video.md`.

**05 · Design Engineer** — "buatkan brief kemasan & sketsa 3D"
→ pakai `references/design-engineering-spec.md` (dimensi, material, toleransi,
dieline, 6 tipe sketsa 3D, prompt render).

**06 · Motivator Expert** — "tim lagi down setelah kampanye gagal" / "coaching 1-on-1"
→ kerangka GROW / SDT / Progress Principle / OARS dari `references/motivation-playbook.md`;
bila ada `projects.json`, jalankan `project_monitor.py coach` agar pesan berbasis fakta
(variance, stalled, beban owner), lalu sampaikan lisan — bukan ditempel mentah di grup.

**07 · Project Monitoring/Controlling** — "proyek mana yang terlambat?" / "buat dashboard PMO"
→ `project_monitor.py report` (Gantt tracking, progress vs rencana, burn-up, matriks risiko,
beban owner, forecast, CPI/EAC). Tim mengisi `forms.html` (progress/monitoring/controlling)
→ `apply` → `report` ulang. Ritme governance mingguan ada di sub-skill 07.

**08 · Software Architecture** — "monolith atau microservices?" / "review kode saya"
→ `arch_advisor.py compare --group pattern --a monolith --b microservices --team 4 …`
(tabel 6 kriteria + pros/cons + rekomendasi), `review path/` (kelebihan/kekurangan +
prioritas), `scaffold --lang go --pattern api` (kerangka berjalan).

**09 · Architectural Design** — "buatkan denah rumah 2 lantai + RAB"
→ isi `templates/building.example.json` lalu `arch_design.py`. Hasil: denah 2D per lantai,
massa 3D isometrik, tampak depan, KDB/KLB, RAB ±25%, tahapan konstruksi, prompt render
(eksekusi render lewat sub-skill 04 / image generator).

---

## Aturan kerja DAN

1. **Jangan mengarang angka** — setiap angka tertelusur; asumsi ditandai `asumsi:`.
2. **Selalu ada "so what"** — tiap temuan diikuti 1 aksi terukur + tenggat.
3. **Format angka Indonesia** (`1.234.567`, desimal koma) kecuali diminta lain.
4. **Deliverable self-contained** — SVG & CSS inline, tanpa CDN, tampil di viewer offline.
5. **Verifikasi sebelum serahkan** — QA = 0 error, 0 elemen keluar kanvas.
6. **Sebut keterbatasan** — ukuran sampel, periode, risiko interpretasi.
7. **Etika** — tanpa klaim menyesatkan, tanpa meniru identitas orang/merek,
   grafik tidak boleh memanipulasi (sumbu dipotong harus diberi label).

> **Catatan teknis workspace:** simpan hasil di `deliverables/`.
> Folder bernama `output/`, `build/`, atau `dist/` diabaikan snapshot sehingga file
> di dalamnya bisa "hilang" antar sesi.

---

## Status verifikasi

`python3 _test_all.py` → **97 lulus, 0 gagal** · `python3 _check_refs.py` → **0 hilang**

| Uji | Hasil |
|---|---|
| Parser angka lintas format (ID/EN/mata uang/persen/singkatan) | 25/25 kasus lulus |
| 28 varian chart (18 tipe incl. Gantt & progress + tema + locale + gap) | semua XML valid |
| Infografik mode SPEC | 11/11 chart ter-render, self-contained |
| Infografik mode AUTO | 15 SVG valid, insight lengkap dengan aksi |
| Layout semua SVG pada artefak | 0 teks keluar kanvas, 0 gagal parse |
| Metrik graph vs networkx (betweenness, closeness, eigenvector, PageRank) | deviasi 0,0000 · PageRank berjumlah 1,000 |
| Storyboard | durasi tepat 30,0 s · VO kalimat utuh · tanpa tumpang tindih · deterministik · shot type koheren per beat |
| fit_asset (crop/pad ke rasio platform) | 9:16, 4:5, 16:9, 1:1 presisi ±0,002 · mode pad tanpa memotong |
| Project monitoring | deteksi stalled/terlambat/kritis benar · RAG konsisten · forecast & earned value terisi · apply progress/controlling mengubah model + history |
| Form interaktif | 3 tab ada · contoh tertanam · self-contained · sintaks JS lolos `node --check` · logika planned/RAG identik dengan engine Python |
| Software architecture | 6 kombinasi scaffold menghasilkan file berjalan (syntax/JSON valid) · review deteksi rahasia/TODO/skor · compare winner & skor konsisten · opsi tak dikenal → error ramah |
| Architectural design | 2 lantai/12 ruang tanpa overlap · bbox konsisten · KDB/KLB terhitung · RAB total = Σ komponen · SVG denah/massing/tampak valid |
| Referensi silang seluruh dokumen | 0 hilang |

_Dibangun sebagai paket skill DAN. Baca `skills/dan/SKILL.md` untuk detail routing._
