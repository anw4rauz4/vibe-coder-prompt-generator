#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_server.py — Server MCP (Model Context Protocol) stdio, zero-dependency.

Membuat seluruh engine DAN dapat dipanggil oleh klien MCP apa pun:
Claude Desktop / Claude Code, Cursor, Gemini CLI, Windsurf, Zed, dst.

Konfigurasi klien (contoh claude_desktop_config.json / mcp.json):
{
  "mcpServers": {
    "dan": { "command": "python3",
             "args": ["/path/ke/skills/dan/scripts/mcp_server.py"] }
  }
}

Tool yang diekspos (whitelist aman):
  dan_list_skills, dan_list_engines, dan_run_engine, dan_demo,
  dan_rag_query, dan_lint_prompt, dan_project_status, dan_arch_compute,
  dan_stack_recommend, dan_weekly_summary

Protokol: JSON-RPC 2.0, pesan dipisah baris baru (stdio). Mendukung:
  initialize, notifications/initialized, tools/list, tools/call, ping.
"""
from __future__ import annotations

import io
import json
import os
import sys
from contextlib import redirect_stdout
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

ALLOWED_ENGINES = {
    "dan_analytics", "make_infographic", "graph_analyst", "storyboard", "fit_asset",
    "project_monitor", "make_forms", "weekly_run", "pmo_guard", "arch_advisor",
    "arch_design", "exec_dashboard", "claim_audit", "prompt_lab", "workflow", "rag",
    "stack_advisor", "assistant_builder", "llm_obs", "weekly_diff", "rag_eval",
    "make_digest", "demo_tour",
}

TOOLS: List[Dict[str, Any]] = [
    {"name": "dan_list_skills", "description": "Daftar 21 sub-skill DAN + deskripsinya.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "dan_list_engines", "description": "Daftar engine CLI yang bisa dijalankan.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "dan_run_engine",
     "description": "Jalankan engine DAN dengan argumen CLI (daftar string). "
                    "Contoh: {\"engine\":\"dan_analytics\",\"args\":[\"data.csv\"]}.",
     "inputSchema": {"type": "object",
                     "properties": {"engine": {"type": "string"},
                                    "args": {"type": "array",
                                             "items": {"type": "string"}}},
                     "required": ["engine"]}},
    {"name": "dan_demo", "description": "Tur demo singkat sub-skill (opsional --only).",
     "inputSchema": {"type": "object",
                     "properties": {"only": {"type": "string"}}}},
    {"name": "dan_rag_query", "description": "Tanya dokumen paket DAN (RAG bersitasi).",
     "inputSchema": {"type": "object",
                     "properties": {"q": {"type": "string"}, "top": {"type": "integer"}},
                     "required": ["q"]}},
    {"name": "dan_lint_prompt", "description": "Lint/skor prompt (sub-skill 10).",
     "inputSchema": {"type": "object",
                     "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "dan_project_status",
     "description": "Status portofolio proyek dari projects.json (monitoring).",
     "inputSchema": {"type": "object",
                     "properties": {"projects": {"type": "string"}}}},
    {"name": "dan_arch_compute",
     "description": "Hitung denah/3D/RAB dari building.json (sub-skill 09).",
     "inputSchema": {"type": "object",
                     "properties": {"building": {"type": "string"}},
                     "required": ["building"]}},
    {"name": "dan_stack_recommend",
     "description": "Rekomendasi stack tool AI (sub-skill 17).",
     "inputSchema": {"type": "object",
                     "properties": {"need": {"type": "string"},
                                    "budget": {"type": "string"}},
                     "required": ["need"]}},
    {"name": "dan_weekly_summary",
     "description": "Ringkasan mingguan PMO dari projects.json (+updates opsional).",
     "inputSchema": {"type": "object",
                     "properties": {"projects": {"type": "string"},
                                    "updates": {"type": "string"},
                                    "lang": {"type": "string"}},
                     "required": ["projects"]}},
]


def _cap(fn, *a, **kw) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        fn(*a, **kw)
    return buf.getvalue()


def _skills_brief() -> str:
    import make_adapters as ma
    return "\n".join(f"- {m['dir'][:2]} {m.get('title', m['name'])}: {m['desc'][:120]}"
                     for m in ma.subskill_meta())


def call_tool(name: str, args: Dict[str, Any]) -> str:
    import importlib
    if name == "dan_list_skills":
        return _skills_brief()
    if name == "dan_list_engines":
        return "\n".join(sorted(ALLOWED_ENGINES))
    if name == "dan_run_engine":
        eng = args.get("engine", "")
        if eng not in ALLOWED_ENGINES:
            return f"engine tidak diizinkan: {eng}. Pilihan: {sorted(ALLOWED_ENGINES)}"
        mod = importlib.import_module(eng)
        return _cap(mod.main, list(args.get("args", [])))
    if name == "dan_demo":
        import demo_tour
        return _cap(demo_tour.main, (["--only", args["only"]] if args.get("only") else []))
    if name == "dan_rag_query":
        import rag
        idx = rag.build_index([os.path.join(ROOT, "skills", "dan")])
        res = rag.query(idx, args["q"], int(args.get("top", 3)))
        return "\n\n".join(f"[{r['score']}] {r['file']} :: {r['heading']}\n{r['text']}"
                           for r in res) or "tidak ada chunk relevan"
    if name == "dan_lint_prompt":
        import prompt_lab
        L = prompt_lab.lint(args["text"])
        return (f"skor {L['score']}/100 ({L['grade']})\nhilang: " +
                ", ".join(m["name"] for m in L["missing"][:8]) +
                "\nsaran: " + " | ".join(L["advice"][:4]))
    if name == "dan_project_status":
        import project_monitor as pm
        p = args.get("projects") or os.path.join(ROOT, "skills", "dan", "templates",
                                                  "projects.example.json")
        A = pm.compute(json.load(open(p, encoding="utf-8")))
        po = A["portfolio"]
        return (f"{po['projects']} proyek · {po['on_track']} on-track · {po['warn']} waspada · "
                f"{po['bad']} kritis · {po['stalled']} stalled\n" +
                "\n".join(f"- {x['name']}: {x['progress']:.0f}% (rencana {x['planned']:.0f}%) "
                          f"{x['rag']}" for x in A["projects"]))
    if name == "dan_arch_compute":
        import arch_design as ad
        A = ad.compute(json.load(open(args["building"], encoding="utf-8")), 20)
        c = A["compliance"]
        return (f"terbangun {A['totals']['built_area']:.0f} m2 · {A['totals']['rooms']} ruang · "
                f"KDB {c['kdb']:.0f}%/{c['kdb_max']:.0f}% · KLB {c['klb']:.0f}%/{c['klb_max']:.0f}% · "
                f"RAB {A['meta']['currency']}{A['rab_total']:,.0f}")
    if name == "dan_stack_recommend":
        import stack_advisor as sa
        r = sa.recommend(args["need"], args.get("budget", "sedang"), 2, "menengah")
        return (f"stack ≈ ${r['monthly_usd']}/bln:\n" +
                "\n".join(f"- [{p['cat']}] {p['label']} (~${p['cost']}) + {'; '.join(p['pros'][:1])}"
                          for p in r["stack"]))
    if name == "dan_weekly_summary":
        import weekly_run as wr
        import project_monitor as pm
        doc = json.load(open(args["projects"], encoding="utf-8"))
        if args.get("updates"):
            up = json.load(open(args["updates"], encoding="utf-8"))
            up = up if isinstance(up, list) else up.get("updates", [])
            doc = pm.apply_updates(doc, up)["doc"]
        A = pm.compute(doc)
        decs = wr.pick_decisions(A, None)
        md = wr.build_summary(A, A["coach"], decs, wr.pick_focus(A),
                              {"marketing": None}, lang=args.get("lang", "id"))
        return md[:6000]
    return f"tool tidak dikenal: {name}"


def handle(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    m = msg.get("method")
    mid = msg.get("id")
    if m == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": msg.get("params", {}).get("protocolVersion",
                                                          "2024-11-05"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "dan-skill-server", "version": "2.2.0"}}}
    if m == "notifications/initialized" or m is None:
        return None
    if m == "ping":
        return {"jsonrpc": "2.0", "id": mid, "result": {}}
    if m == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}}
    if m == "tools/call":
        p = msg.get("params", {})
        name, args = p.get("name"), p.get("arguments", {}) or {}
        try:
            text = call_tool(name, args)
            return {"jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text", "text": text}],
                               "isError": False}}
        except Exception as e:                            # pragma: no cover
            return {"jsonrpc": "2.0", "id": mid,
                    "result": {"content": [{"type": "text", "text": f"error: {e}"}],
                               "isError": True}}
    return {"jsonrpc": "2.0", "id": mid,
            "error": {"code": -32601, "message": f"method tidak didukung: {m}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
