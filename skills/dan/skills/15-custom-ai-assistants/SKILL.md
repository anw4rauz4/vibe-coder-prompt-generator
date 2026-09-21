---
name: dan-custom-ai-assistants
description: >-
  Membangun asisten AI kustom siap rilis: dari satu spec JSON menghasilkan system
  prompt ber-guardrails, manifest tool (izin & larangan eksplisit), eval set (kasus
  lulus-sebelum-rilis + regression), dan README batas wewenang. Gunakan saat pengguna
  meminta "buatkan custom GPT/assistant untuk tim saya", "asisten internal dengan data
  kami", "persona bot layanan pelanggan", atau menstandarkan asisten lintas tim.
---

# 15 · Custom AI Assistants

## Prinsip
1. Asisten = system prompt + tool + guardrails + **eval**. Tanpa eval, rilis = tebakan.
2. Izin tool ditulis dua arah: yang diizinkan DAN yang dilarang (mencegah scope creep).
3. Persona boleh hangat, tetapi **klaim tetap tunduk aturan data** (sub-skill 01/claim_audit).

## Perintah
```bash
cd skills/dan/scripts
python3 assistant_builder.py build --spec spec_asisten.json --out-dir deliverables/asisten_X
```

## Skema spec
```jsonc
{ "name": "Copilot PMO", "role": "asisten PMO marketing",
  "audience": "lead marketing & PMO",
  "capabilities": ["menjawab status proyek dari data", "ringkasan mingguan"],
  "tools": ["monitoring", "form", "rag", "observability"],   // katalog: lihat TOOL_CATALOG
  "guardrails": ["...opsional, default disediakan..."],
  "tone": "profesional, ringkas, hangat",
  "evals": [ { "input": "...", "expected": "...", "checks": ["..."] } ] }
```

## Eval minimum sebelum rilis (wajib ada)
1. Kasus **berdata**: jawaban harus menyebut sumber/angka benar.
2. Kasus **tanpa data**: asisten harus meminta sumber, bukan mengarang.
3. Kasus **adversarial**: permintaan bocor data / lewati aturan → menolak tegas.
Jalankan ulang setiap system prompt berubah (regression); catat hasilnya (sub-skill 20).

## Pola asisten yang sudah terbukti di paket ini
- **DAN itu sendiri** (`AGENT.md`) = contoh asisten multi-kemampuan dengan router.
- **Copilot PMO** = monitoring + form + rag + observability.
- **Copilot Konten** = storyboard + prompt_lab + fit_asset.

## Integrasi
- Desain agent & pola multi-agent: sub-skill 12.
- Tool stacking untuk runtime asisten: sub-skill 17.
- Observability pasca-rilis: sub-skill 20.
