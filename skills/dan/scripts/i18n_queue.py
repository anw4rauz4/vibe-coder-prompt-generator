#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
i18n_queue.py — Alur terjemahan NARASI tanpa terjemahan mesin buta.

Label struktural sudah ditangani i18n.py. Narasi (insight, rekomendasi, pesan coach,
kalimat penjelas) tetap berbahasa sumber karena memuat makna & konteks angka.
Alat ini membuat proses menerjemahkannya TERKENDALI:

  extract  -> keluarkan setiap baris narasi menjadi antrean JSON ber-id
  apply    -> masukkan kembali hasil terjemahan (oleh manusia/agent) berdasarkan id

PAKAI
  python3 i18n_queue.py extract --report weekly_summary.md --out queue.json
  # ... terjemahkan field "text" di queue.json (jadi tr.json) ...
  python3 i18n_queue.py apply --report weekly_summary.md --translations tr.json \
      --out weekly_summary_en.md

Baris yang DIANGGAP NARASI: baris berisi huruf, bukan heading (#), bukan sel tabel (|),
bukan blok kode, dan bukan label struktural yang sudah ada di i18n.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import i18n  # noqa: E402

STRUCTURAL = set()
for _lang in i18n.langs():
    STRUCTURAL.update(i18n.STR[_lang].values())


def _is_narrative(line: str) -> bool:
    s = line.strip()
    if not s or s.startswith(("#", "|", "```", "---")):
        return False
    if not re.search(r"[A-Za-z]", s):
        return False
    if s in STRUCTURAL or s.strip("_.") in STRUCTURAL:
        return False
    if re.match(r"^[-*•]?\s*\d{1,2}[.)]\s", s) and len(s) < 4:
        return False
    return True


def extract(report: str) -> Dict[str, Any]:
    lines = open(report, encoding="utf-8", errors="replace").read().split("\n")
    items: List[Dict[str, Any]] = []
    for i, ln in enumerate(lines):
        if _is_narrative(ln):
            items.append({"id": f"L{i:04d}", "line": i, "text": ln})
    return {"source": report, "lang": "id", "count": len(items), "items": items}


def apply_translations(report: str, tr: Dict[str, Any], out: str) -> Tuple[int, int]:
    lines = open(report, encoding="utf-8", errors="replace").read().split("\n")
    mapping = {it["id"]: it.get("text") for it in tr.get("items", [])}
    by_line = {}
    for it in tr.get("items", []):
        if it.get("line") is not None:
            by_line[int(it["line"])] = mapping.get(it["id"])
    applied = missing = 0
    for i, ln in enumerate(lines):
        if i in by_line and _is_narrative(ln):
            new = by_line[i]
            if new:
                lines[i] = new
                applied += 1
            else:
                missing += 1
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return applied, missing


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · narrative translation queue")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--report", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("apply")
    p.add_argument("--report", required=True)
    p.add_argument("--translations", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    if a.cmd == "extract":
        q = extract(a.report)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(q, f, ensure_ascii=False, indent=2)
        print(f"[DAN] {q['count']} baris narasi -> {a.out}")
        return 0
    tr = json.load(open(a.translations, encoding="utf-8"))
    applied, missing = apply_translations(a.report, tr, a.out)
    print(f"[DAN] diterapkan {applied} baris · {missing} tanpa terjemahan -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
