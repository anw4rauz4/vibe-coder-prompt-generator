---
name: dan-llm-observability
description: >-
  Observabilitas pemanggilan LLM/agent tanpa vendor: trace append-only ke JSONL
  (prompt-id, model, token, biaya, latensi, pass/fail), laporan agregat (pass-rate,
  biaya total/rata-rata, latensi p50/p95, token rata-rata), dan alarm pass-rate
  rendah. Data milik sendiri, bisa diekspor spreadsheet. Gunakan saat pengguna
  bertanya "berapa biaya AI kami", "prompt mana yang sering gagal", "latensi kami
  wajar tidak", atau ingin QA berkelanjutan atas keluaran model.
---

# 20 · LLM Observability

## Prinsip
1. **Tidak ada optimasi tanpa pengukuran**: biaya & mutu per prompt-id, bukan rata-rata global.
2. Trace append-only & milik sendiri; vendor tools boleh menambah, bukan menggantikan.
3. Setiap prompt produksi punya **ambang pass-rate**; di bawah ambang = tiket, bukan gosip.

## Perintah
```bash
cd skills/dan/scripts
python3 llm_obs.py log --prompt-id ringkasan-mingguan --model gpt-4o \
    --tokens-in 4200 --tokens-out 900 --cost 0.031 --latency 4200 --pass true
python3 llm_obs.py report --traces deliverables/llm_traces.jsonl \
    --out deliverables/llm_obs_report.md --min-pass 80
```

## Metrik & ambang bawaan
| Metrik | Ambang awal | Aksi bila lewat |
|---|---|---|
| pass-rate per prompt | ≥80% | review instruksi+contoh; tambah eval kasus gagal |
| latensi p95 | ≤8000 ms | cache, model lebih kecil, atau stream |
| biaya/outcome | ≤4× harga jual unit | re-pricing atau optimasi prompt/context |
| token-in rata-rata | tren naik >20%/bulan | pangkas context/RAG top-k |

## Loop perbaikan (rutin mingguan)
```
report -> pilih prompt terburuk -> reproduksi kasus gagal
 -> perbaiki prompt (prompt_lab) -> eval ulang (eval_set sub-skill 15)
 -> catat perubahan (ADR/catatan) -> lanjut logging
```

## Integrasi
- Eval set & regression: sub-skill 15. Prompt QA: 10. Stack & biaya tool: 17.
- Otomasi ritme laporan: sub-skill 11 (tambahkan langkah log+report ke workflow).
