#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_tour.py — Tur onboarding satu perintah: cuplikan hidup tiap sub-skill DAN.

Menjalankan operasi KECIL & aman (artefak ditulis ke folder temp/demo) untuk
sub-skill 01-21, masing-masing ≤3 baris keluaran, sehingga orang baru bisa
"merasakan" paket dalam ~30 detik.

PAKAI
  python3 demo_tour.py                 # tur penuh
  python3 demo_tour.py --only 13,17    # hanya sub-skill tertentu
  python3 dan.py demo                  # lewat unified CLI
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from typing import Callable, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

import dan_analytics as da          # noqa: E402
import make_infographic as mi       # noqa: E402
import storyboard as sb             # noqa: E402
import project_monitor as pm        # noqa: E402
import arch_advisor as aa           # noqa: E402
import arch_design as ad            # noqa: E402
import prompt_lab as pl             # noqa: E402
import workflow as wfl              # noqa: E402
import rag as ragmod                # noqa: E402
import stack_advisor as sa          # noqa: E402
import assistant_builder as ab      # noqa: E402
import llm_obs as lo                # noqa: E402
import make_sample_data as msd      # noqa: E402


def _cap(fn, *a, **kw) -> List[str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*a, **kw)
    return [ln for ln in buf.getvalue().splitlines() if ln.strip()][:3]


def d01(tmp):
    csv = os.path.join(tmp, "c.csv")
    msd.main(["--days", "14", "--seed", "3", "--out", csv])
    A = da.analyze(csv)
    k = A["kpi"]
    return [f"ROAS {k['roas']:.2f}x · CTR {k['ctr']:.2f}% · CVR {k['cvr']:.2f}% · "
            f"health {A['health_score']:.0f}/100 (14 hari demo)"]


def d03(tmp):
    csv = os.path.join(tmp, "c.csv")
    msd.main(["--days", "14", "--out", csv])
    aj = os.path.join(tmp, "a.json")
    A = da.analyze(csv)
    json.dump(A, open(aj, "w"))
    html = os.path.join(tmp, "i.html")
    mi.main([aj, "--out", html])
    n = open(html, encoding="utf-8").read().count("<svg")
    return [f"infografik HTML self-contained dengan {n} SVG inline (tanpa CDN)"]


def d04(tmp):
    B = sb.build({"product": "Kopi Susu Aren", "audience": "pekerja 22-35",
                  "platform": "tiktok", "duration": 20, "structure": "pas",
                  "goal": "konversi", "tone": "friendly",
                  "problem": "ngantuk siang", "result": "melek sampai sore",
                  "cta": "klik keranjang"})
    return [f"storyboard {len(B['shots'])} shot / {B['meta']['total_duration']}s + "
            f"{len(B['hooks'])} varian hook + SRT siap edit"]


def d07(tmp):
    doc = json.load(open(os.path.join(ROOT, "skills", "dan", "templates",
                                      "projects.example.json"), encoding="utf-8"))
    A = pm.compute(doc)
    p = A["portfolio"]
    return [f"{p['projects']} proyek: {p['on_track']} on-track · {p['warn']} waspada · "
            f"{p['bad']} kritis · {p['stalled']} stalled; guard siap jadi gate CI"]


def d08(_):
    c = aa.compare("pattern", "monolith", "microservices",
                   {"team": 4, "scale": "medium", "deadline": "ketat", "budget": "rendah"})
    return [f"monolith {c['a']['total']} vs microservices {c['b']['total']} → "
            f"rekomendasi: {c['winner']} (konteks tim 4, deadline ketat)"]


def d09(_):
    doc = json.load(open(os.path.join(ROOT, "data", "kafe_case.json"), encoding="utf-8"))
    A = ad.compute(doc, 20)
    return [f"kafe 2 lantai: terbangun {A['totals']['built_area']:.0f} m² · "
            f"KDB {A['compliance']['kdb']:.0f}% (batas {A['compliance']['kdb_max']:.0f}%) · "
            f"RAB {A['meta']['currency']}{A['rab_total'] / 1e9:.2f} M"]


def d10(_):
    bad = "buatkan laporan"
    good = ("Bertindaklah sebagai analis. Berdasarkan campaign.csv Q3, buat tabel ROAS "
            "per channel format markdown maksimal 150 kata, jangan mengarang data.")
    return [f"lint prompt: '{bad}' skor {pl.lint(bad)['score']} vs prompt lengkap "
            f"{pl.lint(good)['score']} → elemen hilang jadi daftar perbaikan"]


def d11(tmp):
    wf = {"name": "demo", "steps": [
        {"id": "a", "engine": "make_sample_data",
         "args": ["--days", "7", "--out", os.path.join(tmp, "w.csv")]}]}
    s = wfl.run(wf, os.path.join(tmp, "wf"))
    return [f"workflow JSON tereksekusi: {s['counts']} + audit workflow_run.json"]


def d12(_):
    return ["pola agent: single+tools dulu; multi-agent hanya bila batas wewenang berbeda;",
            "kartu agent = tujuan + tool diizinkan/dilarang + guardrails + evaluation (sub-skill 15)"]


def d13(_):
    idx = ragmod.build_index([os.path.join(ROOT, "skills", "dan")])
    r = ragmod.query(idx, "ambang waspada variance proyek", 1)
    top = r[0] if r else {"file": "-", "heading": "-"}
    return [f"RAG stdlib: {idx['n']} chunk; jawaban bersitasi → "
            f"{os.path.basename(top['file'])} :: {top['heading'][:40]}"]


def d14(_):
    return ["QC multimodal: rasio via fit_asset, metadata via PIL, wajah/tangan & teks "
            "terbakar dicek manual; gambar AI wajib ditandai sintetis"]


def d15(tmp):
    files = ab.build({"name": "Copilot Demo", "role": "asisten demo",
                      "tools": ["rag", "monitoring"], "evals": []})
    return [f"spec → {len(files)} berkas: system_prompt.md, tools_manifest.json, "
            f"eval_set.json (3 kasus default), README_assistant.md"]


def d16(_):
    return ["naskah TTS: kalimat ≤18 kata, angka dilafalkan, jeda ditandai; kunci atribut "
            "suara agar semua klip satu proyek terdengar satu orang"]


def d17(_):
    r = sa.recommend("chatbot dukungan + rag dokumen", "rendah", 2, "menengah")
    return [f"stack budget rendah ≈ ${r['monthly_usd']}/bln: " +
            " · ".join(p["label"] for p in r["stack"][:4])]


def d18(_):
    return ["video: storyboard → first-frame per shot → video 2-4s per aksi → cut-list + "
            ".srt; 80%+ nonton tanpa suara maka subtitle wajib"]


def d19(_):
    return ["MVP SaaS: jual hasil bukan model; harga ≥4× biaya inferensi p95; fitur lain "
            "masuk daftar TUNDA sampai 10 pengguna lulus alur nilai"]


def d20(tmp):
    tp = os.path.join(tmp, "t.jsonl")
    if os.path.exists(tp):
        os.remove(tp)
    lo.log(tp, {"prompt_id": "demo", "cost": 0.002, "latency": 800, "pass": "true"})
    lo.log(tp, {"prompt_id": "demo", "cost": 0.003, "latency": 1500, "pass": "false"})
    R = lo.report(tp, 80)
    r0 = R["rows"][0]
    return [f"trace JSONL: pass-rate {r0['pass_pct']:.0f}% · biaya ${r0['cost_total']:.3f} · "
            f"p95 {r0['latency_p95']}ms → alarm karena <80%"]


def d21(_):
    return ["staying updated: digest 30 mnt/minggu (scan→baca 2→keputusan adopsi/tunggu→"
            "5 baris utk tim); adopsi teknologi baru lewat proof-of-value ≤1 hari"]


TOUR: List[Tuple[str, str, Callable[[str], List[str]]]] = [
    ("01", "Marketing Data Analyst", d01), ("03", "Infografik", d03),
    ("04", "Image & Video", d04), ("07", "Project Monitoring", d07),
    ("08", "Software Architecture", d08), ("09", "Architectural Design", d09),
    ("10", "Prompt Engineering", d10), ("11", "Workflow Automation", d11),
    ("12", "AI Agents", d12), ("13", "RAG", d13), ("14", "Multimodal", d14),
    ("15", "Custom Assistants", d15), ("16", "Voice & Avatars", d16),
    ("17", "Tool Stacking", d17), ("18", "Video Content", d18),
    ("19", "AI App/SaaS", d19), ("20", "LLM Observability", d20),
    ("21", "Staying Updated", d21),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · demo tour")
    ap.add_argument("--only", default="", help="daftar nomor dipisah koma, mis. 13,17")
    a = ap.parse_args(argv)
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    tmp = tempfile.mkdtemp(prefix="dan_demo_")
    print("=" * 64)
    print("DAN · TUR DEMO (artefak demo di", tmp, ")")
    print("=" * 64)
    for num, title, fn in TOUR:
        if only and num not in only:
            continue
        print(f"\n[{num}] {title}")
        try:
            for ln in fn(tmp):
                print("   ", ln)
        except Exception as e:                            # pragma: no cover
            print("    ! gagal:", e)
    print("\n" + "=" * 64)
    print("Selanjutnya: python3 dan.py list · run_cases.py run all · _test_all.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
