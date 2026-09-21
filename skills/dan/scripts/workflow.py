#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
workflow.py — Sub-skill 11 · AI Workflow Automation: runner DAG langkah antar-engine.

Mendefinisikan otomasi sebagai data (JSON), bukan skrip rapuh:
  steps : [{"id","engine","args":[...],"retry":0|1|2,"on_fail":"skip|abort",
            "when":{"file_exists": path} , "save_as": "kunci"}]
Token args: {root} {out} {prev.<kunci>} (path keluaran langkah sebelumnya yg disimpan).

Hasil eksekusi tercatat di workflow_run.json: status per langkah, durasi, exit code,
pesan — sehingga otomasi bisa diaudit & diulang aman (idempotent bila langkah idempotent).

PAKAI
  python3 workflow.py run workflow.json --out-dir deliverables/wf
  python3 workflow.py validate workflow.json
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)


def _sub(tok: str, out: str, prev: Dict[str, str]) -> str:
    s = tok.replace("{root}", ROOT).replace("{out}", out)
    for k, v in prev.items():
        s = s.replace("{prev." + k + "}", v)
    return s


def validate(wf: Dict[str, Any]) -> List[str]:
    errs = []
    ids = set()
    for i, st in enumerate(wf.get("steps", [])):
        if "engine" not in st:
            errs.append(f"step {i}: tanpa 'engine'")
        if st.get("id"):
            if st["id"] in ids:
                errs.append(f"step {i}: id duplikat {st['id']}")
            ids.add(st["id"])
        if st.get("on_fail") not in (None, "skip", "abort"):
            errs.append(f"step {i}: on_fail harus skip|abort")
        if st.get("retry") not in (None, 0, 1, 2, 3):
            errs.append(f"step {i}: retry harus 0..3")
    return errs


def run(wf: Dict[str, Any], out_dir: str) -> Dict[str, Any]:
    os.makedirs(out_dir, exist_ok=True)
    prev: Dict[str, str] = {}
    results: List[Dict[str, Any]] = []
    ok_all = True
    for i, st in enumerate(wf.get("steps", []), 1):
        cond = st.get("when") or {}
        if "file_exists" in cond and not os.path.exists(_sub(cond["file_exists"], out_dir, prev)):
            results.append({"i": i, "id": st.get("id", f"step{i}"), "status": "skipped-cond",
                            "exit": None, "secs": 0})
            continue
        args = [_sub(a, out_dir, prev) for a in st.get("args", [])]
        tries = int(st.get("retry", 0)) + 1
        rc, secs = None, 0.0
        for attempt in range(tries):
            t0 = time.time()
            try:
                mod = importlib.import_module(st["engine"])
                rc = int(mod.main(args) or 0)
            except SystemExit as e:
                rc = int(e.code or 0)
            except Exception as e:
                rc = 1
                print(f"   ! exception: {e}")
            secs = round(time.time() - t0, 2)
            if rc == 0:
                break
        status = "ok" if rc == 0 else ("skipped" if st.get("on_fail") == "skip" else "failed")
        if rc != 0 and st.get("on_fail") != "skip":
            ok_all = False
        rec = {"i": i, "id": st.get("id", f"step{i}"), "engine": st["engine"],
               "status": status, "exit": rc, "secs": secs, "attempt": attempt + 1}
        results.append(rec)
        print(f"  [{'OK ' if rc == 0 else 'FAIL'}] {rec['id']} ({st['engine']}) "
              f"exit={rc} {secs}s")
        if st.get("save_as") and rc == 0 and args:
            prev[st["save_as"]] = args[-1]
        if rc != 0 and st.get("on_fail") == "abort":
            break
    summary = {"workflow": wf.get("name", "?"), "ok": ok_all,
               "steps": results,
               "counts": {"ok": sum(1 for r in results if r["status"] == "ok"),
                          "failed": sum(1 for r in results if r["status"] == "failed"),
                          "skipped": sum(1 for r in results if r["status"].startswith("skipped"))}}
    with open(os.path.join(out_dir, "workflow_run.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · workflow runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("workflow")
    p.add_argument("--out-dir", default=os.path.join(ROOT, "deliverables", "wf"))
    p = sub.add_parser("validate")
    p.add_argument("workflow")
    a = ap.parse_args(argv)
    wf = json.load(open(a.workflow, encoding="utf-8"))
    errs = validate(wf)
    if a.cmd == "validate":
        if errs:
            print("[DAN] workflow TIDAK valid:")
            for e in errs:
                print("   -", e)
            return 1
        print(f"[DAN] workflow valid: {len(wf.get('steps', []))} langkah")
        return 0
    if errs:
        print("[DAN] workflow tidak valid; perbaiki dulu:", errs)
        return 1
    s = run(wf, a.out_dir)
    print(f"[DAN] workflow {s['workflow']}: {s['counts']} -> "
          f"{os.path.join(a.out_dir, 'workflow_run.json')}")
    return 0 if s["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
