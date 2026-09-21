#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_client.py — Dashboard GABUNGAN lintas-klien dengan filter interaktif.

Membaca beberapa analysis.json (satu per klien) dan menyusun SATU halaman:
  - tabel perbandingan antar-klien (revenue, ROAS, CTR, CVR, CPA, health),
  - tab per klien (KPI + tren + channel) yang bisa difilter tanpa reload,
  - halaman "semua klien" sebagai pandangan portofolio agensi.
Self-contained (SVG inline + JS vanilla, tanpa CDN).

PAKAI
  python3 multi_client.py --client "Kopi Enak=analysis_a.json" \
      --client "Fashion X=analysis_b.json" --out deliverables/dashboard_agensi.html
  python3 multi_client.py --dir deliverables --pattern "analysis_*.json"
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import svg_charts as sc   # noqa: E402

CSS = """
body{font-family:%(font)s;background:#0F172A;color:#F1F5F9;margin:0;padding:26px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:15px;margin:22px 0 8px}
.sub{color:#94A3B8;font-size:12.5px;margin:0 0 16px}
.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}
.tabs button{background:#16233F;border:1px solid #24344F;color:#F1F5F9;border-radius:999px;
padding:7px 16px;font-size:12.5px;cursor:pointer}
.tabs button.on{background:#38BDF8;color:#06283c;border-color:#38BDF8}
table{border-collapse:collapse;width:100%%;font-size:12.5px;margin:8px 0}
th,td{border:1px solid #24344F;padding:7px 9px;text-align:left}
th{color:#94A3B8;font-size:10.5px;text-transform:uppercase}
td.n{text-align:right;font-variant-numeric:tabular-nums}
.kpis{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0}
.kpi{background:#16233F;border:1px solid #24344F;border-radius:14px;padding:12px 16px;
min-width:130px}.kpi .l{font-size:10.5px;color:#94A3B8;text-transform:uppercase}
.kpi .v{font-size:20px;font-weight:800;margin-top:3px}
.row{display:flex;gap:16px;flex-wrap:wrap}.row>div{flex:1;min-width:300px}
.row svg{width:100%%;height:auto}
.view{display:none}.view.on{display:block}
"""


def _load(p: str) -> Dict[str, Any]:
    return json.load(open(p, encoding="utf-8"))


def build(clients: List[Tuple[str, Dict[str, Any]]], theme: str = "dan") -> str:
    th = sc.theme(theme)
    cur = "Rp"
    rows = []
    for name, A in clients:
        k = A.get("kpi", {})
        rows.append((name, k))
    cmp_rows = "".join(
        f"<tr><td>{sc.esc(n)}</td><td class='n'>{cur}{sc.fmt_num(k.get('revenue', 0), 'id')}</td>"
        f"<td class='n'>{k.get('roas', 0):.2f}x</td><td class='n'>{k.get('ctr', 0):.2f}%</td>"
        f"<td class='n'>{k.get('cvr', 0):.2f}%</td>"
        f"<td class='n'>{cur}{sc.fmt_num(k.get('cpa', 0), 'id')}</td>"
        f"<td class='n'>{A.get('health_score', 0):.0f}</td></tr>" for n, k in rows)
    views = []
    for i, (name, A) in enumerate(clients):
        k = A.get("kpi", {})
        ts = (A.get("time") or {}).get("series") or {}
        lb = (A.get("time") or {}).get("labels") or []
        step = max(1, len(lb) // 10)
        trend = sc.line([(lb[j], ts["revenue"][j]) for j in range(0, len(lb), step)],
                        title=f"Tren revenue — {name}", th=theme, width=640, height=300,
                        area=True, markers=False) if ts.get("revenue") and lb else ""
        ch = A.get("by_channel") or []
        roas = sc.hbar([(c["name"], c["kpi"]["roas"]) for c in ch],
                       title="ROAS per channel", th=theme, width=520, height=300,
                       value_fmt=lambda v: f"{v:.2f}x") if ch else ""
        kpis = "".join(f"<div class='kpi'><div class='l'>{l}</div><div class='v'>{v}</div></div>"
                       for l, v in [("Revenue", f"{cur}{sc.fmt_num(k.get('revenue', 0), 'id')}"),
                                    ("ROAS", f"{k.get('roas', 0):.2f}x"),
                                    ("CTR", f"{k.get('ctr', 0):.2f}%"),
                                    ("CVR", f"{k.get('cvr', 0):.2f}%"),
                                    ("Health", f"{A.get('health_score', 0):.0f}")])
        views.append(f"<div class='view' id='v{i}'><div class='kpis'>{kpis}</div>"
                     f"<div class='row'><div>{trend}</div><div>{roas}</div></div></div>")
    tabs = ("<button class='on' onclick=\"show(-1)\">Semua klien</button>" +
            "".join(f"<button onclick='show({i})'>{sc.esc(n)}</button>"
                    for i, (n, _) in enumerate(clients)))
    js = ("function show(i){document.querySelectorAll('.view').forEach(function(v,k)"
          "{v.classList.toggle('on',k===i);});"
          "document.querySelectorAll('.tabs button').forEach(function(b,k)"
          "{b.classList.toggle('on',k===(i+1));});"
          "document.getElementById('cmp').style.display=(i===-1)?'':'none';}"
          "show(-1);")
    body = (f"<h1>Dashboard Agensi — {len(clients)} klien</h1>"
            f"<p class='sub'>Filter tanpa reload · data per klien dari analysis.json "
            f"masing-masing · angka tertelusur ke sumber.</p>"
            f"<div class='tabs'>{tabs}</div>"
            f"<div id='cmp'><h2>Perbandingan antar-klien</h2>"
            f"<table><tr><th>Klien</th><th>Revenue</th><th>ROAS</th><th>CTR</th><th>CVR</th>"
            f"<th>CPA</th><th>Health</th></tr>{cmp_rows}</table></div>"
            + "".join(views))
    css = CSS % {"font": sc.FONT}
    return (f"<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            f"<title>Dashboard Agensi</title><style>{css}</style></head><body>{body}"
            f"<script>{js}</script></body></html>")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · multi-client dashboard")
    ap.add_argument("--client", action="append", default=[],
                    help="Nama=path/analysis.json (boleh berulang)")
    ap.add_argument("--dir", default="")
    ap.add_argument("--pattern", default="analysis_*.json")
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables",
                                                   "dashboard_agensi.html"))
    a = ap.parse_args(argv)
    clients: List[Tuple[str, Dict[str, Any]]] = []
    for c in a.client:
        if "=" in c:
            n, p = c.split("=", 1)
            clients.append((n, _load(p)))
    if a.dir:
        for f in sorted(os.listdir(a.dir)):
            if fnmatch.fnmatch(f, a.pattern):
                clients.append((os.path.splitext(f)[0], _load(os.path.join(a.dir, f))))
    if not clients:
        print("[DAN] tidak ada klien; pakai --client Nama=path atau --dir+--pattern")
        return 2
    html = build(clients, a.theme)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(html)
    print(f"[DAN] dashboard agensi: {len(clients)} klien -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
