#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
narrative_trend.py — Eval berkelanjutan untuk kualitas TULISAN keluaran DAN.

Memindai laporan yang ada (analysis.md, weekly_summary.md, laporan_klien*.md, dll),
menjalankan narrative_check + claim_audit pada masing-masing, lalu mencatat ke
`skills/dan/narrative_history.jsonl` (skor narasi, cakupan angka, jumlah temuan, ts)
dan merender tren + laporan. Dirancang dipanggil cron mingguan bersama weekly_watch.

PAKAI
  python3 narrative_trend.py --dir deliverables --out deliverables/narrative_trend.html
  python3 narrative_trend.py --files a.md b.md          # sampel tertentu
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
HIST = os.path.join(ROOT, "skills", "dan", "narrative_history.jsonl")
sys.path.insert(0, HERE)
import narrative_check as nc   # noqa: E402
import claim_audit as ca       # noqa: E402
import svg_charts as sc        # noqa: E402

PATTERNS = ("analysis.md", "weekly_summary.md", "laporan_klien", "client_report",
            "release_", "digest_")


def scan(files: List[str], sources: List[str]) -> List[Dict[str, Any]]:
    rows = []
    for f in files:
        text = open(f, encoding="utf-8", errors="replace").read()
        N = nc.check(text)
        cov = None
        if sources:
            R = ca.audit(f, sources, 0.051)
            cov = R["coverage_pct"]
        rows.append({"ts": datetime.now().isoformat(timespec="seconds"),
                     "file": os.path.basename(f), "narrative_score": N["score"],
                     "findings": len(N["findings"]), "claim_coverage": cov})
    return rows


def load_hist() -> List[Dict[str, Any]]:
    if not os.path.exists(HIST):
        return []
    return [json.loads(ln) for ln in open(HIST, encoding="utf-8") if ln.strip()]


def render(hist: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> str:
    allr = hist + rows
    seen = {}
    for r in allr:
        seen.setdefault(r["file"], []).append(r)
    cards = []
    for f, rs in seen.items():
        last = rs[-1]
        cards.append(f"<div class='c'><div class='n'>{f}</div>"
                     f"<div>skor narasi <b>{last['narrative_score']}</b> · "
                     f"temuan {last['findings']}" +
                     (f" · cakupan angka {last['claim_coverage']}%"
                      if last.get("claim_coverage") is not None else "") +
                     f" · {len(rs)} pengukuran</div></div>")
    trend = sc.line([(r["ts"][5:16], r["narrative_score"]) for r in allr[-20:]],
                    title="Tren skor narasi (20 pengukuran terakhir)",
                    width=900, height=300, area=True, markers=True) if len(allr) >= 2 \
        else "<div class='c'>tren muncul mulai pengukuran ke-2</div>"
    css = ("body{font-family:%s;background:#0F172A;color:#F1F5F9;margin:0;padding:26px}"
           "h1{font-size:24px}.c{background:#16233F;border:1px solid #24344F;"
           "border-radius:12px;padding:12px;margin:8px 0;font-size:13px}"
           ".n{font-weight:700;margin-bottom:4px}svg{width:100%%;height:auto}"
           ".mut{color:#94A3B8;font-size:12px}") % sc.FONT
    body = ("<h1>Tren Kualitas Narasi DAN</h1><p class='mut'>Diukur otomatis oleh "
            "narrative_check + claim_audit; dicatat append-only di "
            "narrative_history.jsonl.</p>" + trend + "".join(cards))
    return (f"<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            f"<title>Tren Narasi</title><style>{css}</style></head><body>{body}"
            f"</body></html>")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · narrative quality trend")
    ap.add_argument("--dir", default="")
    ap.add_argument("--files", nargs="*", default=[])
    ap.add_argument("--source", action="append", default=[])
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables",
                                                   "narrative_trend.html"))
    ap.add_argument("--no-record", action="store_true")
    a = ap.parse_args(argv)
    files = list(a.files)
    if a.dir:
        files += [os.path.join(a.dir, f) for f in sorted(os.listdir(a.dir))
                  if any(p in f for p in PATTERNS) and f.endswith(".md")]
    if not files:
        print("[DAN] tidak ada berkas laporan untuk dievaluasi")
        return 2
    rows = scan(files, a.source)
    if not a.no_record:
        with open(HIST, "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    hist = load_hist()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(render(hist, []))
    avg = sum(r["narrative_score"] for r in rows) / len(rows)
    print(f"[DAN] narrative trend: {len(rows)} laporan dievaluasi · skor rata-rata "
          f"{avg:.0f}/100 -> {a.out}")
    worst = min(rows, key=lambda r: r["narrative_score"])
    print(f"[DAN] terendah: {worst['file']} ({worst['narrative_score']}) — "
          f"perbaiki dulu sebelum dibagikan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
