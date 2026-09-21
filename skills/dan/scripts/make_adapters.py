#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_adapters.py — Plug-and-play: ekspor paket DAN ke format tiap runtime AI.

Satu sumber kebenaran (AGENT.md + frontmatter SKILL.md tiap sub-skill) diekspor ke:
  adapters/claude/      CLAUDE.md + INSTALL (skills/ sudah sesuai format Agent Skills)
  adapters/cursor/      .cursor rules (.mdc) inti + per sub-skill
  adapters/gemini/      GEMINI.md + Gems (instruksi per sub-skill)
  adapters/chatgpt/     instruksi Custom GPT (≤8000 karakter) + catatan knowledge
  adapters/copilot/     copilot-instructions.md
  adapters/agents/      AGENTS.md (standar lintas-agent: Codex/Cursor/Windsurf/dll)
  adapters/SYSTEM_PROMPT.txt   prompt sistem generik untuk runtime apa pun

PAKAI
  python3 make_adapters.py                 # ekspor semua
  python3 make_adapters.py --only cursor,gemini
  python3 make_adapters.py validate        # cek semua artefak adapter
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SKILLS = os.path.join(ROOT, "skills", "dan", "skills")
OUT = os.path.join(ROOT, "adapters")

GPT_LIMIT = 8000


def subskill_meta() -> List[Dict[str, str]]:
    out = []
    for d in sorted(os.listdir(SKILLS)):
        p = os.path.join(SKILLS, d, "SKILL.md")
        if not os.path.exists(p):
            continue
        txt = open(p, encoding="utf-8").read()
        m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
        name, desc = d, ""
        if m:
            fm = m.group(1)
            mn = re.search(r"^name:\s*(.+)$", fm, re.M)
            md = re.search(r"^description:\s*>-\s*\n((?:\s+.+\n?)+)", fm, re.M)
            if mn:
                name = mn.group(1).strip()
            if md:
                desc = " ".join(x.strip() for x in md.group(1).split("\n"))
        mt = re.search(r"^#\s+(.+)$", txt[m.end():] if m else txt, re.M)
        title = mt.group(1).strip() if mt else name
        out.append({"dir": d, "name": name, "desc": desc, "title": title})
    return out


def persona() -> str:
    txt = open(os.path.join(ROOT, "skills", "dan", "AGENT.md"), encoding="utf-8").read()
    m = re.search(r"```text\n(.*?)```", txt, re.S)
    return m.group(1).strip() if m else txt[:4000]


def routing_lines(meta: List[Dict[str, str]]) -> str:
    return "\n".join(f"- {m['dir'][:2]} {m['title']}: panggil bila permintaan cocok — "
                     f"{m['desc'][:150]}" for m in meta)


def write(path: str, body: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)


def build_all(meta: List[Dict[str, str]], pers: str) -> Dict[str, List[str]]:
    made: Dict[str, List[str]] = {}
    route = routing_lines(meta)
    head = ("# DAN — Agen Marketing & AI Multi-Skill\n\n"
            "Paket skill lengkap tersedia di repositori ini (lihat skills/dan/SKILL.md).\n"
            "Gunakan aturan berikut untuk memilih sub-skill:\n\n" + route +
            "\n\n## Aturan kerja wajib\n"
            "1. Data dulu, opini belakangan; setiap angka harus tertelusur atau ditandai `asumsi:`.\n"
            "2. Setiap temuan diikuti satu aksi terukur + tenggat.\n"
            "3. Engine tersedia sebagai CLI: `python3 skills/dan/scripts/dan.py run <engine> …`.\n"
            "4. QA sebelum menyerahkan: `python3 skills/dan/scripts/_test_all.py`.\n")

    # Claude
    write(f"{OUT}/claude/CLAUDE.md", head + "\n## Persona\n```\n" + pers + "\n```\n")
    write(f"{OUT}/claude/INSTALL.md",
          "# Install untuk Claude (Code / Claude.ai / API)\n\n"
          "1. Claude Code / Agent Skills:\n"
          "   salin folder `skills/dan/` ke `.claude/skills/dan/` (per-proyek) atau\n"
          "   `~/.claude/skills/dan/` (global). Format SKILL.md sudah sesuai Agent Skills.\n"
          "2. Claude.ai Projects: unggah `skills/dan/` sebagai project knowledge;\n"
          "   tempel `adapters/SYSTEM_PROMPT.txt` ke project instructions.\n"
          "3. API: kirim SYSTEM_PROMPT.txt sebagai system message; panggil engine via\n"
          "   tool-use (bash) atau MCP server `skills/dan/scripts/mcp_server.py`.\n")
    made["claude"] = ["CLAUDE.md", "INSTALL.md"]

    # Cursor
    rules = [f"{OUT}/cursor/rules/dan-core.mdc"]
    write(f"{OUT}/cursor/rules/dan-core.mdc",
          "---\ndescription: Router inti agen DAN (marketing, data, desain, PMO, AI skills)\n"
          "globs: **/*\nalwaysApply: false\n---\n\n" + head +
          "\nUntuk detail per sub-skill, rule `dan-<nomor>` akan aktif sesuai konteks.\n")
    for m in meta:
        fn = f"dan-{m['dir'][:2]}.mdc"
        write(f"{OUT}/cursor/rules/{fn}",
              f"---\ndescription: {m['desc'][:300]}\nglobs: \nalwaysApply: false\n---\n\n"
              f"# {m['name']}\n\nBaca selengkapnya: `skills/dan/skills/{m['dir']}/SKILL.md`.\n\n"
              f"{m['desc']}\n")
        rules.append(f"rules/{fn}")
    made["cursor"] = [os.path.relpath(r, f"{OUT}/cursor") for r in rules]

    # Gemini
    write(f"{OUT}/gemini/GEMINI.md", head + "\n## Persona\n```\n" + pers + "\n```\n"
          "\nGemini CLI juga dapat memanggil engine lewat bash atau MCP server paket ini.\n")
    gems = []
    for m in meta:
        fn = f"gems/{m['dir'][:2]}-{m['dir'][3:18]}.txt"
        write(f"{OUT}/gemini/{fn}",
              f"Kamu adalah sub-agent DAN: {m['name']}.\n\n{m['desc']}\n\n"
              f"Rujukan lengkap: skills/dan/skills/{m['dir']}/SKILL.md di repositori.\n"
              f"Patuhi aturan kerja DAN (data dulu, aksi terukur, QA).\n")
        gems.append(fn)
    made["gemini"] = ["GEMINI.md"] + gems

    # ChatGPT
    rules = ("\n\nATURAN: data dulu opini kemudian; angka tertelusur atau `asumsi:`; "
             "setiap temuan = 1 aksi terukur; tawarkan 2-3 langkah berikutnya.")
    instr = pers + "\n\nROUTING SUB-SKILL:\n" + route + rules
    if len(instr.encode("utf-8")) > GPT_LIMIT:
        # pangkas deskripsi routing, lalu potong aman pada batas byte
        short = "\n".join(f"- {m['dir'][:2]} {m['name']}: {m['desc'][:80]}" for m in meta)
        instr = pers + "\n\nROUTING SUB-SKILL:\n" + short + rules
    while len(instr.encode("utf-8")) > GPT_LIMIT - 60:
        instr = instr[:len(instr) - 400]
    instr = instr.rstrip() + "\n…(detail lengkap ada di knowledge project)"
    write(f"{OUT}/chatgpt/custom_gpt_instructions.txt", instr)
    write(f"{OUT}/chatgpt/NOTES.md",
          "# Custom GPT notes\n\n1. Tempel isi `custom_gpt_instructions.txt` ke Instructions.\n"
          "2. Unggah folder `skills/dan/references/` + `templates/` sebagai Knowledge.\n"
          "3. Action/server: arahkan ke MCP server paket ini bila tersedia.\n")
    made["chatgpt"] = ["custom_gpt_instructions.txt", "NOTES.md"]

    # Copilot
    write(f"{OUT}/copilot/copilot-instructions.md", head)
    made["copilot"] = ["copilot-instructions.md"]

    # AGENTS.md (standar lintas agent)
    write(f"{OUT}/agents/AGENTS.md",
          "# AGENTS.md — DAN\n\n" + head +
          "\n## Perintah penting\n"
          "- QA: `python3 skills/dan/scripts/_test_all.py`\n"
          "- Kasus: `python3 skills/dan/scripts/run_cases.py run all`\n"
          "- Tur: `python3 skills/dan/scripts/dan.py demo`\n"
          "- MCP: `python3 skills/dan/scripts/mcp_server.py` (stdio)\n\n"
          "## Struktur\n- `skills/dan/skills/NN-*/SKILL.md` = sub-skill\n"
          "- `skills/dan/scripts/` = engine CLI zero-dependency\n")
    made["agents"] = ["AGENTS.md"]

    # Windsurf
    write(f"{OUT}/windsurf/rules/dan.md",
          "---\ntrigger: manual\n---\n\n# DAN (manual rule)\n\n" + head +
          "\nAktifkan rule ini saat bekerja pada tugas marketing/data/desain/PMO.\n")
    made["windsurf"] = ["rules/dan.md"]

    # Zed
    write(f"{OUT}/zed/settings_snippet.json", json.dumps({
        "assistant": {"default_model": None,
                      "context_servers": [{"name": "dan",
                                           "command": {"path": "python3",
                                                       "args": ["<abs>/skills/dan/scripts/"
                                                                "mcp_server.py"]}}]}},
        indent=2))
    write(f"{OUT}/zed/README.md",
          "# Zed\n\n1. Salin `adapters/agents/AGENTS.md` ke root proyek (dibaca Zed assistant).\n"
          "2. Tambahkan isi `settings_snippet.json` ke `context_servers` di settings Zed\n"
          "   agar tool DAN tersedia lewat MCP.\n")
    made["zed"] = ["settings_snippet.json", "README.md"]

    # Continue.dev
    write(f"{OUT}/continue/config_snippet.json", json.dumps({
        "rules": ["Gunakan paket skill DAN di skills/dan/ untuk tugas marketing/data/"
                  "desain/PMO; baca SKILL.md orchestrator dulu, lalu sub-skill terkait.",
                  "Setiap klaim numerik harus tertelusur ke data atau ditandai `asumsi:`.",
                  "Jalankan QA `python3 skills/dan/scripts/_test_all.py` sebelum menyerahkan."],
        "mcpServers": [{"name": "dan",
                        "command": "python3",
                        "args": ["<abs>/skills/dan/scripts/mcp_server.py"]}]}, indent=2))
    made["continue"] = ["config_snippet.json"]

    # n8n (otomasi ritme mingguan via Execute Command)
    nodes = []
    steps = [("Weekly run", "python3 <abs>/skills/dan/scripts/weekly_run.py "
                           "--projects <abs>/projects.json --out-dir <abs>/out", 0),
             ("PMO guard", "python3 <abs>/skills/dan/scripts/pmo_guard.py "
                           "<abs>/out/projects_updated.json || echo GUARD_GAGAL", 1),
             ("Notify", "echo 'Ringkasan mingguan siap; lihat out/weekly_summary.md'", 2)]
    for i, (nm, cmd, pos) in enumerate(steps):
        nodes.append({"id": f"dan-{i}", "name": nm,
                      "type": "n8n-nodes-base.executeCommand", "typeVersion": 1,
                      "position": [200 + pos * 220, 300],
                      "parameters": {"command": cmd}})
    conns = {steps[i][0]: {"main": [[{"node": steps[i + 1][0], "type": "main", "index": 0}]]}
             for i in range(len(steps) - 1)}
    write(f"{OUT}/n8n/dan-weekly-workflow.json", json.dumps({
        "name": "DAN weekly PMO", "nodes": nodes, "connections": conns,
        "settings": {"executionOrder": "v1"},
        "meta": {"note": "Ganti <abs> dengan path absolut repositori Anda."}}, indent=2))
    write(f"{OUT}/n8n/README.md",
          "# n8n\n\nImpor `dan-weekly-workflow.json`, ganti placeholder `<abs>`, lalu jadwal\n"
          "cron Senin 01:00. Node `PMO guard` menghasilkan teks GUARD_GAGAL bila ada\n"
          "tugas kritis tanpa tindakan — sambungkan ke node notifikasi (Telegram/email/Slack).\n")
    made["n8n"] = ["dan-weekly-workflow.json", "README.md"]

    # Dify / Flowise: tidak digenerate otomatis (DSL proprietary) — catatan jujur
    write(f"{OUT}/dify-flowise/NOTES.md",
          "# Dify / Flowise\n\nDSL keduanya proprietary & berubah cepat, jadi TIDAK kami "
          "generate otomatis.\nCara integrasi yang stabil:\n"
          "1. Buat node *Tool/HTTP* yang memanggil `dan.pyz`/`mcp_server.py` "
          "(mis. `python3 dan.pyz run dan_analytics data.csv`).\n"
          "2. Atau ekspos MCP server paket ini dan daftarkan sebagai plugin MCP di Dify.\n"
          "3. Tempel `SYSTEM_PROMPT.txt` ke LLM node sebagai system message.\n")
    made["dify-flowise"] = ["NOTES.md"]

    # VS Code lokal: .vscode/ aktif di root + salinan distribusi di adapters/vscode
    mcp_cfg = {"servers": {"dan": {"type": "stdio", "command": "python3",
                           "args": ["${workspaceFolder}/skills/dan/scripts/mcp_server.py"]}}}
    settings = {"python.analysis.extraPaths": ["skills/dan/scripts"],
                "python.terminal.launchArgs": [],
                "files.associations": {"*.mdc": "markdown"},
                "search.exclude": {"**/deliverables/cases": True},
                "dan.root": "${workspaceFolder}"}
    tasks = {"version": "2.0.0", "tasks": [
        {"label": "DAN: QA penuh", "type": "shell",
         "command": "python3 skills/dan/scripts/dan.py doctor --full",
         "group": {"kind": "test", "isDefault": True}},
        {"label": "DAN: tur demo", "type": "shell",
         "command": "python3 skills/dan/scripts/dan.py demo"},
        {"label": "DAN: kasus end-to-end", "type": "shell",
         "command": "python3 skills/dan/scripts/run_cases.py run all"},
        {"label": "DAN: ritme mingguan (contoh)", "type": "shell",
         "command": "python3 skills/dan/scripts/weekly.py --projects "
                    "skills/dan/templates/projects.example.json --out-dir deliverables"},
        {"label": "DAN: regenerasi adapter", "type": "shell",
         "command": "python3 skills/dan/scripts/make_adapters.py"},
        {"label": "DAN: MCP smoke", "type": "shell",
         "command": "python3 skills/dan/scripts/mcp_smoke.py"},
        {"label": "DAN: infografik contoh", "type": "shell",
         "command": "python3 skills/dan/scripts/make_infographic.py "
                    "deliverables/analysis.json --out deliverables/infographic.html"}]}
    launch = {"version": "0.2.0", "configurations": [
        {"name": "DAN: engine saat ini", "type": "debugpy", "request": "launch",
         "program": "${file}", "console": "integratedTerminal",
         "env": {"DAN_ROOT": "${workspaceFolder}"}},
        {"name": "DAN: CLI args", "type": "debugpy", "request": "launch",
         "program": "${workspaceFolder}/skills/dan/scripts/dan.py",
         "args": "${input:danArgs}", "console": "integratedTerminal",
         "env": {"DAN_ROOT": "${workspaceFolder}"}}],
        "inputs": [{"id": "danArgs", "type": "promptString",
                    "description": "argumen dan.py, mis.: run dan_analytics data.csv",
                    "default": "list"}]}
    snippets = {"dan engine run": {
        "scope": "python,markdown", "prefix": "danrun",
        "body": ["python3 skills/dan/scripts/dan.py run ${1:engine} ${2:args}"],
        "description": "Jalankan engine DAN"},
        "dan chart": {"scope": "python", "prefix": "danchart",
                      "body": ["import svg_charts as sc",
                               "svg = sc.${1|bar,hbar,line,donut,gantt,progress|}(${2:data}, title='${3:judul}')"],
                      "description": "Buat chart SVG DAN"},
        "dan guard": {"scope": "shell", "prefix": "danguard",
                      "body": ["python3 skills/dan/scripts/pmo_guard.py ${1:projects.json}"],
                      "description": "Jalankan PMO guard"}}
    ws = {"folders": [{"path": "."}, {"path": "skills"}, {"path": "adapters"},
                      {"path": "deliverables"}, {"path": "data"}],
          "settings": {"python.analysis.extraPaths": ["skills/dan/scripts"]}}
    for base in (ROOT, OUT + "/vscode"):
        vd = base if base == ROOT else base
        vdir = os.path.join(vd, ".vscode") if base == ROOT else base + "/dot_vscode"
        # distribusi: adapters/vscode/dot_vscode agar tidak menimpa .vscode pengguna
        write(os.path.join(vdir, "settings.json"), json.dumps(settings, indent=2))
        write(os.path.join(vdir, "tasks.json"), json.dumps(tasks, indent=2))
        write(os.path.join(vdir, "launch.json"), json.dumps(launch, indent=2))
        write(os.path.join(vdir, "mcp.json"), json.dumps(mcp_cfg, indent=2))
        write(os.path.join(vdir, "dan.code-snippets"), json.dumps(snippets, indent=2))
        if base == ROOT:
            write(os.path.join(ROOT, "dan.code-workspace"), json.dumps(ws, indent=2))
    made["vscode"] = ["dot_vscode/settings.json", "dot_vscode/tasks.json",
                      "dot_vscode/launch.json", "dot_vscode/mcp.json",
                      "dot_vscode/dan.code-snippets"]
    # juga tulis .vscode aktif di root (idempoten, aman ditimpa)
    made["vscode_root"] = [".vscode/*", "dan.code-workspace"]

    write(f"{OUT}/SYSTEM_PROMPT.txt", pers + "\n\n" + route)
    made["root"] = ["SYSTEM_PROMPT.txt"]
    return made


def validate() -> Tuple[int, List[str]]:
    problems = []
    n = 0
    for dp, dn, fn in os.walk(OUT):
        for f in fn:
            p = os.path.join(dp, f)
            body = open(p, encoding="utf-8").read()
            n += 1
            if not body.strip():
                problems.append(f"{p}: kosong")
            if f.endswith(".mdc"):
                if not body.startswith("---\n") or "description:" not in body.split("---")[1]:
                    problems.append(f"{p}: frontmatter mdc tidak valid")
            if f == "custom_gpt_instructions.txt" and len(body) > GPT_LIMIT:
                problems.append(f"{p}: >{GPT_LIMIT} karakter")
    # skills frontmatter masih valid (sumber adapter)
    for m in subskill_meta():
        if not m["desc"]:
            problems.append(f"sub-skill {m['dir']}: description frontmatter kosong")
    return n, problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · plug-and-play adapters")
    ap.add_argument("cmd", nargs="?", default="build", choices=["build", "validate"])
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    if a.cmd == "validate":
        n, probs = validate()
        print(f"[DAN] adapter: {n} berkas diperiksa · {len(probs)} masalah")
        for p in probs:
            print("   -", p)
        return 1 if probs else 0
    meta = subskill_meta()
    made = build_all(meta, persona())
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    total = 0
    for k, files in made.items():
        if only and k not in only:
            continue
        total += len(files)
        print(f"[DAN] adapter {k:8} : {len(files)} berkas")
    print(f"[DAN] total {total} berkas adapter -> {OUT}")
    n, probs = validate()
    print(f"[DAN] validasi: {n} berkas · {len(probs)} masalah")
    return 1 if probs else 0


if __name__ == "__main__":
    raise SystemExit(main())
