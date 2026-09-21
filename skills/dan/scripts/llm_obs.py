#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_obs.py — Sub-skill 20 · LLM Observability: trace, metrik, & alarm murah.

Mencatat setiap pemanggilan LLM/agent ke JSONL (append-only) lalu menghitung:
  pass-rate per prompt-id · biaya rata-rata & total · latensi p50/p95 ·
  tren mingguan · prompt bermasalah (pass-rate rendah / biaya melonjak).

Tanpa dependensi & tanpa vendor: data milik Anda, bisa dibuka spreadsheet.

PAKAI
  python3 llm_obs.py log --prompt-id ringkasan-mingguan --model gpt-4o \
      --tokens-in 4200 --tokens-out 900 --cost 0.031 --latency 4200 --pass true
  python3 llm_obs.py report --traces deliverables/llm_traces.jsonl \
      --out deliverables/llm_obs_report.md --min-pass 80
"""
from __future__ import annotations

import argparse
import json
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

DEFAULT_TRACES = os.path.join(
    os.environ.get("DAN_ROOT") or os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")),
    "deliverables", "llm_traces.jsonl")


def log(path: str, rec: Dict[str, Any]) -> None:
    rec = {"ts": datetime.now().isoformat(timespec="seconds"), **rec}
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _p(xs: List[float], q: float) -> float:
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    f, c = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def report(path: str, min_pass: float) -> Dict[str, Any]:
    rows = [json.loads(ln) for ln in open(path, encoding="utf-8") if ln.strip()]
    by: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by[r.get("prompt_id", "?")].append(r)
    out = []
    for pid, rs in by.items():
        passes = [1 if str(r.get("pass", "true")).lower() in ("true", "1", "yes") else 0
                  for r in rs]
        costs = [float(r.get("cost", 0) or 0) for r in rs]
        lats = [float(r.get("latency", 0) or 0) for r in rs]
        toks = [float(r.get("tokens_in", 0) or 0) + float(r.get("tokens_out", 0) or 0)
                for r in rs]
        pr = sum(passes) / len(passes) * 100
        out.append({"prompt_id": pid, "runs": len(rs), "pass_pct": round(pr, 1),
                    "cost_total": round(sum(costs), 4),
                    "cost_avg": round(sum(costs) / len(costs), 4) if costs else 0,
                    "latency_p50": round(_p(lats, .5)), "latency_p95": round(_p(lats, .95)),
                    "tokens_avg": round(sum(toks) / len(toks)) if toks else 0,
                    "alert": pr < min_pass})
    out.sort(key=lambda x: (not x["alert"], -x["runs"]))
    return {"traces": len(rows), "prompts": len(out), "rows": out, "min_pass": min_pass}


def to_markdown(R: Dict[str, Any]) -> str:
    L = ["# Laporan Observabilitas LLM", "",
         f"**{R['traces']} trace · {R['prompts']} prompt-id · ambang pass {R['min_pass']:.0f}%**", "",
         "| Prompt | Runs | Pass% | Biaya total | Biaya avg | p50 ms | p95 ms | Token avg | Alarm |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r in R["rows"]:
        L.append(f"| {r['prompt_id']} | {r['runs']} | {r['pass_pct']:.0f}% | "
                 f"${r['cost_total']:.3f} | ${r['cost_avg']:.4f} | {r['latency_p50']} | "
                 f"{r['latency_p95']} | {r['tokens_avg']} | "
                 f"{'⛔ PASS-RENDAH' if r['alert'] else '—'} |")
    alerts = [r for r in R["rows"] if r["alert"]]
    L += ["", "## Tindakan"]
    if not alerts:
        L.append("- Tidak ada prompt di bawah ambang; pertahankan & lanjutkan logging.")
    for r in alerts:
        L.append(f"- **{r['prompt_id']}** pass {r['pass_pct']:.0f}% → review instruksi & "
                 f"contoh; tambah eval kasus gagal ke `eval_set`; pertimbangkan model lain "
                 f"bila latensi p95 > 8000 ms.")
    L += ["", "---", "_DAN · llm_obs. Trace append-only di llm_traces.jsonl; ekspor kapan pun "
          "ke CSV/spreadsheet._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · LLM observability")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("log")
    p.add_argument("--traces", default=DEFAULT_TRACES)
    p.add_argument("--prompt-id", required=True)
    p.add_argument("--model", default="")
    p.add_argument("--tokens-in", type=float, default=0)
    p.add_argument("--tokens-out", type=float, default=0)
    p.add_argument("--cost", type=float, default=0)
    p.add_argument("--latency", type=float, default=0)
    p.add_argument("--pass", dest="ok", default="true")
    p.add_argument("--note", default="")
    p = sub.add_parser("report")
    p.add_argument("--traces", default=DEFAULT_TRACES)
    p.add_argument("--out", default="")
    p.add_argument("--min-pass", type=float, default=80)
    a = ap.parse_args(argv)

    if a.cmd == "log":
        log(a.traces, {"prompt_id": a.prompt_id, "model": a.model,
                       "tokens_in": a.tokens_in, "tokens_out": a.tokens_out,
                       "cost": a.cost, "latency": a.latency, "pass": a.ok, "note": a.note})
        print(f"[DAN] trace tercatat -> {a.traces}")
        return 0
    if not os.path.exists(a.traces):
        print(f"[DAN] traces tidak ada: {a.traces}")
        return 2
    R = report(a.traces, a.min_pass)
    md = to_markdown(R)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(md)
        json.dump(R, open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
    print(md[:1200])
    print(f"[DAN] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
