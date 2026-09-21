#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
print_deck.py — Deck rapat pimpinan versi CETAK (A4 landscape), dari data yang sama
dengan exec_dashboard. Tiap halaman = satu pesan; chart SVG inline sehingga tajam
dicetak dan tetap bisa "Save as PDF" dengan layout terkunci.

Halaman: 1 sampul+KPI · 2 marketing · 3 eksekusi proyek · 4 portofolio bangunan ·
         5 insight & rekomendasi.

PAKAI
  python3 print_deck.py --marketing analysis.json --project project_report.json \
      --arch arch_report.json --out deliverables/deck_pimpinan.pdf.html
  # lalu browser → Ctrl/Cmd+P → landscape → Save as PDF
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import svg_charts as sc   # noqa: E402
import make_infographic as mi  # noqa: E402

CSS = """
@page { size: A4 landscape; margin: 10mm; }
*{box-sizing:border-box}
body{margin:0;font-family:%(font)s;color:#111;background:#fff}
.pslide{width:277mm;height:190mm;padding:8mm 10mm;page-break-after:always;
position:relative;overflow:hidden}
.pslide:last-child{page-break-after:auto}
h1{font-size:26pt;margin:0 0 4mm;letter-spacing:-.5px}
h2{font-size:15pt;margin:0 0 5mm;border-bottom:2px solid #111;padding-bottom:2mm}
.sub{color:#555;font-size:10pt;line-height:1.5;max-width:200mm}
.row{display:flex;gap:6mm}
.row>div{flex:1;min-width:0}
.row svg{width:100%%;height:auto}
.kpis{display:flex;gap:4mm;flex-wrap:wrap;margin:4mm 0}
.kpi{border:1px solid #ccc;border-radius:4mm;padding:3mm 4mm;min-width:38mm}
.kpi .l{font-size:7.5pt;color:#666;text-transform:uppercase;letter-spacing:.4px}
.kpi .v{font-size:16pt;font-weight:800;letter-spacing:-.5px}
ul{margin:2mm 0;padding-left:6mm}li{font-size:10pt;margin-bottom:2mm;line-height:1.45}
.note{position:absolute;bottom:6mm;left:10mm;right:10mm;font-size:7.5pt;color:#777}
table{border-collapse:collapse;width:100%%;font-size:9pt}
th,td{border:1px solid #bbb;padding:1.6mm 2mm;text-align:left}
th{background:#eee;font-size:7.5pt;text-transform:uppercase}
"""


def _load(p: Optional[str]) -> Optional[Dict[str, Any]]:
    if not p or not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def build(mkt: Optional[Dict], prj: Optional[Dict], archs: List[Dict],
          theme: str = "light", lang: str = "id") -> str:
    import i18n
    t = lambda k: i18n.t(k, lang)
    th = sc.theme(theme)
    pages: List[str] = []
    cur = (mkt or {}).get("meta", {}).get("currency", "Rp")

    # 1 sampul
    k = (mkt or {}).get("kpi", {})
    po = (prj or {}).get("portfolio", {})
    tot_b = sum(a.get("totals", {}).get("built_area", 0) for a in archs)
    kpis = "".join(mi.kpi_card(l, v, color=c) for l, v, c in [
        ("Revenue", f"{cur}{sc.fmt_num(k.get('revenue', 0), 'id')}", "#059669"),
        ("ROAS", f"{k.get('roas', 0):.2f}x", "#2563EB"),
        ("Tugas on-track", f"{po.get('on_track', 0)}/{po.get('tasks', 0)}", "#2563EB"),
        ("Terbangun", f"{tot_b:,.0f} m²", "#7C3AED"),
        ("Mkt health", f"{(mkt or {}).get('health_score', 0):.0f}", "#7C3AED"),
    ]) if k else ""
    pages.append(f"<h1>Review Pimpinan — DAN</h1>"
                 f"<p class='sub'>Satu deck untuk keputusan: performa marketing, kesehatan "
                 f"eksekusi proyek, dan portofolio studi bangunan. Semua angka tertelusur "
                 f"ke sumber; asumsi ditandai.</p><div class='kpis'>{kpis}</div>"
                 f"<div class='note'>Dicetak dari data terkini · DAN print_deck · "
                 f"landscape A4</div>")

    # 2 marketing
    if mkt:
        ts = (mkt.get("time") or {}).get("series") or {}
        lb = (mkt.get("time") or {}).get("labels") or []
        step = max(1, len(lb) // 10)
        trend = sc.line([(lb[i], ts["revenue"][i]) for i in range(0, len(lb), step)],
                        title="Tren revenue", th=theme, width=640, height=300,
                        area=True, markers=False) if ts.get("revenue") and lb else ""
        ch = mkt.get("by_channel") or []
        roas = sc.hbar([(c["name"], c["kpi"]["roas"]) for c in ch], title="ROAS per channel",
                       th=theme, width=520, height=300,
                       value_fmt=lambda v: f"{v:.2f}x") if ch else ""
        pages.append(f"<h2>{t('deck_mkt')}</h2><div class='row'><div>{trend}</div>"
                     f"<div>{roas}</div></div>"
                     f"<div class='note'>Target ROAS ≥ 3x; channel di bawah break-even "
                     f"(1 ÷ margin) adalah kandidat realokasi.</div>")

    # 3 proyek
    if prj:
        P = prj["projects"]
        prog = sc.progress([{"label": p["name"][:22], "value": p["progress"],
                             "target": p["planned"], "rag": p["rag"]} for p in P],
                           title="Progres vs rencana", th=theme, width=560)
        tasks = [{"name": t["name"], "start": t["start"], "end": t["end"],
                  "progress": t["actual"], "rag": t["rag"], "owner": t["owner"]}
                 for p in P for t in p["tasks"]]
        gantt = sc.gantt(tasks, title="Tracking tugas", th=theme, width=640, row_h=22)
        pages.append(f"<h2>{t('deck_prj')}</h2><div class='row'><div>{prog}</div>"
                     f"<div>{gantt}</div></div>"
                     f"<div class='note'>Guard mingguan memastikan tugas kritis/stalled "
                     f"tidak lolos tanpa tindakan ber-owner.</div>")

    # 4 arsitektur
    if archs:
        names = [a.get("meta", {}).get("name", f"Studi {i+1}")[:20]
                 for i, a in enumerate(archs)]
        b1 = sc.bar(list(zip(names, [a.get("totals", {}).get("built_area", 0)
                                     for a in archs])), title="Luas terbangun (m²)",
                    th=theme, width=560, height=300)
        b2 = sc.hbar(list(zip(names, [a.get("rab_total", 0) for a in archs])),
                     title="RAB estimasi", th=theme, width=560, height=300,
                     value_fmt=lambda v: f"{cur}{sc.fmt_num(v, 'id')}")
        rows = "".join(f"<tr><td>{sc.esc(n)}</td><td>{a['totals']['built_area']:.0f}</td>"
                       f"<td>{a['compliance']['kdb']:.0f}% / {a['compliance']['kdb_max']:.0f}%</td>"
                       f"<td>{'aman' if a['compliance']['kdb_ok'] else 'LEBIH'}</td></tr>"
                       for n, a in zip(names, archs))
        pages.append(f"<h2>{t('deck_arch')}</h2><div class='row'><div>{b1}</div>"
                     f"<div>{b2}</div></div>"
                     f"<table><tr><th>Studi</th><th>m²</th><th>KDB vs batas</th><th>Status</th></tr>"
                     f"{rows}</table>")

    # 5 insight
    ins = (mkt or {}).get("insights", [])[:4]
    rec = (mkt or {}).get("recommendations", [])[:5]
    li = "".join(f"<li><b>{sc.esc(i['title'])}</b> — {sc.esc(i['detail'][:140])}</li>"
                 for i in ins)
    lr = "".join(f"<li>{sc.esc(r)}</li>" for r in rec)
    pages.append(f"<h2>{t('deck_ins')}</h2><div class='row'>"
                 f"<div><h2 style='font-size:11pt;border:none'>Insight utama</h2><ul>{li}</ul></div>"
                 f"<div><h2 style='font-size:11pt;border:none'>Rekomendasi</h2><ul>{lr}</ul></div>"
                 f"</div><div class='note'>Keputusan diminta pada rapat ini: setujui/ubah "
                 f"realokasi budget & tenggat uji.</div>")

    body = "".join(f"<section class='pslide'>{p}</section>" for p in pages)
    css = CSS % {"font": sc.FONT}
    return (f"<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            f"<title>Deck Pimpinan</title><style>{css}</style></head><body>{body}"
            f"</body></html>")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · print deck A4 landscape")
    ap.add_argument("--marketing", default="")
    ap.add_argument("--project", default="")
    ap.add_argument("--arch", action="append", default=[])
    ap.add_argument("--theme", default="light", choices=list(sc.THEMES))
    ap.add_argument("--lang", default="id", choices=["id", "en", "zh"])
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables",
                                                   "deck_pimpinan.html"))
    a = ap.parse_args(argv)
    archs = [_load(p) for p in a.arch]
    html = build(_load(a.marketing), _load(a.project), [x for x in archs if x],
                 a.theme, a.lang)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(html)
    print(f"[DAN] deck cetak {html.count('pslide')} halaman -> {a.out} "
          f"(browser → Print → landscape → PDF)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
