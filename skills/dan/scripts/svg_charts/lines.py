"""Chart keluarga garis: line (gap-aware), area, sparkline."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import (FONT, THEMES, theme, esc, fmt_num, nice_ticks, _norm, _wrap, _shell, _title_block, _legend, _xy_path, _arc, _pm_date, _rag_color)

def line(data: Any = None, title: str = "", subtitle: str = "", width: int = 700,
         height: int = 380, th: Any = "dan", loc: str = "id",
         smooth: float = 0.85, area: bool = False, markers: bool = True,
         value_fmt: Optional[Callable[[float], str]] = None,
         x_rotate: bool = True, transparent: bool = False,
         compare: Optional[Dict[str, Sequence[float]]] = None,
         x_labels: Optional[Sequence[str]] = None) -> str:
    """line([v1,v2,...]) atau line([(label,val),...]) atau compare={'2024':[..],'2025':[..]}"""
    th = theme(th)
    vf = value_fmt or (lambda v: fmt_num(v, loc))
    series: Dict[str, List[Optional[float]]] = {}
    labels: List[str] = []

    def _f(x: Any) -> Optional[float]:
        if x is None or x == "":
            return None
        try:
            v = float(x)
        except (TypeError, ValueError):
            return None
        return None if (math.isnan(v) or math.isinf(v)) else v

    if compare:
        for k, v in compare.items():
            series[str(k)] = [_f(x) for x in v]
        n = max(len(v) for v in series.values())
        labels = [str(x_labels[i]) if x_labels and i < len(x_labels) else str(i + 1)
                  for i in range(n)]
    else:
        d = _norm(data)
        if d and isinstance(data, (list, tuple)) and data and isinstance(data[0], (list, tuple)):
            labels = [str(a) for a, _ in d]
        elif d:
            labels = [str(a) for a, _ in d]
        else:
            labels = []
        if not labels:
            raw = list(data or [])
            labels = [str(i + 1) for i in range(len(raw))]
            series["Nilai"] = [_f(x) for x in raw]
        else:
            series["Nilai"] = [_f(v) for _, v in d]
    if x_labels and not compare:
        labels = [str(x) for x in x_labels]
    if not series:
        return _shell(width, height, "", th, transparent)

    head, top = _title_block(24, 18, title, subtitle, th)
    L, R, B = 64, 22, 56
    T = top + 10
    pw, ph = width - L - R, height - T - B
    allv = [v for vs in series.values() for v in vs if v is not None]
    if not allv:
        return _shell(width, height, head, th, transparent)
    ticks = nice_ticks(min(0.0, min(allv)), max(allv), 5)
    lo, hi = ticks[0], ticks[-1]
    span = (hi - lo) or 1.0
    X = lambda i, n: L + (pw * (i / max(1, n - 1)) if n > 1 else pw / 2)
    Y = lambda v: T + ph - (v - lo) / span * ph

    defs, g = [], []
    for t in ticks:
        yy = Y(t)
        g.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{L + pw}" y2="{yy:.1f}" '
                 f'stroke="{th["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{L - 10}" y="{yy + 4:.1f}" fill="{th["muted"]}" '
                 f'font-size="11" text-anchor="end">{vf(t)}</text>')
    n = max(len(v) for v in series.values())
    step = max(1, math.ceil(n / 12))
    for i in range(0, n, step):
        if i < len(labels):
            xx = X(i, n)
            rot = f' transform="rotate(-30 {xx:.1f} {T + ph + 20:.1f})"' if (x_rotate and n > 8) else ""
            anc = "end" if rot else "middle"
            g.append(f'<text x="{xx:.1f}" y="{T + ph + 20:.1f}" fill="{th["muted"]}" '
                     f'font-size="10.5" text-anchor="{anc}"{rot}>{esc(labels[i])}</text>')

    for si, (nm, vs) in enumerate(series.items()):
        col = th["series"][si % len(th["series"])]
        # pecah jadi segmen kontinu (None = gap)
        segs: List[List[Tuple[float, float]]] = []
        cur: List[Tuple[float, float]] = []
        for i, v in enumerate(vs):
            if v is None:
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
            else:
                cur.append((X(i, len(vs)), Y(v)))
        if len(cur) > 1:
            segs.append(cur)
        if not segs:
            continue
        dashed = any(v is None for v in vs) and si > 0
        if area and segs:
            gid = f"ag{si}{random.randint(1000, 9999)}"
            defs.append(f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                        f'<stop offset="0%" stop-color="{col}" stop-opacity="0.42"/>'
                        f'<stop offset="100%" stop-color="{col}" stop-opacity="0.02"/></linearGradient>')
            base = Y(max(lo, 0))
            for sg in segs:
                g.append(f'<path d="{_xy_path(sg, smooth)} L {sg[-1][0]:.2f} {base:.2f} '
                         f'L {sg[0][0]:.2f} {base:.2f} Z" fill="url(#{gid})"/>')
        for sg in segs:
            dash = ' stroke-dasharray="7 5"' if dashed else ''
            g.append(f'<path d="{_xy_path(sg, smooth)}" fill="none" stroke="{col}" '
                     f'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"{dash}/>')
        if markers and n <= 60:
            for sg in segs:
                for (px, py) in sg:
                    g.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="{th["bg"]}" '
                             f'stroke="{col}" stroke-width="2"/>')
    leg, lh = _legend(list(series.keys()), L, T - 2, th, max_w=pw) if len(series) > 1 else ("", 0)
    return _shell(width, height, head + leg + "".join(g), th, transparent,
                  defs="".join(defs))

def area(data: Any, **kw) -> str:
    kw["area"] = True
    return line(data, **kw)


# ----------------------------------------------------------------------------- DONUT / PIE

def sparkline(values: Sequence[float], width: int = 160, height: int = 42,
              color: str = "#38BDF8", fill: bool = True, th: Any = "dan") -> str:
    th = theme(th)
    vs = [float(v) for v in values]
    if len(vs) < 2:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"></svg>'
    lo, hi = min(vs), max(vs)
    span = (hi - lo) or 1
    pts = [(i / (len(vs) - 1) * (width - 4) + 2,
            height - 4 - (v - lo) / span * (height - 10)) for i, v in enumerate(vs)]
    d = _xy_path(pts, 0.8)
    gid = f"sp{random.randint(1000, 9999)}"
    extra = ""
    body = ""
    if fill:
        extra = (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
                 f'<stop offset="0%" stop-color="{color}" stop-opacity="0.35"/>'
                 f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/></linearGradient>')
        body = (f'<path d="{d} L {pts[-1][0]:.1f} {height} L {pts[0][0]:.1f} {height} Z" '
                f'fill="url(#{gid})"/>')
    body += f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
    body += (f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="2.8" fill="{color}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}"><defs>{extra}</defs>{body}</svg>')


# ----------------------------------------------------------------------------- gallery demo

# ----------------------------------------------------------------------------- GANTT & PROGRESS
