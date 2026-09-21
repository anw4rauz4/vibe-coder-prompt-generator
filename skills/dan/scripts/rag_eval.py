#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rag_eval.py — Sub-skill 13 · Evaluasi retrieval RAG (recall@k & MRR) terukur.

Menjalankan gold-set pertanyaan (templates/rag_eval_set.json) terhadap indeks RAG
dan melaporkan:
  recall@1, recall@5, MRR, serta daftar MISSES untuk diperbaiki
  (tambah sinonim ke dokumen, perbaiki heading, atau naik ke embedding/re-ranker).

Gold-set berisi pertanyaan mudah (overlap lexical) DAN sengaja beberapa pertanyaan
"sinonim/parafrase" untuk menunjukkan batas retrieval lexical secara JUJUR.

PAKAI
  python3 rag_eval.py --top 5 --out deliverables/rag_eval.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import rag as ragmod  # noqa: E402

DEFAULT_SET = os.path.join(ROOT, "skills", "dan", "templates", "rag_eval_set.json")


def evaluate(qset: List[Dict[str, Any]], top: int,
             roots: List[str]) -> Dict[str, Any]:
    idx = ragmod.build_index(roots)
    rows, hits1, hitsK, rr = [], 0, 0, 0.0
    for q in qset:
        res = ragmod.query(idx, q["q"], top)
        ranks = [i + 1 for i, r in enumerate(res)
                 if q["expect_file_contains"] in r["file"]]
        hit1 = bool(ranks) and ranks[0] == 1
        hitK = bool(ranks)
        hits1 += 1 if hit1 else 0
        hitsK += 1 if hitK else 0
        if ranks:
            rr += 1.0 / ranks[0]
        rows.append({"id": q.get("id", "?"), "q": q["q"],
                     "kind": q.get("kind", "lexical"),
                     "rank": ranks[0] if ranks else None,
                     "got": [r["file"].split("/")[-1] for r in res[:2]]})
    n = max(1, len(qset))
    return {"n": len(qset), "chunks": idx["n"], "top": top,
            "recall@1": round(hits1 / n * 100, 1), "recall@%d" % top: round(hitsK / n * 100, 1),
            "mrr": round(rr / n, 3), "rows": rows}


def to_markdown(R: Dict[str, Any]) -> str:
    L = ["# Evaluasi Retrieval RAG", "",
         f"**{R['n']} pertanyaan · {R['chunks']} chunk · top-{R['top']}**  ",
         f"recall@1 **{R['recall@1']}%** · recall@{R['top']} **{R['recall@%d' % R['top']]}%** · "
         f"MRR **{R['mrr']}**", "",
         "| id | jenis | pertanyaan | rank | dokumen terambil |", "|---|---|---|---|---|"]
    for r in R["rows"]:
        L.append(f"| {r['id']} | {r['kind']} | {r['q'][:60]} | {r['rank'] or 'miss'} | "
                 f"{', '.join(r['got'])} |")
    misses = [r for r in R["rows"] if not r["rank"]]
    L += ["", "## Misses & tindakan"]
    if not misses:
        L.append("- tidak ada miss pada gold-set ini.")
    for r in misses:
        L.append(f"- **{r['id']}** ({r['kind']}): “{r['q'][:70]}” → tambah kata kunci/"
                 f"sinonim ke dokumen target, perbaiki heading, atau tambah re-ranker "
                 f"embedding bila miss sinonim berulang.")
    lex = [r for r in R["rows"] if r["kind"] == "lexical"]
    syn = [r for r in R["rows"] if r["kind"] == "synonym"]
    if lex and syn:
        la = sum(1 for r in lex if r["rank"]) / len(lex) * 100
        sa = sum(1 for r in syn if r["rank"]) / len(syn) * 100
        L += ["", f"Lexical recall {la:.0f}% vs synonym recall {sa:.0f}% — selisih besar "
                  f"= sinyal butuh embedding/re-ranker; selisih kecil = lexical cukup."]
    L += ["", "---", "_DAN · rag_eval. Gold-set: templates/rag_eval_set.json._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · RAG retrieval eval")
    ap.add_argument("--set", default=DEFAULT_SET)
    ap.add_argument("--roots", nargs="+", default=[os.path.join(ROOT, "skills", "dan")])
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables", "rag_eval.md"))
    a = ap.parse_args(argv)
    qset = json.load(open(a.set, encoding="utf-8"))
    R = evaluate(qset, a.top, a.roots)
    md = to_markdown(R)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(md)
    json.dump(R, open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[DAN] rag eval: recall@1 {R['recall@1']}% · recall@{a.top} "
          f"{R['recall@%d' % a.top]}% · MRR {R['mrr']} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
