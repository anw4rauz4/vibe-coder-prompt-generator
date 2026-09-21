#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_png.py — Ekspor SVG/HTML artefak DAN menjadi PNG.

DAN sengaja zero-dependency, jadi ekspor PNG memakai renderer OPSIONAL bila ada,
dengan deteksi berjenjang dan pesan fallback yang actionable bila tidak:

  1. cairosvg (pip install cairosvg)          -> paling portabel
  2. rsvg-convert / inkscape (paket sistem)   -> via subprocess
  3. chromium/chrome headless (untuk HTML)    -> via subprocess
  bila tidak ada: exit 2 + petunjuk instalasi & alternatif (cetak PDF dari browser).

PAKAI
  python3 export_png.py deliverables/arch_massing_3d.svg --out-dir deliverables/png
  python3 export_png.py deliverables/slides.html --out-dir deliverables/png
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from typing import List, Optional

FALLBACK_MSG = """[DAN] Tidak ada renderer SVG->PNG terpasang di mesin ini.
Pilih salah satu:
  1) pip install cairosvg            (paling mudah, murni Python+lib cairo)
  2) apt-get install librsvg2-bin    (menyediakan rsvg-convert)
     atau: apt-get install inkscape
  3) Untuk HTML (infografik/slide): buka di browser lalu Ctrl/Cmd+P -> "Save as PDF",
     atau print-screen per slide; hasil vektor SVG kami tetap tajam dicetak langsung.
SVG DAN sendiri sudah final untuk keperluan cetak/vector; PNG hanya kebutuhan raster
(mis. tempel ke slide deck pihak ketiga atau chat yang tidak mendukung SVG)."""


def _which() -> Optional[str]:
    for b in ("rsvg-convert", "inkscape"):
        if shutil.which(b):
            return b
    return None


def export_one(src: str, out_dir: str, dpi: int) -> Optional[str]:
    base = os.path.splitext(os.path.basename(src))[0]
    dst = os.path.join(out_dir, base + ".png")
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=src, write_to=dst, dpi=dpi)
        return dst
    except Exception:
        pass
    b = _which()
    if b == "rsvg-convert":
        r = subprocess.run([b, "-d", str(dpi), "-o", dst, src], capture_output=True)
        return dst if r.returncode == 0 and os.path.exists(dst) else None
    if b == "inkscape":
        r = subprocess.run([b, src, "--export-type=png", "--export-filename=" + dst,
                            f"--export-dpi={dpi}"], capture_output=True)
        return dst if r.returncode == 0 and os.path.exists(dst) else None
    if src.endswith(".html"):
        for br in ("chromium", "chromium-browser", "google-chrome"):
            if shutil.which(br):
                subprocess.run([br, "--headless", "--disable-gpu",
                                f"--screenshot={dst}", "--window-size=1600,1000",
                                "file://" + os.path.abspath(src)], capture_output=True)
                if os.path.exists(dst):
                    return dst
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · SVG/HTML -> PNG (renderer opsional)")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--dpi", type=int, default=150)
    a = ap.parse_args(argv)
    out_dir = a.out_dir or os.path.join(os.path.dirname(os.path.abspath(a.paths[0])), "png")
    os.makedirs(out_dir, exist_ok=True)
    done: List[str] = []
    failed: List[str] = []
    for p in a.paths:
        r = export_one(p, out_dir, a.dpi)
        (done if r else failed).append(p if not r else r)
    for d in done:
        print(f"[DAN] png -> {d}")
    if failed or not done:
        print(FALLBACK_MSG)
        for f in failed:
            print(f"   gagal: {f}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
