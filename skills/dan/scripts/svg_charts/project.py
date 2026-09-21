"""Chart manajemen proyek: gantt & progress/bullet bar."""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from .core import (FONT, THEMES, theme, esc, fmt_num, nice_ticks, _norm, _wrap, _shell, _title_block, _legend, _xy_path, _arc, _pm_date, _rag_color)

_MONTH_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul",
             "Agu", "Sep", "Okt", "Nov", "Des"]

def gantt(tasks: Sequence[Dict[str, Any]], title: str = "", subtitle: str = "",
          width: int = 940, th: Any = "dan", today: Any = None,
          show_progress: bool = True, row_h: int = 30, transparent: bool = False,
          loc: str = "id") -> str:
    """Gantt chart untuk monitoring/tracking proyek.

    tasks: [{'name','start','end','progress'(0-1 atau 0-100),'rag','owner','milestone'}]
    Tanggal boleh ISO ('2026-09-01') atau datetime. progress>1 dianggap persen.
    """
    th = theme(th)
    rows: List[Dict[str, Any]] = []
    for t in tasks or []:
        st, en = _pm_date(t.get("start")), _pm_date(t.get("end") or t.get("start"))
        if st is None:
            continue
        en = en or st
        if en < st:
            st, en = en, st
        pr = float(t.get("progress", 0) or 0)
        pr = pr / 100.0 if pr > 1 else pr
        rows.append({"name": str(t.get("name", t.get("task", "?"))), "start": st, "end": en,
                     "progress": max(0.0, min(1.0, pr)),
                     "rag": t.get("rag", t.get("status")),
                     "owner": t.get("owner", ""),
                     "milestone": bool(t.get("milestone"))})
    head, top = _title_block(24, 18, title, subtitle, th)
    if not rows:
        return _shell(width, 120, head, th, transparent)

    n = len(rows)
    L, R = 168, 86
    T = top + 26
    B = 30
    H = T + n * row_h + B
    pw = width - L - R
    t0 = min(r["start"] for r in rows)
    t1 = max(r["end"] for r in rows)
    span_days = max(1, (t1 - t0).days)
    X = lambda d: L + (d - t0).days / span_days * pw

    g = []
    # grid waktu + label tanggal
    ticks = nice_ticks(0, span_days, 6)
    for tk in ticks:
        xx = L + tk / span_days * pw
        d = t0 + timedelta(days=tk)
        g.append(f'<line x1="{xx:.1f}" y1="{T - 8}" x2="{xx:.1f}" y2="{T + n * row_h}" '
                 f'stroke="{th["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{xx:.1f}" y="{T - 12}" fill="{th["muted"]}" font-size="10.5" '
                 f'text-anchor="middle">{d.day} {_MONTH_ID[d.month - 1]}</text>')
    # baris
    for i, r in enumerate(rows):
        y = T + i * row_h
        cy = y + row_h / 2
        x0, x1 = X(r["start"]), X(r["end"])
        w_ = max(x1 - x0, 2.0)
        col = _rag_color(r["rag"], th, th["accent"])
        g.append(f'<text x="{L - 10}" y="{cy + 1:.1f}" fill="{th["text"]}" font-size="11.5" '
                 f'text-anchor="end">{esc(r["name"][:26])}</text>')
        if r["milestone"]:
            s = 7
            g.append(f'<path d="M {x0:.1f} {cy - s:.1f} L {x0 + s:.1f} {cy:.1f} '
                     f'L {x0:.1f} {cy + s:.1f} L {x0 - s:.1f} {cy:.1f} Z" fill="{col}"/>')
        else:
            g.append(f'<rect x="{x0:.1f}" y="{cy - 7:.1f}" width="{w_:.1f}" height="14" '
                     f'rx="7" fill="{th["grid"]}"/>')
            if show_progress and r["progress"] > 0:
                g.append(f'<rect x="{x0:.1f}" y="{cy - 7:.1f}" '
                         f'width="{max(w_ * r["progress"], 3):.1f}" height="14" rx="7" '
                         f'fill="{col}"/>')
            pct = f'{r["progress"] * 100:.0f}%'
            g.append(f'<text x="{x1 + 8:.1f}" y="{cy + 4:.1f}" fill="{th["muted"]}" '
                     f'font-size="10.5">{esc(pct)}</text>')
        if r["owner"]:
            g.append(f'<text x="{width - R + 6}" y="{cy + 4:.1f}" fill="{th["muted"]}" '
                     f'font-size="10">{esc(str(r["owner"])[:10])}</text>')
    # garis "hari ini"
    td = _pm_date(today) or datetime.now()
    if t0 <= td <= t1:
        xx = X(td)
        g.append(f'<line x1="{xx:.1f}" y1="{T - 8}" x2="{xx:.1f}" y2="{T + n * row_h}" '
                 f'stroke="{th["accent"]}" stroke-width="1.6" stroke-dasharray="5 4"/>')
        g.append(f'<text x="{xx:.1f}" y="{T + n * row_h + 16:.1f}" fill="{th["accent"]}" '
                 f'font-size="10.5" text-anchor="middle" font-weight="700">hari ini</text>')
    return _shell(width, H, head + "".join(g), th, transparent)

def progress(items: Sequence[Dict[str, Any]], title: str = "", subtitle: str = "",
             width: int = 640, th: Any = "dan", unit: str = "%", row_h: int = 34,
             show_target: bool = True, transparent: bool = False, loc: str = "id") -> str:
    """Bullet/progress bar untuk tracking progres: nilai vs target.

    items: [{'label','value'(0-100),'target'(0-100,opsional),'rag'(opsional)}]
    Warna otomatis: hijau bila >= target, kuning bila >= target-15, merah di bawahnya.
    """
    th = theme(th)
    rows = []
    for it in items or []:
        v = float(it.get("value", 0) or 0)
        tg = it.get("target")
        tg = float(tg) if tg is not None else None
        rag = it.get("rag")
        if rag is None and tg is not None:
            rag = "good" if v >= tg else ("warn" if v >= tg - 15 else "bad")
        rows.append({"label": str(it.get("label", "?")), "value": max(0.0, min(100.0, v)),
                     "target": tg, "rag": rag})
    head, top = _title_block(24, 18, title, subtitle, th)
    if not rows:
        return _shell(width, 120, head, th, transparent)
    n = len(rows)
    L, R = 150, 64
    T = top + 10
    H = T + n * row_h + 18
    pw = width - L - R
    g = []
    for p in (0, 25, 50, 75, 100):
        xx = L + p / 100 * pw
        g.append(f'<line x1="{xx:.1f}" y1="{T - 4}" x2="{xx:.1f}" y2="{T + n * row_h}" '
                 f'stroke="{th["grid"]}" stroke-width="1"/>')
        g.append(f'<text x="{xx:.1f}" y="{T + n * row_h + 14:.1f}" fill="{th["muted"]}" '
                 f'font-size="10" text-anchor="middle">{p}</text>')
    for i, r in enumerate(rows):
        y = T + i * row_h
        cy = y + row_h / 2
        col = _rag_color(r["rag"], th, th["accent"])
        g.append(f'<text x="{L - 10}" y="{cy + 4:.1f}" fill="{th["text"]}" font-size="11.5" '
                 f'text-anchor="end">{esc(r["label"][:24])}</text>')
        g.append(f'<rect x="{L}" y="{cy - 8:.1f}" width="{pw}" height="16" rx="8" '
                 f'fill="{th["grid"]}"/>')
        g.append(f'<rect x="{L}" y="{cy - 8:.1f}" width="{max(pw * r["value"] / 100, 3):.1f}" '
                 f'height="16" rx="8" fill="{col}"/>')
        if show_target and r["target"] is not None:
            tx = L + pw * r["target"] / 100
            g.append(f'<line x1="{tx:.1f}" y1="{cy - 11:.1f}" x2="{tx:.1f}" y2="{cy + 11:.1f}" '
                     f'stroke="{th["text"]}" stroke-width="2"/>')
        g.append(f'<text x="{L + pw + 8:.1f}" y="{cy + 4:.1f}" fill="{th["text"]}" '
                 f'font-size="11.5" font-weight="700">{r["value"]:.0f}{esc(unit)}</text>')
    return _shell(width, H, head + "".join(g), th, transparent)
