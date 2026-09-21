---
name: dan-ai-agents
description: >-
  Merancang agent AI yang benar: kartu agent (tujuan, tool, guardrails, memori, eval),
  pola single-agent vs multi-agent (router, orchestrator-worker, evaluator-optimizer),
  desain tool yang aman (izin eksplisit, side-effect ditandai), dan loop refleksi.
  Termasuk pembangkit kartu agent & system prompt via assistant_builder.py. Gunakan
  saat pengguna meminta "buatkan agent untuk X", "arsitektur multi-agent", "agent saya
  sering hallucinate/nyasar", atau membagi pekerjaan antar agent.
---

# 12 · AI Agents

## Prinsip
1. **Mulai dari satu agent yang baik.** Multi-agent hanya bila ada batas wewenang/tool
   yang benar-benar berbeda; tiap agent tambahan = permukaan kegagalan baru.
2. Agent tanpa **eval & guardrails terdokumentasi** bukan agent, tapi taruhan.
3. Tool dengan side-effect (kirim email, ubah data, bayar) wajib konfirmasi manusia
   atau dry-run default.

## Kartu agent (isi sebelum membangun)
```
Nama & tujuan   : satu kalimat, terukur
Audiens         : siapa yang dilayani
Tool diizinkan  : daftar eksplisit + yang DILARANG
Guardrails      : aturan keras (data, klaim, keamanan)
Memori          : apa yang disimpan, berapa lama, siapa yang bisa hapus
Gaya jawaban    : nada, panjang, format default
Eval            : ≥3 kasus lulus-sebelum-rilis + regression tiap perubahan
Observability   : semua panggilan di-log (sub-skill 20)
```

## Pola arsitektur
| Pola | Pakai bila | Risiko |
|---|---|---|
| Single + tools | 1 domain, tool ≤8 | overload instruksi → pecah prompt |
| Router | masukan beragam kategori | router salah rute → fallback manual |
| Orchestrator–worker | tugas bisa dipecah independen | biaya & latensi naik |
| Evaluator–optimizer | keluaran butuh mutu tinggi (copy, kode) | loop tak berhenti → set max iterasi |
| Human-in-the-loop | side-effect/keputusan bisnis | throughput turun (sengaja) |

## Perintah
```bash
cd skills/dan/scripts
python3 assistant_builder.py build --spec spec_agent.json --out-dir deliverables/agent_X
# hasil: system_prompt.md, tools_manifest.json, eval_set.json, README_assistant.md
```

## Loop kerja agent DAN (contoh nyata)
`SKILL.md` (router) → sub-skill (worker) → `_test_all/claim_audit` (evaluator) →
`pmo_guard` (gate manusia-otomatis). Ini pola orchestrator–worker + evaluator yang
sudah berjalan di paket ini; jadikan referensi saat membangun agent lain.

## Integrasi
- Spec asisten: sub-skill 15 (custom assistants) memperdalam persona & eval.
- Observability: sub-skill 20. Prompt quality: sub-skill 10.
