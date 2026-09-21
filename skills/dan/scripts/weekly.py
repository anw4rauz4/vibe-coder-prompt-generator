#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly.py — Satu perintah untuk SELURUH ritme mingguan PMO (cron-ready).

Urutan langkah (tiap langkah tercatat di run_log.json):
  1. weekly_run   : apply update form → report → dashboard → coach → exec → summary
  2. snap         : weekly_diff snap → history.jsonl (append-only)
  3. burnup       : burn-up multi-periode dari history.jsonl
  4. guard        : pmo_guard pada projects ter-update (exit code = gate)
  5. notify       : render notifikasi channel pilihan
  6. digest       : digest rilis/periode + naskah audio
  7. claim_audit  : audit angka pada weekly_summary terhadap sumber

Exit code: 0 = ritme selesai & guard bersih · 1 = guard gagal (kecuali --allow-guard-fail)
atau ada langkah error. Cocok untuk cron/GH Actions: kegagalan = sinyal, bukan keheningan.

CRON CONTOH (Senin 06:00):
  0 6 * * 1 cd /path/skills/dan/scripts && python3 weekly.py \
      --projects /path/projects.json --updates /path/batch.json \
      --channel slack --out-dir /path/out >> /path/weekly.log 2>&1

PAKAI
  python3 weekly.py --projects projects.json [--updates batch.json] \
      [--marketing analysis.json] [--arch arch.json ...] \
      [--channel slack] [--lang id] [--out-dir deliverables] [--allow-guard-fail]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Callable, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)


def _step(log: List[Dict[str, Any]], name: str, fn: Callable[[], int],
          allow_fail: bool = False) -> int:
    t0 = time.time()
    try:
        rc = int(fn() or 0)
    except SystemExit as e:
        rc = int(e.code or 0)
    except Exception as e:                                   # pragma: no cover
        print(f"   ! {name}: {e}")
        rc = 1
    secs = round(time.time() - t0, 2)
    status = "ok" if rc == 0 else ("warn" if allow_fail else "fail")
    log.append({"step": name, "exit": rc, "status": status, "secs": secs})
    print(f"  [{'OK ' if rc == 0 else 'FAIL'}] {name:12} {secs:>6}s")
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · weekly rhythm (cron-ready)")
    ap.add_argument("--projects", required=True)
    ap.add_argument("--updates", default="")
    ap.add_argument("--marketing", default="")
    ap.add_argument("--arch", action="append", default=[])
    ap.add_argument("--channel", default="stdout",
                    choices=["telegram", "slack", "email", "stdout"])
    ap.add_argument("--lang", default="id")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "deliverables"))
    ap.add_argument("--history", default="")
    ap.add_argument("--allow-guard-fail", action="store_true")
    ap.add_argument("--skip", default="", help="langkah dilewati, mis. digest,notify")
    a = ap.parse_args(argv)

    import weekly_run as wr
    import weekly_diff as wd
    import burnup as bu
    import pmo_guard as pg
    import notify as nf
    import make_digest as mdg
    import claim_audit as ca
    import project_monitor as pm

    os.makedirs(a.out_dir, exist_ok=True)
    skip = {x.strip() for x in a.skip.split(",") if x.strip()}
    hist = a.history or os.path.join(a.out_dir, "history.jsonl")
    upd_path = os.path.join(a.out_dir, "projects_updated.json")
    rep_path = os.path.join(a.out_dir, "project_report.json")
    summ_path = os.path.join(a.out_dir, "weekly_summary.md")
    log: List[Dict[str, Any]] = []
    failed = []

    print("[DAN] ritme mingguan dimulai")
    if "weekly" not in skip:
        args = ["--projects", a.projects, "--out-dir", a.out_dir, "--lang", a.lang]
        if a.updates:
            args += ["--updates", a.updates]
        if a.marketing:
            args += ["--marketing", a.marketing]
        rc = _step(log, "weekly_run", lambda: wr.main(args))
        if rc:
            failed.append("weekly_run")
    if "snap" not in skip and os.path.exists(rep_path):
        rc = _step(log, "snap", lambda: wd.main(["snap", "--report", rep_path,
                                                 "--log", hist]))
        if rc:
            failed.append("snap")
    if "burnup" not in skip:
        rc = _step(log, "burnup", lambda: bu.main(["--log", hist, "--out",
                                                   os.path.join(a.out_dir, "burnup.html")]),
                   allow_fail=True)
    if "guard" not in skip:
        target = upd_path if os.path.exists(upd_path) else a.projects
        rc = _step(log, "guard", lambda: pg.main([target, "--report",
                                                  os.path.join(a.out_dir, "pmo_guard.md")]),
                   allow_fail=a.allow_guard_fail)
        if rc and not a.allow_guard_fail:
            failed.append("guard")
    if "notify" not in skip:
        docp = upd_path if os.path.exists(upd_path) else a.projects
        rc = _step(log, "notify", lambda: nf.main(["--projects", docp, "--channel",
                                                   a.channel, "--lang", a.lang, "--out",
                                                   os.path.join(a.out_dir,
                                                                f"notif_{a.channel}.txt")]))
        if rc:
            failed.append("notify")
    if "digest" not in skip:
        rc = _step(log, "digest", lambda: mdg.main([
            "--out", os.path.join(a.out_dir, "digest_terbaru.md"),
            "--audio", os.path.join(a.out_dir, "digest_terbaru_audio.txt")]),
            allow_fail=True)
    if "narrative" not in skip and os.path.exists(summ_path):
        import narrative_check as nc
        rc = _step(log, "narrative", lambda: nc.main([
            "--file", summ_path, "--out",
            os.path.join(a.out_dir, "narrative_weekly.md")]), allow_fail=True)
    if "audit" not in skip and os.path.exists(summ_path):
        sources = [s for s in ([rep_path, a.marketing] if a.marketing else [rep_path])
                   if s and os.path.exists(s)]
        rc = _step(log, "claim_audit", lambda: ca.main([
            "--report", summ_path, "--out", os.path.join(a.out_dir, "claim_weekly.md")]
            + sum([["--source", s] for s in sources], [])), allow_fail=True)

    with open(os.path.join(a.out_dir, "run_log.json"), "w", encoding="utf-8") as f:
        json.dump({"steps": log, "failed": failed}, f, ensure_ascii=False, indent=2)
    n_ok = sum(1 for x in log if x["status"] == "ok")
    print(f"[DAN] ritme selesai: {n_ok}/{len(log)} langkah ok"
          + (f" · GAGAL: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
