#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arch_advisor.py — Agent Arsitektur Software (sub-skill DAN #08).

Tiga kemampuan:
  1. SCAFFOLD  — membuat kerangka proyek dari template berbagai bahasa coding
                 (python, node, typescript, go, php) × pola (api, cli, worker).
  2. REVIEW    — analisa heuristik kode/proyek: bahasa, LOC, kompleksitas,
                 rahasia tertanam, TODO, uji, error handling → daftar
                 KELEBIHAN & KEKURANGAN + skor + prioritas perbaikan.
  3. COMPARE   — matriks trade-off (kelebihan/kekurangan) antar pola arsitektur,
                 database, bahasa, atau hosting, plus rekomendasi berdasar konteks
                 (ukuran tim, skala, tenggat, budget).

PAKAI
  python3 arch_advisor.py scaffold --lang python --pattern api --name ordersvc --out dir/
  python3 arch_advisor.py review  path/ke/proyek
  python3 arch_advisor.py compare --a monolith --b microservices \
         --team 4 --scale medium --deadline ketat --budget rendah
  python3 arch_advisor.py kb --list            # lihat isi knowledge base
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ===================================================================== KNOWLEDGE BASE

PATTERNS: Dict[str, Dict[str, Any]] = {
    "monolith": {
        "label": "Monolith",
        "pros": ["deploy & debugging paling sederhana", "latensi rendah (panggilan in-process)",
                 "transaksi ACID mudah", "cocok untuk tim kecil & produk awal"],
        "cons": ["skala tim besar → konflik merge & rilis saling blokir",
                 "satu bug bisa menjatuhkan seluruh sistem", "sulit adopsi teknologi berbeda per modul",
                 "scaling hanya vertikal / replika penuh"],
        "when": "tim ≤ 10 orang, domain belum stabil, time-to-market prioritas",
    },
    "modular-monolith": {
        "label": "Modular Monolith",
        "pros": ["batas modul jelas tanpa biaya jaringan", "bisa dipecah jadi service nanti",
                 "testing lebih terarah", "tetap satu deploy"],
        "cons": ["butuh disiplin arsitektur (mudah bocor antar modul)",
                 "masih satu titik gagal", "perlu tooling untuk enforcing boundary"],
        "when": "tim 5–25 orang yang ingin struktur tanpa kompleksitas distributed",
    },
    "microservices": {
        "label": "Microservices",
        "pros": ["tim bisa rilis independen", "scale per service sesuai beban",
                 "bebas pilih teknologi per service", "isolasi kegagalan per service"],
        "cons": ["kompleksitas jaringan & observability melonjak", "transaksi lintas service sulit (saga)",
                 "butuh platform team (CI/CD, service mesh, logging terpusat)", "latensi antar service",
                 "duplikasi data & konsistensi eventual"],
        "when": "≥ 4 tim otonom, domain sudah terpetakan baik (DDD), ada platform team",
    },
    "serverless": {
        "label": "Serverless / FaaS",
        "pros": ["bayar per eksekusi, idle = Rp0", "scale otomatis tanpa ops",
                 "time-to-market sangat cepat"],
        "cons": ["cold start", "vendor lock-in", "sulit untuk proses panjang/stateful",
                 "biaya bisa meledak bila traffic tinggi & konstan", "debugging terdistribusi sulit"],
        "when": "beban sporadis, event-driven, tim kecil tanpa ops",
    },
    "event-driven": {
        "label": "Event-Driven",
        "pros": ["loose coupling antar produsen/konsumen", "mudah menambah konsumen baru",
                 "tahan lonjakan (buffer di queue)", "audit trail alami"],
        "cons": ["alur sulit ditelusuri", "urutan & duplikasi pesan harus ditangani",
                 "konsistensi eventual", "butuh broker & monitoring queue"],
        "when": "banyak integrasi, aliran data asinkron, notifikasi/audit penting",
    },
    "layered": {
        "label": "Layered (n-tier)",
        "pros": ["pemisahan presentasi/logika/data jelas", "mudah dipahami tim baru",
                 "testing per lapisan"],
        "cons": ["cenderung jadi 'anemic' & boilerplate", "perubahan menembus semua lapisan",
                 "mudah bocor antar lapisan tanpa disiplin"],
        "when": "aplikasi bisnis CRUD klasik, tim umum",
    },
    "hexagonal": {
        "label": "Hexagonal / Ports & Adapters",
        "pros": ["domain terlindungi dari framework/DB", "mudah ganti infra & testing (adapter palsu)",
                 "use-case eksplisit"],
        "cons": ["boilerplate & kurva belajar", "berlebihan untuk CRUD sederhana"],
        "when": "domain bisnis kompleks & berumur panjang, butuh banyak integrasi",
    },
    "cqrs": {
        "label": "CQRS (+ Event Sourcing opsional)",
        "pros": ["model baca & tulis terpisah & optimal masing-masing",
                 "scale baca independen", "event sourcing = audit lengkap"],
        "cons": ["dua model = dua kebenaran yang harus disinkronkan", "kompleksitas tinggi",
                 "query sisi baca eventual consistent"],
        "when": "beban baca ≫ tulis, kebutuhan audit/replay kuat",
    },
    "mvc": {
        "label": "MVC",
        "pros": ["standar de-facto, banyak referensi", "pemisahan view/logika dasar"],
        "cons": ["controller mudah jadi gemuk", "batas model-view kabur di aplikasi besar"],
        "when": "web app tradisional, framework mainstream",
    },
    "mvvm": {
        "label": "MVVM",
        "pros": ["binding UI–state rapi", "viewmodel mudah diuji", "cocok untuk UI reaktif"],
        "cons": ["overhead untuk UI sederhana", "butuh pemahaman binding/lifecycle"],
        "when": "aplikasi desktop/mobile/UI berat (WPF, Flutter-ish, Vue)",
    },
}

DATA_STORES: Dict[str, Dict[str, Any]] = {
    "postgresql": {"label": "PostgreSQL",
                   "pros": ["ACID penuh", "fitur kaya (JSONB, full-text, window fn)", "ekosistem matang"],
                   "cons": ["scaling tulis horizontal sulit", "butuh tuning untuk beban ekstrem"],
                   "when": "data transaksional, relasi jelas, kebutuhan query kompleks"},
    "mysql": {"label": "MySQL/MariaDB",
              "pros": ["mudah & luas dipakai", "replikasi matang"],
              "cons": ["fitur analitik & JSON lebih terbatas dari PG"],
              "when": "web app umum, hosting murah"},
    "mongodb": {"label": "MongoDB",
                "pros": ["skema fleksibel", "scale horizontal mudah", "cocok dokumen嵌套"],
                "cons": ["transaksi lintas dokumen lebih lemah", "joins via agregasi rumit",
                         "risiko skema tak terkelola"],
                "when": "data semi-terstruktur, iterasi skema cepat"},
    "redis": {"label": "Redis",
              "pros": ["sangat cepat", "struktur data kaya (list, stream, sorted set)"],
              "cons": ["memori = biaya", "bukan sumber kebenaran utama"],
              "when": "cache, session, rate-limit, queue ringan"},
    "elasticsearch": {"label": "Elasticsearch/OpenSearch",
                      "pros": ["pencarian & agregasi cepat", "fuzzy/facet kuat"],
                      "cons": ["berat di memori", "sinkronisasi dari DB utama perlu pipeline"],
                      "when": "search & log analytics"},
    "sqlite": {"label": "SQLite",
               "pros": ["zero-config, satu file", "cukup cepat untuk beban besar baca"],
               "cons": ["konkurensi tulis terbatas", "bukan untuk multi-node"],
               "when": "aplikasi lokal, edge, prototipe, embedded"},
    "object-storage": {"label": "Object Storage (S3)",
                       "pros": ["murah, tak terbatas", "tahan lama"],
                       "cons": ["bukan untuk query", "latensi lebih tinggi"],
                       "when": "file, gambar, backup, arsip"},
}

LANGUAGES: Dict[str, Dict[str, Any]] = {
    "python": {"label": "Python",
               "pros": ["produktivitas & readability tinggi", "ekosistem data/AI terbaik",
                        "rekrutmen mudah"],
               "cons": ["kecepatan eksekusi lebih rendah", "GIL untuk paralelisme CPU",
                        "runtime type error bila tanpa type hints"],
               "when": "data/AI/ML, scripting, backend umum, prototipe cepat"},
    "node": {"label": "JavaScript / Node.js",
             "pros": ["satu bahasa front–back", "I/O asinkron efisien", "npm sangat kaya"],
             "cons": ["callback/async complexity", "type safety lemah tanpa TS",
                      "dependency churn cepat"],
             "when": "real-time, API I/O-bound, tim fullstack JS"},
    "typescript": {"label": "TypeScript",
                   "pros": ["type safety & refactoring aman", "DX unggul (autocomplete, error dini)",
                            "dokumentasi lewat tipe"],
                   "cons": ["build step & konfigurasi", "kurva belajar tipe lanjutan"],
                   "when": "codebase JS yang tumbuh, tim > 3 orang"},
    "go": {"label": "Go",
           "pros": ["binary tunggal & deploy mudah", "konkurensi goroutine murah",
                    "performa tinggi, startup cepat"],
           "cons": ["generics terbatas", "ekosistem web lebih kecil", "boilerplate error handling"],
           "when": "service backend, CLI, infrastruktur, konkurensi tinggi"},
    "php": {"label": "PHP",
            "pros": ["hosting murah & luas", "matang untuk web (Laravel)", "deploy sederhana"],
            "cons": ["stigma & inkonsistensi historis", "konkurensi terbatas"],
            "when": "web app budget terbatas, CMS, tim PHP existing"},
    "java": {"label": "Java/Kotlin",
             "pros": ["ekosistem enterprise matang", "type safety & tooling kuat",
                      "performa JVM setelah warm-up"],
             "cons": ["verbose", "startup & memori lebih berat", "build lambat"],
             "when": "enterprise, perbankan, sistem besar berumur panjang"},
    "rust": {"label": "Rust",
             "pros": ["memory safety tanpa GC", "performa puncak", "compile-time correctness"],
             "cons": ["kurva belajar terjal", "compile lambat", "pool talent kecil"],
             "when": "systems, performa kritis, keamanan memori wajib"},
}

HOSTING: Dict[str, Dict[str, Any]] = {
    "vm": {"label": "VM / self-managed",
           "pros": ["kontrol penuh", "biaya predictable"],
           "cons": ["ops burden tinggi", "scaling manual"], "when": "kebutuhan khusus, compliance ketat"},
    "container": {"label": "Container + orchestrator (K8s)",
                  "pros": ["portabel", "scaling & rollout terkelola", "resource efisien"],
                  "cons": ["kompleksitas platform", "butuh keahlian ops"],
                  "when": "banyak service, tim platform ada"},
    "paas": {"label": "PaaS (Render/Fly/Heroku/App Service)",
             "pros": ["ops minimal", "deploy cepat", "preview env mudah"],
             "cons": ["kurang kontrol", "biaya per dyno", "lock-in ringan"],
             "when": "tim kecil fokus produk"},
    "serverless": {"label": "Serverless",
                   "pros": ["bayar per pakai", "scale otomatis"],
                   "cons": ["cold start", "lock-in", "proses panjang sulit"],
                   "when": "beban sporadis/event-driven"},
    "static": {"label": "Static + CDN + edge fn",
               "pros": ["performa global", "biaya sangat murah", "keamanan permukaan kecil"],
               "cons": ["butuh backend terpisah untuk logika", "build-time rendering"],
               "when": "konten/marketing site, docs, dashboard ringan"},
}

COMPARE_GROUPS = {"pattern": PATTERNS, "db": DATA_STORES, "lang": LANGUAGES, "hosting": HOSTING}

CRITERIA = ["time-to-market", "biaya operasional", "kemudahan scaling", "kemudahan hiring",
            "ketahanan/keandalan", "kompleksitas operasional"]


def _score(option: Dict[str, Any], ctx: Dict[str, str]) -> Dict[str, int]:
    """Skor 1-5 per kriteria berdasar konteks sederhana (heuristik, bukan hukum)."""
    npros, ncons = len(option["pros"]), len(option["cons"])
    team = int(ctx.get("team", 5))
    scale = ctx.get("scale", "medium")
    deadline = ctx.get("deadline", "normal")
    budget = ctx.get("budget", "sedang")
    simple = ncons <= 2
    s = {}
    s["time-to-market"] = 5 if (simple and deadline == "ketat") else (4 if simple else 3)
    s["biaya operasional"] = 5 if budget == "rendah" and simple else (4 if simple else 2)
    s["kemudahan scaling"] = 5 if scale == "besar" and not simple else (4 if not simple else 3)
    s["kemudahan hiring"] = 5 if npros >= 3 else 3
    s["ketahanan/keandalan"] = 4 if not simple else 3
    s["kompleksitas operasional"] = 5 if simple else (3 if team >= 8 else 2)
    return s


def compare(group: str, a: str, b: str, ctx: Dict[str, str]) -> Dict[str, Any]:
    g = COMPARE_GROUPS.get(group, PATTERNS)
    oa, ob = g.get(a), g.get(b)
    if not oa or not ob:
        return {"error": f"pilihan tidak dikenal di grup '{group}': {a}/{b}. "
                         f"Opsi: {', '.join(g)}"}
    sa, sb = _score(oa, ctx), _score(ob, ctx)
    ta, tb = sum(sa.values()), sum(sb.values())
    winner = a if ta >= tb else b
    return {
        "group": group, "context": ctx,
        "a": {"key": a, **oa, "scores": sa, "total": ta},
        "b": {"key": b, **ob, "scores": sb, "total": tb},
        "winner": winner,
        "note": "Skor 1–5 per kriteria adalah heuristik konteks, bukan pengukuran. "
                "Gunakan sebagai bahan diskusi, bukan keputusan otomatis.",
    }


# ===================================================================== SCAFFOLD

LANG_FILES: Dict[str, Dict[str, str]] = {
    "python": {
        "requirements.txt": "fastapi==0.11*\nuvicorn[standard]\npydantic>=2\npytest\nhttpx\n",
        "Makefile": "run:\n\tuvicorn {pkg}.main:app --reload\ntest:\n\tpytest -q\nlint:\n\truff check .\n",
        ".gitignore": "__pycache__/\n.venv/\n.env\n.pytest_cache/\n",
        "tests/test_smoke.py": "def test_ok():\n    assert True\n",
    },
    "node": {
        "package.json": ('{{"name": "{name}", "version": "0.1.0", "type": "module",\n'
                         ' "scripts": {{"start": "node src/main.js", "test": "node --test"}}}}\n'),
        ".gitignore": "node_modules/\n.env\n",
        "test/smoke.test.js": "import test from 'node:test';\nimport assert from 'node:assert';\n"
                               "test('ok', () => assert.ok(true));\n",
    },
    "typescript": {
        "package.json": ('{{"name": "{name}", "version": "0.1.0", "type": "module",\n'
                         ' "scripts": {{"build": "tsc -p .", "start": "node dist/main.js",\n'
                         '  "test": "node --test dist"}},"devDependencies": {{"typescript": "^5"}}}}\n'),
        "tsconfig.json": ('{{"compilerOptions": {{"target": "ES2022", "module": "NodeNext",\n'
                          ' "strict": true, "outDir": "dist", "esModuleInterop": true}},\n'
                          ' "include": ["src"]}}\n'),
        ".gitignore": "node_modules/\ndist/\n.env\n",
    },
    "go": {
        "go.mod": "module {name}\n\ngo 1.22\n",
        ".gitignore": "bin/\n.env\n",
        "main_test.go": "package main\n\nimport \"testing\"\n\nfunc TestOk(t *testing.T) {}\n",
    },
    "php": {
        "composer.json": ('{{"name": "dan/{name}", "require": {{"php": ">=8.2"}},\n'
                          ' "autoload": {{"psr-4": {{"App\\\\": "src/"}}}}}}\n'),
        ".gitignore": "vendor/\n.env\n",
        "public/index.php": "<?php\nrequire __DIR__.'/../src/bootstrap.php';\n",
    },
}

ENTRY: Dict[str, Dict[str, str]] = {
    "python": {
        "api": ("{pkg}/main.py",
                'from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel\n\n'
                'app = FastAPI(title="{name}", version="0.1.0")\n\n\n'
                'class Item(BaseModel):\n    id: int\n    name: str\n\n\n'
                '_DB: dict[int, Item] = {{}}\n\n\n'
                '@app.get("/health")\ndef health() -> dict:\n    return {{"status": "ok"}}\n\n\n'
                '@app.get("/items/{{item_id}}")\ndef get_item(item_id: int) -> Item:\n'
                '    if item_id not in _DB:\n        raise HTTPException(404, "item tidak ada")\n'
                '    return _DB[item_id]\n\n\n'
                '@app.post("/items", status_code=201)\ndef create_item(item: Item) -> Item:\n'
                '    _DB[item.id] = item\n    return item\n'),
        "cli": ("{pkg}/main.py",
                'import argparse\n\n\ndef main() -> int:\n'
                '    ap = argparse.ArgumentParser(prog="{name}")\n'
                '    ap.add_argument("input")\n    a = ap.parse_args()\n'
                '    print(f"memproses {{a.input}}")\n    return 0\n\n\n'
                'if __name__ == "__main__":\n    raise SystemExit(main())\n'),
        "worker": ("{pkg}/main.py",
                   'import time\n\n\ndef handle(job: dict) -> None:\n'
                   '    print("proses", job)\n\n\n'
                   'def main() -> None:\n    while True:\n'
                   '        job = None  # TODO: ambil dari queue (redis stream / sqs)\n'
                   '        if job:\n            handle(job)\n        time.sleep(1)\n\n\n'
                   'if __name__ == "__main__":\n    main()\n'),
    },
    "node": {
        "api": ("src/main.js",
                "import http from 'node:http';\nimport { router } from './router.js';\n\n"
                "const server = http.createServer(router);\n"
                "server.listen(process.env.PORT || 3000, () =>\n"
                "  console.log('{name} siap di port', server.address().port));\n"),
        "cli": ("src/main.js",
                "import { readFileSync } from 'node:fs';\n"
                "const [,, input] = process.argv;\n"
                "if (!input) { console.error('pakai: {name} <file>'); process.exit(1); }\n"
                "console.log(readFileSync(input, 'utf8').split('\\n').length, 'baris');\n"),
        "worker": ("src/main.js",
                   "const tick = async () => {\n  // TODO: poll queue (redis stream / sqs)\n};\n"
                   "setInterval(tick, 1000);\nconsole.log('{name} worker berjalan');\n"),
    },
    "typescript": {
        "api": ("src/main.ts",
                "import http from 'node:http';\n\ninterface Item { id: number; name: string }\n"
                "const db = new Map<number, Item>();\n\n"
                "const server = http.createServer((req, res) => {\n"
                "  if (req.url === '/health') { res.end(JSON.stringify({ status: 'ok' })); return; }\n"
                "  res.statusCode = 404; res.end();\n});\n"
                "server.listen(Number(process.env.PORT ?? 3000));\n"),
        "cli": ("src/main.ts",
                "const input = process.argv[2];\nif (!input) throw new Error('pakai: {name} <file>');\n"
                "console.log(`memproses ${input}`);\n"),
        "worker": ("src/main.ts",
                   "setInterval(() => { /* TODO: poll queue */ }, 1000);\n"),
    },
    "go": {
        "api": ("main.go",
                'package main\n\nimport (\n\t"encoding/json"\n\t"log"\n\t"net/http"\n\t"os"\n)\n\n'
                'func main() {\n\tmux := http.NewServeMux()\n'
                '\tmux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {\n'
                '\t\tjson.NewEncoder(w).Encode(map[string]string{"status": "ok"})\n\t})\n'
                '\taddr := ":" + orDefault(os.Getenv("PORT"), "8080")\n'
                '\tlog.Fatal(http.ListenAndServe(addr, mux))\n}\n\n'
                'func orDefault(v, d string) string {\n\tif v == "" {\n\t\treturn d\n\t}\n\treturn v\n}\n'),
        "cli": ("main.go",
                'package main\n\nimport (\n\t"fmt"\n\t"os"\n)\n\n'
                'func main() {\n\tif len(os.Args) < 2 {\n\t\tfmt.Fprintln(os.Stderr, "pakai: {name} <input>")\n'
                '\t\tos.Exit(1)\n\t}\n\tfmt.Println("memproses", os.Args[1])\n}\n'),
        "worker": ("main.go",
                   'package main\n\nimport "time"\n\nfunc main() {\n\tfor range time.Tick(time.Second) {\n'
                   '\t\t// TODO: poll queue\n\t}\n}\n'),
    },
    "php": {
        "api": ("src/bootstrap.php",
                "<?php\ndeclare(strict_types=1);\n\n"
                "header('Content-Type: application/json');\n"
                "$path = $_SERVER['REQUEST_URI'] ?? '/';\n"
                "if ($path === '/health') { echo json_encode(['status' => 'ok']); exit; }\n"
                "http_response_code(404);\n"),
        "cli": ("src/bootstrap.php",
                "<?php\ndeclare(strict_types=1);\n"
                "$input = $argv[1] ?? null;\n"
                "if (!$input) { fwrite(STDERR, \"pakai: {name} <file>\\n\"); exit(1); }\n"
                "echo \"memproses $input\\n\";\n"),
        "worker": ("src/bootstrap.php",
                   "<?php\ndeclare(strict_types=1);\nwhile (true) { /* TODO: poll queue */ sleep(1); }\n"),
    },
}

README_TMPL = """# {name}

Kerangka proyek **{lang_label}** dengan pola **{pattern}** — dibuat oleh `arch_advisor.py`.

## Menjalankan
{run_hint}

## Struktur
{structure}

## Langkah berikutnya
- [ ] Isi logika bisnis di modul utama
- [ ] Tambahkan konfigurasi lewat environment variable (jangan hardcode)
- [ ] Lengkapi test (`{test_hint}`)
- [ ] Tambahkan CI (lint + test) sebelum merge pertama
"""

RUN_HINTS = {
    "python": "```bash\npython -m venv .venv && source .venv/bin/activate\npip install -r requirements.txt\nmake run   # atau: uvicorn {pkg}.main:app --reload\n```",
    "node": "```bash\nnpm install\nnpm start\n```",
    "typescript": "```bash\nnpm install\nnpm run build && npm start\n```",
    "go": "```bash\ngo run .\n```",
    "php": "```bash\nphp -S localhost:8000 -t public\n```",
}
TEST_HINTS = {"python": "pytest", "node": "npm test", "typescript": "npm test",
              "go": "go test ./...", "php": "phpunit (tambahkan)"}


def scaffold(lang: str, pattern: str, name: str, out: str) -> Dict[str, Any]:
    lang = lang.lower()
    pattern = pattern.lower()
    if lang not in LANG_FILES:
        return {"error": f"bahasa '{lang}' belum punya template. Pilihan: {', '.join(LANG_FILES)}"}
    if pattern not in ENTRY.get(lang, {}):
        return {"error": f"pola '{pattern}' tidak tersedia untuk {lang}. "
                         f"Pilihan: {', '.join(ENTRY.get(lang, {}))}"}
    pkg = re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_") or "app"

    def _fmt(body: str) -> str:
        # template memakai .replace (bukan .format), jadi brace literal ditulis ganda
        # di sumber dan di-collapse di sini menjadi brace tunggal yang valid.
        return (body.replace("{name}", name).replace("{pkg}", pkg)
                    .replace("{{", "{").replace("}}", "}"))

    files: Dict[str, str] = {}
    for rel, body in LANG_FILES[lang].items():
        files[rel] = _fmt(body)
    entry_rel, entry_body = ENTRY[lang][pattern]
    files[entry_rel.replace("{pkg}", pkg)] = _fmt(entry_body)
    files["README.md"] = README_TMPL.format(
        name=name, lang_label=LANGUAGES.get(lang, {}).get("label", lang), pattern=pattern,
        run_hint=RUN_HINTS[lang].replace("{pkg}", pkg),
        structure="\n".join(f"- `{k}`" for k in sorted(files)),
        test_hint=TEST_HINTS[lang])
    files[".env.example"] = "PORT=8080\nDATABASE_URL=\nAPI_KEY=\n"
    written = []
    for rel, body in files.items():
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p) or out, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(body)
        written.append(rel)
    return {"lang": lang, "pattern": pattern, "name": name, "out": out, "files": sorted(written)}


# ===================================================================== REVIEW

LANG_EXT = {".py": "python", ".js": "node", ".mjs": "node", ".ts": "typescript", ".tsx": "typescript",
            ".go": "go", ".php": "php", ".java": "java", ".rs": "rust", ".rb": "ruby"}
SECRET_RE = re.compile(r"(?i)(password|passwd|secret|api[_-]?key|token|private[_-]?key)\s*[:=]\s*"
                       r"[\"'][^\"']{6,}[\"']")
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
DEBUG_RE = re.compile(r"(?m)^\s*(print|console\.log|var_dump|dd|fmt\.Println)\(")
BRANCH_RE = re.compile(r"(?m)^\s*(if|elif|else if|for|while|case|switch|catch|except)\b")
FUNC_RE = re.compile(r"(?m)^\s*(def|func|function)\s+\w+")


def _iter_code(root: str):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in {".git", "node_modules", "__pycache__", ".venv",
                                            "vendor", "dist", "build"}]
        for f in fn:
            ext = os.path.splitext(f)[1].lower()
            if ext in LANG_EXT:
                yield os.path.join(dp, f), LANG_EXT[ext]


def review(path: str) -> Dict[str, Any]:
    if os.path.isfile(path):
        items = [(path, LANG_EXT.get(os.path.splitext(path)[1].lower(), "python"))]
    else:
        items = list(_iter_code(path))
    if not items:
        return {"error": f"tidak ada file kode yang dikenali di {path}"}
    langc = Counter(l for _, l in items)
    primary = langc.most_common(1)[0][0]
    tot_lines = tot_files = 0
    secrets, todos, debugs, cli_prints, branches, funcs = 0, 0, 0, 0, 0, 0
    big_files: List[Tuple[str, int]] = []
    has_tests = has_readme = has_env_example = has_ci = False
    for p, _ in items:
        rel = os.path.relpath(p, path if os.path.isdir(path) else os.path.dirname(p))
        txt = open(p, encoding="utf-8", errors="replace").read()
        n = txt.count("\n") + 1
        tot_lines += n
        tot_files += 1
        if n > 600:
            big_files.append((rel, n))
        secrets += len(SECRET_RE.findall(txt))
        todos += len(TODO_RE.findall(txt))
        is_cli = ("argparse" in txt) or ("__main__" in txt) or ("process.argv" in txt) \
            or ("$argv" in txt) or ("os.Args" in txt)
        np_ = len(DEBUG_RE.findall(txt))
        if is_cli:
            cli_prints += np_          # untuk CLI, print = antarmuka (sengaja)
        else:
            debugs += np_              # print di modul non-CLI = dugaan debug tertinggal
        branches += len(BRANCH_RE.findall(txt))
        funcs += len(FUNC_RE.findall(txt))
        low = rel.lower()
        if "test" in low:
            has_tests = True
    if os.path.isdir(path):
        names = {x.lower() for x in os.listdir(path)}
        has_readme = any(x.startswith("readme") for x in names)
        has_env_example = ".env.example" in names or ".env.sample" in names
        has_ci = bool(names & {".github", ".gitlab-ci.yml", "jenkinsfile", ".circleci"})
    cx = (branches / max(1, tot_lines)) * 100
    strengths, weaknesses, actions = [], [], []

    if has_tests:
        strengths.append("ada test — regresi bisa terdeteksi dini")
    else:
        weaknesses.append("tidak ada test sama sekali")
        actions.append("tambahkan smoke test + test untuk logika inti sebelum fitur baru")
    if has_readme:
        strengths.append("punya README (onboarding mudah)")
    else:
        weaknesses.append("tidak ada README")
        actions.append("tulis README: cara run, struktur, keputusan arsitektur (ADR singkat)")
    if has_env_example:
        strengths.append("konfigurasi lewat env, ada contoh .env")
    else:
        weaknesses.append("tidak ada .env.example — konfigurasi rentan hardcode")
        actions.append("pindahkan semua rahasia/konfigurasi ke environment variable")
    if has_ci:
        strengths.append("ada CI (lint/test otomatis)")
    else:
        actions.append("pasang CI minimal: lint + test pada tiap pull request")
    if secrets:
        weaknesses.append(f"{secrets} dugaan rahasia tertanam di kode (RISIKO TINGGI)")
        actions.append("pindahkan rahasia ke secret manager/env; rotasi kunci yang sudah bocor; "
                       "tambahkan pre-commit secret scan")
    else:
        strengths.append("tidak terdeteksi rahasia tertanam")
    if todos:
        weaknesses.append(f"{todos} penanda TODO/FIXME belum tertangani")
        actions.append("ubah TODO jadi tiket; TODO tanpa owner = utang tak terlihat")
    else:
        strengths.append("bersih dari penanda TODO/FIXME")
    if debugs > max(3, tot_lines / 300):
        weaknesses.append(f"{debugs} pernyataan debug (print/log) tertinggal")
        actions.append("ganti debug print dengan logger ber-level")
    if big_files:
        worst = max(big_files, key=lambda x: x[1])
        weaknesses.append(f"file terlalu besar: {worst[0]} ({worst[1]} baris) — kandidat 'god module'")
        actions.append(f"pecah {worst[0]} jadi modul ber-tanggung-jawab tunggal")
    else:
        strengths.append("ukuran file terjaga (tidak ada god module >600 baris)")
    if cx > 12:
        weaknesses.append(f"kompleksitas cabang tinggi ({cx:.1f} cabang/100 baris)")
        actions.append("kurangi nesting: early return, ekstrak fungsi, tabel strategi")
    elif cx < 3 and tot_lines > 200:
        strengths.append(f"kompleksitas cabang rendah ({cx:.1f}/100 baris) — mudah dibaca")
    if funcs:
        strengths.append(f"terstruktur dalam {funcs} fungsi/terpisah")
    score = 100
    score -= 20 if not has_tests else 0
    score -= 10 if not has_readme else 0
    score -= 10 if not has_env_example else 0
    score -= 10 if not has_ci else 0
    score -= 25 if secrets else 0
    score -= min(10, todos)
    score -= 8 if big_files else 0
    score -= 7 if cx > 12 else 0
    score = max(0, min(100, score))

    return {
        "path": path, "primary_language": primary,
        "languages": dict(langc), "files": tot_files, "lines": tot_lines,
        "functions": funcs, "branch_per_100_lines": round(cx, 1),
        "secrets": secrets, "todos": todos, "debug_prints": debugs, "cli_prints": cli_prints,
        "has_tests": has_tests, "has_readme": has_readme,
        "has_env_example": has_env_example, "has_ci": has_ci,
        "score": score,
        "kelebihan": strengths, "kekurangan": weaknesses, "prioritas_perbaikan": actions,
        "saran_bahasa": LANGUAGES.get(primary, {}),
    }


# ===================================================================== report & main

def to_markdown_compare(c: Dict[str, Any]) -> str:
    if "error" in c:
        return f"# Error\n\n{c['error']}"
    a, b = c["a"], c["b"]
    L = [f"# Trade-off: {a['label']} vs {b['label']}", "",
         f"_Grup: {c['group']} · Konteks: {c['context']}_", "",
         f"| Kriteria | {a['label']} | {b['label']} |", "|---|---|---|"]
    for k in CRITERIA:
        L.append(f"| {k} | {a['scores'][k]} | {b['scores'][k]} |")
    L.append(f"| **Total** | **{a['total']}** | **{b['total']}** |")
    L += ["", f"## {a['label']}", "**Kelebihan:**"]
    L += [f"- {x}" for x in a["pros"]]
    L += ["**Kekurangan:**"] + [f"- {x}" for x in a["cons"]]
    L += [f"_Cocok bila: {a['when']}_", "", f"## {b['label']}", "**Kelebihan:**"]
    L += [f"- {x}" for x in b["pros"]]
    L += ["**Kekurangan:**"] + [f"- {x}" for x in b["cons"]]
    L += [f"_Cocok bila: {b['when']}_", "",
          f"## Rekomendasi: **{c['winner']}**", "", c["note"]]
    return "\n".join(L)


def to_markdown_review(r: Dict[str, Any]) -> str:
    if "error" in r:
        return f"# Error\n\n{r['error']}"
    L = [f"# Review Arsitektur & Kode — `{r['path']}`", "",
         f"**Bahasa utama:** {r['primary_language']} · **{r['files']} file · {r['lines']:,} baris** · "
         f"**Skor: {r['score']}/100**", "",
         "| Indikator | Nilai |", "|---|---|",
         f"| Fungsi/terdefinisi | {r['functions']} |",
         f"| Cabang per 100 baris | {r['branch_per_100_lines']} |",
         f"| TODO/FIXME | {r['todos']} |",
         f"| Dugaan rahasia tertanam | {r['secrets']} |",
         f"| Debug print tertinggal | {r['debug_prints']} |",
         f"| Print antarmuka CLI (sengaja) | {r.get('cli_prints', 0)} |",
         f"| Test / README / .env.example / CI | {'✔' if r['has_tests'] else '✘'} / "
         f"{'✔' if r['has_readme'] else '✘'} / {'✔' if r['has_env_example'] else '✘'} / "
         f"{'✔' if r['has_ci'] else '✘'} |", "",
         "## Kelebihan"]
    L += [f"- {x}" for x in r["kelebihan"]] or ["- (belum ada yang menonjol)"]
    L += ["", "## Kekurangan"]
    L += [f"- {x}" for x in r["kekurangan"]] or ["- (tidak ditemukan masalah besar)"]
    L += ["", "## Prioritas perbaikan (urut dampak)"]
    L += [f"{i}. {x}" for i, x in enumerate(r["prioritas_perbaikan"], 1)] or ["1. pertahankan kondisi saat ini"]
    if r.get("saran_bahasa"):
        sb = r["saran_bahasa"]
        L += ["", f"## Catatan bahasa ({sb.get('label')})", "**Kekuatan:** " + "; ".join(sb.get("pros", [])),
              "**Kelemahan:** " + "; ".join(sb.get("cons", [])),
              f"_Paling cocok untuk: {sb.get('when', '')}_"]
    L += ["", "---", "_Heuristik statis; bukan pengganti code review manusia. "
          "Skor = 100 − penalti (test 20, README 10, env 10, CI 10, rahasia 25, TODO ≤10, "
          "god-file 8, kompleksitas 7)._"]
    return "\n".join(L)


def main(argv: Optional[Sequence[str]] = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · Software Architecture Advisor")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("scaffold")
    p.add_argument("--lang", required=True, choices=list(LANG_FILES))
    p.add_argument("--pattern", default="api", choices=["api", "cli", "worker"])
    p.add_argument("--name", default="myservice")
    p.add_argument("--out", default="")

    p = sub.add_parser("review")
    p.add_argument("path")
    p.add_argument("--out", default="")

    p = sub.add_parser("compare")
    p.add_argument("--group", default="pattern", choices=list(COMPARE_GROUPS))
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--team", type=int, default=5)
    p.add_argument("--scale", default="medium", choices=["kecil", "medium", "besar"])
    p.add_argument("--deadline", default="normal", choices=["ketat", "normal", "longgar"])
    p.add_argument("--budget", default="sedang", choices=["rendah", "sedang", "tinggi"])
    p.add_argument("--out", default="")

    p = sub.add_parser("kb")
    p.add_argument("--list", action="store_true")
    p.add_argument("--group", default="")

    a = ap.parse_args(argv)

    if a.cmd == "kb":
        if a.list or not a.group:
            for gname, g in COMPARE_GROUPS.items():
                print(f"[{gname}] " + ", ".join(g))
        else:
            g = COMPARE_GROUPS.get(a.group, {})
            for k, v in g.items():
                print(f"\n### {v['label']}  ({k})")
                print("  + " + "\n  + ".join(v["pros"]))
                print("  - " + "\n  - ".join(v["cons"]))
                print("  ~ " + v["when"])
        return 0

    if a.cmd == "scaffold":
        out = a.out or os.path.join(dl, f"scaffold_{a.lang}_{a.pattern}")
        res = scaffold(a.lang, a.pattern, a.name, out)
        if "error" in res:
            print("[DAN] ERROR:", res["error"])
            return 1
        print(f"[DAN] scaffold {res['lang']}/{res['pattern']} -> {out} "
              f"({len(res['files'])} file)")
        for f in res["files"]:
            print("   -", f)
        return 0

    if a.cmd == "review":
        r = review(a.path)
        out = a.out or os.path.join(dl, "arch_review.md")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            f.write(to_markdown_review(r))
        with open(os.path.splitext(out)[0] + ".json", "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
        if "error" in r:
            print("[DAN] ERROR:", r["error"])
            return 1
        print(f"[DAN] {r['primary_language']} · {r['files']} file · {r['lines']:,} baris · "
              f"skor {r['score']}/100")
        print(f"[DAN] kelebihan {len(r['kelebihan'])} · kekurangan {len(r['kekurangan'])} · "
              f"prioritas {len(r['prioritas_perbaikan'])}")
        print(f"[DAN] -> {out}")
        return 0

    ctx = {"team": a.team, "scale": a.scale, "deadline": a.deadline, "budget": a.budget}
    c = compare(a.group, a.a, a.b, ctx)
    out = a.out or os.path.join(dl, f"arch_compare_{a.a}_vs_{a.b}.md")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(to_markdown_compare(c))
    if "error" in c:
        print("[DAN] ERROR:", c["error"])
        return 1
    print(f"[DAN] {c['a']['label']} ({c['a']['total']}) vs {c['b']['label']} ({c['b']['total']}) "
          f"-> rekomendasi: {c['winner']}")
    print(f"[DAN] -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
