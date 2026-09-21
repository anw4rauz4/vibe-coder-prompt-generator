#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rag.py — Sub-skill 13 · Retrieval Augmented Generation (RAG) stdlib-only.

Mengindeks dokumen Markdown paket (atau folder mana pun) menjadi chunk ber-headings,
lalu menjawab pertanyaan dengan retrieval TF-IDF + cosine dan SITASI file+heading.
Tanpa dependensi: tokenizer sederhana + stopwords ID/EN + tf-idf manual.

PAKAI
  python3 rag.py index --roots skills/dan --out deliverables/rag_index.json
  python3 rag.py query "berapa ambang RAG waspada pada project monitor?" --top 4
  python3 rag.py query "..." --index deliverables/rag_index.json --top 4

Catatan kejujuran: ini retrieval lexical (BM25-ish/TF-IDF), bukan embedding semantik.
Cocok untuk dokumen teknis berisi istilah pasti; untuk sinonim luas, pakai embedding
bila tersedia (opsional) — struktur indeks & sitasi kami tetap sama.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from typing import Any, Dict, List, Tuple

STOP = set("""dan di ke yang dari untuk dengan pada adalah merupakan atau dan/ atau/
the a an of to in for on with and or is are be been as by at from it its this that
these those we you they he she not no yes akan telah sudah bisa dapat harus hanya
juga lebih paling sangat setiap semua ada karena sehingga maka jika bila saat ketika
""".split())
TOKEN = re.compile(r"[a-z0-9_]+")


def tokenize(s: str) -> List[str]:
    return [t for t in TOKEN.findall(s.lower()) if t not in STOP and len(t) > 2]


def chunk_md(path: str, max_chars: int = 900) -> List[Dict[str, Any]]:
    text = open(path, encoding="utf-8", errors="replace").read()
    parts = re.split(r"\n(?=#{1,3} )", text)
    chunks = []
    heading = os.path.basename(path)
    for p in parts:
        m = re.match(r"(?m)^(#{1,3} )+(.*)", p)
        if m:
            heading = m.group(2).strip()
        p = p.strip()
        if len(p) < 60:
            continue
        for i in range(0, len(p), max_chars):
            chunks.append({"file": path, "heading": heading, "text": p[i:i + max_chars]})
    return chunks


def build_index(roots: List[str]) -> Dict[str, Any]:
    chunks: List[Dict[str, Any]] = []
    for root in roots:
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in ("__pycache__", ".git", "node_modules")]
            for f in fn:
                if f.endswith(".md"):
                    chunks.extend(chunk_md(os.path.join(dp, f)))
    tf: List[Counter] = [Counter(tokenize(c["text"])) for c in chunks]
    df: Counter = Counter()
    for t in tf:
        for w in t:
            df[w] += 1
    N = max(1, len(chunks))
    vecs = []
    for t in tf:
        v = {w: (1 + math.log(c)) * math.log(N / (1 + df[w])) for w, c in t.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({w: x / norm for w, x in v.items()})
    return {"n": N, "chunks": chunks, "vecs": vecs}


def query(idx: Dict[str, Any], q: str, top: int = 4) -> List[Dict[str, Any]]:
    qv_raw = Counter(tokenize(q))
    if not qv_raw:
        return []
    N = idx["n"]
    df: Counter = Counter()
    for v in idx["vecs"]:
        for w in v:
            df[w] += 1
    qv = {w: (1 + math.log(c)) * math.log(N / (1 + df.get(w, 0))) for w, c in qv_raw.items()}
    qn = math.sqrt(sum(x * x for x in qv.values())) or 1.0
    qv = {w: x / qn for w, x in qv.items()}
    scored = []
    for i, v in enumerate(idx["vecs"]):
        s = sum(qv.get(w, 0.0) * x for w, x in v.items())
        if s > 0.02:
            scored.append((s, i))
    scored.sort(reverse=True)
    out = []
    for s, i in scored[:top]:
        c = idx["chunks"][i]
        out.append({"score": round(s, 3), "file": c["file"], "heading": c["heading"],
                    "text": c["text"][:420]})
    return out


def main(argv=None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    ap = argparse.ArgumentParser(description="DAN · stdlib RAG")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("index")
    p.add_argument("--roots", nargs="+", default=[os.path.join(root, "skills", "dan")])
    p.add_argument("--out", default=os.path.join(root, "deliverables", "rag_index.json"))
    p = sub.add_parser("query")
    p.add_argument("q")
    p.add_argument("--roots", nargs="+", default=[os.path.join(root, "skills", "dan")])
    p.add_argument("--index", default="")
    p.add_argument("--top", type=int, default=4)
    a = ap.parse_args(argv)

    if a.cmd == "index":
        idx = build_index(a.roots)
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False)
        print(f"[DAN] indeks {idx['n']} chunk -> {a.out}")
        return 0
    idx = json.load(open(a.index, encoding="utf-8")) if a.index and os.path.exists(a.index) \
        else build_index(a.roots)
    res = query(idx, a.q, a.top)
    if not res:
        print("[DAN] tidak ada chunk relevan; coba kata kunci lain atau perbesar --top.")
        return 0
    for r in res:
        print(f"\n[{r['score']}] {r['file']} :: {r['heading']}\n  {r['text']}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
