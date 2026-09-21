#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stack_advisor.py — Sub-skill 17 · AI Tool Stacking: rekomendasi kombinasi tool.

Knowledge base kategori tool AI (LLM API, local LLM, vector/RAG, orchestration,
eval/observability, voice, image, video, app framework, hosting) dengan pros/cons,
perkiraan biaya bulanan, dan level skill. Memberi rekomendasi stack berdasarkan
kebutuhan, budget, ukuran tim — plus alternatif & risiko lock-in.

PAKAI
  python3 stack_advisor.py kb
  python3 stack_advisor.py recommend --need "chatbot dukungan pelanggan + ringkasan dokumen" \
      --budget rendah --team 2 --skill menengah
  python3 stack_advisor.py compare --cat rag --a chroma --b qdrant
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

KB: Dict[str, Dict[str, Dict[str, Any]]] = {
    "llm_api": {
        "openai": {"label": "OpenAI API", "cost": 20, "pros": ["kualitas tinggi", "tooling matang"],
                   "cons": ["biaya per token", "lock-in"], "skill": "pemula"},
        "anthropic": {"label": "Anthropic API", "cost": 20, "pros": ["reasoning & tulisan panjang kuat",
                        "context besar"], "cons": ["biaya per token"], "skill": "pemula"},
        "gemini": {"label": "Google Gemini", "cost": 15, "pros": ["multimodal native", "gratis tier besar"],
                   "cons": ["perilaku berubah antar versi"], "skill": "pemula"},
        "openrouter": {"label": "OpenRouter", "cost": 18, "pros": ["satu pintu banyak model", "mudah pindah"],
                       "cons": ["markup harga"], "skill": "menengah"},
    },
    "local_llm": {
        "ollama": {"label": "Ollama", "cost": 0, "pros": ["gratis", "data tidak keluar"],
                   "cons": ["butuh GPU/RAM", "kualitas di bawah frontier"], "skill": "menengah"},
        "lmstudio": {"label": "LM Studio", "cost": 0, "pros": ["UI mudah", "offline"],
                     "cons": ["kurang cocok produksi"], "skill": "pemula"},
    },
    "rag": {
        "chroma": {"label": "Chroma", "cost": 0, "pros": ["embeddable", "mudah mulai"],
                   "cons": ["fitur enterprise terbatas"], "skill": "pemula"},
        "qdrant": {"label": "Qdrant", "cost": 0, "pros": ["performa", "filter kaya"],
                   "cons": ["ops server"], "skill": "menengah"},
        "pgvector": {"label": "pgvector", "cost": 0, "pros": ["nempel Postgres existing", "SQL biasa"],
                     "cons": ["performa skala sangat besar"], "skill": "menengah"},
        "tantive": {"label": "TF-IDF/BM25 stdlib (seperti rag.py)", "cost": 0,
                    "pros": ["nol dependensi", "cukup utk istilah pasti"],
                    "cons": ["tanpa sinonim semantik"], "skill": "pemula"},
    },
    "orchestration": {
        "langchain": {"label": "LangChain", "cost": 0, "pros": ["komponen lengkap"],
                      "cons": ["abstraksi berat", "breaking changes"], "skill": "menengah"},
        "llamaindex": {"label": "LlamaIndex", "cost": 0, "pros": ["kuat utk data/RAG"],
                       "cons": ["kurva belajar"], "skill": "menengah"},
        "native": {"label": "Kode native + script (seperti workflow.py)", "cost": 0,
                   "pros": ["transparan", "mudah debug", "tanpa lock-in"],
                   "cons": ["fitur harus dibuat sendiri"], "skill": "menengah"},
    },
    "obs": {
        "langsmith": {"label": "LangSmith", "cost": 39, "pros": ["tracing+eval terpadu"],
                      "cons": ["berbayar", "lock-in"], "skill": "menengah"},
        "langfuse": {"label": "Langfuse", "cost": 0, "pros": ["open source", "self-host"],
                     "cons": ["ops server"], "skill": "menengah"},
        "jsonl": {"label": "JSONL trace manual (seperti llm_obs.py)", "cost": 0,
                  "pros": ["nol dependensi", "data milik sendiri"],
                  "cons": ["dashboard buat sendiri"], "skill": "pemula"},
    },
    "voice": {
        "elevenlabs": {"label": "ElevenLabs", "cost": 22, "pros": ["suara natural", "kloning"],
                       "cons": ["berbayar", "izin kloning suara"], "skill": "pemula"},
        "openai_tts": {"label": "OpenAI TTS", "cost": 15, "pros": ["murah per karakter"],
                       "cons": ["variasi suara terbatas"], "skill": "pemula"},
        "piper": {"label": "Piper (lokal)", "cost": 0, "pros": ["gratis offline"],
                  "cons": ["kualitas di bawah cloud"], "skill": "menengah"},
    },
    "image": {
        "midjourney": {"label": "Midjourney", "cost": 30, "pros": ["estetika kuat"],
                       "cons": ["kontrol presisi terbatas"], "skill": "pemula"},
        "sdxl_local": {"label": "Stable Diffusion lokal", "cost": 0, "pros": ["kontrol penuh", "gratis"],
                       "cons": ["butuh GPU", "kurva belajar"], "skill": "mahir"},
        "firefly": {"label": "Adobe Firefly", "cost": 20, "pros": ["aman komersial"],
                    "cons": ["gaya lebih konservatif"], "skill": "pemula"},
    },
    "video": {
        "runway": {"label": "Runway", "cost": 35, "pros": ["gen-video matang"],
                   "cons": ["durasi pendek", "berbayar"], "skill": "pemula"},
        "pika": {"label": "Pika", "cost": 20, "pros": ["mudah"], "cons": ["kontrol terbatas"],
                 "skill": "pemula"},
        "capcut": {"label": "CapCut (editing)", "cost": 0, "pros": ["cepat", "template"],
                   "cons": ["bukan generatif penuh"], "skill": "pemula"},
    },
    "app": {
        "streamlit": {"label": "Streamlit", "cost": 0, "pros": ["prototype super cepat"],
                      "cons": ["batas custom UI"], "skill": "pemula"},
        "nextjs": {"label": "Next.js", "cost": 0, "pros": ["produksional", "ekosistem"],
                   "cons": ["butuh skill web"], "skill": "menengah"},
        "gradio": {"label": "Gradio", "cost": 0, "pros": ["demo ML cepat"],
                   "cons": ["UI terbatas"], "skill": "pemula"},
    },
    "hosting": {
        "vercel": {"label": "Vercel", "cost": 20, "pros": ["deploy mulus"], "cons": ["lock-in ringan"],
                   "skill": "pemula"},
        "fly": {"label": "Fly.io", "cost": 10, "pros": ["container murah"], "cons": ["ops dasar"],
                "skill": "menengah"},
        "vps": {"label": "VPS self-manage", "cost": 6, "pros": ["murah", "kontrol"],
                "cons": ["ops penuh"], "skill": "mahir"},
    },
}

NEED_MAP = {
    "chatbot": ["llm_api", "orchestration", "obs", "app", "hosting"],
    "dokumen": ["rag", "llm_api", "obs"],
    "rag": ["rag", "llm_api", "obs"],
    "konten": ["image", "video", "voice", "llm_api"],
    "suara": ["voice", "llm_api"],
    "video": ["video", "voice", "llm_api"],
    "aplikasi": ["app", "hosting", "llm_api", "obs"],
    "privasi": ["local_llm", "rag", "obs"],
    "murah": ["local_llm", "rag", "native"],
}


def recommend(need: str, budget: str, team: int, skill: str) -> Dict[str, Any]:
    low = need.lower()
    cats: List[str] = []
    for key, v in NEED_MAP.items():
        if key in low:
            cats.extend(v)
    if not cats:
        cats = ["llm_api", "rag", "orchestration", "obs"]
    seen, ordered = set(), []
    for c in cats:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    budget_max = {"rendah": 25, "sedang": 90, "tinggi": 400}[budget]
    picks, total = [], 0
    for c in ordered:
        opts = sorted(KB[c].items(),
                      key=lambda kv: (kv[1]["cost"], kv[1]["skill"] != skill))
        chosen = None
        for k, v in opts:
            if total + v["cost"] <= budget_max:
                chosen = (k, v)
                break
        if chosen is None:
            chosen = min(KB[c].items(), key=lambda kv: kv[1]["cost"])
        total += chosen[1]["cost"]
        picks.append({"cat": c, "key": chosen[0], **chosen[1]})
    risks = []
    if any(p["cat"] in ("llm_api",) for p in picks):
        risks.append("Lock-in penyedia LLM: bungkus pemanggilan di satu modul agar mudah pindah.")
    if budget == "rendah" and team >= 3:
        risks.append("Budget rendah untuk tim ≥3 orang: prioritaskan tool gratis/self-host "
                     "dan batasi fitur berbayar ke satu use-case unggulan.")
    if skill == "pemula" and any(p["skill"] == "mahir" for p in picks):
        risks.append("Ada pilihan level mahir dalam stack: siapkan pendampingan atau ganti "
                     "alternatif lebih sederhana.")
    return {"need": need, "budget": budget, "team": team, "skill": skill,
            "stack": picks, "monthly_usd": total, "risks": risks}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · AI tool stacking advisor")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("kb")
    p = sub.add_parser("recommend")
    p.add_argument("--need", required=True)
    p.add_argument("--budget", default="sedang", choices=["rendah", "sedang", "tinggi"])
    p.add_argument("--team", type=int, default=2)
    p.add_argument("--skill", default="menengah", choices=["pemula", "menengah", "mahir"])
    p.add_argument("--out", default="")
    p = sub.add_parser("compare")
    p.add_argument("--cat", required=True, choices=list(KB))
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "kb":
        for c, opts in KB.items():
            print(f"[{c}] " + ", ".join(opts))
        return 0
    if a.cmd == "compare":
        oa, ob = KB[a.cat].get(a.a), KB[a.cat].get(a.b)
        if not oa or not ob:
            print(f"[DAN] opsi tidak dikenal di {a.cat}: {', '.join(KB[a.cat])}")
            return 2
        print(f"== {oa['label']} vs {ob['label']} (kategori {a.cat}) ==")
        for nm, o in ((a.a, oa), (a.b, ob)):
            print(f"\n{nm}: biaya ~${o['cost']}/bln · level {o['skill']}")
            print("  + " + "; ".join(o["pros"]))
            print("  - " + "; ".join(o["cons"]))
        return 0
    r = recommend(a.need, a.budget, a.team, a.skill)
    print(f"== Stack untuk: {r['need']} (budget {r['budget']}, tim {r['team']}, "
          f"skill {r['skill']}) ≈ ${r['monthly_usd']}/bln ==")
    for p in r["stack"]:
        print(f"  [{p['cat']:14}] {p['label']:34} ~${p['cost']}/bln · {p['skill']}")
        print(f"                    + {'; '.join(p['pros'][:2])}")
        print(f"                    - {'; '.join(p['cons'][:2])}")
    for rk in r["risks"]:
        print("  ! ", rk)
    if a.out:
        json.dump(r, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"[DAN] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
