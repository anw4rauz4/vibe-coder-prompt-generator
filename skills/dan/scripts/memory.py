#!/usr/bin/env python3
"""memory.py — session_log DAN: memori persisten lintas-sesi (JSONL, stdlib).

Menyimpan keputusan/preferensi/fakta/tugas supaya sesi AI baru tidak mulai dari nol.
Store append-only; baris korup dilewati (tahan rusak). Jalankan `dan.py memory ...`.

Contoh:
  python3 memory.py add --text "Klien suka laporan ringkas" --tag preferensi
  python3 memory.py add --text "Target Sep-Des dari klien" --tag tugas
  python3 memory.py search --q kalbe --k 5
  python3 memory.py list --tag keputusan --n 20
  python3 memory.py context --k 12            # markdown siap tempel ke sesi baru
  python3 memory.py stats

Store: --store FILE atau env DAN_MEMORY (default: <repo>/data/session_log.jsonl).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))  # repo root (di atas skills/dan)
TAGS = ("keputusan", "preferensi", "fakta", "tugas", "lainnya")


def default_store() -> str:
    return os.environ.get("DAN_MEMORY") or os.path.join(ROOT, "data", "session_log.jsonl")


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def load(path: str) -> List[Dict[str, Any]]:
    """Baca store JSONL; lewati baris korup/rusak."""
    out: List[Dict[str, Any]] = []
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict) and rec.get("text"):
                out.append(rec)
    return out


def _append(path: str, rec: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def add(path: str, text: str, tag: str = "fakta", src: str = "cli") -> Dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("teks kosong")
    tag = tag if tag in TAGS else "lainnya"
    ts = _now()
    rid = hashlib.sha1((ts + text).encode("utf-8")).hexdigest()[:8]
    rec = {"id": rid, "ts": ts, "tag": tag, "text": text, "src": src}
    _append(path, rec)
    return rec


def _score(q: str, rec: Dict[str, Any]) -> int:
    t = (rec.get("text") or "").lower()
    tg = (rec.get("tag") or "").lower()
    q = q.lower().strip()
    if not q:
        return 0
    s = 3 if q in t else 0
    for w in q.replace(",", " ").split():
        if len(w) < 2:
            continue
        if w in t:
            s += 2
        if w in tg:
            s += 1
    return s


def search(path: str, q: str, k: int = 5) -> List[Dict[str, Any]]:
    recs = load(path)
    scored = [(_score(q, r), r) for r in recs]
    scored = [(s, r) for s, r in scored if s > 0]
    scored.sort(key=lambda x: (-x[0], x[1].get("ts", "")))
    return [r for _, r in scored[: max(1, k)]]


def context_md(path: str, k: int = 12, q: str = "") -> str:
    """Markdown ringkas untuk ditempel ke sesi AI baru (hemat token)."""
    if q:
        recs = search(path, q, k)
        recs = sorted(recs, key=lambda r: r.get("ts", ""))
    else:
        recs = load(path)[-max(1, k):]
    if not recs:
        return "## Memori DAN\n(kosong — isi dengan `dan.py memory add --text ...`)"
    last = recs[-1].get("ts", "")[:10]
    lines = [f"## Memori DAN ({len(recs)} entri · s/d {last})"]
    lines += [f"- [{r.get('tag', 'lainnya')}] {r['text']} ({r.get('ts', '')[:10]})" for r in recs]
    lines.append("\n_Sumber: memory.py · store: " + os.path.basename(path) + "_")
    return "\n".join(lines)


def stats(path: str) -> Dict[str, Any]:
    recs = load(path)
    tags: Dict[str, int] = {}
    for r in recs:
        tags[r.get("tag", "lainnya")] = tags.get(r.get("tag", "lainnya"), 0) + 1
    return {
        "store": path,
        "total": len(recs),
        "tags": tags,
        "first": recs[0]["ts"] if recs else "",
        "last": recs[-1]["ts"] if recs else "",
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="DAN · session_log memory (lintas-sesi)")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--store", default="", help="path JSONL (default: data/session_log.jsonl)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("add", parents=[common])
    p.add_argument("--text", required=True)
    p.add_argument("--tag", default="fakta", choices=TAGS)
    p.add_argument("--src", default="cli")
    p = sub.add_parser("log", parents=[common])
    p.add_argument("--text", action="append", required=True, help="boleh berulang")
    p.add_argument("--tag", default="fakta", choices=TAGS)
    p = sub.add_parser("search", parents=[common])
    p.add_argument("--q", required=True)
    p.add_argument("--k", type=int, default=5)
    p = sub.add_parser("list", parents=[common])
    p.add_argument("--tag", default="", choices=("",) + TAGS)
    p.add_argument("--n", type=int, default=20)
    p = sub.add_parser("context", parents=[common])
    p.add_argument("--k", type=int, default=12)
    p.add_argument("--q", default="")
    sub.add_parser("stats", parents=[common])
    a = ap.parse_args(argv)
    store = getattr(a, "store", "") or default_store()
    cmd = a.cmd or "list"

    if cmd == "add":
        r = add(store, a.text, a.tag, a.src)
        print(f"[memori] + {r['id']} [{r['tag']}] {r['text']}")
        return 0
    if cmd == "log":
        for t in a.text:
            r = add(store, t, a.tag, "batch")
            print(f"[memori] + {r['id']} [{r['tag']}] {r['text']}")
        return 0
    if cmd == "search":
        hits = search(store, a.q, a.k)
        if not hits:
            print(f"[memori] tidak ada hasil untuk '{a.q}'")
            return 0
        for r in hits:
            print(f"{r['ts'][:10]} [{r['tag']}] {r['text']}")
        return 0
    if cmd == "context":
        print(context_md(store, a.k, a.q))
        return 0
    if cmd == "stats":
        s = stats(store)
        print(f"store : {s['store']}")
        print(f"total : {s['total']} entri" + (f" ({s['first'][:10]} .. {s['last'][:10]})" if s["total"] else ""))
        for t in TAGS:
            if s["tags"].get(t):
                print(f"  {t:10} {s['tags'][t]}")
        return 0
    recs = load(store)
    if a.tag:
        recs = [r for r in recs if r.get("tag") == a.tag]
    recs = recs[-max(1, a.n):]
    if not recs:
        print("[memori] kosong — isi dengan `dan.py memory add --text \"...\"`")
        return 0
    for r in recs:
        print(f"{r['ts'][:10]} [{r['tag']}] {r['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
