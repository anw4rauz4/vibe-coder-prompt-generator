"""Chart komposisi & profil: donut, pie, funnel, radar."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import (FONT, THEMES, theme, esc, fmt_num, nice_ticks, _norm, _wrap, _shell, _title_block, _legend, _xy_path, _arc, _pm_date, _rag_color)

def donut(data: Any, title: str = "", subtitle: str = "", width: int = 460,
          height: int = 380, th: Any = "dan", loc: str = "id",
          center_label: str = "", center_value: str = "",
          donut_width: float = 0.34, transparent: bool = False,
          explode_max: bool = True) -> str:
    th = theme(th)
    d = [(k, v) for k, v in _norm(data) if v > 0]
    head, top = _title_block(24, 18, title, subtitle, th)
    if not d:
        return _shell(width, height, head, th, transparent)
    tot = sum(v for _, v in d)
    cx = width * 0.36
    cy = top + (height - top - 24) / 2
    R = min(cx - 30, (height - top - 30) / 2)
    R = max(30.0, R)
    r = R * (1 - donut_width)
    a = -math.pi / 2
    g = []
    mx = max(v for _, v in d) if explode_max else None
    for i, (lab, v) in enumerate(d):
        frac = v / tot
        a1 = a + frac * 2 * math.pi
        col = th["series"][i % len(th["series"])]
        off = 0.0
        if mx is not None and v == mx:
            off = 6
        mid = (a + a1) / 2
        ox, oy = math.cos(mid) * off, math.sin(mid) * off
        path = (f'{_arc(cx + ox, cy + oy, R, a, a1)} '
                f'L {cx + ox + r * math.cos(a1):.2f} {cy + oy + r * math.sin(a1):.2f} '
                f'{_arc(cx + ox, cy + oy, r, a1, a)[2:]} Z')
        g.append(f'<path d="{path}" fill="{col}" stroke="{th["bg"]}" stroke-width="1.5"/>')
        a = a1
    if center_value or center_label:
        g.append(f'<text x="{cx:.1f}" y="{cy - 2:.1f}" fill="{th["text"]}" font-size="24" '
                 f'font-weight="800" text-anchor="middle">{esc(center_value)}</text>')
        g.append(f'<text x="{cx:.1f}" y="{cy + 18:.1f}" fill="{th["muted"]}" font-size="11" '
                 f'text-anchor="middle">{esc(center_label)}</text>')
    lx = width * 0.66
    ly = cy - len(d) * 11
    for i, (lab, v) in enumerate(d):
        col = th["series"][i % len(th["series"])]
        yy = ly + i * 23
        g.append(f'<rect x="{lx:.0f}" y="{yy - 8:.0f}" width="10" height="10" rx="3" fill="{col}"/>')
        g.append(f'<text x="{lx + 16:.0f}" y="{yy + 1:.0f}" fill="{th["text"]}" font-size="11.5">'
                 f'{esc(lab[:18])}</text>')
        g.append(f'<text x="{lx + 16:.0f}" y="{yy + 14:.0f}" fill="{th["muted"]}" font-size="10.5">'
                 f'{fmt_num(v, loc)} · {v / tot * 100:.1f}%</text>')
    return _shell(width, height, head + "".join(g), th, transparent)

def pie(data: Any, **kw) -> str:
    kw["donut_width"] = 0.0001
    kw.pop("center_label", None)
    kw.pop("center_value", None)
    return donut(data, **kw)


# ----------------------------------------------------------------------------- FUNNEL

def funnel(data: Any, title: str = "", subtitle: str = "", width: int = 560,
           height: int = 400, th: Any = "dan", loc: str = "id",
           transparent: bool = False) -> str:
    th = theme(th)
    d = _norm(data)
    head, top = _title_block(24, 18, title, subtitle, th)
    if not d:
        return _shell(width, height, head, th, transparent)
    T = top + 12
    B = 16
    ph = height - T - B
    pw = width - 40
    mx = max(v for _, v in d) or 1.0
    n = len(d)
    rowh = ph / n
    g = []
    cx = 20 + pw / 2
    for i, (lab, v) in enumerate(d):
        w0 = pw * (v / mx)
        w1 = pw * (d[i + 1][1] / mx) if i + 1 < n else w0 * 0.86
        y0, y1 = T + rowh * i + 3, T + rowh * (i + 1) - 3
        col = th["series"][i % len(th["series"])]
        g.append(f'<path d="M {cx - w0 / 2:.1f} {y0:.1f} L {cx + w0 / 2:.1f} {y0:.1f} '
                 f'L {cx + w1 / 2:.1f} {y1:.1f} L {cx - w1 / 2:.1f} {y1:.1f} Z" '
                 f'fill="{col}" opacity="0.92"/>')
        g.append(f'<text x="{cx:.1f}" y="{(y0 + y1) / 2 - 1:.1f}" fill="#0B1220" '
                 f'font-size="12.5" font-weight="700" text-anchor="middle">{esc(lab)}</text>')
        g.append(f'<text x="{cx:.1f}" y="{(y0 + y1) / 2 + 14:.1f}" fill="#0B1220" '
                 f'font-size="11.5" text-anchor="middle" opacity="0.8">'
                 f'{fmt_num(v, loc)} · {v / mx * 100:.1f}%</text>')
        if i > 0:
            drop = (1 - v / (d[i - 1][1] or 1)) * 100
            g.append(f'<text x="{cx + w0 / 2 + 10:.1f}" y="{y0 + 8:.1f}" fill="{th["bad"]}" '
                     f'font-size="10.5">-{drop:.1f}%</text>')
    return _shell(width, height, head + "".join(g), th, transparent)


# ----------------------------------------------------------------------------- RADAR

def radar(series: Dict[str, Sequence[float]], axes: Sequence[str], title: str = "",
          subtitle: str = "", width: int = 480, height: int = 420, th: Any = "dan",
          vmax: Optional[float] = None, transparent: bool = False) -> str:
    th = theme(th)
    head, top = _title_block(24, 18, title, subtitle, th)
    axes = list(axes)
    if not axes or not series:
        return _shell(width, height, head, th, transparent)
    cx, cy = width / 2, top + (height - top - 30) / 2
    R = min(cx, cy - top) - 52
    R = max(40.0, R)
    mx = vmax or max([max(list(v) + [0]) for v in series.values()] + [1])
    n = len(axes)
    ang = lambda i: -math.pi / 2 + i * 2 * math.pi / n
    g = []
    for ring in range(1, 5):
        rr = R * ring / 4
        pts = " ".join(f"{cx + rr * math.cos(ang(i)):.1f},{cy + rr * math.sin(ang(i)):.1f}"
                       for i in range(n))
        g.append(f'<polygon points="{pts}" fill="none" stroke="{th["grid"]}" stroke-width="1"/>')
    for i in range(n):
        g.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx + R * math.cos(ang(i)):.1f}" '
                 f'y2="{cy + R * math.sin(ang(i)):.1f}" stroke="{th["grid"]}" stroke-width="1"/>')
        lx, ly = cx + (R + 20) * math.cos(ang(i)), cy + (R + 20) * math.sin(ang(i))
        anc = "middle" if abs(math.cos(ang(i))) < 0.3 else ("start" if math.cos(ang(i)) > 0 else "end")
        g.append(f'<text x="{lx:.1f}" y="{ly:.1f}" fill="{th["muted"]}" font-size="11" '
                 f'text-anchor="{anc}" dominant-baseline="middle">{esc(str(axes[i])[:16])}</text>')
    for si, (nm, vals) in enumerate(series.items()):
        col = th["series"][si % len(th["series"])]
        pts = []
        for i in range(n):
            v = float(vals[i]) if i < len(vals) else 0.0
            rr = R * (v / (mx or 1))
            pts.append(f"{cx + rr * math.cos(ang(i)):.1f},{cy + rr * math.sin(ang(i)):.1f}")
        g.append(f'<polygon points="{" ".join(pts)}" fill="{col}" fill-opacity="0.18" '
                 f'stroke="{col}" stroke-width="2.2"/>')
        for p in pts:
            px, py = p.split(",")
            g.append(f'<circle cx="{px}" cy="{py}" r="2.8" fill="{col}"/>')
    leg, _ = _legend(list(series.keys()), 24, height - 14, th, max_w=width - 48)
    return _shell(width, height, head + "".join(g) + leg, th, transparent)


# ----------------------------------------------------------------------------- SCATTER
