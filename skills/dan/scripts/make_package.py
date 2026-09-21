#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_package.py — Kemas skill DAN menjadi arsip siap-import (sub-skill lintas runtime).

Menghasilkan:
  deliverables/manifest.json          daftar file + sha256 + versi + status QA
  deliverables/INSTALL.md             cara import ke berbagai runtime agent
  deliverables/dan-skill-<versi>.zip  skills/ + README + manifest + INSTALL
  skills/dan/CHANGELOG.md             riwayat versi

PAKAI
  python3 make_package.py --version 1.1.0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PKG = os.path.join(ROOT, "skills", "dan")

INSTALL_MD = """# INSTALL — paket skill DAN

Arsip ini berisi agen **DAN** (9 sub-skill + 10 engine, zero-dependency wajib).

## 1. Claude (Claude Code / Projects / skill folder)
Salin folder `skills/dan/` ke lokasi skill Anda, mis.:
```
~/.claude/skills/dan/          # global
<projek>/.claude/skills/dan/   # per-proyek
```
Claude akan membaca `SKILL.md` (orchestrator) dan memuat sub-skill/referensi sesuai kebutuhan
(progressive disclosure). Tidak ada instalasi paket wajib.

## 2. Custom GPT / agent berbasis system-prompt
Tempel isi `skills/dan/AGENT.md` (blok system prompt) ke_instructions_ agent Anda.
Bila runtime mendukung file/tools, unggah folder `skills/dan/scripts/` dan izinkan eksekusi
Python; engine dapat dipanggil sebagai tools.

## 3. Runtime berbasis kode (LangChain / n8n / runtime lain)
Tambahkan `skills/dan/scripts/` ke `sys.path`, lalu panggil engine sebagai fungsi:
```python
import sys; sys.path.insert(0, "path/ke/skills/dan/scripts")
import dan_analytics, make_infographic, project_monitor, arch_advisor, arch_design
```
Semua engine punya `main(argv)` dan bisa dijalankan sebagai CLI (`python3 <engine> --help`).

## 4. Dependensi
- Wajib: **tidak ada** (stdlib Python 3.8+).
- Opsional: `pip install -r skills/dan/scripts/requirements.txt`
  (openpyxl utk XLSX · networkx+scipy utk verifikasi graph · Pillow utk fit_asset).

## 5. Verifikasi pasca-install
```bash
cd skills/dan/scripts
python3 _test_all.py        # wajib: 0 gagal
python3 _check_refs.py      # wajib: 0 referensi hilang
```

## 6. Integritas
Cocokkan `manifest.json` (sha256 per file) bila Anda butuh memastikan arsip tidak berubah:
```bash
python3 - <<'PY'
import hashlib, json, os
m = json.load(open("manifest.json"))
bad = [f["path"] for f in m["files"]
       if os.path.exists(f["path"]) and
       hashlib.sha256(open(f["path"], "rb").read()).hexdigest() != f["sha256"]]
print("utuh" if not bad else f"berubah: {bad}")
PY
```
"""


def sha256_of(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files() -> List[Dict[str, Any]]:
    out = []
    bases = [PKG, os.path.join(ROOT, "README-DAN.md")]
    for base in bases:
        if os.path.isfile(base):
            rel = os.path.relpath(base, ROOT).replace(os.sep, "/")
            out.append({"path": rel, "bytes": os.path.getsize(base),
                        "sha256": sha256_of(base)})
            continue
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in sorted(fn):
                if f.endswith(".pyc"):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
                out.append({"path": rel, "bytes": os.path.getsize(p), "sha256": sha256_of(p)})
    return sorted(out, key=lambda x: x["path"])


def run_qa() -> Dict[str, Any]:
    res: Dict[str, Any] = {}
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "_test_all.py")],
                           capture_output=True, text=True, timeout=600)
        m = re.search(r"HASIL: (\d+) lulus, (\d+) gagal", r.stdout)
        res["tests_pass"] = int(m.group(1)) if m else None
        res["tests_fail"] = int(m.group(2)) if m else None
    except Exception as e:                                   # pragma: no cover
        res["tests_error"] = str(e)
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, "_check_refs.py")],
                           capture_output=True, text=True, timeout=300)
        m = re.search(r"referensi hilang\s*:\s*(\d+)", r.stdout)
        res["refs_missing"] = int(m.group(1)) if m else None
    except Exception as e:                                   # pragma: no cover
        res["refs_error"] = str(e)
    return res


def subskills() -> List[Dict[str, str]]:
    out = []
    d = os.path.join(PKG, "skills")
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name, "SKILL.md")
        if os.path.exists(p):
            head = open(p, encoding="utf-8").read()[:400]
            m = re.search(r"description:\s*>-\s*\n\s*(.+)", head)
            out.append({"id": name, "summary": (m.group(1).strip()[:140] if m else "")})
    return out


def main(argv=None) -> int:
    dl = os.path.join(ROOT, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · package builder")
    ap.add_argument("--version", default="1.1.0")
    ap.add_argument("--skip-qa", action="store_true")
    a = ap.parse_args(argv)

    files = collect_files()
    qa = {} if a.skip_qa else run_qa()
    manifest = {
        "name": "dan-agent-skill",
        "version": a.version,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "python_min": "3.8",
        "mandatory_dependencies": [],
        "optional_dependencies": ["openpyxl", "networkx", "scipy", "Pillow"],
        "entrypoint": "skills/dan/SKILL.md",
        "system_prompt": "skills/dan/AGENT.md",
        "subskills": subskills(),
        "engines": ["dan_analytics.py", "svg_charts/ (paket)", "make_infographic.py",
                    "graph_analyst.py", "storyboard.py", "fit_asset.py",
                    "project_monitor.py", "make_forms.py", "arch_advisor.py",
                    "arch_design.py", "exec_dashboard.py", "make_sample_data.py"],
        "qa": qa,
        "file_count": len(files),
        "total_bytes": sum(f["bytes"] for f in files),
        "files": files,
    }
    os.makedirs(dl, exist_ok=True)
    mpath = os.path.join(dl, "manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    ipath = os.path.join(dl, "INSTALL.md")
    with open(ipath, "w", encoding="utf-8") as f:
        f.write(INSTALL_MD)

    # changelog
    cl = os.path.join(PKG, "CHANGELOG.md")
    entry = (f"\n## {a.version} — {datetime.now():%Y-%m-%d}\n"
             f"- Sub-skill 07 (PMO: monitoring/tracking/progress/controlling + form interaktif).\n"
             f"- Sub-skill 08 (software architecture: scaffold multi-bahasa, review pro/kon, compare).\n"
             f"- Sub-skill 09 (architectural design: denah 2D, massa 3D, tampak, KDB/KLB, RAB).\n"
             f"- `svg_charts` dipecah menjadi paket (ADR-004); tambah chart gantt & progress.\n"
             f"- `exec_dashboard.py` (dashboard eksekutif gabungan) & `make_package.py`.\n"
             f"- QA terpadu `_test_all.py`; ADR-001..004; CI `dan-qa.yml`.\n")
    old = open(cl, encoding="utf-8").read() if os.path.exists(cl) else \
        "# CHANGELOG — paket skill DAN\n\nFormat: https://keepachangelog.com · versi mengikuti semver.\n"
    if f"\n## {a.version} " not in old:
        old = old + entry
        with open(cl, "w", encoding="utf-8") as f:
            f.write(old)

    # zip
    zpath = os.path.join(dl, f"dan-skill-{a.version}.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(ROOT, f["path"]), f["path"])
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("INSTALL.md", INSTALL_MD)
    hist = os.path.join(ROOT, "skills", "dan", "qa_history.jsonl")
    with open(hist, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": manifest["generated_at"], "version": a.version,
                            "tests_pass": qa.get("tests_pass"),
                            "tests_fail": qa.get("tests_fail"),
                            "refs_missing": qa.get("refs_missing"),
                            "files": manifest["file_count"],
                            "bytes": manifest["total_bytes"]},
                           ensure_ascii=False) + "\n")
    print(f"[DAN] riwayat QA -> skills/dan/qa_history.jsonl")
    print(f"[DAN] manifest: {manifest['file_count']} file · "
          f"{manifest['total_bytes'] / 1024:.0f} KB · qa={qa}")
    print(f"[DAN] zip -> {zpath} ({os.path.getsize(zpath) / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
