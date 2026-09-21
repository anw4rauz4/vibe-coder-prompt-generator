---
name: dan-ai-tool-stacking
description: >-
  Merekomendasikan kombinasi tool AI yang koheren berdasarkan kebutuhan, budget,
  ukuran tim, dan level skill: knowledge base 10 kategori (LLM API, local LLM,
  vector/RAG, orchestration, observability, voice, image, video, app framework,
  hosting) dengan pros/cons + perkiraan biaya bulanan, plus peringatan risiko
  (lock-in, budget vs tim, skill gap). Gunakan saat pengguna bertanya "tool apa yang
  harus saya pakai", "stack untuk chatbot/RAG/konten", "bandingkan X vs Y", atau
  menghemat biaya langganan AI.
---

# 17 · AI Tool Stacking

## Prinsip
1. **Stack = keputusan bisnis**, bukan koleksi logo: tiap tool harus menghapus
   satu bottleneck terukur.
2. Mulai dari yang gratis/self-host untuk validasi; bayar hanya untuk bottleneck unggulan.
3. Bungkus pemanggilan LLM/vendor di satu modul agar pindah penyedia murah (exit strategy).

## Perintah
```bash
cd skills/dan/scripts
python3 stack_advisor.py kb
python3 stack_advisor.py recommend --need "chatbot dukungan + rag dokumen" \
    --budget rendah --team 2 --skill menengah
python3 stack_advisor.py compare --cat rag --a chroma --b pgvector
```

## Kategori & pertanyaan penentu
| Kategori | Pertanyaan penentu |
|---|---|
| llm_api vs local_llm | data boleh keluar? budget per token? |
| rag | istilah pasti (lexical cukup) atau sinonim luas (embedding)? |
| orchestration | butuh DAG kompleks atau urutan linear cukup (workflow.py)? |
| obs | perlu tracing vendor atau JSONL milik sendiri (llm_obs.py)? |
| voice/image/video | volume produksi & kebutuhan kontrol presisi |
| app/hosting | skill tim web & target latency/cost |

## Aturan budget (heuristik bawaan)
rendah ≤ $25/bln · sedang ≤ $90/bln · tinggi ≤ $400/bln.
Bila tim ≥3 dengan budget rendah: prioritaskan self-host & batasi berbayar ke 1 use-case.

## Anti-pola stack
- 5 langganan LLM berbeda tanpa router → biaya bocor, evaluasi sulit.
- Vector DB sebelum ada keluhan retrieval → biaya & ops tanpa manfaat.
- Framework orchestration berat untuk 2 langkah linear → debt abstraksi.

## Integrasi
- Biaya & trade-off arsitektur software: sub-skill 08.
- Observability untuk mengukur apakah stack bekerja: sub-skill 20.
