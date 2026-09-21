#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_pyz.py — Kemas seluruh engine DAN menjadi SATU berkas executable (.pyz).

Menghasilkan deliverables/dan.pyz yang bisa dijalankan di mesin mana pun yang punya
python3 >= 3.8, TANPA instalasi apa pun (stdlib-only):
    python3 dan.pyz list
    python3 dan.pyz run dan_analytics data.csv
    python3 dan.pyz doctor          # QA in-process, template dibaca dari dalam zip

Catatan:
  - Berkas data/template eksternal tetap dibaca dari path yang Anda berikan.
    Bila butuh path default paket, set DAN_ROOT ke salinan paket yang diekstrak.
  - `dan.pyz new <template>` membaca template dari dalam zip secara otomatis.

PAKAI
  python3 make_pyz.py --out ../../../deliverables/dan.pyz
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipapp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))

MAIN = '''import sys
import dan
if __name__ == "__main__":
    sys.exit(dan.main())
'''


def build(out: str) -> str:
    stage = tempfile.mkdtemp(prefix="dan_pyz_")
    try:
        for f in sorted(os.listdir(HERE)):
            src = os.path.join(HERE, f)
            if os.path.isdir(src):
                # subpaket (mis. svg_charts/) ikut disertakan
                if not any(x.endswith(".py") for x in os.listdir(src)):
                    continue
                dst = os.path.join(stage, f)
                os.makedirs(dst, exist_ok=True)
                for g in sorted(os.listdir(src)):
                    if g.endswith(".py"):
                        shutil.copyfile(os.path.join(src, g), os.path.join(dst, g))
            elif f.endswith(".py"):
                shutil.copyfile(src, os.path.join(stage, f))
        tdir = os.path.join(stage, "templates")
        os.makedirs(tdir, exist_ok=True)
        src_t = os.path.join(ROOT, "skills", "dan", "templates")
        for f in sorted(os.listdir(src_t)):
            shutil.copyfile(os.path.join(src_t, f), os.path.join(tdir, f))
        with open(os.path.join(stage, "__main__.py"), "w", encoding="utf-8") as f:
            f.write(MAIN)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        zipapp.create_archive(stage, out, interpreter="/usr/bin/env python3",
                              compressed=True)
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · single-file package builder")
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables", "dan.pyz"))
    a = ap.parse_args(argv)
    p = build(a.out)
    print(f"[DAN] pyz -> {p} ({os.path.getsize(p) / 1024:.0f} KB)")
    print("[DAN] coba:  python3 dan.pyz list | python3 dan.pyz doctor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
