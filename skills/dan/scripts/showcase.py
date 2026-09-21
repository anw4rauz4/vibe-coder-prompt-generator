#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
showcase.py — Galeri showcase satu halaman: etalase seluruh artefak contoh paket.

Memindai deliverables/ + contoh sektor, lalu menyusun halaman indeks dengan:
  - kartu per artefak (jenis, ukuran, tautan relatif yang bisa dibuka langsung),
  - tren QA paket (dari qa_history.jsonl) sebagai sparkline,
  - inventaris paket (sub-skill, engine, adapter, kasus, contoh sektor).
Halaman self-contained (SVG inline, tanpa CDN); tautan bekerja saat dibuka dari
folder deliverables/ di filesystem lokal.

PAKAI
  python3 showcase.py --out ../showcase.html      # di root agar tautan relatif benar
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
import svg_charts as sc   # noqa: E402
import pkg_health as ph   # noqa: E402

KIND = [
    ("infographic", ("infographic", "infografik", "exec_dashboard", "burnup",
                     "project_dashboard", "pkg_health")),
    ("deck/slide", ("slides", "deck_pimpinan")),
    ("laporan", ("analysis.md", "report", "summary", "digest", "release_", "claim_",
                 "narrative_", "laporan_klien", "client_report", "qa_report",
                 "pmo_guard", "coach")),
    ("visual statis", (".svg", ".png")),
    ("interaktif", ("_review.html", "forms.html")),
    ("audio", (".mp3", ".txt audio")),
    ("data", (".csv", ".json")),
]


def kind_of(name: str) -> str:
    for k, keys in KIND:
        for key in keys:
            if key in name:
                return k
    return "lainnya"


def build(out_rel: str, lang: str = "id") -> str:
    dl = os.path.join(ROOT, "deliverables")
    files = sorted(f for f in os.listdir(dl) if os.path.isfile(os.path.join(dl, f))
                   and not f.endswith(".zip") and not f.endswith(".pyz"))
    import i18n
    t = lambda k: i18n.t(k, lang)
    hist = ph.load()
    inv = ph.inventory()
    trend = sc.sparkline([h.get("tests_pass", 0) for h in hist], 220, 46,
                         color="#34D399") if len(hist) >= 2 else ""
    cards = []
    for f in files:
        sz = os.path.getsize(os.path.join(dl, f))
        base = os.path.relpath(dl, os.path.dirname(os.path.abspath(out_rel)))
        href = os.path.join(base, f).replace(os.sep, "/")
        cards.append(f"<a class='c' href='{href}'><div class='k'>{kind_of(f)}</div>"
                     f"<div class='n'>{f}</div><div class='s'>{sz / 1024:.0f} KB</div></a>")
    sec = [f"<div class='sec'><h2>{n}</h2><div class='v'>{v}</div></div>"
           for n, v in (("Sub-skill", inv["subskills"]), ("Engine", inv["engines"]),
                        ("Adapter", inv["adapters"]), ("Kasus", inv["cases"]),
                        ("Referensi", inv["references"]), ("Template", inv["templates"]),
                        ("Rilis tercatat", len(hist)))]
    css = ("body{font-family:%s;background:#0F172A;color:#F1F5F9;margin:0;padding:28px}"
           "h1{font-size:26px;margin:0 0 4px}h2{font-size:12px;color:#94A3B8;"
           "text-transform:uppercase;letter-spacing:.8px;margin:0 0 6px}"
           ".sub{color:#94A3B8;font-size:13px;margin:0 0 18px}"
           ".secs{display:flex;gap:14px;flex-wrap:wrap;margin:0 0 22px}"
           ".sec{background:#16233F;border:1px solid #24344F;border-radius:14px;"
           "padding:12px 16px;min-width:110px}.sec .v{font-size:22px;font-weight:800}"
           ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));"
           "gap:12px}.c{display:block;background:#16233F;border:1px solid #24344F;"
           "border-radius:14px;padding:12px;text-decoration:none;color:inherit}"
           ".c:hover{border-color:#38BDF8}.k{font-size:10px;color:#38BDF8;"
           "text-transform:uppercase;letter-spacing:.6px}.n{font-size:12.5px;"
           "margin:6px 0 4px;word-break:break-all}.s{font-size:10.5px;color:#94A3B8}"
           ".trend{margin:6px 0 22px}") % sc.FONT
    body = ("<h1>" + t("show_title") + "</h1><p class='sub'>" + t("show_sub") +
            " " + ("Tren test lulus antar-rilis: " if lang == "id"
                  else "Passing-test trend per release: ") +
            (trend or ("belum cukup riwayat" if lang == "id" else "not enough history")) +
            "</p>"
            "<div class='secs'>" + "".join(sec) + "</div>"
            "<div class='grid'>" + "".join(cards) + "</div>"
            "<p class='sub' style='margin-top:20px'>" +
            ("Dibangun oleh showcase.py · tautan relatif terhadap folder berkas ini."
             if lang == "id" else "Built by showcase.py · links are relative to this file.")
            + "</p>")
    return (f"<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            f"<title>Showcase DAN</title><style>{css}</style></head><body>{body}"
            f"</body></html>")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · showcase gallery")
    ap.add_argument("--out", default=os.path.join(ROOT, "showcase.html"))
    ap.add_argument("--lang", default="id", choices=["id", "en", "zh"])
    a = ap.parse_args(argv)
    html = build(a.out, a.lang)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(html)
    n = html.count("class='c'")
    print(f"[DAN] showcase: {n} artefak terindeks -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
