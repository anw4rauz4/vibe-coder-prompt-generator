"""Chart statistik: scatter, heatmap, waterfall, gauge."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import (FONT, THEMES, theme, esc, fmt_num, nice_ticks, _norm, _wrap, _shell, _title_block, _legend, _xy_path, _arc, _pm_date, _rag_color)

def scatter(points: Sequence[Sequence[float]], title: str = "", subtitle: str = "",
            width: int = 620, height: int = 420, th: Any = "dan", loc: str = "id",
            xlabel: str = "", ylabel: str = "", size: Optional[Sequence[float]] = None,
            groups: Optional[Sequence[str]] = None, trend: bool = True,
            transparent: bool = False) -> str:
    """points: [(x,y), ...] atau [(x,y,label), ...]"""
    th = theme(th)
    head, top = _title_block(24, 18, title, subtitle, th)
    L, R, B = 66, 24, 58
    T = top + 12
    pw, ph = width - L - R, height - T - B
    pts = [(float(p[0]), float(p[1]), (p[2] if len(p) > 2 else "")) for p in points]
    if not pts:
        return _shell(width, height, head, th, transparent)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    xt = nice_ticks(min(xs), max(xs), 5)
    yt = nice_ticks(min(ys), max(ys), 5)
    x0, x1 = xt[0], xt[-1]
    y0, y1 = yt[0], yt[-1]
    X = lambda v: L + (v - x0) / ((x1 - x0) or 1) * pw
    Y = lambda v: T + ph - (v - y0) / ((y1 - y0) or 1) * ph
    g = []
    for t in yt:
        g.append(f'<line x1="{L}" y1="{Y(t):.1f}" x2="{L + pw}" y2="{Y(t):.1f}" '
                 f'stroke="{th["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{L - 10}" y="{Y(t) + 4:.1f}" fill="{th["muted"]}" font-size="11" '
                 f'text-anchor="end">{fmt_num(t, loc)}</text>')
    for t in xt:
        g.append(f'<text x="{X(t):.1f}" y="{T + ph + 20:.1f}" fill="{th["muted"]}" '
                 f'font-size="11" text-anchor="middle">{fmt_num(t, loc)}</text>')
    if trend and len(pts) > 2:
        n = len(pts)
        mx, my = sum(xs) / n, sum(ys) / n
        den = sum((x - mx) ** 2 for x in xs) or 1
        slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den
        inter = my - slope * mx
        g.append(f'<line x1="{X(x0):.1f}" y1="{Y(inter + slope * x0):.1f}" '
                 f'x2="{X(x1):.1f}" y2="{Y(inter + slope * x1):.1f}" stroke="{th["accent"]}" '
                 f'stroke-width="1.8" stroke-dasharray="6 5" opacity="0.85"/>')
        r_num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
        r_den = math.sqrt(sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) or 1
        rr = r_num / r_den
        g.append(f'<text x="{L + pw - 6}" y="{T + 14}" fill="{th["accent"]}" font-size="11" '
                 f'text-anchor="end" font-weight="600">r = {rr:.2f}</text>')
    smax = max(size) if size else 1
    for i, (x, y, lab) in enumerate(pts):
        col = th["series"][(list(groups).index(groups[i]) if groups else i) % len(th["series"])]
        rr = 4 + (8 * (size[i] / (smax or 1))) if size else 5.5
        g.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{rr:.1f}" fill="{col}" '
                 f'fill-opacity="0.62" stroke="{col}" stroke-width="1.4"/>')
        if lab and len(pts) <= 24:
            g.append(f'<text x="{X(x) + rr + 4:.1f}" y="{Y(y) + 4:.1f}" fill="{th["muted"]}" '
                     f'font-size="10">{esc(str(lab)[:18])}</text>')
    if xlabel:
        g.append(f'<text x="{L + pw / 2:.1f}" y="{height - 12}" fill="{th["muted"]}" '
                 f'font-size="11.5" text-anchor="middle">{esc(xlabel)}</text>')
    if ylabel:
        g.append(f'<text x="16" y="{T + ph / 2:.1f}" fill="{th["muted"]}" font-size="11.5" '
                 f'text-anchor="middle" transform="rotate(-90 16 {T + ph / 2:.1f})">{esc(ylabel)}</text>')
    leg, _ = _legend(sorted(set(groups)), L, height - 30, th, max_w=pw) if groups else ("", 0)
    return _shell(width, height, head + "".join(g) + leg, th, transparent)


# ----------------------------------------------------------------------------- HEATMAP

def heatmap(rows: Sequence[str], cols: Sequence[str], matrix: Sequence[Sequence[float]],
            title: str = "", subtitle: str = "", width: int = 680, height: int = 400,
            th: Any = "dan", loc: str = "id", transparent: bool = False,
            low: str = "", high: str = "") -> str:
    th = theme(th)
    head, top = _title_block(24, 18, title, subtitle, th)
    L, B = 108, 46
    T = top + 10
    R = 20
    pw, ph = width - L - R, height - T - B
    if not rows or not cols:
        return _shell(width, height, head, th, transparent)
    cw, ch = pw / len(cols), ph / len(rows)
    vals = [v for r in matrix for v in r]
    lo, hi = (min(vals), max(vals)) if vals else (0, 1)
    low = low or th["grid"]
    high = high or th["accent"]

    def mix(t: float) -> str:
        t = max(0.0, min(1.0, t))
        a = [int(low[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(high[i:i + 2], 16) for i in (1, 3, 5)]
        c = [round(a[i] + (b[i] - a[i]) * t) for i in range(3)]
        return "#{:02X}{:02X}{:02X}".format(*c)

    g = []
    for ri, rname in enumerate(rows):
        g.append(f'<text x="{L - 10}" y="{T + ch * ri + ch / 2 + 4:.1f}" fill="{th["text"]}" '
                 f'font-size="11" text-anchor="end">{esc(str(rname)[:18])}</text>')
        for ci, cname in enumerate(cols):
            v = matrix[ri][ci] if ci < len(matrix[ri]) else 0
            t = (v - lo) / ((hi - lo) or 1)
            x0, y0 = L + cw * ci, T + ch * ri
            g.append(f'<rect x="{x0 + 1:.1f}" y="{y0 + 1:.1f}" width="{cw - 2:.1f}" '
                     f'height="{ch - 2:.1f}" rx="4" fill="{mix(t)}"/>')
            if cw > 34 and ch > 20:
                tc = "#0B1220" if t > 0.55 else th["text"]
                g.append(f'<text x="{x0 + cw / 2:.1f}" y="{y0 + ch / 2 + 4:.1f}" fill="{tc}" '
                         f'font-size="10.5" font-weight="600" text-anchor="middle">{fmt_num(v, loc)}</text>')
    for ci, cname in enumerate(cols):
        g.append(f'<text x="{L + cw * ci + cw / 2:.1f}" y="{T + ph + 18:.1f}" fill="{th["muted"]}" '
                 f'font-size="10.5" text-anchor="middle">{esc(str(cname)[:12])}</text>')
    return _shell(width, height, head + "".join(g), th, transparent)


# ----------------------------------------------------------------------------- WATERFALL

def waterfall(data: Any, title: str = "", subtitle: str = "", width: int = 700,
              height: int = 400, th: Any = "dan", loc: str = "id",
              transparent: bool = False) -> str:
    th = theme(th)
    d = _norm(data)
    head, top = _title_block(24, 18, title, subtitle, th)
    if not d:
        return _shell(width, height, head, th, transparent)
    L, R, B = 66, 20, 62
    T = top + 10
    pw, ph = width - L - R, height - T - B
    run, cum = 0.0, [0.0]
    for _, v in d[:-1]:
        run += v
        cum.append(run)
    lo = min(cum + [0.0])
    hi = max(cum + [0.0])
    ticks = nice_ticks(lo, hi, 5)
    lo, hi = ticks[0], ticks[-1]
    span = (hi - lo) or 1
    Y = lambda v: T + ph - (v - lo) / span * ph
    slot = pw / len(d)
    bw = min(slot * 0.6, 60)
    g = []
    for t in ticks:
        g.append(f'<line x1="{L}" y1="{Y(t):.1f}" x2="{L + pw}" y2="{Y(t):.1f}" '
                 f'stroke="{th["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{L - 10}" y="{Y(t) + 4:.1f}" fill="{th["muted"]}" font-size="11" '
                 f'text-anchor="end">{fmt_num(t, loc)}</text>')
    acc = 0.0
    for i, (lab, v) in enumerate(d):
        last = (i == len(d) - 1)
        start = 0.0 if last else acc
        end = v if last else acc + v
        cx = L + slot * i + slot / 2
        col = th["accent"] if last else (th["good"] if v >= 0 else th["bad"])
        y0, y1 = Y(max(start, end)), Y(min(start, end))
        g.append(f'<rect x="{cx - bw / 2:.1f}" y="{y0:.1f}" width="{bw:.1f}" '
                 f'height="{max(y1 - y0, 1):.1f}" rx="3" fill="{col}"/>')
        g.append(f'<text x="{cx:.1f}" y="{y0 - 6:.1f}" fill="{th["text"]}" font-size="10.5" '
                 f'font-weight="600" text-anchor="middle">{("+" if v > 0 and not last else "")}{fmt_num(v, loc)}</text>')
        if not last:
            g.append(f'<line x1="{cx + bw / 2:.1f}" y1="{Y(end):.1f}" x2="{cx + slot - bw / 2:.1f}" '
                     f'y2="{Y(end):.1f}" stroke="{th["muted"]}" stroke-width="1" stroke-dasharray="3 3"/>')
            acc = end
        lines = _wrap(lab, 10)
        for k, ln in enumerate(lines[:2]):
            g.append(f'<text x="{cx:.1f}" y="{T + ph + 18 + k * 12:.1f}" fill="{th["muted"]}" '
                     f'font-size="10.5" text-anchor="middle">{esc(ln)}</text>')
    return _shell(width, height, head + "".join(g), th, transparent)


# ----------------------------------------------------------------------------- GAUGE

def gauge(value: float, vmax: float = 100.0, label: str = "", title: str = "",
          width: int = 300, height: int = 200, th: Any = "dan", loc: str = "id",
          unit: str = "%", transparent: bool = False) -> str:
    th = theme(th)
    frac = max(0.0, min(1.0, value / (vmax or 1)))
    cx, cy, R = width / 2, height - 42, min(width / 2 - 26, 74)
    a0, a1 = math.pi, 2 * math.pi
    av = a0 + frac * math.pi
    col = th["bad"] if frac < 0.4 else (th["warn"] if frac < 0.75 else th["good"])
    g = [f'<path d="{_arc(cx, cy, R, a0, a1)}" fill="none" stroke="{th["grid"]}" '
         f'stroke-width="15" stroke-linecap="round"/>',
         f'<path d="{_arc(cx, cy, R, a0, av)}" fill="none" stroke="{col}" '
         f'stroke-width="15" stroke-linecap="round"/>']
    if title:
        g.append(f'<text x="{cx:.0f}" y="26" fill="{th["muted"]}" font-size="12" '
                 f'text-anchor="middle">{esc(title)}</text>')
    g.append(f'<text x="{cx:.0f}" y="{cy - 10:.0f}" fill="{th["text"]}" font-size="27" '
             f'font-weight="800" text-anchor="middle">{fmt_num(value, loc)}{esc(unit)}</text>')
    if label:
        g.append(f'<text x="{cx:.0f}" y="{cy + 12:.0f}" fill="{th["muted"]}" font-size="11" '
                 f'text-anchor="middle">{esc(label)}</text>')
    return _shell(width, height, "".join(g), th, transparent)


# ----------------------------------------------------------------------------- NETWORK
