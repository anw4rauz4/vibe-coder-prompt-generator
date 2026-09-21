#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
release.py — Satu perintah rilis terurutan; QA tidak bisa dilompati.

Urutan WAJIB (kecuali disebut di --skip):
  1 test      : _test_all.py (smoke+property+integrasi)      -> gagal = berhenti
  2 cases     : run_cases.py run all                        -> gagal = berhenti
  3 refs      : _check_refs.py                              -> gagal = berhenti
  4 adapters  : make_adapters.py build + validate           -> gagal = berhenti
  5 package   : make_package.py --version V (zip+pyz+manifest+riwayat QA)
  6 digest    : make_digest.py (digest rilis + naskah audio)
  7 notify    : notify.py (bila --channel diberi)
  8 health    : pkg_health.py (dashboard kesehatan paket)

Bila langkah 1-4 gagal, rilis DIHENTIKAN sebelum paket dibuat — sehingga tidak ada
zip "cacat" yang beredar. Laporan rilis ditulis ke deliverables/release_<V>.md.

PAKAI
  python3 release.py --version 2.9.0
  python3 release.py --version 2.9.0 --channel slack --skip notify
  python3 release.py --version 2.9.0 --dry-run     # hanya cetak rencana langkah
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

GATE = ["test", "cases", "refs", "adapters"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · gated release pipeline")
    ap.add_argument("--version", required=True)
    ap.add_argument("--channel", default="",
                    choices=["", "telegram", "slack", "email", "stdout"])
    ap.add_argument("--skip", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--with-sec", action="store_true",
                    help="jadikan sec_audit gate wajib (S1 harus nol)")
    a = ap.parse_args(argv)
    skip = {x.strip() for x in a.skip.split(",") if x.strip()}
    dl = os.path.join(ROOT, "deliverables")
    os.makedirs(dl, exist_ok=True)

    steps: List[Dict[str, Any]] = []
    log: List[str] = []

    def run(name: str, fn, gate: bool) -> int:
        if name in skip:
            steps.append({"step": name, "status": "skipped"})
            log.append(f"  [--] {name} (dilewati)")
            return 0
        t0 = time.time()
        try:
            rc = int(fn() or 0)
        except SystemExit as e:
            rc = int(e.code or 0)
        except Exception as e:                                   # pragma: no cover
            print(f"   ! {name}: {e}")
            rc = 1
        secs = round(time.time() - t0, 1)
        steps.append({"step": name, "status": "ok" if rc == 0 else "fail", "secs": secs})
        log.append(f"  [{'OK ' if rc == 0 else 'FAIL'}] {name:9} {secs:>6}s")
        return rc

    import _test_all, run_cases, _check_refs, make_adapters, make_package
    import make_digest, notify, pkg_health, sec_audit

    print(f"[DAN] rilis v{a.version} dimulai" + (" (dry-run)" if a.dry_run else ""))
    if a.dry_run:
        plan = GATE + (["sec"] if a.with_sec else []) + ["package", "digest"] + \
        (["notify"] if a.channel else []) + ["health"]
        for p in plan:
            print("   rencana:", p, "(skip)" if p in skip else "")
        return 0

    failed = None
    for name, fn in (("test", lambda: _test_all.main()),
                     ("cases", lambda: run_cases.main(["run", "all"])),
                     ("refs", lambda: _check_refs.main()),
                     ("adapters", lambda: make_adapters.main(["build"])),
                     *((("sec", lambda: sec_audit.main(["--path", ROOT])),)
                       if a.with_sec else ())):
        rc = run(name, fn, True)
        if rc != 0:
            failed = name
            break
    if failed:
        msg = (f"[DAN] RILIS DIHENTIKAN: gate '{failed}' gagal. "
               f"Perbaiki dulu, jangan kirim paket cacat.")
        print(msg)
        with open(os.path.join(dl, f"release_{a.version}.md"), "w", encoding="utf-8") as f:
            f.write(f"# Rilis v{a.version} — DIHENTIKAN\n\nGate gagal: **{failed}**\n\n"
                    + "\n".join(log) + "\n")
        return 1

    run("package", lambda: make_package.main(["--version", a.version]), False)
    run("digest", lambda: make_digest.main([
        "--version", a.version,
        "--out", os.path.join(dl, f"digest_v{a.version}.md"),
        "--audio", os.path.join(dl, f"digest_v{a.version}_audio.txt")]), False)
    if a.channel:
        run("notify", lambda: notify.main([
            "--projects", os.path.join(ROOT, "skills", "dan", "templates",
                                       "projects.example.json"),
            "--channel", a.channel,
            "--out", os.path.join(dl, f"notif_release_{a.channel}.txt")]), False)
    run("health", lambda: pkg_health.main(["--out", os.path.join(dl, "pkg_health.html")]),
        False)

    n_ok = sum(1 for s in steps if s["status"] == "ok")
    rep = (f"# Rilis v{a.version} — SELESAI\n\n"
           f"**{n_ok}/{len(steps)} langkah ok**\n\n```\n" + "\n".join(log) +
           f"\n```\n\nArtefak: dan-skill-{a.version}.zip · dan.pyz · digest_v{a.version}.md · "
           f"pkg_health.html\n")
    with open(os.path.join(dl, f"release_{a.version}.md"), "w", encoding="utf-8") as f:
        f.write(rep)
    print("\n".join(log))
    print(f"[DAN] rilis v{a.version}: {n_ok}/{len(steps)} langkah ok -> "
          f"{os.path.join(dl, f'release_{a.version}.md')}")
    return 0 if n_ok == len(steps) else 1


if __name__ == "__main__":
    raise SystemExit(main())
