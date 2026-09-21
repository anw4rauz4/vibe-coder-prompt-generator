#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claim_audit.py — Validator provenance angka (menegakkan aturan DAN #1:
"jangan mengarang angka").

Memindai laporan (Markdown/HTML), mengekstrak setiap klaim numerik, lalu mencocokkannya
dengan SATU atau lebih sumber data (analysis.json / project_report.json / arch_report.json).
Angka yang tidak ditemukan di sumber mana pun ditandai UNVERIFIED untuk ditinjau manusia
(bisa jadi angka hasil perhitungan sah, benchmark industri, atau — yang berbahaya — karangan).

Bukan auto-fail: keluaran bersifat advisories + skor cakupan. Pakai --fail-under bila
ingin menjadikannya gate CI.

Yang DIABAIKAN saat ekstraksi (bukan klaim data):
  - blok kode ``` ... ```
  - tanggal (2026-09-16, 16/09/2026) & tahun berdiri sendiri
  - penomoran daftar di awal baris ("1.", "2)")
  - versi (v1.2.0) dan baris pemisah tabel
  - angka dalam tanda pagar heading

PAKAI
  python3 claim_audit.py --report deliverables/analysis.md \
      --source deliverables/analysis.json --out deliverables/claim_audit.md
  python3 claim_audit.py --report nota.md --source analysis.json --fail-under 80
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dan_analytics as da  # noqa: E402
import svg_charts as sc    # noqa: E402

NUM_RE = re.compile(
    r"(?<![\w./-])((?:Rp\.?|IDR|US\$|\$|€|£)\s?)?"
    r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)\s?(%|x|jt|rb)?")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}")
TIME_RE = re.compile(r"\d{1,2}:\d{2}(?::\d{2})?")          # jam 15:28:54
DIM_RE = re.compile(r"\d+\s?(?:x|×|:)\s?\d+")              # 60x60, 16:9, 24mm?
K_RE = re.compile(r"\b\d{1,2}K\b")                          # 8K, 4K
VER_RE = re.compile(r"(?:\bv|versi\s)\d+\.\d+\.\d+\b")
LIST_RE = re.compile(r"^\s*(?:[-*•]|\d{1,2}[.)])\s+")
UNIT_MULT = {"%": 0.01, "x": 1, "jt": 1e6, "rb": 1e3}


def _walk_numbers(node: Any, out: Set[float]) -> None:
    if isinstance(node, dict):
        for v in node.values():
            _walk_numbers(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk_numbers(v, out)
    elif isinstance(node, bool):
        return
    elif isinstance(node, (int, float)):
        v = float(node)
        if abs(v) < 1e12:
            out.add(v)
            out.add(round(v, 0))
            out.add(round(v, 1))
            out.add(round(v, 2))


def allowed_set(sources: Iterable[str]) -> Set[float]:
    out: Set[float] = set()
    for p in sources:
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                _walk_numbers(json.load(f), out)
        except Exception:
            continue
    return out


def strip_noise(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.S)          # blok kode
    text = re.sub(r"<[^>]+>", " ", text)                        # tag html
    text = DATE_RE.sub(" ", text)
    text = re.sub(r"\b(?:19|20)\d{2}\b", " ", text)   # tahun bukan klaim data
    text = TIME_RE.sub(" ", text)
    text = DIM_RE.sub(" ", text)
    text = K_RE.sub(" ", text)
    text = VER_RE.sub(" ", text)
    lines = []
    for ln in text.split("\n"):
        if re.match(r"^\s*\|?[\s:|-]+\|?\s*$", ln):             # pemisah tabel
            continue
        if ln.startswith("#"):
            continue
        m = LIST_RE.match(ln)
        if m:
            ln = ln[m.end():]
        lines.append(ln)
    return "\n".join(lines)


def extract(text: str) -> List[Tuple[float, str, str]]:
    """-> [(nilai, satuan, konteks)]"""
    clean = strip_noise(text)
    out = []
    for m in NUM_RE.finditer(clean):
        raw, unit = m.group(2), m.group(3) or ""
        v = da.parse_number(raw)
        if v is None:
            continue
        v *= UNIT_MULT.get(unit, 1)
        ctx = clean[max(0, m.start() - 45):m.end() + 25].replace("\n", " ").strip()
        out.append((v, unit, ctx))
    return out


def audit(report: str, sources: List[str], tol: float) -> Dict[str, Any]:
    text = open(report, encoding="utf-8", errors="replace").read()
    allowed = allowed_set(sources)
    claims = extract(text)
    verified, unverified = [], []
    for v, unit, ctx in claims:
        # persen di sumber disimpan sebagai 60.0 (bukan 0.60), jadi coba kedua skala
        cands = [v, v * 100] if unit == "%" else [v]
        hit = any(abs(c - a) <= max(tol, abs(a) * 1e-6) for c in cands for a in allowed)
        (verified if hit else unverified).append({"value": v, "unit": unit, "context": ctx})
    total = len(claims)
    cov = (len(verified) / total * 100) if total else 100.0
    return {"report": report, "sources": [s for s in sources if os.path.exists(s)],
            "total_claims": total, "verified": len(verified),
            "unverified": unverified, "coverage_pct": round(cov, 1),
            "tolerance": tol}


def to_markdown(A: Dict[str, Any]) -> str:
    L = [f"# Audit Klaim Angka — `{os.path.basename(A['report'])}`", "",
         f"Sumber pembanding: {', '.join(os.path.basename(s) for s in A['sources']) or '(tidak ada)'}  ",
         f"**Klaim numerik: {A['total_claims']} · terverifikasi {A['verified']} · "
         f"cakupan {A['coverage_pct']:.1f}%** (toleransi {A['tolerance']})", "",
         "## Perlu tinjauan manusia (tidak ditemukan di sumber)", "",
         "| Nilai | Konteks |", "|---|---|"]
    if not A["unverified"]:
        L.append("| — | semua klaim numerik cocok dengan sumber |")
    for u in A["unverified"][:60]:
        L.append(f"| {sc.fmt_num(u['value'], 'id')}{u['unit']} | {u['context'][:90]} |")
    if len(A["unverified"]) > 60:
        L.append(f"| … | +{len(A['unverified']) - 60} lainnya |")
    L += ["", "> Angka UNVERIFIED belum tentu salah: bisa jadi hasil perhitungan sah, "
          "benchmark industri, atau target. Namun setiap angka semacam ini WAJIB punya "
          "dasar yang bisa ditunjukkan. Bila tidak ada — hapus atau tandai `asumsi:`.", "",
          "---", "_DAN · claim_audit. Ini advisory, bukan vonis; gunakan --fail-under "
          "untuk menjadikannya gate CI._"]
    return "\n".join(L)


def main(argv=None) -> int:
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · audit provenance angka")
    ap.add_argument("--report", required=True)
    ap.add_argument("--source", action="append", default=[],
                    help="JSON sumber; boleh berulang")
    ap.add_argument("--tol", type=float, default=0.051)
    ap.add_argument("--out", default=os.path.join(dl, "claim_audit.md"))
    ap.add_argument("--fail-under", type=float, default=0,
                    help="exit 1 bila cakupan < nilai ini (persen)")
    a = ap.parse_args(argv)
    sources = a.source or [os.path.join(dl, "analysis.json")]
    A = audit(a.report, sources, a.tol)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(to_markdown(A))
    with open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(A, f, ensure_ascii=False, indent=2)
    print(f"[DAN] claim audit: {A['verified']}/{A['total_claims']} terverifikasi "
          f"({A['coverage_pct']:.1f}%) · {len(A['unverified'])} perlu tinjauan")
    for u in A["unverified"][:6]:
        print(f"   ? {sc.fmt_num(u['value'], 'id')}{u['unit']} — {u['context'][:70]}")
    print(f"[DAN] -> {a.out}")
    if a.fail_under and A["coverage_pct"] < a.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
