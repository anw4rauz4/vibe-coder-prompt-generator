#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_smoke.py — Uji integrasi NYATA server MCP: panggil semua tool, verifikasi keluaran.

Menjalankan mcp_server.py sebagai subprocess, lalu mengirim urutan pesan JSON-RPC:
  initialize → tools/list → tools/call untuk SETIAP tool (dengan argumen aman)
dan memverifikasi tiap balasan: isError=False + teks tidak kosong + penanda konten.

PAKAI
  python3 mcp_smoke.py                 # tabel hasil + exit 0 bila semua lulus
  python3 mcp_smoke.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))

TPL = os.path.join(ROOT, "skills", "dan", "templates")
DATA = os.path.join(ROOT, "data")

# argumen aman & deterministik untuk tiap tool
CALLS: List[Dict[str, Any]] = [
    {"name": "dan_list_skills", "args": {}, "expect": "Prompt Engineering"},
    {"name": "dan_list_engines", "args": {}, "expect": "dan_analytics"},
    {"name": "dan_demo", "args": {"only": "10"}, "expect": "[10]"},
    {"name": "dan_rag_query", "args": {"q": "ambang waspada variance proyek", "top": 2},
     "expect": "SKILL.md"},
    {"name": "dan_lint_prompt",
     "args": {"text": "Bertindaklah sebagai analis. Berdasarkan campaign.csv Q3 buat tabel "
                       "ROAS per channel format markdown maksimal 150 kata jangan mengarang."},
     "expect": "skor"},
    {"name": "dan_project_status",
     "args": {"projects": os.path.join(TPL, "projects.example.json")},
     "expect": "proyek"},
    {"name": "dan_arch_compute", "args": {"building": os.path.join(DATA, "kafe_case.json")},
     "expect": "terbangun"},
    {"name": "dan_stack_recommend", "args": {"need": "chatbot rag dokumen", "budget": "rendah"},
     "expect": "stack"},
    {"name": "dan_weekly_summary",
     "args": {"projects": os.path.join(TPL, "projects.example.json"), "lang": "id"},
     "expect": "Angka minggu ini"},
    {"name": "dan_run_engine",
     "args": {"engine": "prompt_lab",
              "args": ["lint", "--text", "buatkan ringkasan untuk pimpinan maksimal 5 poin"]},
     "expect": "skor"},
]


def run() -> List[Dict[str, Any]]:
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                        "clientInfo": {"name": "mcp-smoke", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    for i, c in enumerate(CALLS, 10):
        msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call",
                     "params": {"name": c["name"], "arguments": c["args"]}})
    p = subprocess.run([sys.executable, os.path.join(HERE, "mcp_server.py")],
                       input="\n".join(json.dumps(m) for m in msgs),
                       capture_output=True, text=True, timeout=300)
    byid = {}
    for ln in p.stdout.splitlines():
        if ln.strip():
            o = json.loads(ln)
            byid[o.get("id")] = o
    rows = []
    listed = byid.get(2, {}).get("result", {}).get("tools", [])
    rows.append({"tool": "(tools/list)", "ok": len(listed) >= 10,
                 "detail": f"{len(listed)} tool terdaftar"})
    for i, c in enumerate(CALLS, 10):
        r = byid.get(i, {})
        res = r.get("result", {})
        text = (res.get("content") or [{}])[0].get("text", "")
        ok = (res.get("isError") is False) and bool(text.strip()) \
            and c["expect"].lower() in text.lower()
        rows.append({"tool": c["name"], "ok": ok,
                     "detail": (text.strip().splitlines() or [""])[0][:70]})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · MCP integration smoke")
    ap.add_argument("--json", default="")
    a = ap.parse_args(argv)
    rows = run()
    print(f"{'TOOL':24} {'STATUS':7} KELUARAN")
    print("-" * 78)
    for r in rows:
        print(f"{r['tool']:24} {'OK' if r['ok'] else 'GAGAL':7} {r['detail']}")
    bad = [r for r in rows if not r["ok"]]
    if a.json:
        os.makedirs(os.path.dirname(os.path.abspath(a.json)) or ".", exist_ok=True)
        json.dump(rows, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n[DAN] mcp smoke: {len(rows) - len(bad)}/{len(rows)} tool lulus")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
