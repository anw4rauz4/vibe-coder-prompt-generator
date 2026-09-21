#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sec_audit.py — Audit keamanan ringan sebagai gate tambahan rilis.

Memindai repo/bundle untuk kelas masalah yang paling sering lolos tanpa disadari:
  S1 secret tertanam      : AWS AKIA…, GitHub ghp_/gho_, Slack xox…, private key block,
                            api_key/token/password = "literal", .env ikut tersimpan
  S2 pola kode berisiko   : eval(, exec(, pickle.load, yaml.load tanpa SafeLoader,
                            subprocess(..., shell=True), chmod 0o777
  S3 transport lemah      : http:// (non-localhost/127.) pada kode & konfigurasi
  S4 izin file longgar    : berkas world-writable (mode & 0o022)
  S5 blob mencurigakan    : berkas biner >5 MB di repo (kecuali deliverables sengaja)

Keluaran: laporan md+json; exit 1 bila ada temuan high (S1) — sehingga bisa dipakai
sebagai gate (`release.py --with-sec`). Bukan pengganti pentest; ini pagar pertama.

PAKAI
  python3 sec_audit.py                      # scan root workspace
  python3 sec_audit.py --path adapters --out deliverables/sec_audit.md
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))

SECRET_RX = [
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Secret literal", re.compile(
        r"(?i)(api[_-]?key|secret|token|passwd|password)\s*[:=]\s*[\"'][A-Za-z0-9/_\-]{8,}[\"']")),
    ("Telegram bot token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{20,}\b")),
]
RISKY_RX = [
    ("eval()", re.compile(r"(?<![.\w])eval\s*\(")),
    ("exec()", re.compile(r"(?<![.\w])exec\s*\(")),
    ("pickle.load", re.compile(r"pickle\.loads?\s*\(")),
    ("yaml.load tanpa SafeLoader", re.compile(r"yaml\.load\s*\((?![^)]*Loader)")),
    ("subprocess shell=True", re.compile(r"shell\s*=\s*True")),
    ("chmod 0o777", re.compile(r"0o777|chmod\s+777")),
]
HTTP_RX = re.compile(r"http://(?!localhost|127\.|0\.0\.0|\[::|www\.w3\.org)")
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "deliverables", "dist", "build"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".mp3", ".zip", ".pyz", ".pdf", ".svg", ".gif"}


def scan(path: str) -> List[Dict[str, Any]]:
    finds: List[Dict[str, Any]] = []

    def add(sev: str, kind: str, where: str, detail: str):
        finds.append({"severity": sev, "kind": kind, "where": where, "detail": detail})

    for dp, dn, fn in os.walk(path):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            fp = os.path.join(dp, f)
            rel = os.path.relpath(fp, path)
            # S1 file terlarang
            if f == ".env" or f.endswith(".env") and not f.endswith(".env.example"):
                add("high", "S1 .env tersimpan", rel, "secret harus di environment, bukan file")
            ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_EXT:
                if os.path.getsize(fp) > 5 * 1024 * 1024 and "deliverables" not in rel:
                    add("low", "S5 blob besar", rel, f"{os.path.getsize(fp) / 1e6:.1f} MB")
                continue
            try:
                txt = open(fp, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for kind, rx in SECRET_RX:
                for m in rx.finditer(txt):
                    add("high", f"S1 {kind}", rel, m.group(0)[:24] + "…")
            self_lex = rel.replace(os.sep, "/").endswith("sec_audit.py")
            for kind, rx in ([] if self_lex else RISKY_RX):
                for m in rx.finditer(txt):
                    add("med", f"S2 {kind}", rel, m.group(0)[:40])
            for m in HTTP_RX.finditer(txt):
                add("low", "S3 http://", rel, txt[m.start():m.start() + 40])
            try:
                mode = os.stat(fp).st_mode
                if mode & stat.S_IWOTH:
                    add("med", "S4 world-writable", rel, oct(mode))
            except OSError:
                pass
    order = {"high": 0, "med": 1, "low": 2}
    return sorted(finds, key=lambda x: order[x["severity"]])


def to_markdown(finds: List[Dict[str, Any]], path: str) -> str:
    nh = sum(1 for f in finds if f["severity"] == "high")
    L = [f"# Audit Keamanan Ringan — `{os.path.basename(path) or path}`", "",
         f"**{len(finds)} temuan · {nh} high** · "
         + ("⛔ **GATE GAGAL** (perbaiki S1 dulu)" if nh else "✅ gate lulus"), "",
         "| Sev | Jenis | Berkas | Detail |", "|---|---|---|---|"]
    for f in finds[:80]:
        L.append(f"| {f['severity']} | {f['kind']} | {f['where']} | {f['detail']} |")
    if not finds:
        L.append("| — | — | — | tidak ada temuan |")
    L += ["", "## Catatan",
          "- S1 (secret) wajib nol sebelum rilis; rotasi bila pernah tercecer.",
          "- S2 bukan larangan mutlak: `eval`/`shell=True` boleh hanya dengan alasan "
          "tertulis di kode.",
          "- Audit ini pagar pertama, bukan pengganti penetration test.", "",
          "---", "_DAN · sec_audit._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · light security audit")
    ap.add_argument("--path", default=ROOT)
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables", "sec_audit.md"))
    a = ap.parse_args(argv)
    finds = scan(a.path)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(to_markdown(finds, a.path))
    json.dump(finds, open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    nh = sum(1 for f in finds if f["severity"] == "high")
    print(f"[DAN] sec audit: {len(finds)} temuan ({nh} high) -> {a.out}")
    for f in finds[:6]:
        print(f"   [{f['severity']}] {f['kind']} @ {f['where']}")
    return 1 if nh else 0


if __name__ == "__main__":
    raise SystemExit(main())
