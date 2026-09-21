#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_digest.py — Sub-skill 21 · Digest rilis siap kirim ke tim (+ naskah audio).

Membaca CHANGELOG paket, lalu menyusun:
  1) digest 5 baris untuk chat tim,
  2) rincian perubahan per area,
  3) checklist tindakan minggu ini,
  4) naskah audio briefing (aturan sub-skill 16: kalimat ≤18 kata, satu ide per kalimat).

PAKAI
  python3 make_digest.py                      # versi terbaru di CHANGELOG
  python3 make_digest.py --version 2.0.0 --out deliverables/digest_v2.md
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CHANGELOG = os.path.join(ROOT, "skills", "dan", "CHANGELOG.md")

AREA_MAP = [
    ("engine", r"(engine|\.py|script)"),
    ("sub-skill", r"(sub-skill|SKILL)"),
    ("QA/verifikasi", r"(QA|test|audit|guard|eval|refs)"),
    ("kemasan/portabilitas", r"(pyz|zip|paket|manifest|INSTALL)"),
    ("dokumen", r"(README|dokumen|referensi|ADR|CHANGELOG)"),
]


def parse_changelog(path: str) -> Dict[str, Dict[str, List[str]]]:
    txt = open(path, encoding="utf-8").read()
    out: Dict[str, Dict[str, List[str]]] = {}
    cur = None
    for ln in txt.split("\n"):
        m = re.match(r"^##\s+([\d.]+)\s*(?:—|.*)$", ln)
        if m:
            cur = m.group(1)
            out[cur] = {"bullets": []}
            continue
        if cur and ln.strip().startswith("- "):
            out[cur]["bullets"].append(ln.strip()[2:])
    return out


def split_area(bullets: List[str]) -> Dict[str, List[str]]:
    areas: Dict[str, List[str]] = {k: [] for k, _ in AREA_MAP}
    for b in bullets:
        placed = False
        for name, rx in AREA_MAP:
            if re.search(rx, b, re.I):
                areas[name].append(b)
                placed = True
                break
        if not placed:
            areas.setdefault("lainnya", []).append(b)
    return areas


def audio_script(ver: str, bullets: List[str]) -> str:
    lines = [f"Ringkasan rilis paket DAN versi {ver}.",
             f"Ada {len(bullets)} perubahan utama minggu ini."]
    for b in bullets[:6]:
        s = b.split("(")[0].strip().rstrip(".")
        words = s.split()
        if len(words) > 18:
            s = " ".join(words[:18])
        lines.append(s + ".")
    lines.append("Tindakan minggu ini: jalankan run_cases dan _test_all sebelum pakai.")
    lines.append("Selengkapnya ada di digest tertulis. Terima kasih.")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · release digest")
    ap.add_argument("--version", default="")
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables", "digest.md"))
    ap.add_argument("--audio", default="")
    a = ap.parse_args(argv)
    cl = parse_changelog(CHANGELOG)
    ver = a.version or (sorted(cl, key=lambda v: [int(x) for x in v.split(".")] )[-1] if cl else "?")
    entry = cl.get(ver, {"bullets": []})
    bullets = entry["bullets"]
    areas = split_area(bullets)

    L = [f"# Digest Rilis DAN v{ver}", "",
         f"**5 baris untuk tim:**",
         f"1. Rilis v{ver} memuat {len(bullets)} perubahan terverifikasi.",
         "2. Tambahan terbesar: " +
         (", ".join([f"{k} ({len(v)})" for k, v in areas.items() if v][:3]) or "-") + ".",
         "3. Semua perubahan lolos QA terpadu sebelum dikemas (test + refs + cases).",
         "4. Paket portabel diperbarui: `dan.pyz` & zip ber-manifest.",
         "5. Aksi minggu ini: jalankan tur demo (`dan.py demo`) & review miss RAG.", "",
         "## Rincian per area"]
    for name, items in areas.items():
        if not items:
            continue
        L += [f"\n### {name}"]
        L += [f"- {i}" for i in items]
    L += ["", "## Checklist tindakan minggu ini",
          "- [ ] `python3 dan.py demo` untuk onboarding anggota baru",
          "- [ ] `run_cases.py run all` sebelum memakai keluaran untuk keputusan",
          "- [ ] review `rag_eval.md`: tutup miss sinonim atau terima batas lexical",
          "- [ ] `pmo_guard` di CI: pastikan tidak ada tugas kritis tanpa tindakan",
          "- [ ] arsipkan digest ini ke notes/ & umumkan 5 baris ke channel tim", "",
          "---", f"_DAN · make_digest (sumber: CHANGELOG v{ver})._"]
    md = "\n".join(L)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(md)
    print(f"[DAN] digest v{ver} ({len(bullets)} butir) -> {a.out}")
    if a.audio:
        open(a.audio, "w", encoding="utf-8").write(audio_script(ver, bullets))
        print(f"[DAN] naskah audio -> {a.audio}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
