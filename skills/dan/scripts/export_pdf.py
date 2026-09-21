#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_pdf.py — Ekspor HTML/SVG deliverable ke PDF secara headless BILA renderer ada.

Deteksi berjenjang: chromium/chrome/wkhtmltopdf/weasyprint. Bila tidak ada SATU PUN,
keluar dengan exit 2 + petunjuk jelas (termasuk alternatif: cetak dari browser,
atau biarkan SVG/HTML sebagai format final). Tidak pernah berpura-pura berhasil.

PAKAI
  python3 export_pdf.py deliverables/infographic.html
  python3 export_pdf.py deliverables/slides.html --out deliverables/slides.pdf
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

FALLBACK = """[DAN] Tidak ada renderer PDF headless terpasang di mesin ini.
Pilihan Anda:
  1) pasang salah satu:  apt-get install chromium | wkhtmltopdf | python3 -m pip install weasyprint
  2) cetak manual: buka berkas HTML di browser → Ctrl/Cmd+P → "Save as PDF"
     (CSS cetak sudah disertakan: tiap slide/section = 1 halaman)
  3) pakai format asli: HTML/SVG DAN sudah final untuk layar & vektor cetak.
"""


def find_renderer() -> str:
    for b in ("chromium", "chromium-browser", "google-chrome", "chrome", "wkhtmltopdf"):
        if shutil.which(b):
            return b
    try:
        import weasyprint  # noqa: F401
        return "weasyprint"
    except Exception:
        return ""


def export(src: str, out: str) -> int:
    r = find_renderer()
    if not r:
        sys.stdout.write(FALLBACK)
        return 2
    src = os.path.abspath(src)
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    if r in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        cmd = [r, "--headless", "--disable-gpu", "--no-pdf-header-footer",
               f"--print-to-pdf={out}", "file://" + src]
    elif r == "wkhtmltopdf":
        cmd = [r, "--enable-local-file-access", src, out]
    else:
        cmd = [sys.executable, "-m", "weasyprint", src, out]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 500:
        print(f"[DAN] pdf -> {out} ({os.path.getsize(out) / 1024:.0f} KB, renderer: {r})")
        return 0
    print(f"[DAN] renderer {r} gagal (exit {p.returncode}):")
    print((p.stderr or p.stdout)[-600:])
    return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · HTML/SVG -> PDF (renderer opsional)")
    ap.add_argument("src")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    out = a.out or os.path.splitext(a.src)[0] + ".pdf"
    return export(a.src, out)


if __name__ == "__main__":
    raise SystemExit(main())
