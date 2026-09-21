"""Chart keluarga bar: bar, hbar, stacked_bar."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import (FONT, THEMES, theme, esc, fmt_num, nice_ticks, _norm, _wrap, _shell, _title_block, _legend, _xy_path, _arc, _pm_date, _rag_color)

def bar(data: Any, title: str = "", subtitle: str = "", width: int = 640,
        height: int = 380, th: Any = "dan", loc: str = "id",
        value_fmt: Optional[Callable[[float], str]] = None,
        highlight: Optional[int] = None, transparent: bool = False,
        show_values: bool = True, horizontal_labels: bool = False) -> str:
    th = theme(th)
    vf = value_fmt or (lambda v: fmt_num(v, loc))
    d = _norm(data)
    if not d:
        return _shell(width, height, "", th, transparent)
    head, top = _title_block(24, 18, title, subtitle, th)
    L, R, B = 62, 20, 62
    T = top + 10
    pw, ph = width - L - R, height - T - B
    vals = [v for _, v in d]
    lo = min(0.0, min(vals))
    hi = max(0.0, max(vals))
    ticks = nice_ticks(lo, hi, 5)
    lo, hi = ticks[0], ticks[-1]
    span = (hi - lo) or 1.0
    y = lambda v: T + ph - (v - lo) / span * ph

    g = []
    for t in ticks:
        yy = y(t)
        dash = 'stroke-dasharray="3 4"' if t != 0 else ''
        g.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L + pw}" y2="{yy:.1f}" '
                 f'stroke="{th["grid"]}" stroke-width="1" {dash}/>')
        g.append(f'<text x="{L - 10}" y="{yy + 4:.1f}" fill="{th["muted"]}" '
                 f'font-size="11" text-anchor="end">{vf(t)}</text>')

    n = len(d)
    slot = pw / n
    bw = max(4.0, min(slot * 0.62, 74))
    zero = y(0)
    for i, (lab, v) in enumerate(d):
        cx = L + slot * i + slot / 2
        col = th["series"][i % len(th["series"])]
        if highlight is not None and i == highlight:
            col = th["accent"]
        yv = y(v)
        top_, h_ = (min(yv, zero), abs(zero - yv))
        g.append(f'<rect x="{cx - bw / 2:.1f}" y="{top_:.1f}" width="{bw:.1f}" '
                 f'height="{max(h_, 0.6):.1f}" rx="4" fill="{col}"/>')
        if show_values:
            vy = top_ - 7 if v >= 0 else top_ + h_ + 14
            g.append(f'<text x="{cx:.1f}" y="{vy:.1f}" fill="{th["text"]}" '
                     f'font-size="11.5" font-weight="600" text-anchor="middle">{vf(v)}</text>')
        # label sumbu X: wrap pendek, atau rotasi kalau label panjang & slot sempit
        tx = cx
        ty = height - B + 20
        need_rot = (not horizontal_labels) and (len(lab) * 6.3 > slot - 4) and len(lab) > 8
        if need_rot:
            rot = f' transform="rotate(-32 {tx:.1f} {ty:.1f})"'
            anc = "end"
            lines = [lab]
        else:
            rot = ""
            anc = "middle"
            lines = _wrap(lab, max(6, int(slot / 6.2)))[:3]
        for k, ln in enumerate(lines):
            g.append(f'<text x="{tx:.1f}" y="{ty + k * 13:.1f}" fill="{th["muted"]}" '
                     f'font-size="11" text-anchor="{anc}"{rot}>{esc(ln)}</text>')
    return _shell(width, height, head + "".join(g), th, transparent)

def hbar(data: Any, title: str = "", subtitle: str = "", width: int = 640,
         height: int = 380, th: Any = "dan", loc: str = "id",
         value_fmt: Optional[Callable[[float], str]] = None,
         sort: bool = True, transparent: bool = False) -> str:
    th = theme(th)
    vf = value_fmt or (lambda v: fmt_num(v, loc))
    d = _norm(data)
    if sort:
        d = sorted(d, key=lambda x: x[1], reverse=True)
    if not d:
        return _shell(width, height, "", th, transparent)
    head, top = _title_block(24, 18, title, subtitle, th)
    L, R = 138, 78
    T = top + 8
    B = 26
    pw, ph = width - L - R, height - T - B
    hi = max([v for _, v in d] + [0.0])
    ticks = nice_ticks(0, hi, 4)
    hi = ticks[-1] or 1.0
    x = lambda v: L + v / hi * pw
    n = len(d)
    slot = ph / n
    bh = max(4.0, min(slot * 0.6, 30))
    g = []
    for t in ticks:
        xx = x(t)
        g.append(f'<line x1="{xx:.1f}" y1="{T}" x2="{xx:.1f}" y2="{T + ph}" '
                 f'stroke="{th["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{xx:.1f}" y="{T + ph + 16:.1f}" fill="{th["muted"]}" '
                 f'font-size="10.5" text-anchor="middle">{vf(t)}</text>')
    for i, (lab, v) in enumerate(d):
        cy = T + slot * i + slot / 2
        col = th["series"][i % len(th["series"])]
        w_ = max(x(v) - L, 0.6)
        g.append(f'<rect x="{L}" y="{cy - bh / 2:.1f}" width="{w_:.1f}" height="{bh:.1f}" '
                 f'rx="4" fill="{col}"/>')
        g.append(f'<text x="{L - 10}" y="{cy + 4:.1f}" fill="{th["text"]}" font-size="11.5" '
                 f'text-anchor="end">{esc(lab[:24])}</text>')
        g.append(f'<text x="{L + w_ + 8:.1f}" y="{cy + 4:.1f}" fill="{th["muted"]}" '
                 f'font-size="11" font-weight="600">{vf(v)}</text>')
    return _shell(width, height, head + "".join(g), th, transparent)

def stacked_bar(categories: Sequence[str], series: Dict[str, Sequence[float]],
                title: str = "", subtitle: str = "", width: int = 680,
                height: int = 400, th: Any = "dan", loc: str = "id",
                pct: bool = False, transparent: bool = False) -> str:
    th = theme(th)
    names = list(series.keys())
    head, top = _title_block(24, 18, title, subtitle, th)
    leg, lh = _legend(names, 24, top + 4, th, max_w=width - 48)
    L, R, B = 62, 20, 58
    T = top + lh + 12
    pw, ph = width - L - R, height - T - B
    if pw <= 0 or ph <= 0 or not categories:
        return _shell(width, height, head, th, transparent)
    mat = [[float(series[nm][i]) if i < len(series[nm]) else 0.0 for nm in names]
           for i in range(len(categories))]
    if pct:
        mat = [[(v / (sum(r) or 1)) * 100 for v in r] for r in mat]
    hi = max([sum(r) for r in mat] + [0.0])
    ticks = nice_ticks(0, hi, 5)
    hi = ticks[-1] or 1.0
    y = lambda v: T + ph - v / hi * ph
    g = []
    for t in ticks:
        yy = y(t)
        g.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L + pw}" y2="{yy:.1f}" '
                 f'stroke="{th["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{L - 10}" y="{yy + 4:.1f}" fill="{th["muted"]}" '
                 f'font-size="11" text-anchor="end">{fmt_num(t, loc)}{"%" if pct else ""}</text>')
    slot = pw / len(categories)
    bw = max(6.0, min(slot * 0.58, 62))
    for i, cat in enumerate(categories):
        cx = L + slot * i + slot / 2
        acc = 0.0
        for j, nm in enumerate(names):
            v = mat[i][j]
            if v <= 0:
                acc += v
                continue
            y0, y1 = y(acc), y(acc + v)
            col = th["series"][j % len(th["series"])]
            g.append(f'<rect x="{cx - bw / 2:.1f}" y="{y1:.1f}" width="{bw:.1f}" '
                     f'height="{max(y0 - y1, 0.6):.1f}" fill="{col}" '
                     f'rx="{3 if j == len(names) - 1 else 0}"/>')
            acc += v
        g.append(f'<text x="{cx:.1f}" y="{T + ph + 20:.1f}" fill="{th["muted"]}" '
                 f'font-size="11" text-anchor="middle">{esc(str(cat)[:14])}</text>')
    return _shell(width, height, head + leg + "".join(g), th, transparent)


# ----------------------------------------------------------------------------- LINE / AREA
