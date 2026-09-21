#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pkg_health.py — Dashboard kesehatan PAKET DAN itu sendiri.

Membaca `skills/dan/qa_history.jsonl` (diisi otomatis oleh make_package.py tiap rilis)
lalu menampilkan:
  - scorecard rilis terbaru: test lulus/gagal, refs hilang, jumlah file/byte,
    jumlah sub-skill & engine, adapter, kasus;
  - tren antar-versi (garis): test lulus, refs hilang, ukuran paket — muncul begitu
    riwayat ≥2 rilis (kami tidak mengarang data historis);
  - skor kesehatan 0-100 dengan rincian penalti.

PAKAI
  python3 pkg_health.py                     # cetak scorecard + tren (bila ada)
  python3 pkg_health.py --out deliverables/pkg_health.html
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
HIST = os.path.join(ROOT, "skills", "dan", "qa_history.jsonl")
sys.path.insert(0, HERE)
import svg_charts as sc        # noqa: E402
import make_infographic as mi  # noqa: E402


def inventory() -> Dict[str, int]:
    def count(d, ext=None):
        n = 0
        for dp, dn, fn in os.walk(os.path.join(ROOT, d)):
            dn[:] = [x for x in dn if x != "__pycache__"]
            for f in fn:
                if ext is None or f.endswith(ext):
                    n += 1
        return n
    return {
        "subskills": count("skills/dan/skills"),
        "engines": count("skills/dan/scripts", ".py"),
        "references": count("skills/dan/references", ".md"),
        "templates": count("skills/dan/templates"),
        "adapters": count("adapters"),
        "cases": count("skills/dan/cases", ".json"),
    }


def score(e: Dict[str, Any]) -> int:
    s = 100
    if e.get("tests_fail", 0):
        s -= 40
    if e.get("refs_missing", 0):
        s -= 20
    if e.get("tests_pass", 0) < 100:
        s -= 10
    return max(0, s)


def load() -> List[Dict[str, Any]]:
    if not os.path.exists(HIST):
        return []
    return [json.loads(ln) for ln in open(HIST, encoding="utf-8") if ln.strip()]


def build_spec(hist: List[Dict[str, Any]], inv: Dict[str, int]) -> Dict[str, Any]:
    sections: List[Dict[str, Any]] = []
    if hist:
        last = hist[-1]
        k = score(last)
        sections.append({"type": "kpi", "items": [
            {"label": "Versi", "value": last.get("version", "?")},
            {"label": "Skor kesehatan", "value": k, "format": "number",
             "color": "#34D399" if k >= 90 else "#FBBF24"},
            {"label": "Test lulus", "value": f"{last.get('tests_pass', 0)}/"
                                             f"{last.get('tests_pass', 0) + last.get('tests_fail', 0)}"},
            {"label": "Refs hilang", "value": last.get("refs_missing", 0), "format": "number"},
            {"label": "Ukuran", "value": f"{last.get('bytes', 0) / 1024:.0f} KB"},
            {"label": "Sub-skill", "value": inv["subskills"], "format": "number"},
            {"label": "Engine", "value": inv["engines"], "format": "number"},
            {"label": "Adapter", "value": inv["adapters"], "format": "number"},
        ]})
    if len(hist) >= 2:
        vers = [h.get("version", "?") for h in hist]
        sections.append({"type": "chart", "chart": "line", "span": 6,
                         "title": "Tren test lulus per versi", "width": 620, "height": 320,
                         "data": {"labels": vers,
                                  "series": {"lulus": [h.get("tests_pass", 0) for h in hist]}},
                         "options": {"area": True, "markers": True}})
        sections.append({"type": "chart", "chart": "line", "span": 6,
                         "title": "Tren masalah (refs hilang + test gagal)",
                         "width": 620, "height": 320,
                         "data": {"labels": vers,
                                  "series": {"masalah": [h.get("refs_missing", 0) +
                                                        h.get("tests_fail", 0)
                                                        for h in hist]}},
                         "options": {"markers": True}})
        sections.append({"type": "chart", "chart": "bar", "span": 12,
                         "title": "Ukuran paket per versi (KB)", "width": 1000,
                         "height": 300,
                         "data": [(v, round(h.get("bytes", 0) / 1024)) for v, h in
                                  zip(vers, hist)]})
    else:
        sections.append({"type": "html", "span": 12,
                         "html": "<div class='note'>Tren antar-versi muncul mulai rilis "
                                 "ke-2 (riwayat saat ini: %d entri). Kami tidak mengarang "
                                 "data historis.</div>" % len(hist)})
    rows = "".join(f"<tr><td>{n}</td><td>{v}</td></tr>" for n, v in inv.items())
    sections.append({"type": "html", "span": 12,
                     "html": "<div style='padding:6px 8px'><div style='font-size:15px;"
                            "font-weight:700;margin-bottom:10px'>Inventaris paket saat ini"
                            "</div><table><thead><tr><th>Komponen</th><th>Jumlah</th></tr>"
                            f"</thead><tbody>{rows}</tbody></table></div>"})
    return {"title": "Kesehatan Paket DAN",
            "subtitle": f"{len(hist)} entri riwayat QA (qa_history.jsonl) · "
                        "diisi otomatis oleh make_package.py",
            "theme": "dan", "locale": "id", "currency": "Rp",
            "sections": sections,
            "footer": "DAN · pkg_health — memantau paket sebagaimana DAN memantau kampanye."}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · package health dashboard")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    hist = load()
    inv = inventory()
    if hist:
        last = hist[-1]
        print(f"[DAN] rilis {last.get('version')}: test {last.get('tests_pass')}/"
              f"{last.get('tests_pass', 0) + last.get('tests_fail', 0)} · "
              f"refs hilang {last.get('refs_missing')} · skor {score(last)}/100")
    else:
        print("[DAN] belum ada riwayat QA — jalankan make_package.py untuk mulai mencatat.")
    print(f"[DAN] inventaris: {inv}")
    if a.out:
        html = mi.to_html(mi.build_spec(build_spec(hist, inv)), "dan", "wide")
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(html)
        print(f"[DAN] dashboard -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
