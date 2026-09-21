#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exec_dashboard.py — Dashboard Eksekutif GABUNGAN (sub-skill DAN #03).

Menyatukan tiga sumber kebenaran menjadi SATU infografik untuk rapat pimpinan:
  1. Marketing   : deliverables/analysis.json      (hasil dan_analytics.py)
  2. Proyek      : deliverables/project_report.json(hasil project_monitor.py)
  3. Arsitektur  : deliverables/arch_report.json + kasus lain (hasil arch_design.py)

PAKAI
  python3 exec_dashboard.py \
      --marketing ../../../deliverables/analysis.json \
      --project   ../../../deliverables/project_report.json \
      --arch      ../../../deliverables/arch_report.json \
      --arch      ../../../deliverables/kafe_report.json \
      --arch      ../../../deliverables/ruko_report.json \
      --out       ../../../deliverables/exec_dashboard.html

Bila suatu sumber tidak ada, bagiannya dilewati dengan anggun (tidak gagal).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_infographic as mi  # noqa: E402
import svg_charts as sc        # noqa: E402


def _load(p: Optional[str]) -> Optional[Dict[str, Any]]:
    if not p or not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def build_spec(mkt: Optional[Dict], prj: Optional[Dict],
               archs: List[Dict], title: str, theme: str) -> Dict[str, Any]:
    cur = (mkt or {}).get("meta", {}).get("currency", "Rp")
    sections: List[Dict[str, Any]] = []
    kpis: List[Dict[str, Any]] = []
    insights: List[Dict[str, Any]] = []
    recos: List[str] = []
    chips: List[str] = []

    # ---------------- marketing
    if mkt:
        k = mkt.get("kpi", {})
        t = mkt.get("trend", {}) or {}
        kpis += [
            {"label": "Revenue", "value": f"{cur}{sc.fmt_num(k.get('revenue', 0), 'id')}",
             "delta": t.get("growth_pct_period"), "color": "#34D399"},
            {"label": "ROAS", "value": f"{k.get('roas', 0):.2f}x", "color": "#38BDF8"},
            {"label": "Mkt Health", "value": f"{mkt.get('health_score', 0):.0f}",
             "color": "#A78BFA"},
        ]
        chips.append(f"Mkt health {mkt.get('health_score', 0):.0f}/100")
        ts = (mkt.get("time") or {}).get("series") or {}
        labels = (mkt.get("time") or {}).get("labels") or []
        if ts.get("revenue") and labels:
            step = max(1, len(labels) // 12)
            sections.append({
                "type": "chart", "chart": "line", "span": 8,
                "title": "Marketing · Tren Revenue",
                "subtitle": f"slope {t.get('slope_revenue', 0):+,.0f}/hari · R² {t.get('r2_revenue', 0):.2f}",
                "width": 880, "height": 340,
                "data": {"labels": [labels[i] for i in range(0, len(labels), step)],
                         "series": {"Revenue": [ts["revenue"][i] for i in range(0, len(labels), step)]}},
                "options": {"area": True, "markers": False}})
        ch = mkt.get("by_channel") or []
        if ch:
            sections.append({"type": "chart", "chart": "hbar", "span": 4,
                             "title": "Marketing · ROAS per Channel",
                             "subtitle": "target ≥ 3,0x", "width": 520, "height": 340,
                             "data": [(c["name"], c["kpi"]["roas"]) for c in ch],
                             "options": {"value_fmt": "x"}})
            sections.append({"type": "chart", "chart": "donut", "span": 4,
                             "title": "Marketing · Kontribusi Revenue",
                             "width": 520, "height": 340,
                             "data": [(c["name"], c["kpi"]["revenue"]) for c in ch],
                             "options": {"center_value": f"{cur}{sc.fmt_num(k.get('revenue', 0), 'id')}",
                                         "center_label": "total"}})
        for i in (mkt.get("insights") or [])[:2]:
            insights.append(i)
        recos += (mkt.get("recommendations") or [])[:2]

    # ---------------- project
    if prj:
        port = prj.get("portfolio", {})
        P = prj.get("projects", [])
        kpis += [
            {"label": "Proyek on-track", "value": f"{port.get('on_track', 0)}/{port.get('tasks', 0)}",
             "color": "#34D399"},
            {"label": "Tugas kritis", "value": port.get("bad", 0), "color": "#FB7185"},
            {"label": "Stalled", "value": port.get("stalled", 0), "color": "#FBBF24"},
        ]
        chips.append(f"{port.get('on_track', 0)} on-track · {port.get('bad', 0)} kritis · "
                     f"{port.get('stalled', 0)} stalled")
        if P:
            sections.append({"type": "chart", "chart": "progress", "span": 6,
                             "title": "Proyek · Progres vs Rencana",
                             "subtitle": "bar = aktual · garis = rencana hari ini",
                             "width": 620, "height": max(140, 40 + len(P) * 34),
                             "data": [{"label": p["name"][:24], "value": p["progress"],
                                       "target": p["planned"], "rag": p["rag"]} for p in P]})
            tasks = [{"name": f"{t['name']}", "start": t["start"], "end": t["end"],
                      "progress": t["actual"], "rag": t["rag"], "owner": t["owner"]}
                     for p in P for t in p["tasks"]]
            sections.append({"type": "chart", "chart": "gantt", "span": 6,
                             "title": "Proyek · Tracking Tugas (Gantt)",
                             "subtitle": "warna = RAG · angka = progres aktual",
                             "width": 620, "height": max(160, 40 + len(tasks) * 26),
                             "data": tasks, "options": {"row_h": 26,
                                                        "today": prj.get("meta", {}).get("today")}})
        for i in (prj.get("insights") or [])[:2]:
            insights.append(i)
        for c in (prj.get("coach") or [])[:2]:
            recos.append(f"[Coach {c['owner']}] {c['step_15min']}")

    # ---------------- architecture
    archs = [a for a in archs if a]
    if archs:
        tot_built = sum(a.get("totals", {}).get("built_area", 0) for a in archs)
        tot_rab = sum(a.get("rab_total", 0) for a in archs)
        kpis += [
            {"label": "Portofolio bangunan", "value": len(archs), "format": "number"},
            {"label": "Total terbangun", "value": f"{tot_built:,.0f} m²", "color": "#22D3EE"},
            {"label": "Total RAB", "value": f"{cur}{sc.fmt_num(tot_rab, 'id')}", "color": "#F472B6"},
        ]
        chips.append(f"{len(archs)} studi bangunan · {tot_built:,.0f} m²")
        names = [a.get("meta", {}).get("name", f"Studi {i + 1}")[:22] for i, a in enumerate(archs)]
        sections.append({"type": "chart", "chart": "bar", "span": 6,
                         "title": "Arsitektur · Luas Terbangun per Studi",
                         "width": 620, "height": 320,
                         "data": list(zip(names, [a.get("totals", {}).get("built_area", 0)
                                                  for a in archs])),
                         "options": {"value_fmt": lambda v: f"{v:,.0f} m²"}})
        sections.append({"type": "chart", "chart": "hbar", "span": 6,
                         "title": "Arsitektur · RAB per Studi",
                         "subtitle": "estimasi kelas konsep ±25%",
                         "width": 620, "height": 320,
                         "data": list(zip(names, [a.get("rab_total", 0) for a in archs])),
                         "options": {"value_fmt": lambda v: f"{cur}{sc.fmt_num(v, 'id')}"}})
        kdb = [a for a in archs if not a.get("compliance", {}).get("kdb_ok", True)
               or not a.get("compliance", {}).get("klb_ok", True)]
        if kdb:
            insights.append({"title": f"{len(kdb)} studi melanggar KDB/KLB",
                             "detail": ", ".join(a.get("meta", {}).get("name", "?") for a in kdb),
                             "severity": "bad",
                             "action": "Kurangi footprint atau naikkan jumlah lantai bila diizinkan."})
        else:
            insights.append({"title": f"Semua {len(archs)} studi memenuhi KDB/KLB",
                             "detail": "Kepatuhan lahan aman pada seluruh studi aktif.",
                             "severity": "good",
                             "action": "Lanjutkan ke gambar kerja & verifikasi harga lokal."})

    if not sections:
        sections.append({"type": "html", "span": 12,
                         "html": "<div class='note'>Tidak ada sumber data yang ditemukan. "
                                 "Jalankan dan_analytics / project_monitor / arch_design dulu.</div>"})
    sections.append({"type": "insights", "items": insights})
    if recos:
        sections.append({"type": "recommendations", "items": recos})

    return {
        "title": title,
        "subtitle": "Satu layar untuk pimpinan: performa marketing, kesehatan eksekusi "
                    "proyek, dan portofolio studi bangunan. Marketing dari analysis.json, "
                    "eksekusi dari project_report.json, studi dari arch_report.json.",
        "theme": theme, "locale": "id", "currency": cur,
        "badge": {"value": f"{(mkt or {}).get('health_score', 0):.0f}", "label": "mkt health"},
        "chips": chips,
        "sections": ([{"type": "kpi", "items": kpis}] if kpis else []) + sections,
        "footer": "Sumber: analysis.json (marketing) · project_report.json (eksekusi) · "
                  "arch_report.json dkk (studi bangunan). RAB kelas konsep ±25%; korelasi ≠ "
                  "kausalitas; planned progress = interpolasi linear. · DAN · Executive Dashboard",
    }


def main(argv=None) -> int:
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · Executive Dashboard gabungan")
    ap.add_argument("--marketing", default=os.path.join(dl, "analysis.json"))
    ap.add_argument("--project", default=os.path.join(dl, "project_report.json"))
    ap.add_argument("--arch", action="append", default=[],
                    help="boleh berulang untuk banyak studi bangunan")
    ap.add_argument("--title", default="Dashboard Eksekutif DAN")
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    ap.add_argument("--out", default=os.path.join(dl, "exec_dashboard.html"))
    a = ap.parse_args(argv)

    archs = a.arch or [os.path.join(dl, "arch_report.json")]
    spec = build_spec(_load(a.marketing), _load(a.project),
                      [_load(p) for p in archs], a.title, a.theme)
    html = mi.to_html(mi.build_spec(spec), a.theme, "wide")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    n = len(spec["sections"])
    print(f"[DAN] executive dashboard: {n} section -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
