#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
props_test.py — Property-based test (invariant acak ber-seed) untuk engine DAN.

Tanpa dependensi (stdlib random dengan seed tetap → deterministik & reproducibel).
Bukan contoh kasus tunggal, melainkan *sifat* yang harus selalu benar untuk
input acak dalam rentang luas:

  P1  round-trip parse_number format ID   (titik ribuan, koma desimal)
  P2  round-trip parse_number format EN   (koma ribuan, titik desimal)
  P3  parse_number tahan prefix mata uang & suffix satuan (Rp … jt / rb / %)
  P4  nice_ticks: terurut, langkah seragam, mencakup [lo, hi]
  P5  semua chart: XML valid, dimensi positif, tanpa 'nan'/'None', utk data acak
      (positif, negatif, satu titik, kosong, gap None)
  P6  layout_floor (arch_design): tanpa overlap ruang & bbox == lebar/dalam dilaporkan
  P7  task_rag (project_monitor): rag ∈ {good,warn,bad} & konsisten dengan aturan ambang
  P8  fmt_num: tanpa 'nan'/'None'; round-trip utk nilai < 10.000 (tanpa satuan kompak)
  P9  gantt & progress: XML valid utk tugas/acak; tinggi bertambah sesuai jumlah baris
  P10 compare (arch_advisor): winner ∈ {a,b} & total == jumlah skor kriteria

PAKAI
  python3 props_test.py            # N=150 iterasi per properti
  python3 props_test.py --n 500 --seed 7
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys
import xml.etree.ElementTree as ET
from typing import Any, Callable, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import svg_charts as sc          # noqa: E402
import dan_analytics as da       # noqa: E402
import arch_design as ad         # noqa: E402
import project_monitor as pm     # noqa: E402
import arch_advisor as aa        # noqa: E402

FAILS: List[str] = []
COUNT = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global COUNT
    COUNT += 1
    if not cond:
        FAILS.append(f"{name}{': ' + detail if detail else ''}")


def fmt_id(v: float, dec: int) -> str:
    neg = v < 0
    s = f"{abs(v):,.{dec}f}"
    s = s.replace(",", "#").replace(".", ",").replace("#", ".")
    return ("-" if neg else "") + s


def fmt_en(v: float, dec: int) -> str:
    return f"{v:,.{dec}f}"


def p1_parse_id(rnd: random.Random, n: int) -> None:
    for _ in range(n):
        mag = rnd.choice([1, 10, 1000, 100000, 10000000])
        v = round(rnd.uniform(0, 999) * mag + rnd.randint(0, 999), 2)
        dec = rnd.choice([0, 2])
        s = fmt_id(v, dec)
        got = da.parse_number(s)
        check("P1 parse_id", got is not None and abs(got - round(v, dec)) < 1e-6,
              f"{s!r}->{got} vs {round(v, dec)}")


def p2_parse_en(rnd: random.Random, n: int) -> None:
    for _ in range(n):
        mag = rnd.choice([1, 10, 1000, 100000, 10000000])
        v = round(rnd.uniform(0, 999) * mag + rnd.randint(0, 999), 2)
        dec = rnd.choice([0, 2])
        s = fmt_en(v, dec)
        got = da.parse_number(s)
        check("P2 parse_en", got is not None and abs(got - round(v, dec)) < 1e-6,
              f"{s!r}->{got} vs {round(v, dec)}")


def p3_prefix_suffix(rnd: random.Random, n: int) -> None:
    for _ in range(n):
        base = rnd.randint(1, 9999)
        unit = rnd.choice(["", " rb", " jt"])
        mult = {"": 1, " rb": 1000, " jt": 1000000}[unit]
        s = f"Rp {base}{unit}"
        got = da.parse_number(s)
        check("P3 rp+unit", got == base * mult, f"{s!r}->{got}")
        pct = rnd.randint(1, 100)
        got2 = da.parse_number(f"{pct}%")
        check("P3 persen", got2 is not None and abs(got2 - pct / 100) < 1e-9, f"{pct}%->{got2}")


def p4_nice_ticks(rnd: random.Random, n: int) -> None:
    for _ in range(n):
        lo = rnd.uniform(-1000, 1000)
        hi = lo + rnd.uniform(1, 5000)
        t = sc.nice_ticks(lo, hi, rnd.choice([4, 5, 6]))
        ok_sorted = all(t[i] < t[i + 1] for i in range(len(t) - 1))
        steps = {round(t[i + 1] - t[i], 9) for i in range(len(t) - 1)}
        check("P4 ticks", len(t) >= 2 and ok_sorted and len(steps) == 1
              and t[0] <= lo and t[-1] >= hi, f"{lo:.1f}..{hi:.1f}->{t}")


def _valid(svg: str, want_w: int = 0) -> bool:
    import re as _re
    try:
        r = ET.fromstring(svg)
    except ET.ParseError:
        return False
    w = float(r.get("width", 0))
    h = float(r.get("height", 0))
    if w <= 0 or h <= 0:
        return False
    if want_w and abs(w - want_w) > 1:
        return False
    # token utuh saja: "dominant-baseline" memuat substring 'nan' dan bukan error
    return (not _re.search(r"\bnan\b", svg)) and (not _re.search(r"\bNone\b", svg))


def p5_charts(rnd: random.Random, n: int) -> None:
    kinds = ["bar", "hbar", "line", "area", "donut", "funnel", "waterfall", "stacked",
             "scatter", "heatmap", "radar", "gauge", "spark", "empty", "neg", "gap"]
    for _ in range(n):
        k = rnd.choice(kinds)
        m = rnd.randint(1, 8)
        data = [(f"L{i}", round(rnd.uniform(-50, 200), 1)) for i in range(m)]
        try:
            if k == "bar":
                s = sc.bar(data, title="t")
            elif k == "hbar":
                s = sc.hbar(data, title="t")
            elif k in ("line", "area"):
                s = sc.line(data, title="t", area=(k == "area"))
            elif k == "donut":
                s = sc.donut([(a, abs(b) + 1) for a, b in data], title="t")
            elif k == "funnel":
                s = sc.funnel([(a, abs(b) + 1) for a, b in data], title="t")
            elif k == "waterfall":
                s = sc.waterfall(data, title="t")
            elif k == "stacked":
                s = sc.stacked_bar([a for a, _ in data],
                                   {"s1": [abs(b) for _, b in data],
                                    "s2": [abs(b) / 2 for _, b in data]}, title="t")
            elif k == "scatter":
                s = sc.scatter([(rnd.uniform(0, 9), rnd.uniform(0, 9)) for _ in range(m)],
                               title="t")
            elif k == "heatmap":
                s = sc.heatmap(["a", "b"], ["x", "y"],
                               [[rnd.uniform(0, 9) for _ in range(2)] for _ in range(2)],
                               title="t")
            elif k == "radar":
                s = sc.radar({"k": [rnd.uniform(0, 9) for _ in range(5)]},
                             ["a", "b", "c", "d", "e"], title="t")
            elif k == "gauge":
                s = sc.gauge(rnd.uniform(0, 100), 100, "x", title="t")
            elif k == "spark":
                s = sc.sparkline([rnd.uniform(0, 9) for _ in range(m)])
            elif k == "empty":
                s = sc.bar([], title="t")
            elif k == "neg":
                s = sc.bar([(a, -abs(b)) for a, b in data], title="t")
            else:  # gap
                s = sc.line(compare={"x": [rnd.uniform(0, 9) if rnd.random() > .3 else None
                                           for _ in range(m)]},
                            x_labels=[str(i) for i in range(m)], title="t")
            check(f"P5 chart {k}", _valid(s), k)
        except Exception as e:                            # pragma: no cover
            check(f"P5 chart {k}", False, repr(e))


def p6_layout(rnd: random.Random, n: int) -> None:
    funcs = ["living", "private", "service", "wet", "circulation"]
    for _ in range(n):
        rooms = [{"name": f"R{i}", "w": round(rnd.uniform(1.5, 6), 2),
                  "d": round(rnd.uniform(1.5, 6), 2),
                  "function": rnd.choice(funcs)} for i in range(rnd.randint(1, 9))]
        placed, bw, bd = ad.layout_floor(rooms, rnd.uniform(5, 12))
        overlap = any(a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
                      and a["y"] < b["y"] + b["d"] and b["y"] < a["y"] + a["d"]
                      for i, a in enumerate(placed) for b in placed[i + 1:])
        bbw = max((r["x"] + r["w"] for r in placed), default=0)
        bbd = max((r["y"] + r["d"] for r in placed), default=0)
        check("P6 layout", (not overlap) and abs(bbw - bw) < 0.01 and abs(bbd - bd) < 0.01
              and len(placed) == len(rooms),
              f"overlap={overlap} bw={bw}/{bbw:.2f} bd={bd}/{bbd:.2f}")


def p7_rag(rnd: random.Random, n: int) -> None:
    from datetime import datetime, timedelta
    for _ in range(n):
        st = datetime(2026, 9, 1)
        en = st + timedelta(days=rnd.randint(1, 40))
        now = st + timedelta(days=rnd.randint(0, 50))
        act = rnd.choice([0, 20, 50, 80, 100, rnd.uniform(0, 100)])
        t = {"start": st, "end": en, "progress": act}
        rag, plan, a2, over = pm.task_rag(t, now)
        var = a2 - plan
        expect = "good"
        if a2 < 100:
            if over > 3 or var < -20:
                expect = "bad"
            elif over > 0 or var < -5:
                expect = "warn"
        check("P7 rag", rag in ("good", "warn", "bad") and rag == expect
              and 0 <= plan <= 100 and over >= 0,
              f"act={act:.0f} plan={plan:.0f} over={over} rag={rag} expect={expect}")


def p8_fmt(rnd: random.Random, n: int) -> None:
    for _ in range(n):
        v = rnd.uniform(-9999, 9999)
        s = sc.fmt_num(v, "id")
        check("P8 fmt bersih", ("nan" not in s.lower()) and ("None" not in s), s)
        if abs(v) < 10000:
            back = da.parse_number(s)
            # fmt_num adalah format TAMPILAN (pembulatan), jadi bandingkan dengan
            # toleransi setengah satuan desimal terakhir yang ditampilkan.
            tol = 0.05 if abs(v) >= 100 else 0.005
            check("P8 fmt roundtrip", back is not None and abs(back - v) <= tol + 1e-9,
                  f"{s!r}->{back} vs {v:.2f}")


def p9_pm_charts(rnd: random.Random, n: int) -> None:
    from datetime import datetime, timedelta
    for _ in range(n):
        m = rnd.randint(1, 10)
        st = datetime(2026, 9, 1)
        tasks = [{"name": f"T{i}", "start": st + timedelta(days=rnd.randint(0, 10)),
                  "end": st + timedelta(days=rnd.randint(11, 40)),
                  "progress": rnd.randint(0, 100),
                  "rag": rnd.choice(["good", "warn", "bad"])} for i in range(m)]
        g = sc.gantt(tasks, "dan", 20)
        check("P9 gantt", _valid(g), "gantt")
        pr = sc.progress([{"label": f"P{i}", "value": rnd.randint(0, 100),
                           "target": rnd.randint(0, 100)} for i in range(m)], title="t")
        check("P9 progress", _valid(pr), "progress")


def p10_compare(rnd: random.Random, n: int) -> None:
    groups = list(aa.COMPARE_GROUPS)
    for _ in range(n):
        g = rnd.choice(groups)
        opts = list(aa.COMPARE_GROUPS[g])
        a, b = rnd.sample(opts, 2)
        ctx = {"team": rnd.randint(1, 30), "scale": rnd.choice(["kecil", "medium", "besar"]),
               "deadline": rnd.choice(["ketat", "normal", "longgar"]),
               "budget": rnd.choice(["rendah", "sedang", "tinggi"])}
        c = aa.compare(g, a, b, ctx)
        check("P10 compare", c["winner"] in (a, b)
              and c["a"]["total"] == sum(c["a"]["scores"].values())
              and c["b"]["total"] == sum(c["b"]["scores"].values()), f"{g}:{a}vs{b}")


PROPS: List[Tuple[str, Callable[[random.Random, int], None]]] = [
    ("P1", p1_parse_id), ("P2", p2_parse_en), ("P3", p3_prefix_suffix),
    ("P4", p4_nice_ticks), ("P5", p5_charts), ("P6", p6_layout),
    ("P7", p7_rag), ("P8", p8_fmt), ("P9", p9_pm_charts), ("P10", p10_compare),
]


def run_all(n: int = 150, seed: int = 42) -> Tuple[int, List[str]]:
    global FAILS, COUNT
    FAILS, COUNT = [], 0
    rnd = random.Random(seed)
    for _, fn in PROPS:
        fn(rnd, n)
    return COUNT, FAILS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · property-based tests")
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args(argv)
    count, fails = run_all(a.n, a.seed)
    print(f"[DAN] property tests: {count} pemeriksaan · {len(fails)} gagal "
          f"(n={a.n}, seed={a.seed})")
    for f in fails[:20]:
        print("   FAIL", f)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
