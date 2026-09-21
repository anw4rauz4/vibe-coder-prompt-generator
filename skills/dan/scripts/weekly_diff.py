#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly_diff.py — Lanjutan arahan: riwayat append-only + diff antar-minggu.

  snap   -> tambahkan satu snapshot ringkas project_report.json ke history.jsonl
            (append-only: tidak pernah mengubah baris lama => bisa diaudit)
  diff   -> bandingkan dua snapshot/report: delta progres, perubahan RAG,
            tugas baru/stalled/terlambat, delta budget, dan narasi "apa yang berubah"

PAKAI
  python3 weekly_diff.py snap --report project_report.json --log history.jsonl
  python3 weekly_diff.py diff --a history.jsonl@3 --b history.jsonl@latest --out diff.md
  python3 weekly_diff.py diff --a report_lalu.json --b report_sekarang.json --out diff.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

RAG_ICON = {"good": "🟢", "warn": "🟡", "bad": "🔴"}


def _load_report(p: str) -> Dict[str, Any]:
    d = json.load(open(p, encoding="utf-8"))
    if "projects" in d and "portfolio" in d:
        return d
    if "projects" in d:                      # projects.json mentah
        import project_monitor as pm
        return pm.compute(d)
    raise ValueError("bukan report/projects json")


def snapshot(rep: Dict[str, Any]) -> Dict[str, Any]:
    return {"ts": datetime.now().isoformat(timespec="seconds"),
            "today": rep["meta"].get("today"),
            "portfolio": {k: rep["portfolio"].get(k) for k in
                          ("tasks", "on_track", "warn", "bad", "stalled", "overdue",
                           "budget_actual")},
            "projects": [{ "id": p["id"], "name": p["name"], "progress": p["progress"],
                           "planned": p["planned"], "rag": p["rag"],
                           "forecast": p.get("forecast_end"),
                           "tasks": [{"id": t["id"], "actual": t["actual"], "rag": t["rag"],
                                      "stalled": t["stalled"], "overdue": t["overdue_days"]}
                                     for t in p["tasks"]]}
                          for p in rep["projects"]]}


def _resolve(ref: str) -> Dict[str, Any]:
    """path.json  atau  path.jsonl@N  (N=index baris ke-, 'latest' = terakhir)"""
    if "@" in ref:
        path, idx = ref.rsplit("@", 1)
        lines = [ln for ln in open(path, encoding="utf-8") if ln.strip()]
        return json.loads(lines[-1 if idx == "latest" else int(idx)])
    if ref.endswith(".jsonl"):
        lines = [ln for ln in open(ref, encoding="utf-8") if ln.strip()]
        return json.loads(lines[-1])
    return snapshot(_load_report(ref))


def diff(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    pa = {p["id"]: p for p in a["projects"]}
    pb = {p["id"]: p for p in b["projects"]}
    rows, notes = [], []
    for pid, p in pb.items():
        old = pa.get(pid)
        if not old:
            rows.append({"project": p["name"], "d_progress": p["progress"],
                         "rag_from": "-", "rag_to": p["rag"], "note": "proyek baru"})
            notes.append(f"Proyek baru masuk portofolio: {p['name']}.")
            continue
        dprog = p["progress"] - old["progress"]
        moved = [t for t in p["tasks"]
                 for ot in old["tasks"] if ot["id"] == t["id"] and ot["rag"] != t["rag"]]
        new_stalled = [t["id"] for t in p["tasks"] if t["stalled"] and
                       not next((ot for ot in old["tasks"] if ot["id"] == t["id"]),
                                {}).get("stalled", False)]
        rows.append({"project": p["name"], "d_progress": round(dprog, 1),
                     "rag_from": old["rag"], "rag_to": p["rag"],
                     "moved_tasks": len(moved), "new_stalled": len(new_stalled),
                     "forecast": p.get("forecast")})
        if dprog <= 0 and p["rag"] != "good":
            notes.append(f"{p['name']} tidak bergerak ({dprog:+.1f} pp) padahal status "
                         f"{p['rag']} — perlu intervensi minggu ini.")
        if new_stalled:
            notes.append(f"{p['name']}: {len(new_stalled)} tugas baru stalled.")
        if old["rag"] != p["rag"]:
            notes.append(f"{p['name']} berubah status {RAG_ICON.get(old['rag'], '')}"
                         f"{old['rag']} → {RAG_ICON.get(p['rag'], '')}{p['rag']}.")
    ba = a.get("portfolio", {}).get("budget_actual", 0) or 0
    bb = b.get("portfolio", {}).get("budget_actual", 0) or 0
    return {"from": a.get("ts") or a.get("today"), "to": b.get("ts") or b.get("today"),
            "rows": rows, "notes": notes, "d_budget": bb - ba}


def to_markdown(D: Dict[str, Any]) -> str:
    L = [f"# Diff Mingguan — {D['from']} → {D['to']}", "",
         "| Proyek | Δ Progres (pp) | RAG | Tugas berubah | Stalled baru | Forecast |",
         "|---|---|---|---|---|---|"]
    for r in D["rows"]:
        L.append(f"| {r['project']} | {r['d_progress']:+.1f} | "
                 f"{RAG_ICON.get(r.get('rag_from'), '')}{r.get('rag_from', '-')} → "
                 f"{RAG_ICON.get(r.get('rag_to'), '')}{r.get('rag_to', '-')} | "
                 f"{r.get('moved_tasks', 0)} | {r.get('new_stalled', 0)} | "
                 f"{r.get('forecast') or r.get('note', '—')} |")
    L += ["", f"**Delta budget aktual:** {D['d_budget']:,.0f}", "", "## Apa yang berubah"]
    L += [f"- {n}" for n in D["notes"]] or ["- tidak ada perubahan signifikan"]
    L += ["", "---", "_DAN · weekly_diff (riwayat append-only di history.jsonl)._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · weekly diff & append-only history")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("snap")
    p.add_argument("--report", required=True)
    p.add_argument("--log", required=True)
    p = sub.add_parser("diff")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--out", default="")
    a = ap.parse_args(argv)

    if a.cmd == "snap":
        rep = _load_report(a.report)
        sn = snapshot(rep)
        os.makedirs(os.path.dirname(os.path.abspath(a.log)) or ".", exist_ok=True)
        with open(a.log, "a", encoding="utf-8") as f:
            f.write(json.dumps(sn, ensure_ascii=False) + "\n")
        n = sum(1 for _ in open(a.log, encoding="utf-8"))
        print(f"[DAN] snapshot #{n} -> {a.log}")
        return 0
    A, B = _resolve(a.a), _resolve(a.b)
    D = diff(A, B)
    md = to_markdown(D)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(md)
    print(md)
    if a.out:
        print(f"[DAN] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
