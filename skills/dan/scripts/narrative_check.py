#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
narrative_check.py — Sub-skill 20/QA · Pemeriksa kualitas NARASI otomatis.

Memindai teks (insight, ringkasan, slide, caption) untuk pola berbahasa yang
berisiko menyesatkan, lalu memberi saran perbaikan:
  C  klaim kausal tanpa eksperimen   ("menyebabkan", "karena kami", "berdampak akibat")
  O  overclaim / jaminan              ("pasti", "dijamin", "terbaik sepanjang", "selalu")
  U  ketidakpastian tanpa penanda     (angka proyeksi tanpa "estimasi/±/asumsi")
  S  superlatif tanpa pembanding      ("tercepat", "termurah" tanpa rujukan)
  P  person-blame                     ("kesalahan X", "X gagal") — bertentangan blameless

Keluaran: daftar temuan (baris, jenis, kutipan, saran) + skor kebersihan narasi.
Bukan sensor: temuan = undangan menulis lebih presisi, bukan larangan berpendapat.

PAKAI
  python3 narrative_check.py --file deliverables/weekly_summary.md
  python3 narrative_check.py --text "Pendapatan naik karena kampanye kami brilian."
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

RULES: List[Tuple[str, str, str, str]] = [
    ("C", r"(?i)\b(menyebabkan|menyebabkan|caused by|akibat dari|berdampak karena|"
          r"karena kampanye kami|karena tindakan kami)\b",
     "klaim kausal",
     "Ganti dengan korelasi + rencana uji: 'berbarengan dengan X; validasi via A/B'."),
    ("O", r"(?i)\b(pasti akan|dijamin|guaranteed|pasti naik|pasti sukses|"
          r"terbaik sepanjang masa|selalu berhasil)\b",
     "overclaim/jaminan",
     "Ganti dengan rentang atau kondisi: 'proyeksi p10–p90 … bila asumsi bertahan'."),
    ("U", r"(?i)\b(proyeksi|forecast|estimasi masa depan|akan mencapai)\b"
          r"(?![^\n]{0,60}(?:±|estimasi|asumsi|sekitar|kira-kira|p10|p90))",
     "proyeksi tanpa penanda ketidakpastian",
     "Tambahkan penanda: '±', 'estimasi', 'asumsi:', atau interval p10–p90."),
    ("S", r"(?i)\b(tercepat|termurah|terbesar|tertinggi|number one|#1)\b"
          r"(?![^\n]{0,40}(?:versi|menurut|berdasarkan|sumber))",
     "superlatif tanpa pembanding",
     "Sebutkan pembanding & sumber: 'tercepat di kategori X versi Y (tahun)'."),
    ("P", r"(?i)\b(kesalahan (?:tim|budi|sari|andi|dewi)|[A-Z][a-z]+ gagal|tim gagal)\b",
     "person-blame",
     "Fokus sistem: 'proses X belum punya Y' alih-alih menamai orang."),
]

SAFE = [r"(?i)\bkorelasi\b", r"(?i)\btidak membuktikan\b", r"(?i)\basumsi:"]


def check(text: str) -> Dict[str, Any]:
    lines = text.split("\n")
    findings: List[Dict[str, Any]] = []
    for i, ln in enumerate(lines, 1):
        if not ln.strip() or ln.startswith(("|", "#", "---")):
            continue
        if any(re.search(s, ln) for s in SAFE):
            continue
        for code, rx, kind, fix in RULES:
            for m in re.finditer(rx, ln):
                findings.append({"line": i, "code": code, "kind": kind,
                                 "quote": m.group(0), "context": ln.strip()[:90],
                                 "fix": fix})
    clean = 100 - min(100, 12 * len(findings))
    return {"findings": findings, "score": max(0, clean),
            "lines": len(lines),
            "verdict": ("bersih" if not findings else
                        f"{len(findings)} temuan — perbaiki sebelum dipublikasikan")}


def to_markdown(R: Dict[str, Any], src: str) -> str:
    L = [f"# Pemeriksaan Narasi — `{os.path.basename(src)}`", "",
         f"**Skor kebersihan: {R['score']}/100 · {R['verdict']}**", "",
         "| Baris | Kode | Jenis | Kutipan | Saran |", "|---|---|---|---|---|"]
    for f in R["findings"]:
        L.append(f"| {f['line']} | {f['code']} | {f['kind']} | {f['quote']} | {f['fix']} |")
    if not R["findings"]:
        L.append("| — | — | — | tidak ada pola berisiko | pertahankan |")
    L += ["", "## Legenda kode",
          "- C klaim kausal tanpa eksperimen · O overclaim/jaminan · "
          "U proyeksi tanpa penanda ketidakpastian · S superlatif tanpa pembanding · "
          "P person-blame", "",
          "> Alat ini mendukung prinsip DAN: angka tertelusur, klaim berbatas, "
          "dan evaluasi tanpa menyalahkan orang.", "",
          "---", "_DAN · narrative_check._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · narrative quality checker")
    ap.add_argument("--file", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--fail-under", type=int, default=0)
    a = ap.parse_args(argv)
    text = a.text or (open(a.file, encoding="utf-8", errors="replace").read()
                      if a.file else "")
    if not text:
        print("[DAN] butuh --file atau --text")
        return 2
    R = check(text)
    if a.out:
        src = a.file or "text"
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(to_markdown(R, src))
        json.dump(R, open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    print(f"[DAN] narrative: skor {R['score']}/100 · {R['verdict']}")
    for f in R["findings"][:8]:
        print(f"   [{f['code']}] baris {f['line']}: “{f['quote']}” → {f['fix']}")
    if a.fail_under and R["score"] < a.fail_under:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
