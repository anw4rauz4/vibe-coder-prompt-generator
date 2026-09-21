---
name: dan-ai-workflow-automation
description: >-
  Mengotomasikan pekerjaan berulang sebagai workflow terdeklarasi (JSON), bukan skrip
  rapuh: langkah antar-engine DAN dengan token {root}/{out}/{prev.*}, kondisi
  (file_exists), retry, dan kebijakan on_fail (skip/abort); hasil eksekusi tercatat
  (workflow_run.json) sehingga bisa diaudit & diulang. Gunakan saat pengguna meminta
  "otomatiskan proses ini", "jalankan pipeline tiap minggu", "rangkaian langkah tanpa
  perlu saya ingat urutan", atau integrasi antar tool internal.
---

# 11 · AI Workflow Automation

## Prinsip
1. **Otomasi = data**: workflow disimpan sebagai JSON ber-versi; perubahan = diff yang bisa direview.
2. Setiap langkah **idempoten atau ditandai**; retry hanya untuk langkah yang aman diulang.
3. Kegagalan harus **bersuara**: on_fail=abort untuk langkah kritis, skip untuk opsional.
4. Selalu ada artefak audit (`workflow_run.json`: status, exit, durasi, percobaan).

## Perintah
```bash
cd skills/dan/scripts
python3 workflow.py validate wf.json
python3 workflow.py run wf.json --out-dir deliverables/wf
```

## Skema langkah
```jsonc
{ "id": "analisa",                 // unik, untuk log & {prev.*}
  "engine": "dan_analytics",       // nama modul engine DAN
  "args": ["{prev.csv}", "--out", "{out}/a.json"],
  "retry": 1,                     // 0..3
  "on_fail": "skip",              // skip | abort
  "when": { "file_exists": "{out}/c.csv" },
  "save_as": "analysis" }         // menyimpan arg terakhir utk {prev.analysis}
```

## Resep workflow siap pakai
- **Ritme mingguan PMO**: make_sample/ingest → dan_analytics → make_infographic →
  project_monitor report → weekly_run → pmo_guard (abort bila gagal) → claim_audit.
- **Kasus demo/onboarding**: lihat `cases/` + `run_cases.py` (runner khusus ber-assert).
- **Produksi konten**: storyboard → fit_asset → (render eksternal) → claim_audit narasi.

## Menjadwalkan
- CI: `.github/workflows/weekly-pmo.yml` sudah menjalankan ritme mingguan + guard.
- Lokal: cron `0 7 * * 1 cd …/scripts && python3 workflow.py run wf.json`.

## Integrasi & batas
- Engine tersedia: lihat `dan.py list`.
- Workflow TIDAK mendukung paralel/cabang kompleks sengaja: urutan linear + kondisi
  mencakup 95% kebutuhan dan jauh lebih mudah diaudit. Bila butuh DAG sejati,
  pertimbangkan tools orchestration eksternal (lihat sub-skill 17).
