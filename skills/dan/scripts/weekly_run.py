#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly_run.py — Otomasi ritme mingguan PMO (sub-skill DAN #07).

Satu perintah untuk menutup loop governance mingguan:
  1. terapkan update dari form tim (batch.json) bila ada      -> projects_updated.json
  2. hitung laporan monitoring + dashboard                    -> project_report.* / project_dashboard.html
  3. bangkitkan pesan coach per owner                         -> coach.md
  4. rakit dashboard eksekutif gabungan                       -> exec_dashboard.html
  5. tulis RINGKASAN 1 HALAMAN siap kirim/cetak               -> weekly_summary.md + .html

PAKAI
  python3 weekly_run.py --projects projects.json \
      --updates batch.json \
      --marketing ../../../deliverables/analysis.json \
      --arch ../../../deliverables/arch_report.json \
      --out-dir ../../../deliverables

Bila --updates tidak diberi, langkah 1 dilewati (laporan tetap dibuat dari projects.json).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import project_monitor as pm   # noqa: E402
import i18n                # noqa: E402
import exec_dashboard as xd    # noqa: E402
import make_infographic as mi  # noqa: E402
import svg_charts as sc        # noqa: E402

RAG_ICON = {"good": "🟢", "warn": "🟡", "bad": "🔴"}


def _load(p: Optional[str]) -> Optional[Dict[str, Any]]:
    if not p or not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def pick_decisions(A: Dict[str, Any], mkt: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    """3 keputusan yang paling butuh persetujuan minggu ini."""
    out: List[Dict[str, str]] = []
    for ins in A.get("insights", []):
        if ins.get("severity") in ("bad", "warn") and len(out) < 3:
            out.append({"keputusan": ins["title"],
                        "alasan": ins["detail"],
                        "aksi": ins.get("action", ""),
                        "sumber": "monitoring proyek"})
    if mkt:
        for ins in (mkt.get("insights") or []):
            if ins.get("severity") in ("bad", "warn") and len(out) < 3:
                out.append({"keputusan": ins["title"], "alasan": ins["detail"],
                            "aksi": ins.get("action", ""), "sumber": "marketing"})
    while len(out) < 3:
        out.append({"keputusan": "Tidak ada keputusan mendesak",
                    "alasan": "Semua indikator dalam ambang; pertahankan ritme.",
                    "aksi": "Lanjutkan eksekusi rencana minggu ini.", "sumber": "-"})
    return out[:3]


def pick_focus(A: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Tugas fokus minggu depan: variance terburuk + stalled + terlambat."""
    rows = [(t, p) for p in A["projects"] for t in p["tasks"]]
    rows.sort(key=lambda tp: (not tp[0]["stalled"], tp[0]["variance"]))
    seen, out = set(), []
    for t, p in rows:
        if t["rag"] == "good" and not t["stalled"]:
            continue
        key = (p["id"], t["id"])
        if key in seen:
            continue
        seen.add(key)
        out.append({"project": p["id"], "task": t["name"], "owner": t["owner"],
                    "actual": t["actual"], "planned": t["planned"],
                    "variance": t["variance"], "rag": t["rag"], "stalled": t["stalled"],
                    "overdue": t["overdue_days"]})
        if len(out) >= 5:
            break
    return out


def build_summary(A: Dict[str, Any], coach: List[Dict[str, Any]],
                  decs: List[Dict[str, str]], focus: List[Dict[str, Any]],
                  meta_extra: Dict[str, Any], lang: str = "id") -> str:
    m, port = A["meta"], A["portfolio"]
    cur = m.get("currency", "Rp")
    L = [f"# {i18n.t('weekly_title', lang)} — {m.get('name', 'Portofolio Proyek')}", "",
         f"**{i18n.t('period', lang)}:** {meta_extra.get('period', m.get('today'))} · "
         f"**{i18n.t('compiled', lang)}:** {datetime.now():%d %b %Y %H:%M} · _DAN · PMO_", "",
         f"## {i18n.t('sec_numbers', lang)}", "",
         f"| {i18n.t('th_project', lang)} | {i18n.t('th_progress', lang)} | "
         f"{i18n.t('th_plan', lang)} | {i18n.t('th_var', lang)} | "
         f"{i18n.t('th_status', lang)} | {i18n.t('th_forecast', lang)} | "
         f"{i18n.t('th_slip', lang)} |",
         "|---|---|---|---|---|---|---|"]
    for p in A["projects"]:
        slip = f"{p['slip_days']}h" if p.get("slip_days") else "—"
        L.append(f"| {p['name']} | {p['progress']:.0f}% | {p['planned']:.0f}% | "
                 f"{p['variance']:+.0f} | {RAG_ICON[p['rag']]} {pm.RAG_LABEL[p['rag']]} | "
                 f"{p['forecast_end'] or '—'} | {slip} |")
    L += ["", f"**{i18n.t('portfolio', lang)}:** {port['tasks']} {i18n.t('tasks', lang)} · "
              f"{port['on_track']} {i18n.t('on_track', lang)} · "
              f"{port['warn']} {i18n.t('warn', lang)} · {port['bad']} "
              f"{i18n.t('critical', lang)} · {port['stalled']} {i18n.t('stalled', lang)} · "
              f"{port['overdue']} {i18n.t('overdue', lang)} · "
              f"{i18n.t('budget_used', lang)} "
              f"{port['budget_actual'] / max(1, port['budget_planned']) * 100:.0f}%", ""]
    if meta_extra.get("marketing"):
        k = meta_extra["marketing"].get("kpi", {})
        L += [f"**Marketing:** ROAS {k.get('roas', 0):.2f}x · CTR {k.get('ctr', 0):.2f}% · "
              f"health {meta_extra['marketing'].get('health_score', 0):.0f}/100 · "
              f"revenue {cur}{sc.fmt_num(k.get('revenue', 0), 'id')}", ""]
    L += [f"## {i18n.t('sec_decisions', lang)}", ""]
    for i, d in enumerate(decs, 1):
        L.append(f"{i}. **{d['keputusan']}**  ")
        L.append(f"   {i18n.t('reason', lang)}: {d['alasan']}  ")
        L.append(f"   {i18n.t('action', lang)}: {d['aksi']}  ")
        L.append(f"   _{i18n.t('source', lang)}: {d['sumber']}_")
    L += ["", f"## {i18n.t('sec_focus', lang)}", "",
          f"| {i18n.t('th_project', lang)} | {i18n.t('th_task', lang)} | "
          f"{i18n.t('th_owner', lang)} | {i18n.t('th_actual', lang)} | "
          f"{i18n.t('th_plan', lang)} | {i18n.t('th_var', lang)} | "
          f"{i18n.t('th_status', lang)} |",
          "|---|---|---|---|---|---|---|"]
    for f in focus:
        tag = (i18n.t('stalled', lang) if f["stalled"]
               else (f"{i18n.t('overdue', lang)} {f['overdue']}h" if f["overdue"]
                     else pm.RAG_LABEL[f["rag"]]))
        L.append(f"| {f['project']} | {f['task']} | {f['owner']} | {f['actual']:.0f}% | "
                 f"{f['planned']:.0f}% | {f['variance']:+.0f} | {RAG_ICON[f['rag']]} {tag} |")
    if not focus:
        L.append(f"| — | {i18n.t('all_clear', lang)} | — | — | — | — | "
                 f"{RAG_ICON['good']} {i18n.t('keep', lang)} |")
    L += ["", f"## {i18n.t('sec_coach', lang)}", ""]
    for c in coach:
        L.append(f"- **{c['owner']}** ({c['facts']['done']}/{c['facts']['tasks']} "
                 f"{i18n.t('tasks', lang)}, avg {c['facts']['avg_progress']}%): "
                 f"{c['step_15min']}")
    risks = sorted([r for p in A["projects"] for r in p["risks"]],
                   key=lambda r: -float(r.get("prob", 1)) * float(r.get("impact", 1)))[:3]
    if risks:
        L += ["", f"## {i18n.t('sec_risks', lang)}", ""]
        for r in risks:
            L.append(f"- {i18n.t('score', lang)} "
                     f"{float(r.get('prob', 1)) * float(r.get('impact', 1)):.0f} — "
                     f"{r.get('desc', '')} · {i18n.t('mitigation', lang)}: "
                     f"{r.get('mitigation', '-')} · {i18n.t('th_owner', lang).lower()}: "
                     f"{r.get('owner', '-')}")
    L += ["", "---", f"_{i18n.t('footer', lang)}_"]
    return "\n".join(L)


def summary_html(md: str, theme: str) -> str:
    """One-pager siap cetak dari ringkasan markdown (tanpa chart, ringan & ramah printer)."""
    th = sc.theme(theme)
    import re as _re
    body = []
    for line in md.split("\n"):
        s = line.rstrip()
        if s.startswith("# "):
            body.append(f"<h1>{sc.esc(s[2:])}</h1>")
        elif s.startswith("## "):
            body.append(f"<h2>{sc.esc(s[3:])}</h2>")
        elif s.startswith("|"):
            body.append(("ROW" + s))
        elif s.startswith("- "):
            body.append(f"<li>{sc.esc(s[2:])}</li>")
        elif s[:2].strip().isdigit() and ". " in s[:4]:
            body.append(f"<li>{sc.esc(s)}</li>")
        elif s.startswith("_") and s.endswith("_"):
            body.append(f"<p class='muted'>{sc.esc(s.strip('_'))}</p>")
        elif s.strip():
            body.append(f"<p>{sc.esc(s)}</p>")
    # rakit tabel
    out, table = [], []
    for b in body:
        if b.startswith("ROW"):
            cells = [c.strip() for c in b[3:].strip("|").split("|")]
            table.append(cells)
        else:
            if table:
                out.append(_table_html(table))
                table = []
            out.append(b)
    if table:
        out.append(_table_html(table))
    css = (f"body{{font-family:{sc.FONT};color:#111;margin:34px;line-height:1.5;font-size:12.5px}}"
           "h1{font-size:21px;margin:0 0 4px}h2{font-size:14px;margin:18px 0 6px;"
           "border-bottom:2px solid #111;padding-bottom:3px}"
           "table{border-collapse:collapse;width:100%;margin:8px 0;font-size:11.5px}"
           "th,td{border:1px solid #bbb;padding:4px 7px;text-align:left}"
           "th{background:#eee}li{margin:2px 0 2px 18px}.muted{color:#666;font-size:11px}"
           "@media print{body{margin:14mm}}")
    return (f"<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            f"<title>Ringkasan Mingguan</title><style>{css}</style></head><body>"
            + "\n".join(out) + "</body></html>")


def _table_html(rows: List[List[str]]) -> str:
    head, body = rows[0], rows[1:]
    h = "".join(f"<th>{sc.esc(c)}</th>" for c in head)
    trs = "".join("<tr>" + "".join(f"<td>{sc.esc(c)}</td>" for c in r) + "</tr>" for r in body)
    return f"<table><thead><tr>{h}</tr></thead><tbody>{trs}</tbody></table>"


def main(argv=None) -> int:
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · ritme mingguan PMO")
    ap.add_argument("--projects", required=True)
    ap.add_argument("--updates", default="")
    ap.add_argument("--marketing", default=os.path.join(dl, "analysis.json"))
    ap.add_argument("--arch", action="append", default=[])
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    ap.add_argument("--out-dir", default=dl)
    ap.add_argument("--period", default="")
    ap.add_argument("--lang", default="id", choices=i18n.langs())
    a = ap.parse_args(argv)

    os.makedirs(a.out_dir, exist_ok=True)
    doc = _load(a.projects)
    applied = 0
    if a.updates and os.path.exists(a.updates):
        up = _load(a.updates)
        up = up if isinstance(up, list) else up.get("updates", [])
        res = pm.apply_updates(doc, up)
        doc = res["doc"]
        applied = res["applied"]
        up_path = os.path.join(a.out_dir, "projects_updated.json")
        with open(up_path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)

    A = pm.compute(doc)
    with open(os.path.join(a.out_dir, "project_report.json"), "w", encoding="utf-8") as f:
        json.dump(A, f, ensure_ascii=False, indent=2)
    with open(os.path.join(a.out_dir, "project_report.md"), "w", encoding="utf-8") as f:
        f.write(pm.to_markdown(A))
    with open(os.path.join(a.out_dir, "project_dashboard.html"), "w", encoding="utf-8") as f:
        f.write(mi.to_html(mi.build_spec(pm.build_dashboard_spec(A)), a.theme, "a3"))
    with open(os.path.join(a.out_dir, "coach.md"), "w", encoding="utf-8") as f:
        f.write("\n\n".join(f"## {c['owner']}\n\n> {c['message']}\n\n"
                            f"**Langkah 15 menit:** {c['step_15min']}" for c in A["coach"]))

    mkt = _load(a.marketing)
    archs = [_load(p) for p in (a.arch or [os.path.join(dl, "arch_report.json")])]
    spec = xd.build_spec(mkt, A, [x for x in archs if x], "Dashboard Eksekutif DAN", a.theme)
    with open(os.path.join(a.out_dir, "exec_dashboard.html"), "w", encoding="utf-8") as f:
        f.write(mi.to_html(mi.build_spec(spec), a.theme, "wide"))

    decs = pick_decisions(A, mkt)
    focus = pick_focus(A)
    md = build_summary(A, A["coach"], decs, focus,
                       {"marketing": mkt, "period": a.period or A["meta"]["today"]},
                       lang=a.lang)
    with open(os.path.join(a.out_dir, "weekly_summary.md"), "w", encoding="utf-8") as f:
        f.write(md)
    with open(os.path.join(a.out_dir, "weekly_summary.html"), "w", encoding="utf-8") as f:
        f.write(summary_html(md, a.theme))

    port = A["portfolio"]
    print(f"[DAN] weekly run: updates diterapkan {applied} | "
          f"{port['on_track']} on-track / {port['warn']} waspada / {port['bad']} kritis / "
          f"{port['stalled']} stalled")
    print(f"[DAN] -> weekly_summary.md / weekly_summary.html / exec_dashboard.html / "
          f"project_dashboard.html / coach.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
