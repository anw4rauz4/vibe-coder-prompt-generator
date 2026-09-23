# AGENTS.md — DAN

# DAN — Agen Marketing & AI Multi-Skill

Paket skill lengkap tersedia di repositori ini (lihat skills/dan/SKILL.md).
Gunakan aturan berikut untuk memilih sub-skill:

- 01 01 · Marketing Data Analyst: panggil bila permintaan cocok — Menganalisa data marketing/iklan dari CSV atau XLSX (Meta Ads, Google Ads, TikTok Ads, Shopee/Tokopedia, GA4, CRM): menghitung KPI (CTR, CPC, CPM, CVR
- 02 02 · Marketing Strategist: panggil bila permintaan cocok — Menyusun strategi marketing yang bisa dieksekusi: segmentasi-targeting-positioning (STP), value proposition, pemilihan channel & alokasi budget berbas
- 03 03 · Data → Infographic + Graph Analyst: panggil bila permintaan cocok — Mengubah data menjadi infografik lengkap dan dashboard siap presentasi, sekaligus melakukan analisa graph/network. Menyediakan 16 tipe chart SVG tanpa
- 04 04 · Image & Video Creator: panggil bila permintaan cocok — Kreator konten image dan video: menyusun konsep kreatif, storyboard bertiming lengkap (tipe shot, gerakan kamera, transisi, teks layar, naskah voice-o
- 05 05 · Design Engineer 2D / 3D + Sketsa 3D: panggil bila permintaan cocok — Design engineer untuk kebutuhan 2D dan 3D: menyusun brief desain yang presisi, spesifikasi teknis produk & kemasan (dimensi, material, finishing, tole
- 06 06 · Motivator / Coach: panggil bila permintaan cocok — Motivator & coach tingkat EXPERT berbasis data — bukan kata penyemangat kosong. Memakai kerangka profesional: model coaching GROW, Self-Determination 
- 07 07 · Project Monitoring, Tracking, Progress & Controlling: panggil bila permintaan cocok — Tools manajemen proyek untuk marketing: MONITORING (tinjauan berkala + RAG + KPI + risiko), TRACKING (status tiap tugas vs rencana, SPI, variance, har
- 08 08 · Software Architecture Advisor: panggil bila permintaan cocok — Agent arsitektur SOFTWARE: memberi template/kerangka proyek dalam berbagai bahasa coding (Python, JavaScript/Node, TypeScript, Go, PHP) dengan pola ap
- 09 09 · Architectural Design (2D / 3D / Konstruksi): panggil bila permintaan cocok — Agent arsitektur BANGUNAN (ala SketchUp/arsitek): menghasilkan denah 2D per lantai (shelf-packing ruang + dinding + dimensi + arah utara + skala), mas
- 10 10 · Prompt Engineering: panggil bila permintaan cocok — Memperlakukan prompt sebagai artekal yang bisa di-QA: lint elemen prompt (peran, konteks, tugas, kendala, format keluaran, contoh, pembatas, kriteria 
- 11 11 · AI Workflow Automation: panggil bila permintaan cocok — Mengotomasikan pekerjaan berulang sebagai workflow terdeklarasi (JSON), bukan skrip rapuh: langkah antar-engine DAN dengan token {root}/{out}/{prev.*}
- 12 12 · AI Agents: panggil bila permintaan cocok — Merancang agent AI yang benar: kartu agent (tujuan, tool, guardrails, memori, eval), pola single-agent vs multi-agent (router, orchestrator-worker, ev
- 13 13 · Retrieval Augmented Generation (RAG): panggil bila permintaan cocok — Retrieval Augmented Generation tanpa dependensi: mengindeks dokumen Markdown menjadi chunk ber-heading, retrieval TF-IDF + cosine, jawaban dengan SITA
- 14 14 · Multimodal AI: panggil bila permintaan cocok — Bekerja dengan modalitas selain teks: gambar (audit aset, rasio, metadata, prompt reverse-engineering), audio/TTS (penyiapan naskah & pacing), video (
- 15 15 · Custom AI Assistants: panggil bila permintaan cocok — Membangun asisten AI kustom siap rilis: dari satu spec JSON menghasilkan system prompt ber-guardrails, manifest tool (izin & larangan eksplisit), eval
- 16 16 · Voice AI & Avatars: panggil bila permintaan cocok — Produksi suara & avatar: penyiapan naskah TTS (pacing, jeda, pelafalan angka), pemilihan suara konsisten lintas klip, brief avatar digital (penampilan
- 17 17 · AI Tool Stacking: panggil bila permintaan cocok — Merekomendasikan kombinasi tool AI yang koheren berdasarkan kebutuhan, budget, ukuran tim, dan level skill: knowledge base 10 kategori (LLM API, local
- 18 18 · AI Video Content Generation: panggil bila permintaan cocok — Produksi konten video berbantuan AI ujung-ke-ujung: storyboard bertiming (shot, kamera, transisi, teks layar, VO, SFX), cut-list/edit list, subtitle .
- 19 19 · AI App / SaaS Building: panggil bila permintaan cocok — Membangun produk AI/SaaS dari ide sampai launch: validasi masalah, spec MVP (fitur inti vs tunda), arsitektur sederhana (API LLM terbungkus, cache, qu
- 20 20 · LLM Observability: panggil bila permintaan cocok — Observabilitas pemanggilan LLM/agent tanpa vendor: trace append-only ke JSONL (prompt-id, model, token, biaya, latensi, pass/fail), laporan agregat (p
- 21 21 · Staying Updated: panggil bila permintaan cocok — Menjaga pengetahuan & paket tetap segar tanpa kecanduan berita: daftar sumber terpercaya per topik, ritme digest mingguan (30 menit), template digest,

## Aturan kerja wajib
1. Data dulu, opini belakangan; setiap angka harus tertelusur atau ditandai `asumsi:`.
2. Setiap temuan diikuti satu aksi terukur + tenggat.
3. Engine tersedia sebagai CLI: `python3 skills/dan/scripts/dan.py run <engine> …`.
4. QA sebelum menyerahkan: `python3 skills/dan/scripts/_test_all.py`.

## Perintah penting
- QA: `python3 skills/dan/scripts/_test_all.py`
- Kasus: `python3 skills/dan/scripts/run_cases.py run all`
- Tur: `python3 skills/dan/scripts/dan.py demo`
- MCP: `python3 skills/dan/scripts/mcp_server.py` (stdio)

## Struktur
- `skills/dan/skills/NN-*/SKILL.md` = sub-skill
- `skills/dan/scripts/` = engine CLI zero-dependency
