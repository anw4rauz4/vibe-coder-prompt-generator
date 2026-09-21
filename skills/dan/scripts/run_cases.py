#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_cases.py — Katalog kasus end-to-end: demo, onboarding, DAN integration test.

Setiap kasus = satu folder di `skills/dan/cases/<nama>/case.json` berisi:
  steps   : daftar langkah {"engine": <nama>, "args": [...], "expect_exit": [0,1]}
  asserts : daftar pemeriksaan hasil
            {"kind":"file", "path": ...}
            {"kind":"json", "path":..., "key":"a.b.c", "op":"eq|gte|lte|gt|lt", "value":...}
            {"kind":"text", "path":..., "needle":...}
Token pada args: {root} = root workspace · {case} = folder kasus · {out} = folder keluaran
(keluaran tiap kasus diisolasi di deliverables/cases/<nama>/ agar tidak menimpa artefak utama).

PAKAI
  python3 run_cases.py list
  python3 run_cases.py run launch-serum
  python3 run_cases.py run all
  exit 0 bila semua kasus & assert lulus
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CASES = os.path.join(ROOT, "skills", "dan", "cases")
sys.path.insert(0, HERE)


def _sub(tok: str, root: str, case: str, out: str) -> str:
    return (tok.replace("{root}", root).replace("{case}", case).replace("{out}", out))


def _get(doc: Any, key: str) -> Any:
    cur = doc
    for p in key.split("."):
        if isinstance(cur, list):
            cur = cur[int(p)]
        else:
            cur = cur[p]
    return cur


def run_case(name: str, out_root: str) -> Tuple[bool, List[str]]:
    cdir = os.path.join(CASES, name)
    with open(os.path.join(cdir, "case.json"), encoding="utf-8") as f:
        case = json.load(f)
    out = os.path.join(out_root, name)
    os.makedirs(out, exist_ok=True)
    log: List[str] = []
    ok = True
    for i, st in enumerate(case.get("steps", []), 1):
        args = [_sub(a, ROOT, cdir, out) for a in st.get("args", [])]
        want = st.get("expect_exit", [0])
        try:
            mod = importlib.import_module(st["engine"])
            rc = int(mod.main(args) or 0)
        except SystemExit as e:                     # pragma: no cover
            rc = int(e.code or 0)
        good = rc in want
        ok = ok and good
        log.append(f"  [{'OK ' if good else 'FAIL'}] step {i} {st['engine']} "
                   f"(exit {rc}, ingin {want})")
    for a in case.get("asserts", []):
        p = _sub(a["path"], ROOT, cdir, out)
        good = False
        detail = ""
        if a["kind"] == "file":
            good = os.path.exists(p)
            detail = p
        elif a["kind"] == "text":
            good = os.path.exists(p) and a["needle"] in open(p, encoding="utf-8",
                                                             errors="replace").read()
            detail = f"{a['needle']} in {os.path.basename(p)}"
        elif a["kind"] == "json":
            try:
                v = _get(json.load(open(p, encoding="utf-8")), a["key"])
                op, want = a["op"], a["value"]
                good = {"eq": v == want, "gte": v >= want, "lte": v <= want,
                        "gt": v > want, "lt": v < want}[op]
                detail = f"{a['key']}={v} {op} {want}"
            except Exception as e:
                detail = f"error: {e}"
        ok = ok and good
        log.append(f"  [{'OK ' if good else 'FAIL'}] assert {a['kind']}: {detail}")
    return ok, log


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · cases runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    p = sub.add_parser("run")
    p.add_argument("name")
    p.add_argument("--out", default=os.path.join(ROOT, "deliverables", "cases"))
    a = ap.parse_args(argv)

    names = sorted(d for d in os.listdir(CASES)
                   if os.path.exists(os.path.join(CASES, d, "case.json")))
    if a.cmd == "list":
        for n in names:
            meta = json.load(open(os.path.join(CASES, n, "case.json"), encoding="utf-8"))
            print(f"  {n:16} {meta.get('title', '')} — {len(meta.get('steps', []))} langkah, "
                  f"{len(meta.get('asserts', []))} assert")
        return 0

    todo = names if a.name == "all" else [a.name]
    allok = True
    for n in todo:
        print(f"\n=== kasus: {n} ===")
        ok, log = run_case(n, a.out)
        print("\n".join(log))
        print(f"  -> {'LULUS' if ok else 'GAGAL'}")
        allok = allok and ok
    print(f"\n[DAN] cases: {'SEMUA LULUS' if allok else 'ADA YANG GAGAL'}")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
