#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_bundle.py — Bundle offline-total: satu zip yang cukup untuk mesin sasaran.

Isi bundle:
  dan.pyz                  seluruh engine dalam SATU berkas (zipapp, stdlib-only)
  examples/                contoh sektor (fnb, fashion, b2b) + brief
  adapters/                adapter runtime (claude/cursor/gemini/…/vscode)
  docs/                    README-DAN, PLUGPLAY, ONBOARDING, showcase
  INSTALL-OFFLINE.md       langkah per OS BILA python3 belum ada (termasuk Windows
                           embeddable python + menjalankan dan.pyz tanpa instalasi)

JUJUR soal batas: kami tidak menyertakan interpreter Python (lisensi/ukuran); bundle
ini menjamin TIDAK ADA dependensi pip & TIDAK ADA jaringan saat dipakai — cukup
python3 ≥3.8 bawaan OS atau embeddable build.

PAKAI
  python3 make_bundle.py --version 3.2.0
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

INSTALL_OFFLINE = """# INSTALL OFFLINE — mesin tanpa akses internet & tanpa pip

## Bila python3 sudah ada (mayoritas kasus)
1. Ekstrak bundle ini ke folder mana pun, mis. `D:\\dan` atau `/opt/dan`.
2. Verifikasi: `python3 dan.pyz list`  (Windows: `py dan.pyz list`).
3. Mulai: `python3 dan.pyz demo` lalu `python3 dan.pyz init`.
   Tidak ada `pip install` apa pun: seluruh engine stdlib-only.

## Bila python3 BELUM ada
- **Windows**: unduh sekali (di mesin berinternet) "Windows embeddable package"
  python.org → ekstrak → taruh `dan.pyz` di dalamnya → jalankan
  `python.exe dan.pyz list`. Tidak perlu installer/admin.
- **Linux**: `apt/dnf/yum install python3` dari mirror lokal/repo offline, atau
  salin binary python3 + lib standar dari mesin sejenis.
- **macOS**: gunakan python3 bawaan Xcode CLT, atau python.org pkg offline.

## Memakai sebagai skill di AI lokal
- VS Code: buka folder bundle di VS Code; `.vscode/` tidak ikut dalam bundle demi
  keamanan — salin dari `adapters/vscode/dot_vscode/` bila diinginkan.
- Runtime lain: tempel `docs/`SYSTEM_PROMPT` dari adapters/SYSTEM_PROMPT.txt.

## Verifikasi integritas
Bandingkan sha256 `dan.pyz` dengan yang tercatat di `manifest-bundle.json`.
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · offline bundle")
    ap.add_argument("--version", default="offline")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    import make_pyz
    dl = os.path.join(ROOT, "deliverables")
    pyz = os.path.join(dl, "dan.pyz")
    if not os.path.exists(pyz):
        make_pyz.main(["--out", pyz])
    stage = tempfile.mkdtemp(prefix="dan_bundle_")
    try:
        shutil.copyfile(pyz, os.path.join(stage, "dan.pyz"))
        for src, dst in ((os.path.join(ROOT, "examples"), "examples"),
                         (os.path.join(ROOT, "adapters"), "adapters")):
            shutil.copytree(src, os.path.join(stage, dst),
                            ignore=shutil.ignore_patterns("__pycache__"))
        ddocs = os.path.join(stage, "docs")
        os.makedirs(ddocs, exist_ok=True)
        for f in ("README-DAN.md", "PLUGPLAY.md", "ONBOARDING.md"):
            p = os.path.join(ROOT, f)
            if os.path.exists(p):
                shutil.copyfile(p, os.path.join(ddocs, f))
        with open(os.path.join(stage, "INSTALL-OFFLINE.md"), "w", encoding="utf-8") as f:
            f.write(INSTALL_OFFLINE)
        import hashlib
        h = hashlib.sha256(open(os.path.join(stage, "dan.pyz"), "rb").read()).hexdigest()
        import json
        with open(os.path.join(stage, "manifest-bundle.json"), "w", encoding="utf-8") as f:
            json.dump({"version": a.version, "dan_pyz_sha256": h}, f, indent=2)
        out = a.out or os.path.join(dl, f"dan-offline-{a.version}.zip")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        n = 0
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for dp, dn, fn in os.walk(stage):
                dn[:] = [x for x in dn if x != "__pycache__"]
                for f in fn:
                    fp = os.path.join(dp, f)
                    z.write(fp, os.path.relpath(fp, stage))
                    n += 1
        print(f"[DAN] bundle offline -> {out} ({os.path.getsize(out) / 1024:.0f} KB, "
              f"{n} berkas)")
        print(f"[DAN] sha256 dan.pyz: {h[:16]}… (lengkap di manifest-bundle.json)")
        return 0
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
