#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
burnup.py — Dashboard lintas-proyek multi-periode dari riwayat append-only.

Membaca history.jsonl (diisi `weekly_diff.py snap`) lalu menampilkan:
  - burn-up portofolio: garis Aktual vs Rencana per snapshot (minggu),
  - tabel pergerakan per proyek antar snapshot pertama→terakhir,
  - deteksi proyek yang stagnan ≥2 snapshot berturut-turut.

Bila riwayat <2 snapshot, keluar dengan pesan jelas (bukan grafik bohong).

PAKAI
  python3 weekly_diff.py snap --report project_report.json --log history.jsonl   # tiap minggu
  python3 burnup.py --log history.jsonl --out deliverables/burnup.html
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import svg_charts as sc        # noqa: E402
import make_infographic as mi  # noqa: E402


def load(log: str) -> List[Dict[str, Any]]:
    if not os.path.exists(log):
        return []
    return [json.loads(ln) for ln in open(log, encoding="utf-8") if ln.strip()]


def build(snaps: List[Dict[str, Any]], theme: str = "dan") -> Dict[str, Any]:
    labels = [s.get("today") or s.get("ts", f"W{i+1}")[:10] for i, s in enumerate(snaps)]
    act = [sum(p["progress"] for p in s["projects"]) / max(1, len(s["projects"]))
           for s in snaps]
    plan = [sum(p["planned"] for p in s["projects"]) / max(1, len(s["projects"]))
            for s in snaps]
    first, last = snaps[0], snaps[-1]
    fp = {p["id"]: p for p in first["projects"]}
    moves = []
    for p in last["projects"]:
        o = fp.get(p["id"])
        if not o:
            moves.append({"name": p["name"], "d": p["progress"], "from": "-",
                          "to": p["progress"], "rag": p["rag"], "stagnant": False})
            continue
        stagnant = all(abs(s["projects"][[x["id"] for x in s["projects"]].index(p["id"])]
                           ["progress"] - o["progress"]) < 0.5 for s in snaps[1:])
        moves.append({"name": p["name"], "d": round(p["progress"] - o["progress"], 1),
                      "from": o["progress"], "to": p["progress"], "rag": p["rag"],
                      "stagnant": stagnant})
    return {"labels": labels, "act": [round(a, 1) for a in act],
            "plan": [round(p, 1) for p in plan], "moves": moves, "n": len(snaps)}


def to_spec(B: Dict[str, Any], theme: str) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = [
        {"type": "kpi", "items": [
            {"label": "Snapshot", "value": B["n"], "format": "number"},
            {"label": "Progres akhir", "value": f"{B['act'][-1]:.0f}%", "color": "#38BDF8"},
            {"label": "Rencana akhir", "value": f"{B['plan'][-1]:.0f}%", "color": "#94A3B8"},
            {"label": "Selisih", "value": f"{B['act'][-1] - B['plan'][-1]:+.0f} pp",
             "color": "#34D399" if B["act"][-1] >= B["plan"][-1] else "#FB7185"},
        ]},
        {"type": "chart", "chart": "line", "span": 12,
         "title": "Burn-up portofolio (rata-rata progres tertimbang sederhana)",
         "subtitle": "Aktual vs Rencana per snapshot mingguan",
         "width": 1000, "height": 380,
         "data": {"labels": B["labels"], "series": {"Aktual": B["act"], "Rencana": B["plan"]}},
         "options": {"area": True, "markers": True}},
        {"type": "html", "span": 12, "html":
            "<div style='padding:6px 8px'><div style='font-size:15px;font-weight:700;"
            "margin-bottom:10px'>Pergerakan antar snapshot pertama → terakhir</div>"
            "<table><thead><tr><th>Proyek</th><th>Dari</th><th>Ke</th><th>Δ pp</th>"
            "<th>Status</th><th>Catatan</th></tr></thead><tbody>"
            + "".join(f"<tr><td>{sc.esc(m['name'])}</td><td>{m['from']}</td>"
                      f"<td>{m['to']:.0f}%</td><td>{m['d']:+.1f}</td><td>{m['rag']}</td>"
                      f"<td>{'⚠️ stagnan ≥2 snapshot' if m['stagnant'] else ''}</td></tr>"
                      for m in B["moves"])
            + "</tbody></table></div>",
         "note": "Stagnan = progres berubah <0,5 pp pada seluruh snapshot setelah yang pertama."},
    ]
    return {"title": "Burn-up Portofolio Multi-Periode",
            "subtitle": f"{B['n']} snapshot riwayat append-only (history.jsonl)",
            "theme": theme, "locale": "id", "currency": "Rp",
            "chips": [f"{B['n']} minggu", f"akhir {B['act'][-1]:.0f}% vs "
                                          f"{B['plan'][-1]:.0f}%"],
            "sections": sections,
            "footer": "Sumber: history.jsonl via weekly_diff.py snap · DAN · burnup.py"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · multi-period burn-up")
    ap.add_argument("--log", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables", "burnup.html"))
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    a = ap.parse_args(argv)
    snaps = load(a.log)
    if len(snaps) < 2:
        print("[DAN] riwayat <2 snapshot — jalankan `weekly_diff.py snap` tiap minggu "
              "dulu; tidak membuat grafik dari data yang belum cukup.")
        return 2
    B = build(snaps)
    html = mi.to_html(mi.build_spec(to_spec(B, a.theme)), a.theme, "wide")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(html)
    print(f"[DAN] burn-up {B['n']} snapshot: aktual {B['act'][-1]:.0f}% vs rencana "
          f"{B['plan'][-1]:.0f}% -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
