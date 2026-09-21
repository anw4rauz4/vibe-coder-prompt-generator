"""Inti svg_charts: tema, util format, dan helper pembentuk SVG.

Bagian dari paket svg_charts (lihat ADR-004). Helper ber-prefix "_" internal.
"""
from __future__ import annotations

import html as _html
import math
import random
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
        "'Helvetica Neue', Arial, 'Noto Sans', sans-serif")

# ----------------------------------------------------------------------------- theme

THEMES: Dict[str, Dict[str, Any]] = {
    "dan": {
        "bg": "#0F172A", "panel": "#111C33", "card": "#16233F",
        "text": "#F1F5F9", "muted": "#94A3B8", "grid": "#24344F",
        "accent": "#38BDF8", "good": "#34D399", "warn": "#FBBF24", "bad": "#FB7185",
        "series": ["#38BDF8", "#A78BFA", "#34D399", "#FBBF24", "#FB7185",
                   "#22D3EE", "#F472B6", "#84CC16", "#F97316", "#818CF8"],
    },
    "light": {
        "bg": "#FFFFFF", "panel": "#F8FAFC", "card": "#FFFFFF",
        "text": "#0F172A", "muted": "#64748B", "grid": "#E2E8F0",
        "accent": "#2563EB", "good": "#059669", "warn": "#D97706", "bad": "#DC2626",
        "series": ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626",
                   "#0891B2", "#DB2777", "#65A30D", "#EA580C", "#4F46E5"],
    },
    "neon": {
        "bg": "#07070F", "panel": "#0D0D1A", "card": "#12122A",
        "text": "#EAF6FF", "muted": "#7C86A8", "grid": "#1E2140",
        "accent": "#00E5FF", "good": "#00FF9C", "warn": "#FFD400", "bad": "#FF3D71",
        "series": ["#00E5FF", "#FF3D71", "#00FF9C", "#FFD400", "#A855F7",
                   "#FF8A00", "#4ADE80", "#F472B6", "#38BDF8", "#FACC15"],
    },
    "mono": {
        "bg": "#FFFFFF", "panel": "#F4F4F5", "card": "#FFFFFF",
        "text": "#18181B", "muted": "#71717A", "grid": "#E4E4E7",
        "accent": "#18181B", "good": "#3F3F46", "warn": "#71717A", "bad": "#A1A1AA",
        "series": ["#18181B", "#3F3F46", "#52525B", "#71717A", "#A1A1AA",
                   "#C4C4CB", "#27272A", "#5A5A63", "#8B8B94", "#D4D4D8"],
    },
}

def theme(name: str | Dict[str, Any] = "dan") -> Dict[str, Any]:
    if isinstance(name, dict):
        base = dict(THEMES["dan"])
        base.update(name)
        return base
    return dict(THEMES.get(name, THEMES["dan"]))


# ----------------------------------------------------------------------------- utils

def esc(s: Any) -> str:
    return _html.escape("" if s is None else str(s), quote=True)

def fmt_num(v: float, loc: str = "id", dec: Optional[int] = None,
            prefix: str = "", suffix: str = "", compact: bool = True) -> str:
    """Format angka. loc='id' -> 1.234,5 | loc='en' -> 1,234.5"""
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    v = float(v)
    sign = "-" if v < 0 else ""
    av = abs(v)
    unit = ""
    if compact and av >= 1_000_000_000_000:
        av, unit = av / 1_000_000_000_000, "T"
    elif compact and av >= 1_000_000_000:
        av, unit = av / 1_000_000_000, "M"  # miliar (id) / billion
    elif compact and av >= 1_000_000:
        av, unit = av / 1_000_000, "jt" if loc == "id" else "M"
    elif compact and av >= 10_000:
        av, unit = av / 1_000, "rb" if loc == "id" else "K"

    if dec is None:
        if unit:
            dec = 1 if av < 100 else 0
        else:
            dec = 0 if abs(av - round(av)) < 1e-9 else (2 if av < 100 else 1)
    s = f"{av:,.{dec}f}"
    if loc == "id":
        s = s.replace(",", "#").replace(".", ",").replace("#", ".")
    return f"{sign}{prefix}{s}{unit}{suffix}"

def nice_ticks(lo: float, hi: float, n: int = 5) -> List[float]:
    """Sumbu angka yang 'cantik' (1/2/2.5/5 x 10^k)."""
    if hi is None or lo is None:
        return [0, 1]
    if hi - lo < 1e-12:
        if abs(hi) < 1e-12:
            lo, hi = 0.0, 1.0
        else:
            pad = abs(hi) * 0.25
            lo, hi = lo - pad, hi + pad
    span = hi - lo
    raw = span / max(1, n)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw / mag <= m:
            step = m * mag
            break
    else:
        step = 10 * mag
    start = math.floor(lo / step) * step
    ticks: List[float] = []
    t = start
    # pastikan ticks selalu mencakup [lo, hi]; tanpa ini sumbu bisa lebih kecil
    # dari data maksimum sehingga bar/label tergambar di luar area plot.
    while t <= hi + 1e-9 and len(ticks) < 60:
        ticks.append(round(t, 12))
        t += step
    if not ticks or ticks[-1] < hi - 1e-9:
        ticks.append(round(t, 12))
    return ticks

def _norm(data: Any) -> List[Tuple[str, float]]:
    """Terima banyak bentuk input -> [(label, value), ...]"""
    out: List[Tuple[str, float]] = []
    if data is None:
        return out
    if isinstance(data, dict):
        items = data.items()
    else:
        items = list(data)
    for it in items:
        if isinstance(it, dict):
            lab = it.get("label", it.get("name", it.get("k", "")))
            val = it.get("value", it.get("v", it.get("y", 0)))
        elif isinstance(it, (list, tuple)):
            lab = it[0]
            val = it[1] if len(it) > 1 else 0
        else:
            lab, val = str(it), 0
        try:
            val = float(val)
        except (TypeError, ValueError):
            val = 0.0
        out.append((str(lab), val))
    return out

def _wrap(text: str, width: int) -> List[str]:
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]

def _shell(w: int, h: int, inner: str, th: Dict[str, Any],
           transparent: bool = False, radius: int = 18,
           defs: str = "") -> str:
    bg = "none" if transparent else th["bg"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{FONT}" role="img">'
            f'<defs>{defs}</defs>'
            f'<rect width="{w}" height="{h}" rx="{radius}" fill="{bg}"/>{inner}</svg>')

def _title_block(x: int, y: int, title: Optional[str], subtitle: Optional[str],
                 th: Dict[str, Any]) -> Tuple[str, int]:
    if not title and not subtitle:
        return "", y
    parts, dy = [], 0
    if title:
        parts.append(f'<text x="{x}" y="{y + 17}" fill="{th["text"]}" '
                     f'font-size="17" font-weight="700" letter-spacing="-0.2">{esc(title)}</text>')
        dy += 24
    if subtitle:
        parts.append(f'<text x="{x}" y="{y + dy + 14}" fill="{th["muted"]}" '
                     f'font-size="12">{esc(subtitle)}</text>')
        dy += 20
    return "".join(parts), y + dy + 6

def _legend(items: Sequence[str], x: int, y: int, th: Dict[str, Any],
            max_w: int = 520) -> Tuple[str, int]:
    """Legenda horizontal, auto-wrap. Mengembalikan (svg, tinggi terpakai)."""
    if not items:
        return "", 0
    out, cx, cy = [], x, y
    for i, it in enumerate(items):
        col = th["series"][i % len(th["series"])]
        est = 18 + min(len(str(it)) * 6.6, max_w * 0.5) + 16
        if cx + est > x + max_w and cx > x:
            cx = x
            cy += 20
        out.append(f'<rect x="{cx:.0f}" y="{cy - 8:.0f}" width="10" height="10" rx="3" fill="{col}"/>')
        out.append(f'<text x="{cx + 16:.0f}" y="{cy + 1:.0f}" fill="{th["muted"]}" '
                   f'font-size="11.5">{esc(it)}</text>')
        cx += est
    return "".join(out), (cy - y) + 16


# ----------------------------------------------------------------------------- BAR

def _xy_path(pts: Sequence[Tuple[float, float]], smooth: float = 0.0) -> str:
    if not pts:
        return ""
    if smooth <= 0 or len(pts) < 3:
        return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)
    d = [f"M {pts[0][0]:.2f} {pts[0][1]:.2f}"]
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6 * smooth, p1[1] + (p2[1] - p0[1]) / 6 * smooth)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6 * smooth, p2[1] - (p3[1] - p1[1]) / 6 * smooth)
        d.append(f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {p2[0]:.2f} {p2[1]:.2f}")
    return " ".join(d)

def _arc(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    large = 1 if (a1 - a0) > math.pi else 0
    return f"M {x0:.2f} {y0:.2f} A {r:.2f} {r:.2f} 0 {large} 1 {x1:.2f} {y1:.2f}"

def _pm_date(v: Any) -> Optional[datetime]:
    """Parse tanggal longgar untuk gantt: ISO, 'YYYY-MM-DD', datetime, atau day-offset int."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    if isinstance(v, (int, float)):
        return datetime(1970, 1, 1) + timedelta(days=int(v))
    s = str(v).strip()
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s[:10], f)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s[:10])
    except Exception:
        return None

def _rag_color(rag: Any, th: Dict[str, Any], default: Optional[str] = None) -> str:
    m = {"green": th["good"], "good": th["good"], "on": th["good"], "done": th["good"],
         "selesai": th["good"],
         "yellow": th["warn"], "warn": th["warn"], "warning": th["warn"],
         "risiko": th["warn"], "waspada": th["warn"],
         "red": th["bad"], "bad": th["bad"], "critical": th["bad"], "kritis": th["bad"],
         "terlambat": th["bad"],
         "grey": th["muted"], "gray": th["muted"], "muted": th["muted"],
         "tunda": th["muted"], "hold": th["muted"]}
    if rag is None:
        return default or th["accent"]
    return m.get(str(rag).lower(), default or th["accent"])
