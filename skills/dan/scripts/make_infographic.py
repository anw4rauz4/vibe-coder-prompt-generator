#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_infographic.py — Data -> Infografik lengkap (sub-skill DAN #03).

Dua mode:
  AUTO  : input = analysis.json hasil dan_analytics.py
  SPEC  : input = JSON spesifikasi bebas (lihat templates/data-spec.example.json)

Output:
  * HTML self-contained (SVG inline + CSS inline, tanpa internet/CDN) -> bisa di-preview & di-print
  * opsional poster SVG tunggal (--svg) -> siap diubah ke PNG/PDF

PAKAI:
  python3 make_infographic.py ../../../deliverables/analysis.json
  python3 make_infographic.py spec.json --theme light --svg poster.svg --paper a3
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svg_charts as sc  # noqa: E402

CSS_TMPL = """
:root{--bg:%(bg)s;--panel:%(panel)s;--card:%(card)s;--text:%(text)s;--muted:%(muted)s;
--grid:%(grid)s;--accent:%(accent)s;--good:%(good)s;--warn:%(warn)s;--bad:%(bad)s;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font-family:%(font)s;-webkit-font-smoothing:antialiased;padding:26px}
.ig{max-width:%(maxw)spx;margin:0 auto}
.hdr{background:linear-gradient(135deg,var(--panel),var(--card));border:1px solid var(--grid);
border-radius:22px;padding:26px 28px;margin-bottom:18px;position:relative;overflow:hidden}
.hdr:after{content:"";position:absolute;right:-70px;top:-70px;width:240px;height:240px;
border-radius:50%%;background:var(--accent);opacity:.10}
.hdr h1{margin:0 0 6px;font-size:clamp(22px,3.1vw,34px);letter-spacing:-.7px;line-height:1.15}
.hdr p{margin:0;color:var(--muted);font-size:13.5px;max-width:76ch;line-height:1.5}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.chip{background:var(--bg);border:1px solid var(--grid);border-radius:999px;padding:5px 12px;
font-size:11.5px;color:var(--muted)}
.chip b{color:var(--text)}
.badge{position:absolute;right:26px;top:24px;text-align:center}
.badge .n{font-size:30px;font-weight:800;line-height:1;color:var(--accent)}
.badge .l{font-size:10px;color:var(--muted);letter-spacing:.9px;text-transform:uppercase}
h2.sec{font-size:13px;letter-spacing:1.6px;text-transform:uppercase;color:var(--muted);
margin:26px 0 12px;font-weight:700}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:12px}
.kpi{background:var(--card);border:1px solid var(--grid);border-radius:16px;padding:14px 16px}
.kpi .l{font-size:11px;color:var(--muted);letter-spacing:.4px;text-transform:uppercase}
.kpi .v{font-size:24px;font-weight:800;margin:5px 0 2px;letter-spacing:-.6px}
.kpi .d{font-size:11.5px;font-weight:600}
.up{color:var(--good)}.down{color:var(--bad)}.flat{color:var(--muted)}
.kpi svg{margin-top:6px;display:block}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}
.card{background:var(--card);border:1px solid var(--grid);border-radius:18px;padding:12px;
grid-column:span %(span)s;min-width:0;overflow:hidden}
.card svg{width:100%%;height:auto;display:block}
.card .note{font-size:11px;color:var(--muted);padding:2px 8px 6px;line-height:1.45}
.ins{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:12px}
.in{background:var(--card);border:1px solid var(--grid);border-left:4px solid var(--accent);
border-radius:14px;padding:14px 16px}
.in.good{border-left-color:var(--good)}.in.warn{border-left-color:var(--warn)}
.in.bad{border-left-color:var(--bad)}
.in h3{margin:0 0 6px;font-size:14px;letter-spacing:-.2px}
.in p{margin:0 0 8px;font-size:12.5px;color:var(--muted);line-height:1.55}
.in .act{font-size:12px;background:var(--bg);border:1px dashed var(--grid);border-radius:10px;
padding:8px 10px;color:var(--text);line-height:1.45}
.in .act:before{content:"Aksi  ";color:var(--accent);font-weight:700;font-size:10.5px;
letter-spacing:.8px;text-transform:uppercase}
ol.reco{margin:0;padding-left:20px;columns:2;column-gap:26px}
ol.reco li{font-size:12.5px;color:var(--text);margin-bottom:9px;line-height:1.5;break-inside:avoid}
table{width:100%%;border-collapse:collapse;font-size:12px}
th,td{text-align:left;padding:7px 9px;border-bottom:1px solid var(--grid)}
th{color:var(--muted);font-weight:600;font-size:10.5px;text-transform:uppercase;letter-spacing:.6px}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
.ftr{margin-top:26px;padding-top:14px;border-top:1px solid var(--grid);color:var(--muted);
font-size:11px;line-height:1.6}
@media(max-width:900px){.card{grid-column:span 12}ol.reco{columns:1}.badge{position:static;
text-align:left;margin-top:10px}}
@media print{body{padding:0;background:#fff}.card,.kpi,.in,.hdr{break-inside:avoid}}
"""


# --------------------------------------------------------------------- helpers

def money(v: float, cur: str, loc: str = "id") -> str:
    return f"{cur}{sc.fmt_num(v, loc)}"


def delta_html(d: Optional[float], suffix: str = "%") -> str:
    if d is None:
        return '<div class="d flat">—</div>'
    cls = "up" if d > 0.5 else ("down" if d < -0.5 else "flat")
    arrow = "▲" if d > 0.5 else ("▼" if d < -0.5 else "■")
    return f'<div class="d {cls}">{arrow} {abs(d):.1f}{suffix}</div>'


def kpi_card(label: str, value: str, d: Optional[float] = None,
             spark: Optional[Sequence[float]] = None, color: str = "#38BDF8",
             suffix: str = "%") -> str:
    sp = sc.sparkline(spark, 168, 38, color=color) if spark and len(spark) > 2 else ""
    return (f'<div class="kpi"><div class="l">{sc.esc(label)}</div>'
            f'<div class="v">{sc.esc(value)}</div>{delta_html(d, suffix)}{sp}</div>')


def card(inner: str, span: int = 4, note: str = "") -> str:
    n = f'<div class="note">{sc.esc(note)}</div>' if note else ""
    return f'<div class="card" style="grid-column:span {span}">{inner}{n}</div>'


# --------------------------------------------------------------------- AUTO mode

def build_auto(A: Dict[str, Any], th_name: str = "dan", loc: str = "id",
               title: str = "", subtitle: str = "") -> Dict[str, Any]:
    th = sc.theme(th_name)
    cur = A["meta"].get("currency", "Rp")
    k = A["kpi"]
    t = A.get("trend") or {}
    ts = (A.get("time") or {}).get("series") or {}
    labels = (A.get("time") or {}).get("labels") or []
    span_days = (A.get("time") or {}).get("span_days", 0)
    rng = f"{labels[0]} → {labels[-1]}" if labels else "—"

    title = title or f"Dashboard Analisa Marketing · {A['meta'].get('source', '')}"
    subtitle = subtitle or (
        f"{A['meta'].get('rows', 0):,} baris data · periode {rng} ({span_days} hari) · "
        f"ROAS {k.get('roas', 0):.2f}x · margin {k.get('margin', 0):.1f}%. "
        f"Disusun otomatis oleh DAN (Marketing Data Analyst).")

    chips = [f'<span class="chip">Sumber <b>{sc.esc(A["meta"].get("source", ""))}</b></span>',
             f'<span class="chip">Periode <b>{sc.esc(rng)}</b></span>',
             f'<span class="chip">Baris <b>{A["meta"].get("rows", 0):,}</b></span>',
             f'<span class="chip">Dibuat <b>{sc.esc(A["meta"].get("generated_at", ""))}</b></span>']
    badge = (f'<div class="badge"><div class="n">{A.get("health_score", 0):.0f}</div>'
             f'<div class="l">health score</div></div>') if A.get("health_score") else ""

    # ---- KPI cards
    g_pct = t.get("growth_pct_period")
    kpis = [
        kpi_card("Revenue", money(k.get("revenue", 0), cur, loc), g_pct, ts.get("revenue"), th["good"]),
        kpi_card("Ad Spend", money(k.get("spend", 0), cur, loc), None, ts.get("spend"), th["warn"]),
        kpi_card("ROAS", f"{k.get('roas', 0):.2f}x", None, ts.get("roas"), th["accent"], suffix=""),
        kpi_card("Konversi", sc.fmt_num(k.get("conversions", 0), loc), None, None, th["series"][2]),
        kpi_card("CTR", f"{k.get('ctr', 0):.2f}%", None, ts.get("ctr"), th["series"][1]),
        kpi_card("CVR", f"{k.get('cvr', 0):.2f}%", None, None, th["series"][3]),
        kpi_card("CPA", money(k.get("cpa", 0), cur, loc), None, None, th["bad"]),
        kpi_card("AOV", money(k.get("aov", 0), cur, loc), None, None, th["series"][4]),
        kpi_card("Klik", sc.fmt_num(k.get("clicks", 0), loc), None, None, th["series"][5]),
        kpi_card("Profit", money(k.get("profit", 0), cur, loc), None, None, th["good"]),
    ]

    cards: List[str] = []
    vf_money = lambda v: sc.fmt_num(v, loc)

    # ---- 1. tren + proyeksi
    if labels:
        cmp_: Dict[str, List[Optional[float]]] = {"Revenue": list(ts.get("revenue", []))}
        if t.get("ma3_revenue"):
            cmp_["MA-3"] = list(t["ma3_revenue"])
        xl = list(labels)
        f = A.get("forecast") or {}
        if f.get("revenue"):
            n = len(labels)
            cmp_["Revenue"] = list(ts.get("revenue", [])) + [None] * len(f["revenue"])
            cmp_["Proyeksi"] = [None] * (n - 1) + [ts.get("revenue", [None])[-1]] + list(f["revenue"])
            if "MA-3" in cmp_:
                cmp_["MA-3"] = cmp_["MA-3"] + [None] * len(f["revenue"])
            xl = xl + list(f.get("labels", []))
        # ringkas label kalau terlalu panjang
        step = max(1, len(xl) // 14)
        xl2 = [xl[i] if i % step == 0 else "" for i in range(len(xl))]
        note = ("Regresi linear least-square. Garis putus-putus = proyeksi, bukan angka aktual."
                if f.get("revenue") else "Garis MA-3 menghaluskan noise harian.")
        cards.append(card(sc.line(compare=cmp_, x_labels=xl2, title="Tren Revenue & Proyeksi",
                                subtitle=f"slope {t.get('slope_revenue', 0):+,.0f}/hari · "
                                         f"R² {t.get('r2_revenue', 0):.2f}",
                                width=880, height=380, th=th_name, loc=loc,
                                value_fmt=vf_money, area=True, markers=False),
                        span=8, note=note))
        cards.append(card(sc.gauge(A.get("health_score", 0), 100, "dari skor 100",
                                   title="Marketing Health Score", width=380, height=230,
                                   th=th_name, loc=loc, unit=""), span=4,
                        note="Komposit: ROAS (30) + CTR (25) + CVR (25) + arah tren (20)."))
    elif A.get("by_channel"):
        cards.append(card(sc.gauge(A.get("health_score", 0), 100, "dari skor 100",
                                   title="Marketing Health Score", width=380, height=230,
                                   th=th_name, loc=loc, unit=""), span=4))

    ch = A.get("by_channel") or []
    if ch:
        cards.append(card(sc.donut([(c["name"], c["kpi"]["revenue"]) for c in ch],
                                   title="Kontribusi Revenue per Channel",
                                   center_value=money(k.get("revenue", 0), cur, loc),
                                   center_label="total revenue", width=520, height=360,
                                   th=th_name, loc=loc), span=4))
        cards.append(card(sc.hbar([(c["name"], c["kpi"]["roas"]) for c in ch],
                                  title="ROAS per Channel", subtitle="target sehat ≥ 3,0x",
                                  width=520, height=360, th=th_name, loc=loc,
                                  value_fmt=lambda v: f"{v:.2f}x"), span=4,
                        note="ROAS < 1x = rugi. 1–3x = evaluasi. > 3x = kandidat scale-up."))
        cards.append(card(sc.hbar([(c["name"], c["kpi"]["cpa"]) for c in ch if c["kpi"]["cpa"]],
                                  title="CPA per Channel (makin kecil makin baik)",
                                  width=520, height=340, th=th_name, loc=loc,
                                  value_fmt=lambda v: money(v, cur, loc)), span=4))

    if A.get("funnel"):
        cards.append(card(sc.funnel(A["funnel"], title="Funnel Konversi",
                                    subtitle="impresi → klik → konversi", width=520, height=380,
                                    th=th_name, loc=loc), span=4,
                        note=(f"CTR {A.get('funnel_rates', {}).get('ctr', 0):.2f}% · "
                              f"CVR {A.get('funnel_rates', {}).get('cvr', 0):.2f}% · "
                              f"impresi→konversi {A.get('funnel_rates', {}).get('imp_to_conv', 0):.2f}%")))

    camp = A.get("by_campaign") or []
    if camp:
        top = camp[:8]
        cards.append(card(sc.hbar([(c["name"], c["kpi"]["revenue"]) for c in top],
                                  title="Top 8 Kampanye (Revenue)", width=620, height=380,
                                  th=th_name, loc=loc, value_fmt=vf_money), span=6))
        cards.append(card(sc.scatter([(c["kpi"]["spend"], c["kpi"]["roas"], c["name"]) for c in camp
                                      if c["kpi"]["spend"] > 0],
                                     title="Spend vs ROAS per Kampanye",
                                     subtitle="kuadran kanan-atas = pemenang", xlabel="Spend",
                                     ylabel="ROAS", width=620, height=380, th=th_name, loc=loc,
                                     trend=True), span=6,
                        note="Bubble di atas garis tren = efisiensi di atas rata-rata."))

    if A.get("by_weekday"):
        cards.append(card(sc.bar([(d["label"], d["value"]) for d in A["by_weekday"]],
                                 title="Revenue per Hari (dalam pekan)", width=620, height=330,
                                 th=th_name, loc=loc, value_fmt=vf_money), span=6))
    if A.get("by_hour"):
        cards.append(card(sc.bar([(d["label"], d["value"]) for d in A["by_hour"]],
                                 title="Revenue per Jam", width=620, height=330, th=th_name,
                                 loc=loc, value_fmt=vf_money), span=6))
    if A.get("by_weekday") and ch and len(ch) >= 3:
        axes = ["ROAS", "CTR", "CVR", "Volume", "Efisiensi"]
        mx = {a: max([_norm_metric(c, a) for c in ch] + [1e-9]) for a in axes}
        series = {}
        for c in ch[:5]:
            series[c["name"]] = [_norm_metric(c, a) / mx[a] * 10 for a in axes]
        cards.append(card(sc.radar(series, axes, title="Profil Kompetitif Channel",
                                   subtitle="skala 0–10 (ternormalisasi)", width=560, height=400,
                                   th=th_name), span=6,
                        note="Semakin luas poligon, semakin seimbang performa channel tersebut."))
    if A.get("pareto") and A["pareto"].get("items"):
        it = A["pareto"]["items"]
        cards.append(card(sc.line([(i["name"], i["cumulative"]) for i in it],
                                  title="Kurva Pareto (kumulatif %)",
                                  subtitle=A["pareto"]["concentration"]["note"],
                                  width=620, height=340, th=th_name, loc=loc,
                                  value_fmt=lambda v: f"{v:.0f}%", area=True), span=6))
    if A.get("correlations"):
        rows = "".join(
            f'<tr><td>{sc.esc(c["a"])}</td><td>{sc.esc(c["b"])}</td>'
            f'<td class="n">{c["r"]:+.2f}</td>'
            f'<td>{"kuat" if abs(c["r"]) >= .7 else "sedang" if abs(c["r"]) >= .4 else "lemah"} '
            f'{"positif" if c["r"] > 0 else "negatif"}</td></tr>'
            for c in A["correlations"])
        cards.append(card(
            f'<div style="padding:6px 8px"><div style="font-size:15px;font-weight:700;'
            f'margin-bottom:8px">Korelasi Antar Metrik</div><table><thead><tr><th>A</th><th>B</th>'
            f'<th class="n">r</th><th>Kekuatan</th></tr></thead><tbody>{rows}</tbody></table></div>',
            span=6, note="Pearson r pada time series harian. Korelasi ≠ kausalitas."))

    # ---- tabel channel
    tbl = ""
    if ch:
        body = "".join(
            f'<tr><td>{sc.esc(c["name"])}</td><td class="n">{money(c["kpi"]["spend"], cur, loc)}</td>'
            f'<td class="n">{money(c["kpi"]["revenue"], cur, loc)}</td>'
            f'<td class="n">{c["kpi"]["roas"]:.2f}x</td><td class="n">{c["kpi"]["ctr"]:.2f}%</td>'
            f'<td class="n">{c["kpi"]["cvr"]:.2f}%</td>'
            f'<td class="n">{money(c["kpi"]["cpa"], cur, loc)}</td>'
            f'<td class="n">{c["share_revenue"]:.1f}%</td></tr>' for c in ch)
        tbl = (f'<div class="card" style="grid-column:span 12"><div style="padding:6px 8px">'
               f'<div style="font-size:15px;font-weight:700;margin-bottom:10px">'
               f'Tabel Detail per Channel</div><table><thead><tr><th>Channel</th>'
               f'<th class="n">Spend</th><th class="n">Revenue</th><th class="n">ROAS</th>'
               f'<th class="n">CTR</th><th class="n">CVR</th><th class="n">CPA</th>'
               f'<th class="n">Share</th></tr></thead><tbody>{body}</tbody></table></div></div>')

    ins_html = "".join(
        f'<div class="in {sc.esc(i.get("severity", "info"))}"><h3>{sc.esc(i["title"])}</h3>'
        f'<p>{sc.esc(i["detail"])}</p>'
        + (f'<div class="act">{sc.esc(i["action"])}</div>' if i.get("action") else "")
        + '</div>' for i in A.get("insights", []))
    reco_html = "".join(f"<li>{sc.esc(r)}</li>" for r in A.get("recommendations", []))

    return {
        "title": title, "subtitle": subtitle, "chips": "".join(chips), "badge": badge,
        "kpis": "".join(kpis), "cards": "".join(cards) + tbl,
        "insights": ins_html, "reco": reco_html,
        "footer": (f"Metode: KPI = CTR klik/impresi · CVR konversi/klik · CPA spend/konversi · "
                   f"ROAS revenue/spend · AOV revenue/konversi. Tren = regresi linear least-square "
                   f"(R² dilampirkan). Anomali = z-score ≥ 2σ. Angka dibulatkan; korelasi bukan "
                   f"kausalitas. · Dibuat oleh <b>DAN</b> — Marketing Data Analyst &amp; "
                   f"Infographic Engine · {sc.esc(A['meta'].get('generated_at', ''))}"),
        "charts_count": len(cards),
    }


def _norm_metric(c: Dict[str, Any], axis: str) -> float:
    x = c["kpi"]
    return {"ROAS": x.get("roas", 0), "CTR": x.get("ctr", 0), "CVR": x.get("cvr", 0),
            "Volume": x.get("clicks", 0), "Efisiensi": (1 / x["cpa"] * 1000) if x.get("cpa") else 0
            }.get(axis, 0.0)


# --------------------------------------------------------------------- SPEC mode

def _value_fmt(spec_v: Any, loc: str):
    """Ubah hint string di spec menjadi fungsi format angka.

    'x' -> 2 desimal + 'x'   | '%' -> persen   | 'Rp' -> uang   | callable -> apa adanya
    """
    if spec_v is None:
        return None
    if callable(spec_v):
        return spec_v
    s = str(spec_v)
    if s == "x":
        return lambda v: f"{v:,.2f}x".replace(",", "#").replace(".", ",").replace("#", ".")
    if s == "%":
        return lambda v: f"{sc.fmt_num(v, loc)}%"
    return lambda v: f"{s}{sc.fmt_num(v, loc)}"


def _filter_kwargs(fn, kw: Dict[str, Any]) -> Dict[str, Any]:
    """Buang kwargs yang tidak diterima fungsi chart (agar spec toleran)."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):                      # pragma: no cover
        return kw
    params = sig.parameters
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return kw
    return {k: v for k, v in kw.items() if k in params}


def render_chart(spec: Dict[str, Any], th_name: str, loc: str) -> str:
    t = spec.get("chart", "bar")
    kw = dict(spec.get("options") or {})
    kw.setdefault("th", th_name)
    kw.setdefault("loc", loc)
    kw.setdefault("title", spec.get("title", ""))
    kw.setdefault("subtitle", spec.get("subtitle", ""))
    kw.setdefault("width", spec.get("width", 620))
    kw.setdefault("height", spec.get("height", 360))
    if "value_fmt" in kw:
        vf = _value_fmt(kw.pop("value_fmt"), loc)
        if vf:
            kw["value_fmt"] = vf
    d = spec.get("data")
    fn = sc.REGISTRY.get(t)
    if not fn:
        return f'<div class="note">Chart tidak dikenal: {sc.esc(t)}</div>'
    try:
        if t in ("stacked_bar",):
            return fn(d["categories"], d["series"], **_filter_kwargs(fn, kw))
        if t in ("radar",):
            kw.pop("loc", None)
            return fn(d["series"], d["axes"], **_filter_kwargs(fn, kw))
        if t in ("heatmap",):
            return fn(d["rows"], d["cols"], d["matrix"], **_filter_kwargs(fn, kw))
        if t in ("network",):
            return fn(d["nodes"], d["edges"], **_filter_kwargs(fn, kw))
        if t in ("scatter",):
            pts = d["points"] if isinstance(d, dict) else d
            return fn(pts, **_filter_kwargs(fn, kw))
        if t in ("gauge",):
            gkw = _filter_kwargs(fn, kw)
            gkw.pop("subtitle", None)
            gkw.pop("title", None)
            return fn(d["value"], d.get("vmax", 100), d.get("label", ""),
                      title=spec.get("title", ""), **gkw)
        if t in ("line", "area"):
            if isinstance(d, dict) and "series" in d:
                return fn(compare=d["series"], x_labels=d.get("labels"),
                          **_filter_kwargs(fn, kw))
            return fn(d, **_filter_kwargs(fn, kw))
        return fn(d, **_filter_kwargs(fn, kw))
    except Exception as e:  # pragma: no cover
        return f'<div class="note">Gagal render {sc.esc(t)}: {sc.esc(e)}</div>'


def build_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    th_name = spec.get("theme", "dan")
    loc = spec.get("locale", "id")
    cur = spec.get("currency", "Rp")
    cards, kpis, ins, reco = [], [], [], []
    for s in spec.get("sections", []):
        t = s.get("type", "chart")
        if t == "kpi":
            for it in s.get("items", []):
                v = it.get("value")
                if it.get("format") == "currency":
                    v = money(float(v or 0), it.get("currency", cur), loc)
                elif it.get("format") == "number":
                    v = sc.fmt_num(float(v or 0), loc)
                elif it.get("format") == "percent":
                    v = f"{float(v or 0):.2f}%"
                kpis.append(kpi_card(it.get("label", ""), str(v), it.get("delta"),
                                     it.get("spark"), it.get("color", "#38BDF8"),
                                     it.get("delta_suffix", "%")))
        elif t == "chart":
            cards.append(card(render_chart(s, th_name, loc), int(s.get("span", 6)),
                              s.get("note", "")))
        elif t == "html":
            cards.append(card(s.get("html", ""), int(s.get("span", 12)), s.get("note", "")))
        elif t == "insights":
            for i in s.get("items", []):
                ins.append(f'<div class="in {sc.esc(i.get("severity", "info"))}">'
                           f'<h3>{sc.esc(i.get("title", ""))}</h3><p>{sc.esc(i.get("detail", ""))}</p>'
                           + (f'<div class="act">{sc.esc(i["action"])}</div>' if i.get("action") else "")
                           + '</div>')
        elif t == "recommendations":
            reco.extend(f"<li>{sc.esc(r)}</li>" for r in s.get("items", []))
    return {
        "title": spec.get("title", "Infografik"), "subtitle": spec.get("subtitle", ""),
        "chips": "".join(f'<span class="chip">{sc.esc(c)}</span>' for c in spec.get("chips", [])),
        "badge": (f'<div class="badge"><div class="n">{spec["badge"]["value"]}</div>'
                  f'<div class="l">{sc.esc(spec["badge"].get("label", ""))}</div></div>'
                  if spec.get("badge") else ""),
        "kpis": "".join(kpis), "cards": "".join(cards),
        "insights": "".join(ins), "reco": "".join(reco),
        "footer": spec.get("footer", "Dibuat oleh DAN · Infographic Engine"),
        "charts_count": len(cards),
    }


# --------------------------------------------------------------------- assemble

PAPER_W = {"a4": 1180, "a3": 1580, "poster": 1980, "wide": 2400}


def to_html(B: Dict[str, Any], th_name: str = "dan", paper: str = "a3",
            lang: str = "id") -> str:
    th = sc.theme(th_name)
    maxw = PAPER_W.get(paper, 1580)
    css = CSS_TMPL % {**{k: th[k] for k in ("bg", "panel", "card", "text", "muted", "grid",
                                            "accent", "good", "warn", "bad")},
                      "font": sc.FONT, "maxw": maxw, "span": 4}
    import i18n
    sec = lambda cond, head, body: (
        f'<h2 class="sec">{head}</h2>{body}' if cond and body.strip() else "")
    return f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{sc.esc(B['title'])}</title><style>{css}</style></head><body><div class="ig">
<div class="hdr">{B['badge']}<h1>{sc.esc(B['title'])}</h1><p>{sc.esc(B['subtitle'])}</p>
<div class="chips">{B['chips']}</div></div>
{sec(B['kpis'], i18n.t('inf_kpi', lang), f'<div class="kpis">{B["kpis"]}</div>')}
{sec(B['cards'], i18n.t('inf_vis', lang), f'<div class="grid">{B["cards"]}</div>')}
{sec(B['insights'], i18n.t('inf_ins', lang), f'<div class="ins">{B["insights"]}</div>')}
{sec(B['reco'], i18n.t('inf_rec', lang), f'<ol class="reco">{B["reco"]}</ol>')}
<div class="ftr">{B['footer']}</div></div></body></html>"""


def to_poster_svg(B: Dict[str, Any], A: Optional[Dict[str, Any]], th_name: str = "dan",
                  paper: str = "a3") -> str:
    """Poster SVG tunggal: menyusun ulang chart secara vertikal (nested <svg>)."""
    th = sc.theme(th_name)
    W = PAPER_W.get(paper, 1580)
    blocks: List[str] = []
    y = 24
    blocks.append(f'<rect x="0" y="0" width="{W}" height="150" rx="20" fill="{th["panel"]}"/>')
    blocks.append(f'<text x="30" y="58" fill="{th["text"]}" font-size="30" font-weight="800">'
                  f'{sc.esc(B["title"])}</text>')
    for i, ln in enumerate(sc._wrap(B["subtitle"], int(W / 7.2))[:3]):
        blocks.append(f'<text x="30" y="{88 + i * 18}" fill="{th["muted"]}" font-size="13">{sc.esc(ln)}</text>')
    y = 180
    return _stack(blocks, y, W, th, B, A, th_name)


def _stack(blocks, y, W, th, B, A, th_name):
    """Helper poster: susun chart 2 kolom."""
    if not A:
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{y + 40}" viewBox="0 0 {W} {y + 40}">{"".join(blocks)}</svg>'
    cur = A["meta"].get("currency", "Rp")
    k = A["kpi"]
    cw = (W - 60 - 20) // 2
    items: List[str] = []
    if A.get("time"):
        ts = A["time"]["series"]
        items.append(sc.line([(l, v) for l, v in zip(A["time"]["labels"], ts.get("revenue", []))],
                             title="Tren Revenue", width=cw, height=320, th=th_name, area=True,
                             markers=False))
    if A.get("by_channel"):
        items.append(sc.donut([(c["name"], c["kpi"]["revenue"]) for c in A["by_channel"]],
                              title="Kontribusi Revenue", center_value=money(k["revenue"], cur),
                              center_label="total", width=cw, height=320, th=th_name))
        items.append(sc.hbar([(c["name"], c["kpi"]["roas"]) for c in A["by_channel"]],
                             title="ROAS per Channel", width=cw, height=320, th=th_name,
                             value_fmt=lambda v: f"{v:.2f}x"))
    if A.get("funnel"):
        items.append(sc.funnel(A["funnel"], title="Funnel Konversi", width=cw, height=320, th=th_name))
    if A.get("by_weekday"):
        items.append(sc.bar([(d["label"], d["value"]) for d in A["by_weekday"]],
                            title="Revenue per Hari", width=cw, height=300, th=th_name))
    items.append(sc.gauge(A.get("health_score", 0), 100, "dari 100", title="Health Score",
                          width=cw, height=230, th=th_name, unit=""))
    H = 340
    for i, svg in enumerate(items):
        col, row = i % 2, i // 2
        x = 30 + col * (cw + 20)
        yy = y + row * H
        blocks.append(f'<g transform="translate({x},{yy})">{svg}</g>')
    y += ((len(items) + 1) // 2) * H + 20
    blocks.append(f'<text x="30" y="{y}" fill="{th["muted"]}" font-size="11">'
                  f'{sc.esc(B["footer"])}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{y + 30}" '
            f'viewBox="0 0 {W} {y + 30}" font-family="{sc.FONT}">'
            f'<rect width="{W}" height="{y + 30}" fill="{th["bg"]}"/>{"".join(blocks)}</svg>')


# --------------------------------------------------------------------- main

def main(argv: Optional[Sequence[str]] = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    ap = argparse.ArgumentParser(description="DAN · Data → Infografik")
    ap.add_argument("json", help="analysis.json atau data-spec.json")
    ap.add_argument("--out", default="")
    ap.add_argument("--svg", default="")
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    ap.add_argument("--locale", default="id", choices=["id", "en"])
    ap.add_argument("--paper", default="a3", choices=list(PAPER_W))
    ap.add_argument("--lang", default="id", choices=["id", "en", "zh"])
    ap.add_argument("--title", default="")
    ap.add_argument("--subtitle", default="")
    a = ap.parse_args(argv)

    with open(a.json, encoding="utf-8") as f:
        data = json.load(f)
    spec_mode = "sections" in data
    A = None if spec_mode else data
    B = build_spec(data) if spec_mode else build_auto(data, a.theme, a.locale, a.title, a.subtitle)

    out = a.out or os.path.join(root, "deliverables",
                                "infographic_spec.html" if spec_mode else "infographic.html")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(to_html(B, a.theme, a.paper, a.lang))
    print(f"[DAN] mode={'SPEC' if spec_mode else 'AUTO'} charts={B['charts_count']} -> {out}")
    if a.svg:
        p = a.svg if os.path.isabs(a.svg) else os.path.join(root, a.svg)
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(to_poster_svg(B, A, a.theme, a.paper))
        print(f"[DAN] poster svg -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
