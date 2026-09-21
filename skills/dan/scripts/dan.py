#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dan.py — Pintu masuk tunggal (unified CLI) untuk seluruh paket skill DAN.

SUB-PERINTAH
  list                       daftar sub-skill & engine
  run <engine> [arg...]      jalankan engine apa pun (teruskan argumen apa adanya)
  new <template> --out F     salin template siap isi ke F
                             (.json: --set key=value mengisi kunci tingkat atas)
  audit --report F --source  validator provenance angka (claim_audit)
  doctor                     jalankan QA terpadu + audit referensi, cetak ringkasan
  web [--outdir D]           bangun situs hub DAN (satu HTML self-contained)
  serve [port]               sajikan situs + deliverables di localhost (default 8686)
  memory <add|search|list|context|stats>   session_log memori lintas-sesi

CONTOH
  python3 dan.py list
  python3 dan.py run dan_analytics ../../../data/sample_campaign.csv
  python3 dan.py new building.blank.json --out ../../../data/rumah_saya.json \
        --set 'meta.name=Rumah Saya'
  python3 dan.py audit --report ../../../deliverables/analysis.md \
        --source ../../../deliverables/analysis.json
  python3 dan.py doctor
  python3 dan.py memory add --text "Klien suka laporan ringkas" --tag preferensi
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from typing import List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

ENGINES = [
    ("dan_analytics", "01", "CSV/XLSX → KPI, tren, anomali, forecast, insight"),
    ("svg_charts", "03", "paket 18 chart SVG (pakai: python3 -m svg_charts)"),
    ("make_infographic", "03", "JSON → infografik HTML self-contained + poster"),
    ("graph_analyst", "03", "metrik jaringan + visual + laporan"),
    ("storyboard", "04", "brief → shot list, VO, prompt, SRT"),
    ("fit_asset", "04", "crop/pad aset ke rasio platform"),
    ("project_monitor", "07", "monitoring/tracking/progress/controlling + coach"),
    ("make_forms", "07", "form interaktif progress/monitoring/controlling"),
    ("weekly_run", "07", "ritme mingguan: apply→report→coach→dashboard→ringkasan"),
    ("pmo_guard", "07", "policy gate (exit code untuk CI/cron)"),
    ("arch_advisor", "08", "scaffold multi-bahasa, review pro/kon, compare trade-off"),
    ("arch_design", "09", "denah 2D, massa 3D, tampak, KDB/KLB, RAB, konstruksi"),
    ("make_slides", "07", "slide deck HTML self-contained"),
    ("exec_dashboard", "03", "dashboard eksekutif gabungan"),
    ("claim_audit", "QA", "validator provenance angka"),
    ("props_test", "QA", "property-based test"),
    ("make_package", "QA", "manifest + zip siap-import"),
    ("make_sample_data", "demo", "generator data demo"),
    ("prompt_lab", "10", "lint/skor/perbaiki/varian prompt"),
    ("workflow", "11", "runner workflow terdeklarasi (JSON) antar-engine"),
    ("rag", "13", "RAG stdlib: indeks md + query bersitasi"),
    ("stack_advisor", "17", "rekomendasi stack tool AI + biaya"),
    ("assistant_builder", "15", "spec -> system prompt + tools + eval set"),
    ("llm_obs", "20", "trace JSONL + laporan pass-rate/biaya/latensi"),
    ("weekly_diff", "07", "riwayat append-only + diff antar-minggu"),
    ("demo_tour", "onboarding", "tur cuplikan hidup sub-skill 01-21"),
    ("rag_eval", "13", "eval retrieval RAG (recall@k, MRR, miss)"),
    ("make_digest", "21", "digest rilis + checklist + naskah audio"),
    ("make_adapters", "plug", "ekspor adapter Claude/Cursor/Gemini/ChatGPT/Copilot/AGENTS"),
    ("mcp_server", "plug", "server MCP stdio (tool DAN untuk klien MCP apa pun)"),
    ("weekly", "07", "satu perintah ritme mingguan lengkap (cron-ready)"),
    ("narrative_check", "QA", "pemeriksa klaim kausal/overclaim/person-blame"),
    ("annotate", "kolab", "lapisan komentar review pada deliverable HTML"),
    ("release", "QA", "rilis terurutan ber-gate (test→cases→refs→adapters→package→…)"),
    ("print_deck", "03", "deck rapat pimpinan cetak A4 landscape"),
    ("init_wizard", "onboarding", "wizard ≤5 pertanyaan: sektor → data → keluaran pertama"),
    ("weekly_watch", "QA", "watchdog mingguan: release dry-run + drift + guard + notify"),
    ("showcase", "etalase", "galeri satu halaman seluruh artefak contoh"),
    ("narrative_trend", "QA", "tren kualitas narasi lintas laporan (append-only)"),
    ("make_bundle", "plug", "bundle offline: dan.pyz + examples + adapters + docs"),
    ("multi_client", "03", "dashboard gabungan lintas-klien dengan filter"),
    ("make_sop", "07", "SOP/runbook tim: cadence + RACI + eskalasi"),
    ("crisis_sim", "02", "simulasi krisis terukur + rencana respons terurut"),
    ("make_web", "web", "situs hub DAN: profil + 21 skill + tools interaktif + unduhan"),
    ("serve", "web", "server lokal stdlib untuk situs + artefak deliverables"),
    ("memory", "kolab", "session_log: memori persisten lintas-sesi (add/search/context)"),
    ("publish_gh", "web", "deploy GitHub Pages GRATIS: prepare folder siap push + guide"),
]

SUBSKILLS = [
    ("01", "Marketing Data Analyst"), ("02", "Marketing Strategist"),
    ("03", "Data→Infographic + Graph Analyst"), ("04", "Image & Video Creator"),
    ("05", "Design Engineer 2D/3D"), ("06", "Motivator / Coach Expert"),
    ("07", "Project Monitoring / Tracking / Progress / Controlling"),
    ("08", "Software Architecture Advisor"), ("09", "Architectural Design (bangunan)"),
    ("10", "Prompt Engineering"), ("11", "AI Workflow Automation"),
    ("12", "AI Agents"), ("13", "RAG / Retrieval"), ("14", "Multimodal AI"),
    ("15", "Custom AI Assistants"), ("16", "Voice AI & Avatars"),
    ("17", "AI Tool Stacking"), ("18", "AI Video Content"),
    ("19", "AI App / SaaS Building"), ("20", "LLM Observability"),
    ("21", "Staying Updated"),
]

TEMPLATES = ["strategy-brief.md", "campaign-plan.md", "report-template.md",
             "design-brief-2d.md", "projects.example.json", "building.example.json",
             "building.blank.json", "form-progress.md", "form-monitoring.md",
             "form-controlling.md", "data-spec.example.json",
             "storyboard-brief.example.json", "content-calendar.csv"]


def cmd_list(_: argparse.Namespace) -> int:
    print("SUB-SKILL")
    for n, t in SUBSKILLS:
        print(f"  {n}  {t}")
    print("\nENGINE (python3 dan.py run <nama> ...)")
    for name, sk, desc in ENGINES:
        print(f"  {name:18} [{sk}] {desc}")
    print("\nTEMPLATE (python3 dan.py new <nama> --out ...)")
    for t in TEMPLATES:
        print("  " + t)
    return 0


def cmd_run(a: argparse.Namespace) -> int:
    name = a.engine
    if name == "svg_charts":
        return subprocess.call([sys.executable, "-m", "svg_charts"] + a.args, cwd=HERE)
    try:
        mod = importlib.import_module(name)
    except ImportError as e:
        print(f"[DAN] engine tidak dikenal: {name} ({e})")
        return 2
    return int(mod.main(a.args) or 0)


def _template_src(name: str):
    """('fs', path) | ('zip', bytes) | (None, None) — tahan terhadap jalankan-dari-.pyz."""
    cands = [os.path.join(ROOT, "skills", "dan", "templates", name),
             os.path.join(HERE, "templates", name)]
    for c in cands:
        if os.path.exists(c):
            return "fs", c
    import zipfile
    for sp in sys.path:
        if str(sp).endswith(".pyz") and zipfile.is_zipfile(sp):
            z = zipfile.ZipFile(sp)
            entry = "templates/" + name
            if entry in z.namelist():
                return "zip", z.read(entry)
    return None, None


def cmd_new(a: argparse.Namespace) -> int:
    kind, src = _template_src(a.template)
    if kind is None:
        print(f"[DAN] template tidak ada: {a.template}\n  pilihan: {', '.join(TEMPLATES)}")
        return 2
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    if kind == "fs":
        shutil.copyfile(src, a.out)
    else:
        with open(a.out, "wb") as f:
            f.write(src)
    if a.set and a.out.endswith(".json"):
        with open(a.out, encoding="utf-8") as f:
            doc = json.load(f)
        for kv in a.set:
            if "=" not in kv:
                continue
            k, v = kv.split("=", 1)
            cur = doc
            parts = k.split(".")
            for p in parts[:-1]:
                cur = cur.setdefault(p, {})
            try:
                v = json.loads(v)
            except Exception:
                pass
            cur[parts[-1]] = v
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    print(f"[DAN] template {a.template} -> {a.out}")
    print("[DAN] langkah berikutnya: isi field ber-placeholder, lalu jalankan engine "
          "terkait (lihat `dan.py list`).")
    return 0


def cmd_audit(a: argparse.Namespace) -> int:
    import claim_audit
    return claim_audit.main(["--report", a.report] +
                            sum([["--source", s] for s in a.source], []) +
                            (["--fail-under", str(a.fail_under)] if a.fail_under else []) +
                            (["--out", a.out] if a.out else []))


def cmd_doctor(a: argparse.Namespace) -> int:
    # in-process (bukan subprocess) agar tetap berfungsi saat dijalankan dari dalam .pyz
    import _test_all
    import _check_refs
    import dan_analytics
    rows = []
    ok = True
    nested = os.environ.get("DAN_IN_QA") == "1"
    if not nested:
        r1 = _test_all.main()
        ok = ok and (r1 == 0)
        rows.append(("_test_all (smoke+property+integrasi)", r1 == 0))
        print(f"  [{'OK ' if r1 == 0 else 'FAIL'}] _test_all (in-process)")
    else:
        rows.append(("_test_all (dilewati: sudah berjalan di pemanggil)", True))
    r2 = _check_refs.main()
    ok = ok and (r2 == 0)
    rows.append(("_check_refs (referensi silang)", r2 == 0))
    print(f"  [{'OK ' if r2 == 0 else 'FAIL'}] _check_refs (in-process)")
    r3 = dan_analytics.self_test()
    ok = ok and (r3 == 0)
    rows.append(("parser angka (25 kasus)", r3 == 0))
    print(f"  [{'OK ' if r3 == 0 else 'FAIL'}] parser angka")
    if getattr(a, "full", False):
        import run_cases as rc
        import make_adapters as mad
        import mcp_smoke as ms
        import narrative_check as nc
        r4 = rc.main(["run", "all"])
        ok = ok and (r4 == 0)
        rows.append(("run_cases (3 kasus end-to-end)", r4 == 0))
        n, probs = mad.validate()
        rows.append((f"adapters ({n} berkas)", not probs))
        ok = ok and not probs
        srows = ms.run()
        bads = [r for r in srows if not r["ok"]]
        rows.append((f"mcp_smoke ({len(srows)} baris)", not bads))
        ok = ok and not bads
        R = nc.check("Pendapatan pasti naik karena kami terbaik sepanjang masa.")
        rows.append(("narrative_check menangkap overclaim", len(R["findings"]) >= 2))
        ok = ok and len(R["findings"]) >= 2
        import sec_audit as sa
        fnds = sa.scan(ROOT)
        nhigh = sum(1 for f in fnds if f["severity"] == "high")
        rows.append((f"sec_audit ({len(fnds)} temuan, {nhigh} high)", nhigh == 0))
        ok = ok and (nhigh == 0)
        out = os.path.join(ROOT, "deliverables", "qa_report.md")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write("# Laporan QA Terpadu\n\n" +
                    "| Pemeriksaan | Status |\n|---|---|\n" +
                    "\n".join(f"| {nm} | {'✅ OK' if g else '⛔ GAGAL'} |"
                               for nm, g in rows) +
                    f"\n\n**Hasil: {'SEMUA OK' if ok else 'ADA KEGAGALAN'}** "
                    f"({sum(1 for _, g in rows if g)}/{len(rows)})\n")
        print(f"  -> {out}")
    print("[DAN] doctor:", "SEHAT" if ok else "ADA MASALAH")
    return 0 if ok else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="dan.py", description="DAN unified CLI",
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list")
    p = sub.add_parser("run")
    p.add_argument("engine")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("new")
    p.add_argument("template")
    p.add_argument("--out", required=True)
    p.add_argument("--set", action="append", default=[])
    p = sub.add_parser("audit")
    p.add_argument("--report", required=True)
    p.add_argument("--source", action="append", default=[])
    p.add_argument("--fail-under", type=float, default=0)
    p.add_argument("--out", default="")
    p = sub.add_parser("doctor")
    p.add_argument("--full", action="store_true")
    sub.add_parser("demo")
    p = sub.add_parser("adapters")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("weekly")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("narrative")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("annotate")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("release")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("print_deck")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("init")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("watch")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("showcase")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("narrative_trend")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("bundle")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("multi_client")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("sop")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("crisis")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("web")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("serve")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("memory")
    p.add_argument("args", nargs=argparse.REMAINDER)
    p = sub.add_parser("deploy")
    p.add_argument("args", nargs=argparse.REMAINDER)

    a = ap.parse_args(argv)
    if a.cmd == "demo":
        import demo_tour
        return demo_tour.main([])
    if a.cmd == "adapters":
        import make_adapters
        return make_adapters.main(a.args or ["build"])
    if a.cmd == "weekly":
        import weekly
        return weekly.main(a.args)
    if a.cmd == "narrative":
        import narrative_check
        return narrative_check.main(a.args)
    if a.cmd == "annotate":
        import annotate
        return annotate.main(a.args)
    if a.cmd == "release":
        import release
        return release.main(a.args)
    if a.cmd == "print_deck":
        import print_deck
        return print_deck.main(a.args)
    if a.cmd == "init":
        import init_wizard
        return init_wizard.main(a.args)
    if a.cmd == "watch":
        import weekly_watch
        return weekly_watch.main(a.args)
    if a.cmd == "showcase":
        import showcase
        return showcase.main(a.args)
    if a.cmd == "narrative_trend":
        import narrative_trend
        return narrative_trend.main(a.args)
    if a.cmd == "bundle":
        import make_bundle
        return make_bundle.main(a.args)
    if a.cmd == "multi_client":
        import multi_client
        return multi_client.main(a.args)
    if a.cmd == "sop":
        import make_sop
        return make_sop.main(a.args)
    if a.cmd == "crisis":
        import crisis_sim
        return crisis_sim.main(a.args)
    if a.cmd == "web":
        import make_web
        return make_web.main(a.args)
    if a.cmd == "serve":
        import serve
        return serve.main(a.args)
    if a.cmd == "memory":
        import memory
        return memory.main(a.args)
    if a.cmd == "deploy":
        import publish_gh
        return publish_gh.main(a.args)
    return {"list": cmd_list, "run": cmd_run, "new": cmd_new,
            "audit": cmd_audit, "doctor": cmd_doctor}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
