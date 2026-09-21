#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
budget_sim.py — Simulator budget what-if dengan interval ketidakpastian.

Membaca analysis.json (hasil dan_analytics.py), lalu mensimulasikan skenario
realokasi antar channel:
  baseline       : kondisi sekarang
  shift-N        : pindahkan N% budget dari channel ROAS terendah ke tertinggi
  cut-loser      : hapus budget channel dengan ROAS < 1 (bila ada)

Model sederhana & JUJUR:
  revenue_baru = Σ (spend_c × roas_c) dengan roas tujuan diberi faktor penurunan
  manfaat (damp, default 0.85) karena budget tambahan jarang selinier awal, dan
  roas sumber hilang penuh. Ketidakpastian: Monte-Carlo (default 2000 sampel,
  seed tetap) dengan roas ~ normal(mu=roas_teramati, sigma=cv×roas), cv default 0,2.
Keluaran: p10/p50/p90 revenue & ROAS blend per skenario + tabel + chart.

PAKAI
  python3 budget_sim.py --analysis analysis.json --shift 20 --cv 0.2 \
      --out deliverables/budget_sim.md
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics as st
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import svg_charts as sc  # noqa: E402


def _pct(xs: List[float], q: float) -> float:
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    f, c = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def scenarios(ch: List[Dict[str, Any]], shift: float) -> List[Dict[str, Any]]:
    out = [{"id": "baseline", "desc": "kondisi sekarang", "moves": []}]
    if len(ch) >= 2:
        srt = sorted(ch, key=lambda c: c["kpi"]["roas"])
        loser, winner = srt[0], srt[-1]
        amt = loser["kpi"]["spend"] * shift / 100
        out.append({"id": f"shift-{shift:.0f}",
                    "desc": f"geser {shift:.0f}% budget {loser['name']} → {winner['name']}",
                    "moves": [(loser["name"], -amt), (winner["name"], amt)],
                    "damp": True})
    losers = [c for c in ch if c["kpi"]["roas"] < 1 and c["kpi"]["spend"] > 0]
    if losers:
        mv = [(c["name"], -c["kpi"]["spend"]) for c in losers]
        out.append({"id": "cut-loser", "desc": "hentikan channel ROAS<1: " +
                    ", ".join(c["name"] for c in losers), "moves": mv, "damp": False})
    return out


def simulate(ch: List[Dict[str, Any], ], sc_: Dict[str, Any], cv: float, damp: float,
             n: int, seed: int) -> Dict[str, Any]:
    rnd = random.Random(seed)
    base_spend = {c["name"]: c["kpi"]["spend"] for c in ch}
    base_roas = {c["name"]: c["kpi"]["roas"] for c in ch}
    spend = dict(base_spend)
    for name, delta in sc_.get("moves", []):
        spend[name] = max(0.0, spend[name] + delta)

    def rev_of(name: str, roas_mult: float = 1.0) -> float:
        """Revenue channel: porsi existing linier; porsi TAMBAHAN kena damp."""
        roas = base_roas[name] * roas_mult
        existing = min(spend[name], base_spend[name])
        added = max(0.0, spend[name] - base_spend[name])
        dampf = damp if sc_.get("damp") else 1.0
        return existing * roas + added * roas * dampf

    tot_spend = sum(spend.values())
    det_rev = sum(rev_of(c) for c in spend)
    revs, roas_bl = [], []
    for _ in range(n):
        r = 0.0
        for c in spend:
            mu = base_roas[c]
            sample = max(0.0, rnd.gauss(mu, cv * mu))
            existing = min(spend[c], base_spend[c])
            added = max(0.0, spend[c] - base_spend[c])
            dampf = damp if sc_.get("damp") else 1.0
            r += existing * sample + added * sample * dampf
        revs.append(r)
        roas_bl.append(r / tot_spend if tot_spend else 0)
    return {"spend": tot_spend, "revenue_det": det_rev,
            "rev_p10": _pct(revs, .1), "rev_p50": _pct(revs, .5), "rev_p90": _pct(revs, .9),
            "roas_p50": _pct(roas_bl, .5), "roas_p10": _pct(roas_bl, .1),
            "roas_p90": _pct(roas_bl, .9)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · budget what-if simulator")
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--shift", type=float, default=20)
    ap.add_argument("--cv", type=float, default=0.2)
    ap.add_argument("--damp", type=float, default=0.85)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables", "budget_sim.md"))
    a = ap.parse_args(argv)
    A = json.load(open(a.analysis, encoding="utf-8"))
    ch = A.get("by_channel") or []
    if not ch:
        print("[DAN] analysis.json tanpa by_channel")
        return 2
    cur = A.get("meta", {}).get("currency", "Rp")
    sims = []
    for sc_ in scenarios(ch, a.shift):
        r = simulate(ch, sc_, a.cv, a.damp, a.n, a.seed)
        sims.append({**sc_, **r})
    base = sims[0]
    L = ["# Simulasi Budget What-If", "",
         f"**Asumsi:** damp {a.damp} (benefit menurun utk budget tambahan) · cv {a.cv} · "
         f"{a.n} sampel Monte-Carlo (seed {a.seed}) · geser {a.shift:.0f}%.", "",
         "| Skenario | Spend | Revenue p10 | p50 | p90 | ROAS p50 | Δ revenue p50 |",
         "|---|---|---|---|---|---|---|"]
    for s in sims:
        d = (s["rev_p50"] - base["rev_p50"]) / base["rev_p50"] * 100 if base["rev_p50"] else 0
        L.append(f"| {s['id']} — {s['desc']} | {cur}{s['spend']:,.0f} | "
                 f"{cur}{s['rev_p10']:,.0f} | {cur}{s['rev_p50']:,.0f} | "
                 f"{cur}{s['rev_p90']:,.0f} | {s['roas_p50']:.2f}x | {d:+.1f}% |")
    L += ["", "## Interpretasi",
          f"- Interval p10–p90 menunjukkan **ketidakpastian**: jangan ambil keputusan "
          f"hanya dari titik tengah.",
          f"- Skenario dianggap layak bila **p10-nya** masih ≥ revenue baseline "
          f"(worst-case tidak rugi peluang)."]
    for s in sims[1:]:
        ok = s["rev_p10"] >= base["rev_p50"]
        L.append(f"- `{s['id']}`: worst-case {cur}{s['rev_p10']:,.0f} "
                 f"{'≥' if ok else '<'} baseline p50 → "
                 f"{'LAYAK diuji' if ok else 'RISIKO, uji kecil dulu'}.")
    L += ["", "## Catatan kejujuran model",
          "- ROAS channel tujuan diasumsikan turun manfaat (damp) saat menerima budget "
          "tambahan; tanpa data historis skala, ini asumsi konservatif.",
          "- Tidak memodelkan seasonality, frekuensi, atau perubahan kompetisi.",
          "- Gunakan sebagai **penyaring arah**, bukan ramalan; validasi dengan uji "
          "budget kecil 7–14 hari.", "",
          "---", "_DAN · budget_sim. Monte-Carlo seed tetap sehingga hasil reproducibel._"]
    md = "\n".join(L)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(md)
    json.dump(sims, open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[DAN] budget sim: {len(sims)} skenario · baseline p50 "
          f"{cur}{base['rev_p50']:,.0f} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
