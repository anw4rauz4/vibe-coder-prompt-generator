# CHANGELOG — paket skill DAN

Format: https://keepachangelog.com · versi mengikuti semver.

## 2.1.0 — 2026-09-17
- Tur onboarding `demo_tour.py` (+ `dan.py demo`): cuplikan hidup sub-skill 01–21.
- `rag_eval.py` + gold-set 18 pertanyaan: recall@1/@5 & MRR terukur; miss dilaporkan jujur.
- `make_digest.py`: digest rilis 5 baris + rincian area + checklist + naskah audio briefing.
- Perbaikan dokumen: chart `gantt`/`progress` kini disebut di sub-skill 03 & 07
  (ditemukan lewat miss Q13 pada rag_eval).

## 2.0.0 — 2026-09-17
- 12 sub-skill keterampilan AI baru (10–21) sesuai kerangka "12 AI skills":
  prompt engineering, workflow automation, agents, RAG, multimodal, custom assistants,
  voice & avatars, tool stacking, video content, app/SaaS, observability, staying updated.
- Engine baru: `prompt_lab.py`, `workflow.py`, `rag.py`, `stack_advisor.py`,
  `assistant_builder.py`, `llm_obs.py`, `weekly_diff.py`.
- `dan.py` kini menampilkan 21 sub-skill & 28 engine.

## 1.6.0 — 2026-09-17
- `make_pyz.py`: paket single-file `dan.pyz` (zipapp) — jalan tanpa instalasi;
  `doctor` in-process & resolver template tahan-zip.
- `i18n_queue.py`: antrean terjemahan narasi (extract/apply) tanpa terjemahan mesin buta.
- `export_png.py`: renderer opsional (cairosvg/rsvg/inkscape/chromium) + fallback jujur.

## 1.5.0 — 2026-09-17
- Katalog kasus end-to-end `cases/` + `run_cases.py` (demo, onboarding, integration test).
- `i18n.py`: label struktural ID/EN untuk ringkasan mingguan & slide (`--lang`).

## 1.4.0 — 2026-09-17
- `claim_audit.py`: validator provenance angka (anti angka karangan) + gate `--fail-under`.
- `dan.py`: unified CLI (list/run/new/audit/doctor).

## 1.3.0 — 2026-09-17
- `weekly_run.py`: otomasi ritme mingguan (apply→report→coach→dashboard→ringkasan).
- `pmo_guard.py` + CI `weekly-pmo.yml`: policy gate (sinyal buruk wajib bertindakan).
- `make_slides.py`: slide deck HTML self-contained (cetak = PDF).

## 1.2.0 — 2026-09-16
- `exec_dashboard.py`: dashboard eksekutif gabungan marketing+proyek+arsitektur.
- `make_package.py`: manifest sha256 + zip siap-import + INSTALL.md.

## 1.1.0 — 2026-09-16
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture) & 09 (architectural design).
- `svg_charts` dipecah menjadi paket (ADR-004); chart `gantt` & `progress` ditambah.
- QA terpadu `_test_all.py`, property-based `props_test.py`, ADR-001..004, CI `dan-qa.yml`.

## 1.0.0 — 2026-09-16
- Rilis pertama: sub-skill 01–06 (data analyst, strategist, infographic/graph,
  image/video, design engineer, motivator), engine inti, template, dan referensi.

## 2.2.0 — 2026-09-17
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 2.3.0 — 2026-09-17
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 2.4.0 — 2026-09-17
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 2.5.0 — 2026-09-17
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 2.6.0 — 2026-09-17
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 2.7.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 2.8.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 2.9.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 3.0.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 3.1.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 3.2.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 3.3.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 3.4.0 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 3.5.0 — 2026-09-18
- `xlsx_lite.py`: pembaca .xlsx murni stdlib (nilai cache + formula, CSV/JSON dump) —
  tanpa openpyxl/pandas, jadi workbook klien bisa dibaca di mesin mana pun.
- `plan_analyst.py`: analis business plan distributor (omset per divisi vs target vs LY,
  metrik EA/CB/IPT, kanal & top produk, stock cover days, pencapaian salesman per periode,
  3 skenario proyeksi, rekonsiliasi tim↔divisi, temuan kualitas data DQ-01..14) →
  analysis.json/md, data_quality.md, spec_infografik.json, projects.json, 4 CSV.
- Indeks SKILL.md dirampingkan (−83% token); detail pindah ke `references/pipeline-runbook.md`
  dan dijaga probe regresi [29].
- `cost_router.py`: rute tugas ke model gratis/lokal/berbayar saat kuota menipis.
- QA: seksi [30] (18 pemeriksaan) membuat .xlsx sintetis lalu menguji round-trip, agregasi,
  RAG divisi, SCD, skema insight/proyek, dan ketahanan sheet hilang → 210 lulus, 0 gagal.
- `_check_refs.py`: whitelist nama keluaran runtime engine business-plan.

## 3.5.1 — 2026-09-18
- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).
- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).
- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).
- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.
- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.
- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.

## 3.6.0 — 2026-09-16
- Web hub DAN: `make_web.py` menghasilkan satu HTML self-contained (profil agent,
  katalog 21 sub-skill + 60 engine, 12 adapter, riwayat rilis/QA, tautan unduh) —
  data dibaca langsung dari paket sehingga situs selalu sinkron; tanpa CDN/tracker.
- 6 tools interaktif murni browser (versi mini engine DAN): kalkulator KPI marketing
  (CTR/CPC/CPM/CVR/CPA/ROAS/AOV + RAG), format Rupiah & singkatan rb/jt/M/T, BEP,
  alokator budget per-ROAS + proyeksi, pemeriksa narasi (superlatif/proyeksi tanpa ±),
  prompt lint 7 elemen — semua format angka Indonesia.
- `serve.py`: server lokal stdlib untuk situs + artefak deliverables (zip/pyz terunduh).
- QA: seksi [31] (7 pemeriksaan) — bangun situs ke dir sementara, verifikasi 7 tab,
  0 URL eksternal, blob data parse-able & sinkron (21 skill/>50 engine/adapters≥12).

## 3.6.1 — 2026-09-16
- `dan.py web` / `dan.py serve [port]`: bangun & sajikan situs hub DAN dari CLI terpadu;
  engine make_web/serve terdaftar di `dan.py list` kategori [web].

## 3.7.0 — 2026-09-16
- `memory.py` + `dan.py memory`: session_log memori persisten lintas-sesi (JSONL append-only;
  add/log/search/list/context/stats; tag keputusan/preferensi/fakta/tugas; tahan baris korup;
  `memory context` = markdown siap tempel ke sesi AI baru, hemat token).
- Web hub: 2 tools browser baru (total 8) — 📦 SCD Checker (stock cover days, RAG
  risiko-habis/sehat/overstock, hari stok habis, saran order ke target+safety) dan
  📈 Proyeksi Musiman (sisa bulan = periode sama tahun lalu × (1+growth YoY), selalu
  dengan rentang ± + pembanding target setahun penuh).
- QA: seksi [32] (7 pemeriksaan memory, termasuk integrasi dan.py) + probe [31] diperbarui
  menjadi 8 tools → 224 lulus, 0 gagal.
- SKILL.md: seksi "Memori lintas-sesi" + daftar perintah dan.py lengkap (memory|web|serve).

## 3.7.1 — 2026-09-16
- Hotfix `memory.py`: ROOT store default kini benar di `<repo>/data/session_log.jsonl`
  (sebelumnya salah resolve ke `skills/data/`); `--store` dipindah ke tiap subparser
  (pola parent-parser) agar valid di semua sub-perintah.
- QA: probe [32] tambah cek ROOT default store (= ROOT dan.py) → 225 lulus, 0 gagal.

## 3.8.0 — 2026-09-16
- Deploy GRATIS ke GitHub Pages: `publish_gh.py` + `dan.py deploy` — `prepare` membangun
  folder siap push (index.html ter-patch tautan unduh → files/, .nojekyll, 404.html,
  site.zip utk unggah-web tanpa git); `guide` mencetak panduan A (repo situs manual) /
  B (repo penuh + Actions otomatis).
- Workflow `.github/workflows/deploy-pages.yml`: build+deploy Pages tiap push ke main
  (gratis utk repo publik; sekali set Source: GitHub Actions).
- `DEPLOY-GITHUB.md` (root): panduan lengkap free-only + tabel batas gratis +
  troubleshooting + kebijakan "bayar nanti setelah semua OK".
- Web hub: tab Pasang menambah blok perintah deploy + catatan GitHub Pages gratis.
- QA: seksi [33] (8 pemeriksaan deploy) → 233 lulus, 0 gagal.
