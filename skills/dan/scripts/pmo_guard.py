#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pmo_guard.py — Policy-as-code: gerbang kualitas ritme mingguan (sub-skill DAN #07).

Memastikan setiap sinyal buruk punya tanggungan, altrimenti exit code != 0
(sehingga bisa dipakai sebagai gate di CI/cron):

  G1  Tugas Kritis (rag=bad) atau STALLED wajib punya SALAH SATU:
        - tindakan controlling ber-status open/in-progress di proyeknya, ATAU
        - update progress dalam 7 hari terakhir (tercatat di history)
  G2  Proyek dengan CPI < 0,85 wajib punya tindakan open/in-progress
  G3  Risiko skor >= 12 wajib punya owner DAN mitigasi
  G4  Tugas terlambat > 3 hari wajib disebut di tindakan ATAU punya update < 7 hari
  G5  (warn) Proyek waspada (rag=warn) tanpa catatan monitoring dalam 14 hari

PAKAI
  python3 pmo_guard.py projects.json                 # baca model terhitung bila ada
  python3 pmo_guard.py projects.json --report out.md
  python3 pmo_guard.py projects.json --strict        # pelanggaran warn pun menggagalkan
  exit code: 0 = bersih · 1 = ada pelanggaran high · 2 = file/model error
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import project_monitor as pm  # noqa: E402

SEV_ICON = {"high": "⛔", "warn": "⚠️"}


def _d(v: Any) -> Optional[datetime]:
    return pm.d(v)


def evaluate(doc: Dict[str, Any], A: Dict[str, Any]) -> List[Dict[str, Any]]:
    now = _d(A["meta"].get("today")) or datetime.now()
    hist = doc.get("history", []) or []
    viol: List[Dict[str, Any]] = []

    def last_update(pid: str, days: int) -> bool:
        cut = now - timedelta(days=days)
        return any((h.get("project") == pid and h.get("form") in ("progress", "monitoring")
                    and (_d(h.get("date")) or cut) >= cut) for h in hist)

    for p in A["projects"]:
        pid = p["id"]
        open_act = [a for a in p.get("actions", [])
                    if str(a.get("status", "open")).lower() in ("open", "in-progress")]
        upd7 = last_update(pid, 7)
        upd14 = last_update(pid, 14)
        for t in p["tasks"]:
            if t["rag"] == "bad" or t["stalled"]:
                if not (open_act or upd7):
                    viol.append({"code": "G1", "severity": "high",
                                 "message": f"Tugas {'stalled' if t['stalled'] else 'kritis'} "
                                            f"tanpa tindakan/update: {pid}/{t['name']} "
                                            f"({t['actual']:.0f}% vs {t['planned']:.0f}%)",
                                 "owner": t["owner"]})
            if t["overdue_days"] > 3 and not (open_act or upd7):
                viol.append({"code": "G4", "severity": "high",
                             "message": f"Tugas terlambat {t['overdue_days']} hari tanpa "
                                        f"tindakan: {pid}/{t['name']}", "owner": t["owner"]})
        if p.get("cpi") and p["cpi"] < 0.85 and not open_act:
            viol.append({"code": "G2", "severity": "high",
                         "message": f"CPI {p['cpi']:.2f} (<0,85) tanpa tindakan korektif: "
                                    f"{pid} {p['name']}", "owner": p["owner"]})
        for r in p.get("risks", []):
            score = float(r.get("prob", 1)) * float(r.get("impact", 1))
            if score >= 12 and (not r.get("owner") or not r.get("mitigation")):
                viol.append({"code": "G3", "severity": "high",
                             "message": f"Risiko skor {score:.0f} tanpa owner/mitigasi: "
                                        f"{pid} — {r.get('desc', '')[:50]}",
                             "owner": r.get("owner", "-")})
        if p["rag"] == "warn" and not upd14:
            viol.append({"code": "G5", "severity": "warn",
                         "message": f"Proyek waspada tanpa catatan monitoring 14 hari: "
                                    f"{pid} {p['name']}", "owner": p["owner"]})
    order = {"high": 0, "warn": 1}
    return sorted(viol, key=lambda v: (order[v["severity"]], v["code"]))


def to_markdown(viol: List[Dict[str, Any]], A: Dict[str, Any], strict: bool) -> str:
    m = A["meta"]
    n_high = sum(1 for v in viol if v["severity"] == "high")
    n_warn = sum(1 for v in viol if v["severity"] == "warn")
    L = [f"# PMO Guard — {m.get('name', '')}", "",
         f"**Per {m.get('today')}** · status: "
         + ("**GAGAL**" if (n_high or (strict and n_warn)) else "**BERSIH**")
         + f" · pelanggaran: {n_high} high / {n_warn} warn", "",
         "| Kode | Sev | Temuan | Owner |", "|---|---|---|---|"]
    for v in viol:
        L.append(f"| {v['code']} | {SEV_ICON[v['severity']]} {v['severity']} | "
                 f"{v['message']} | {v.get('owner', '-')} |")
    if not viol:
        L.append("| — | — | tidak ada pelanggaran; semua sinyal buruk punya tanggungan | — |")
    L += ["", "## Aturan yang ditegakkan", "",
          "- G1 tugas kritis/stalled → wajib tindakan open atau update ≤7 hari",
          "- G2 CPI < 0,85 → wajib tindakan korektif open",
          "- G3 risiko skor ≥12 → wajib owner + mitigasi",
          "- G4 terlambat >3 hari → wajib tindakan atau update ≤7 hari",
          "- G5 (warn) proyek waspada → wajib catatan monitoring ≤14 hari", "",
          "_Dijalankan otomatis oleh CI/cron (`weekly-pmo.yml`). Exit 0 = bersih, "
          "1 = ada high, 2 = error input._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · PMO policy gate")
    ap.add_argument("projects")
    ap.add_argument("--report", default="")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    try:
        with open(a.projects, encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        print(f"[DAN] ERROR membaca projects: {e}")
        return 2
    A = pm.compute(doc)
    viol = evaluate(doc, A)
    n_high = sum(1 for v in viol if v["severity"] == "high")
    n_warn = sum(1 for v in viol if v["severity"] == "warn")
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(to_markdown(viol, A, a.strict))
    for v in viol:
        print(f"[{v['code']} {v['severity'].upper()}] {v['message']} (owner: {v.get('owner', '-')})")
    print(f"[DAN] pmo guard: {n_high} high / {n_warn} warn -> "
          + ("GAGAL" if (n_high or (a.strict and n_warn)) else "BERSIH"))
    if n_high or (a.strict and n_warn):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
