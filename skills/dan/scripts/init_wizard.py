#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
init_wizard.py — Tuntun pengguna baru dari nol sampai keluaran pertama (≤5 pertanyaan).

Mode interaktif (stdin tty) bertanya: sektor → data → keluaran pertama → identitas →
bahasa. Mode non-interaktif (flag / CI) melewati prompt bila argumen diberi.

PAKAI
  python3 init_wizard.py                      # interaktif
  python3 init_wizard.py --sektor fnb --data examples/fnb/campaign.csv \
      --kind infografik --nama "Kopi Enak" --period "Q3 2026" --lang id --out-dir /tmp/init
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

SEKTOR = {
    "fnb": {"csv": "examples/fnb/campaign.csv", "brief": "examples/fnb/brief.md",
            "tip": "Fokus: margin vs diskon & heatmap jam ramai."},
    "fashion": {"csv": "examples/fashion/campaign.csv",
                "brief": "examples/fashion/brief.md",
                "tip": "Fokus: funnel halaman produk & revenue bersih setelah retur."},
    "b2b": {"csv": "examples/b2b/campaign.csv", "brief": "examples/b2b/brief.md",
            "tip": "Fokus: biaya-per-SQL & kapasitas follow-up sales."},
    "sendiri": {"csv": "", "brief": "", "tip": "Pakai data Anda; skema bebas asal bermakna sama."},
}
KIND = ["infografik", "laporan_klien", "storyboard", "deck"]


def ask(q: str, opts: str, default: str) -> str:
    if not sys.stdin.isatty():
        return default
    try:
        v = input(f"{q} [{opts}] (default: {default}): ").strip()
        return v or default
    except EOFError:
        return default


def run(sektor: str, data: str, kind: str, nama: str, period: str, lang: str,
        out_dir: str) -> Dict[str, Any]:
    import dan_analytics as da
    import make_infographic as mi
    import client_report as cr
    import storyboard as sb
    import print_deck as pd_
    os.makedirs(out_dir, exist_ok=True)
    csv_path = data or SEKTOR.get(sektor, {}).get("csv", "")
    if csv_path and not os.path.isabs(csv_path) and not os.path.exists(csv_path):
        csv_path = os.path.join(ROOT, csv_path)
    if not csv_path or not os.path.exists(csv_path):
        return {"ok": False, "error": f"data tidak ditemukan: {csv_path}"}
    A = da.analyze(csv_path)
    aj = os.path.join(out_dir, "analysis.json")
    json.dump(A, open(aj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    am = os.path.join(out_dir, "analysis.md")
    open(am, "w", encoding="utf-8").write(da.to_markdown(A))
    made = [aj, am]
    if kind == "infografik":
        o = os.path.join(out_dir, "infografik.html")
        mi.main([aj, "--out", o, "--theme", "light" if lang == "en" else "dan"])
        made.append(o)
    elif kind == "laporan_klien":
        o = os.path.join(out_dir, f"laporan_klien_{lang}.md")
        cr.main(["--analysis", aj, "--nama", nama, "--period", period, "--lang", lang,
                 "--out", o])
        made.append(o)
    elif kind == "storyboard":
        o = os.path.join(out_dir, "storyboard.md")
        B = sb.build({"product": nama, "audience": "pelanggan " + nama,
                      "platform": "tiktok", "duration": 20, "structure": "hook_story_offer",
                      "goal": "konversi", "tone": "friendly",
                      "problem": "masalah utama pelanggan", "result": "hasil yang dijanjikan",
                      "cta": "beli sekarang"})
        open(o, "w", encoding="utf-8").write(sb.to_markdown(B))
        made.append(o)
    else:
        o = os.path.join(out_dir, "deck_pimpinan.html")
        pd_.main(["--marketing", aj, "--out", o])
        made.append(o)
    k = A["kpi"]
    return {"ok": True, "made": made,
            "ringkasan": f"ROAS {k['roas']:.2f}x · CTR {k['ctr']:.2f}% · "
                         f"revenue {A['meta']['currency']}{k['revenue'] / 1e6:,.1f} jt",
            "tip": SEKTOR.get(sektor, {}).get("tip", ""),
            "next": ["Baca analysis.md → pilih 1 insight terbesar",
                     "Jalankan budget_sim.py untuk uji realokasi",
                     "Jadikan rutinitas: weekly.py tiap Senin"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · wizard onboarding")
    ap.add_argument("--sektor", default="", choices=list(SEKTOR) + [""])
    ap.add_argument("--data", default="")
    ap.add_argument("--kind", default="", choices=KIND + [""])
    ap.add_argument("--nama", default="")
    ap.add_argument("--period", default="")
    ap.add_argument("--lang", default="", choices=["id", "en", ""])
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "deliverables", "init"))
    a = ap.parse_args(argv)

    sektor = a.sektor or ask("Sektor Anda?", "/".join(SEKTOR), "fnb")
    data = a.data or ("" if sektor == "sendiri" else "")
    if sektor == "sendiri" and not a.data:
        data = ask("Path CSV Anda?", "path", "")
    kind = a.kind or ask("Keluaran pertama?", "/".join(KIND), "infografik")
    nama = a.nama or ask("Nama bisnis?", "teks", "Bisnis Anda")
    period = a.period or ask("Periode?", "teks", "periode ini")
    lang = a.lang or ask("Bahasa?", "id/en", "id")

    print(f"[DAN] wizard: sektor={sektor} kind={kind} nama={nama} lang={lang}")
    R = run(sektor, data, kind, nama, period, lang, a.out_dir)
    if not R.get("ok"):
        print("[DAN] gagal:", R.get("error"))
        return 2
    print("[DAN] ringkasan:", R["ringkasan"])
    print("[DAN] tip sektor:", R["tip"])
    for m in R["made"]:
        print("   ->", m)
    print("[DAN] langkah berikutnya:")
    for n in R["next"]:
        print("   -", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
