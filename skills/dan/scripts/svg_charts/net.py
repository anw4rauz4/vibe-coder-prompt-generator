"""Graph/network: layout Fruchterman-Reingold + network."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import (FONT, THEMES, theme, esc, fmt_num, nice_ticks, _norm, _wrap, _shell, _title_block, _legend, _xy_path, _arc, _pm_date, _rag_color)

def fruchterman_reingold(n: int, edges: Sequence[Tuple[int, int]], w: int, h: int,
                         iters: int = 320, seed: int = 7,
                         pad: int = 46) -> List[Tuple[float, float]]:
    """Layout graph sederhana (pure python)."""
    if n <= 0:
        return []
    rnd = random.Random(seed)
    if n == 1:
        return [(w / 2, h / 2)]
    pos = [(rnd.uniform(pad, w - pad), rnd.uniform(pad, h - pad)) for _ in range(n)]
    area = (w - 2 * pad) * (h - 2 * pad)
    k = math.sqrt(area / n) * 0.85
    t = w / 8
    adj = [[] for _ in range(n)]
    for a, b in edges:
        if 0 <= a < n and 0 <= b < n and a != b:
            adj[a].append(b)
            adj[b].append(a)
    for _ in range(iters):
        disp = [[0.0, 0.0] for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
                d = math.hypot(dx, dy) or 0.01
                f = k * k / d
                disp[i][0] += dx / d * f
                disp[i][1] += dy / d * f
                disp[j][0] -= dx / d * f
                disp[j][1] -= dy / d * f
        for i in range(n):
            for j in adj[i]:
                dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
                d = math.hypot(dx, dy) or 0.01
                f = d * d / k
                disp[i][0] -= dx / d * f
                disp[i][1] -= dy / d * f
        for i in range(n):
            d = math.hypot(*disp[i]) or 0.01
            pos[i] = (pos[i][0] + disp[i][0] / d * min(d, t),
                      pos[i][1] + disp[i][1] / d * min(d, t))
            pos[i] = (max(pad, min(w - pad, pos[i][0])),
                      max(pad, min(h - pad, pos[i][1])))
        t *= 0.985
    return pos

def network(nodes: Sequence[Dict[str, Any]], edges: Sequence[Tuple[Any, Any]],
            title: str = "", subtitle: str = "", width: int = 760, height: int = 520,
            th: Any = "dan", transparent: bool = False,
            size_by: str = "degree", color_by: str = "group",
            weighted: bool = False) -> str:
    """nodes: [{'id':..,'label':..,'group':..,'value':..}] ; edges: [(id,id) atau (id,id,weight)]"""
    th = theme(th)
    head, top = _title_block(24, 18, title, subtitle, th)
    ids = [n["id"] if isinstance(n, dict) else n for n in nodes]
    idx = {v: i for i, v in enumerate(ids)}
    E = []
    for e in edges:
        a, b = idx.get(e[0]), idx.get(e[1])
        if a is None or b is None or a == b:
            continue
        w_ = float(e[2]) if len(e) > 2 else 1.0
        E.append((a, b, w_))
    if not ids:
        return _shell(width, height, head, th, transparent)
    deg = [0] * len(ids)
    for a, b, w_ in E:
        deg[a] += 1
        deg[b] += 1
    pos = fruchterman_reingold(len(ids), [(a, b) for a, b, _ in E],
                               width, height - top - 8, pad=54)
    pos = [(x, y + top + 4) for x, y in pos]
    wmax = max([w_ for _, _, w_ in E] + [1])
    smax = max([float(n.get("value", 0)) if isinstance(n, dict) else 0 for n in nodes] + [1])
    g = []
    for a, b, w_ in E:
        x0, y0 = pos[a]
        x1, y1 = pos[b]
        sw = (0.8 + 3.4 * (w_ / wmax)) if weighted else 1.4
        g.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                 f'stroke="{th["muted"]}" stroke-opacity="0.42" stroke-width="{sw:.1f}"/>')
    for i, nd in enumerate(nodes):
        nd = nd if isinstance(nd, dict) else {"id": nd}
        x, y = pos[i]
        grp = nd.get("group", i)
        try:
            gi = int(grp)
        except (TypeError, ValueError):
            gi = abs(hash(str(grp)))
        col = th["series"][gi % len(th["series"])]
        base = float(nd.get("value", 0)) / (smax or 1) if size_by == "value" else deg[i] / (max(deg) or 1)
        r = 5 + 15 * math.sqrt(max(0.0, base))
        g.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" '
                 f'fill-opacity="0.9" stroke="{th["bg"]}" stroke-width="1.6"/>')
        lab = nd.get("label", nd.get("id"))
        if r > 7 or len(ids) <= 40:
            g.append(f'<text x="{x:.1f}" y="{y + r + 12:.1f}" fill="{th["text"]}" '
                     f'font-size="10" text-anchor="middle">{esc(str(lab)[:20])}</text>')
    return _shell(width, height, head + "".join(g), th, transparent)


# ----------------------------------------------------------------------------- sparkline
