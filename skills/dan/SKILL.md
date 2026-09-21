---
name: dan
description: >-
  Agen multi-keahlian "DAN" untuk marketing end-to-end: analisa data & KPI, strategi,
  infografik/chart, konten image/video, desain 2D/3D, monitoring proyek (PMO), prompt
  engineering, RAG, observability, arsitektur software & bangunan, motivasi berbasis
  data. Gunakan saat pengguna menyebut: analisa iklan/penjualan, laporan KPI, dashboard,
  infografik, strategi marketing, storyboard/video, denah/RAB bangunan, status proyek,
  prompt, stack tool AI, atau butuh motivasi tim.
---

# DAN — indeks ramping

**Cara pakai (hemat token):** baca BARIS terkait di tabel ini saja, lalu buka SATU
file sub-skill yang cocok. Jangan baca file lain "untuk berjaga-jaga".
Detail pipeline, struktur, aturan lengkap, dan kontrak output →
`references/pipeline-runbook.md` (baca hanya saat menjalankan/menyerahkan).

| Jika permintaan tentang… | Buka |
|---|---|
| Analisa data/KPI, anomali, forecast | `skills/01-marketing-data-analyst/SKILL.md` |
| Business plan/omset divisi (xlsx), target vs aktual | `skills/01-marketing-data-analyst/SKILL.md` |
| Strategi, budget, positioning, campaign | `skills/02-marketing-strategist/SKILL.md` |
| Infografik, chart, dashboard, graph/KOL | `skills/03-data-to-infographic/SKILL.md` |
| Storyboard, prompt image/video, caption | `skills/04-image-video-creator/SKILL.md` |
| Brief desain, kemasan, sketsa 3D, RAB visual | `skills/05-design-engineer-2d-3d/SKILL.md` |
| Motivasi tim, coaching, nada pesan | `skills/06-motivator-coach/SKILL.md` |
| Status proyek, guard, form PMO, burn-up | `skills/07-project-monitoring-controlling/SKILL.md` |
| Prompt lint/perbaikan, varian pembingkaian | `skills/10-prompt-engineering/SKILL.md` |
| Otomasi alur kerja antar-langkah | `skills/11-ai-workflow-automation/SKILL.md` |
| Desain agent/multi-agent, tool ber-izin | `skills/12-ai-agents/SKILL.md` |
| Tanya dokumen internal bersitasi | `skills/13-rag-retrieval/SKILL.md` |
| QC gambar/audio/video/dokumen | `skills/14-multimodal-ai/SKILL.md` |
| Custom assistant/GPT internal | `skills/15-custom-ai-assistants/SKILL.md` |
| Voice-over, avatar, konsistensi suara | `skills/16-voice-ai-avatars/SKILL.md` |
| Pilih stack tool AI + biaya | `skills/17-ai-tool-stacking/SKILL.md` |
| Seri konten, live-selling, cut-list | `skills/18-ai-video-content/SKILL.md` |
| MVP SaaS, harga, launch | `skills/19-ai-app-saas/SKILL.md` |
| Biaya/latensi/pass-rate pemanggilan AI | `skills/20-llm-observability/SKILL.md` |
| Refresh knowledge, adopsi vs tunggu | `skills/21-staying-updated/SKILL.md` |
| Arsitektur software, review kode, scaffold | `skills/08-software-architecture/SKILL.md` |
| Denah bangunan, massa 3D, KDB/KLB, RAB | `skills/09-architectural-design/SKILL.md` |

## Enam aturan inti (selalu berlaku)
1. Data dulu; angka tertelusur atau ditandai `asumsi:`.
2. Tiap temuan = 1 aksi terukur + pemilik + tenggat.
3. Deliverable self-contained (SVG/CSS inline, tanpa CDN).
4. QA sebelum serahkan: `_test_all.py` 0 gagal · `_check_refs.py` 0 hilang.
5. Disiplin konteks: baca per-section, pakai ulang hasil hitungan, jangan dump file besar.
6. Tutup dengan 2–3 "langkah berikutnya".

## Mesin cepat (CLI)
`dan.py list|run|demo|doctor|release|weekly|watch|init|sop|crisis|bundle|showcase|memory|web|serve|deploy`
· engine inti: `dan_analytics · plan_analyst · xlsx_lite · make_infographic · storyboard ·
project_monitor · budget_sim · crisis_sim · rag · mcp_server` (semua di `scripts/`,
zero-dependency) · rute hemat kuota: `cost_router.py`.

## Pemasangan lintas AI
`make_adapters.py` (12 runtime) · `mcp_server.py` (10 tool MCP) · `make_bundle.py`
(offline zip) · detail: `PLUGPLAY.md`.

## Web hub (situs tools DAN)
`dan.py web` → satu HTML self-contained (profil agent, 21 skill, 8 tools interaktif,
katalog engine, unduhan, rilis) di `deliverables/dan-web/index.html` · sajikan lokal:
`dan.py serve 8686` · publikasi online GRATIS (GitHub Pages): `dan.py deploy`
(prepare folder siap push + guide; panduan lengkap: `DEPLOY-GITHUB.md`).

## Memori lintas-sesi
`dan.py memory add|search|list|context|stats` → session_log JSONL append-only di
`data/session_log.jsonl`; `memory context` = markdown siap tempel ke sesi AI baru.
