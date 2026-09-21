"""svg_charts — mesin grafik SVG zero-dependency (paket, lihat ADR-004).

Pemakaian tetap sama seperti dulu:
    import svg_charts as sc
    sc.bar([("IG", 4200)], title="Klik")

Modul: core (tema/util) · bars · lines · parts · stats · net · project ·
__main__ (galeri: python3 -m svg_charts).
"""
from .core import (FONT, THEMES, theme, esc, fmt_num, nice_ticks, _norm, _wrap, _shell,
                   _title_block, _legend, _xy_path, _arc, _pm_date, _rag_color)
from .bars import bar, hbar, stacked_bar
from .lines import line, area, sparkline
from .parts import donut, pie, funnel, radar
from .stats import scatter, heatmap, waterfall, gauge
from .net import fruchterman_reingold, network
from .project import gantt, progress

REGISTRY = {
    "bar": bar, "hbar": hbar, "stacked_bar": stacked_bar, "line": line, "area": area,
    "donut": donut, "pie": pie, "funnel": funnel, "radar": radar, "scatter": scatter,
    "heatmap": heatmap, "waterfall": waterfall, "gauge": gauge, "network": network,
    "sparkline": sparkline, "gantt": gantt, "progress": progress,
}

__all__ = ["REGISTRY", "FONT", "THEMES", "theme", "esc", "fmt_num", "nice_ticks",
           "bar", "hbar", "stacked_bar", "line", "area", "sparkline", "donut", "pie",
           "funnel", "radar", "scatter", "heatmap", "waterfall", "gauge", "network",
           "fruchterman_reingold", "gantt", "progress"]
