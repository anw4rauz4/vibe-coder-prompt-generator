#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dan_analytics.py — Engine Analis Data Marketing (sub-skill DAN #01).

Zero-dependency (stdlib saja). Membaca CSV/XLSX mentah dari platform ads,
menormalisasi nama kolom (ID/EN), menghitung KPI, agregasi, tren, anomali,
funnel, pareto, korelasi, lalu menghasilkan:
  * analysis.json  -> siap dipakai make_infographic.py
  * analysis.md    -> laporan insight berbahasa Indonesia
  * summary.csv    -> tabel agregat

PAKAI:
  python3 dan_analytics.py ../../../../data/sample_campaign.csv
  python3 dan_analytics.py data.csv --out a.json --report a.md --currency Rp --forecast 4

Kolom yang dikenali (alias fleksibel, case-insensitive):
  date/tanggal, channel/kanal/platform, campaign/kampanye, ad/iklan,
  impressions/impression/tayangan, clicks/klik, spend/biaya/cost,
  conversions/konversi, revenue/pendapatan/omzet, engagements/engagement,
  video_views/views, ctr, cpc, roas
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------- parsing

ALIASES: Dict[str, List[str]] = {
    "date": ["date", "tanggal", "tgl", "day", "hari", "start_date", "waktu", "time"],
    "channel": ["channel", "kanal", "platform", "source", "sumber", "media", "placement"],
    "campaign": ["campaign", "kampanye", "campaign_name", "nama_kampanye", "adset", "ad_set"],
    "ad": ["ad", "iklan", "ad_name", "creative", "kreatif", "materi"],
    "impressions": ["impressions", "impression", "impr", "tayangan", "impresi", "reach", "jangkauan"],
    "clicks": ["clicks", "click", "klik", "taps", "link_clicks"],
    "spend": ["spend", "cost", "biaya", "anggaran", "amount_spent", "total_cost", "pengeluaran"],
    "conversions": ["conversions", "conversion", "konversi", "conv", "purchases", "transaksi", "sales_count", "orders", "leads"],
    "revenue": ["revenue", "pendapatan", "omzet", "omset", "sales", "nilai_penjualan", "purchase_value", "gmv"],
    "engagements": ["engagements", "engagement", "interaksi", "likes", "suka", "comments", "shares", "total_engagements"],
    "views": ["views", "video_views", "penonton", "tayangan_video", "watch_time"],
}

NUMERIC = ["impressions", "clicks", "spend", "conversions", "revenue", "engagements", "views"]

_MONEY_NOISE = re.compile(r"(rp|idr|usd|\$|€|£|rs|\.|\s)", re.I)

# "auto" | "id" | "en"  -> cara membaca pemisah ribuan/desimal yang ambigu.
NUM_LOCALE = "auto"

_MULT = {"jt": 1e6, "juta": 1e6, "ribu": 1e3, "k": 1e3, "rb": 1e3, "m": 1e6,
         "miliar": 1e9, "milliar": 1e9, "milyar": 1e9, "b": 1e9,
         "t": 1e12, "triliun": 1e12, "bn": 1e9}


def parse_number(v: Any, loc: Optional[str] = None) -> Optional[float]:
    """Parse angka lintas-format.

    Didukung: 1234 | '1.234.567' (ID) | '1,234,567' (EN) | '1.234,56' (ID)
              '1,234.56' (EN) | 'Rp 14.397.036' | '12,5%' | '3.4 jt' | '12K' | '1.2M'
    Aturan ambiguitas (loc='auto'):
      * ada titik DAN koma      -> pemisah terakhir adalah desimal
      * hanya titik, >=2 titik  -> titik = ribuan (ID)
      * hanya titik, 1 titik dgn tepat 3 angka di belakang -> ribuan (ID), kecuali loc='en'
      * hanya koma, >=2 koma grup 3 digit / 1 koma dgn tepat 3 digit -> koma = ribuan (EN)
      * hanya koma, selain itu -> koma = desimal (ID)
    """
    loc = (loc or NUM_LOCALE or "auto").lower()
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s or s.lower() in {"-", "na", "n/a", "null", "none", "nan"}:
        return None
    pct = s.endswith("%")
    if pct:
        s = s[:-1].strip()
    s = s.replace("\u00a0", " ").strip()
    s = re.sub(r"(?i)\b(rp|idr|usd|eur|sgd|myr)\b", "", s).strip()   # "Rp 1.000"
    s = re.sub(r"(?i)^(rp|idr|usd|eur|sgd|myr)", "", s).strip()      # "Rp1.000"
    s = s.replace("$", "").replace("€", "").replace("£", "")
    mult = 1.0
    m = re.search(r"(?i)\s?(jt|juta|miliar|milliar|milyar|ribu|rb|triliun|bn|[kmbt])\s*$", s)
    if m and len(s) > len(m.group(1)):
        mult = _MULT.get(m.group(1).lower(), 1.0)
        s = s[:m.start()].strip()
    s = s.replace(" ", "")
    if not s:
        return None

    has_c, has_d = "," in s, "." in s
    if has_c and has_d:
        if s.rfind(",") > s.rfind("."):          # 1.234,56  -> ID
            s = s.replace(".", "").replace(",", ".")
        else:                                     # 1,234.56  -> EN
            s = s.replace(",", "")
    elif has_d:
        parts = s.split(".")
        if len(parts) > 2:                        # 1.234.567 -> ID
            s = s.replace(".", "")
        elif len(parts) == 2 and len(parts[1]) == 3 and loc != "en":
            s = s.replace(".", "")                # 14.397    -> ID (asumsi ribuan)
    elif has_c:
        parts = s.split(",")
        if len(parts) > 2 and all(len(p) == 3 for p in parts[1:]):
            s = s.replace(",", "")                # 1,234,567 -> EN
        elif len(parts) == 2 and len(parts[1]) == 3 and loc != "id":
            s = s.replace(",", "")                # 103,241   -> EN (asumsi ribuan)
        elif len(parts) == 2 and loc == "en":
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")               # 12,5      -> ID desimal
    try:
        val = float(s) * mult
    except ValueError:
        return None
    return val / 100.0 if pct else val


def parse_date(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    s = str(v).strip()
    if not s:
        return None
    fmts = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y",
            "%d %b %Y", "%d %B %Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
            "%Y%m%d", "%b %d, %Y", "%d.%m.%Y"]
    for f in fmts:
        try:
            return datetime.strptime(s[:19] if "T" in s else s, f)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00").split("+")[0])
    except Exception:
        return None


def map_columns(header: Sequence[str]) -> Dict[str, str]:
    """Peta: field kanonik -> nama kolom asli di file."""
    out: Dict[str, str] = {}
    norm = {h.strip().lower().replace(" ", "_"): h for h in header if h}
    for canon, alts in ALIASES.items():
        for a in alts:
            if a in norm:
                out[canon] = norm[a]
                break
        if canon in out:
            continue
        for k, orig in norm.items():                      # fallback substring
            if any(a in k for a in alts):
                out[canon] = orig
                break
    return out


# --------------------------------------------------------------------- metrics

def safe_div(a: float, b: float) -> float:
    return (a / b) if b else 0.0


def kpis(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    s = lambda k: sum(float(r.get(k) or 0) for r in rows)
    imp, clk, spd, cnv, rev = s("impressions"), s("clicks"), s("spend"), s("conversions"), s("revenue")
    eng, vw = s("engagements"), s("views")
    return {
        "impressions": imp, "clicks": clk, "spend": spd, "conversions": cnv,
        "revenue": rev, "engagements": eng, "views": vw,
        "ctr": safe_div(clk, imp) * 100,
        "cpc": safe_div(spd, clk),
        "cpm": safe_div(spd, imp) * 1000,
        "cvr": safe_div(cnv, clk) * 100,
        "cpa": safe_div(spd, cnv),
        "roas": safe_div(rev, spd),
        "aov": safe_div(rev, cnv),
        "profit": rev - spd,
        "margin": safe_div(rev - spd, rev) * 100,
        "engagement_rate": safe_div(eng, imp) * 100,
        "cost_per_engagement": safe_div(spd, eng),
        "rows": len(rows),
    }


def group_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
    g: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in rows:
        k = r.get(key)
        if k is None or k == "":
            k = "(kosong)"
        g[str(k)].append(r)
    return dict(g)


def linreg(ys: Sequence[float]) -> Tuple[float, float, float]:
    """Regresi linear sederhana -> (slope, intercept, r2)."""
    n = len(ys)
    if n < 2:
        return 0.0, (ys[0] if ys else 0.0), 0.0
    xs = list(range(n))
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs) or 1
    slope = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den
    inter = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys) or 1
    ss_res = sum((ys[i] - (slope * xs[i] + inter)) ** 2 for i in range(n))
    return slope, inter, max(0.0, 1 - ss_res / ss_tot)


def moving_avg(ys: Sequence[float], w: int = 3) -> List[float]:
    out = []
    for i in range(len(ys)):
        lo = max(0, i - w + 1)
        chunk = ys[lo:i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def anomalies(ys: Sequence[float], labels: Sequence[str], k: float = 2.0) -> List[Dict[str, Any]]:
    if len(ys) < 5:
        return []
    mu, sd = st.mean(ys), (st.pstdev(ys) or 1e-9)
    out = []
    for lab, v in zip(labels, ys):
        z = (v - mu) / sd
        if abs(z) >= k:
            out.append({"label": lab, "value": v, "z": round(z, 2),
                        "direction": "spike" if z > 0 else "drop",
                        "deviation_pct": round((v - mu) / (mu or 1) * 100, 1)})
    return sorted(out, key=lambda d: -abs(d["z"]))


def corr(a: Sequence[float], b: Sequence[float]) -> float:
    n = min(len(a), len(b))
    if n < 3:
        return 0.0
    ma, mb = st.mean(a[:n]), st.mean(b[:n])
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((a[i] - ma) ** 2 for i in range(n))) or 1
    db = math.sqrt(sum((b[i] - mb) ** 2 for i in range(n))) or 1
    return num / (da * db)


def pareto(rows: List[Dict[str, Any]], key: str, metric: str = "revenue",
           top: int = 8) -> Dict[str, Any]:
    g = {k: sum(float(r.get(metric) or 0) for r in v) for k, v in group_by(rows, key).items()}
    items = sorted(g.items(), key=lambda x: -x[1])
    tot = sum(v for _, v in items) or 1
    cum, out = 0.0, []
    for name, v in items[:top]:
        cum += v
        out.append({"name": name, "value": round(v, 2), "share": round(v / tot * 100, 2),
                    "cumulative": round(cum / tot * 100, 2)})
    n80 = next((i + 1 for i, o in enumerate(out) if o["cumulative"] >= 80), len(out))
    return {"metric": metric, "key": key, "items": out,
            "concentration": {"top_n": n80, "covers_pct": 80,
                              "note": f"{n80} dari {len(items)} {key} menyumbang 80% {metric}"}}


# --------------------------------------------------------------------- loader

def load_rows(path: str) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    ext = os.path.splitext(path)[1].lower()
    if ext in {".xlsx", ".xlsm"}:
        try:
            from openpyxl import load_workbook
        except ImportError:
            sys.exit("Butuh openpyxl untuk XLSX: pip install openpyxl")
        wb = load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        header = [str(c) if c is not None else "" for c in next(it)]
        raw = [dict(zip(header, r)) for r in it if any(c is not None for c in r)]
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except csv.Error:
                dialect = csv.excel
            rd = csv.DictReader(f, dialect=dialect)
            header = rd.fieldnames or []
            raw = [r for r in rd]
    cmap = map_columns(header)
    if not cmap:
        sys.exit(f"Tidak ada kolom yang dikenali di {path}. Header: {header}")
    rows: List[Dict[str, Any]] = []
    for r in raw:
        o: Dict[str, Any] = {}
        for canon, col in cmap.items():
            v = r.get(col)
            o[canon] = parse_date(v) if canon == "date" else (
                parse_number(v) if canon in NUMERIC else (str(v).strip() if v is not None else None))
        for k in NUMERIC:
            o.setdefault(k, 0.0)
            if o[k] is None:
                o[k] = 0.0
        rows.append(o)
    return rows, cmap


# --------------------------------------------------------------------- insight

def r0(x: float) -> float:
    return round(float(x or 0), 2)


def build_insights(A: Dict[str, Any], cur: str) -> List[Dict[str, str]]:
    ins: List[Dict[str, str]] = []
    k = A["kpi"]

    def add(t: str, d: str, sev: str = "info", act: str = ""):
        ins.append({"title": t, "detail": d, "severity": sev, "action": act})

    if k["roas"]:
        sev = "good" if k["roas"] >= 3 else ("warn" if k["roas"] >= 1 else "bad")
        add("ROAS keseluruhan {:.2f}x".format(k["roas"]),
            f"Setiap {cur}1 biaya iklan menghasilkan {cur}{k['roas']:.2f} pendapatan. "
            f"Margin kotor {k['margin']:.1f}%.", sev,
            "Scale channel dengan ROAS > 4x, pause yang < 1x." if sev != "good" else
            "Pertahankan; naikkan budget 15-20% bertahap pada kampanye terbaik.")
    if k["ctr"]:
        sev = "good" if k["ctr"] >= 2 else ("warn" if k["ctr"] >= 1 else "bad")
        add(f"CTR {k['ctr']:.2f}%", f"Benchmark umum paid social 0,9-2%. Posisi Anda "
            f"{'di atas' if k['ctr'] >= 2 else 'di sekitar/bawah'} rata-rata industri.", sev,
            "Refresh creative & uji 3 hook baru bila CTR < 1%." if sev == "bad" else
            "Dokumentasikan pola creative pemenang ke dalam swipe file.")
    if k["cvr"]:
        sev = "good" if k["cvr"] >= 3 else ("warn" if k["cvr"] >= 1 else "bad")
        add(f"Conversion rate {k['cvr']:.2f}%",
            f"Dari {k['clicks']:,.0f} klik menghasilkan {k['conversions']:,.0f} konversi.", sev,
            "Perbaiki landing page: kecepatan, social proof, dan form yang lebih pendek."
            if sev != "good" else "Lakukan A/B test untuk mendorong CVR lebih tinggi.")
    if k["cpa"] and k["aov"]:
        ratio = k["aov"] / k["cpa"] if k["cpa"] else 0
        add(f"CPA {cur}{k['cpa']:,.0f} vs AOV {cur}{k['aov']:,.0f}",
            f"Rasio AOV/CPA = {ratio:.2f}x. {'Sehat' if ratio >= 3 else 'Perlu perhatian'} "
            f"(aturan praktis: minimal 3x).",
            "good" if ratio >= 3 else ("warn" if ratio >= 1.5 else "bad"),
            "Naikkan AOV lewat bundling/upsell, atau turunkan CPA lewat audience refinement.")

    ch = A.get("by_channel", [])
    if len(ch) >= 2:
        best = max(ch, key=lambda d: d["kpi"]["roas"])
        worst = min(ch, key=lambda d: d["kpi"]["roas"])
        add(f"Channel terbaik: {best['name']} (ROAS {best['kpi']['roas']:.2f}x)",
            f"Kontribusi revenue {best['share_revenue']:.1f}%. Terlemah: {worst['name']} "
            f"(ROAS {worst['kpi']['roas']:.2f}x, spend {cur}{worst['kpi']['spend']:,.0f}).",
            "good" if best["kpi"]["roas"] >= 3 else "warn",
            f"Realokasi 20-30% budget dari {worst['name']} ke {best['name']} dan uji selama 14 hari.")

    t = A.get("trend", {})
    if t.get("slope_revenue") is not None:
        pct = t["growth_pct_period"]
        add("Tren pendapatan " + ("naik" if t["slope_revenue"] > 0 else "turun"),
            f"Slope {t['slope_revenue']:+,.0f}/periode, R²={t['r2_revenue']:.2f}, "
            f"perubahan periode terakhir {pct:+.1f}%.",
            "good" if t["slope_revenue"] > 0 else "bad",
            "Proyeksi " + str(A.get("forecast", {}).get("horizon", 0)) +
            " periode ke depan: " + ", ".join(f"{v:,.0f}" for v in A.get("forecast", {}).get("revenue", [])) + "."
            if A.get("forecast") else "Jaga momentum dengan kalender konten konsisten.")

    an = A.get("anomalies", [])
    if an:
        a = an[0]
        add(f"Anomali: {a['label']} ({a['direction']})",
            f"Nilai {a['value']:,.0f}, menyimpang {a['deviation_pct']:+.1f}% dari rata-rata "
            f"(z={a['z']}). Total {len(an)} titik anomali terdeteksi.",
            "warn" if a["direction"] == "spike" else "bad",
            "Cek penyebab: promo, viral, tracking error, atau perubahan bidding.")

    p = A.get("pareto", {}).get("concentration") if A.get("pareto") else None
    if p:
        add("Konsentrasi Pareto", p["note"], "info",
            "Fokus optimasi pada sedikit item teratas; sisanya dievaluasi ulang tiap bulan.")

    dow = A.get("by_weekday", [])
    if dow:
        b = max(dow, key=lambda d: d["value"])
        w = min(dow, key=lambda d: d["value"])
        add(f"Hari terbaik: {b['label']}", f"Revenue {cur}{b['value']:,.0f} "
            f"({b['share']:.1f}% total). Terlemah: {w['label']} ({cur}{w['value']:,.0f}).",
            "info", f"Jadwalkan kampanye besar & posting utama pada {b['label']}.")

    c = A.get("correlations", [])
    if c:
        top = c[0]
        add(f"Korelasi terkuat: {top['a']} ↔ {top['b']} (r={top['r']:.2f})",
            "Hubungan linear " + ("kuat" if abs(top["r"]) >= 0.7 else "sedang") +
            ". Korelasi bukan kausalitas — validasi dengan eksperimen.",
            "info", f"Uji dengan menaikkan {top['a']} pada 1 kampanye selama 7 hari.")
    return ins


# --------------------------------------------------------------------- main

def analyze(path: str, currency: str = "Rp", forecast_n: int = 3,
            date_col: str = "date") -> Dict[str, Any]:
    rows, cmap = load_rows(path)
    if not rows:
        sys.exit("File kosong / tidak ada baris data.")
    K = kpis(rows)
    A: Dict[str, Any] = {
        "meta": {"source": os.path.basename(path), "generated_at": datetime.now().isoformat(timespec="seconds"),
                 "rows": len(rows), "columns_mapped": cmap, "currency": currency},
        "kpi": {k: r0(v) for k, v in K.items()},
    }

    # --- per channel / campaign
    def agg(key: str, metric: str = "revenue") -> List[Dict[str, Any]]:
        tot_rev = K["revenue"] or 1
        out = []
        for name, rs in group_by(rows, key).items():
            kk = kpis(rs)
            out.append({"name": name, "rows": len(rs),
                        "share_revenue": r0(kk["revenue"] / tot_rev * 100),
                        "kpi": {x: r0(v) for x, v in kk.items()}})
        return sorted(out, key=lambda d: -d["kpi"][metric])

    if "channel" in cmap:
        A["by_channel"] = agg("channel")
    if "campaign" in cmap:
        A["by_campaign"] = agg("campaign")[:15]
        A["campaign_count"] = len(group_by(rows, "campaign"))

    # --- time series
    dated = [r for r in rows if r.get("date")]
    if dated:
        by_day: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in dated:
            by_day[r["date"].strftime("%Y-%m-%d")].append(r)
        days = sorted(by_day)
        series = {m: [sum(float(x.get(m) or 0) for x in by_day[d]) for d in days] for m in NUMERIC}
        series["roas"] = [safe_div(series["revenue"][i], series["spend"][i]) for i in range(len(days))]
        series["ctr"] = [safe_div(series["clicks"][i], series["impressions"][i]) * 100 for i in range(len(days))]
        A["time"] = {"labels": days, "series": {k: [r0(v) for v in vs] for k, vs in series.items()},
                     "span_days": (parse_date(days[-1]) - parse_date(days[0])).days + 1 if len(days) > 1 else 1}
        sl, ic, r2 = linreg(series["revenue"])
        growth = ((series["revenue"][-1] / series["revenue"][0] - 1) * 100
                  if series["revenue"] and series["revenue"][0] else 0.0)
        ma = moving_avg(series["revenue"], 3)
        A["trend"] = {"slope_revenue": r0(sl), "intercept": r0(ic), "r2_revenue": r0(r2),
                      "growth_pct_period": r0(growth), "ma3_revenue": [r0(v) for v in ma],
                      "direction": "up" if sl > 0 else "down"}
        if forecast_n > 0 and len(days) >= 3:
            n = len(days)
            fut = [max(0.0, sl * (n + i) + ic) for i in range(1, forecast_n + 1)]
            last = parse_date(days[-1])
            A["forecast"] = {"horizon": forecast_n,
                             "labels": [(last + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, forecast_n + 1)],
                             "revenue": [r0(v) for v in fut],
                             "spend": [r0(max(0.0, linreg(series["spend"])[0] * (n + i) + linreg(series["spend"])[1]))
                                       for i in range(1, forecast_n + 1)],
                             "method": "linear regression (least squares)",
                             "ci_note": "Estimasi titik; untuk interval kepercayaan gunakan residual std × 1,96."}
        A["anomalies"] = anomalies(series["revenue"], days)

        # day of week
        dow_names = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        dw: Dict[int, float] = defaultdict(float)
        for i, d in enumerate(days):
            dw[parse_date(d).weekday()] += series["revenue"][i]
        tot = sum(dw.values()) or 1
        A["by_weekday"] = [{"label": dow_names[i], "value": r0(dw[i]), "share": r0(dw[i] / tot * 100)}
                           for i in range(7)]
        # hour of day (jika ada jam)
        hours: Dict[int, float] = defaultdict(float)
        for r in dated:
            if r["date"].hour or r["date"].minute:
                hours[r["date"].hour] += float(r.get("revenue") or 0)
        if len(hours) > 1:
            tot_h = sum(hours.values()) or 1
            A["by_hour"] = [{"label": f"{h:02d}:00", "value": r0(hours[h]),
                             "share": r0(hours[h] / tot_h * 100)} for h in sorted(hours)]
    else:
        A["time"] = None

    # --- funnel
    A["funnel"] = [
        {"label": "Impresi", "value": r0(K["impressions"])},
        {"label": "Klik", "value": r0(K["clicks"])},
        {"label": "Konversi", "value": r0(K["conversions"])},
    ]
    if K["revenue"] and K["conversions"]:
        A["funnel_rates"] = {"ctr": r0(K["ctr"]), "cvr": r0(K["cvr"]),
                             "imp_to_conv": r0(safe_div(K["conversions"], K["impressions"]) * 100)}

    # --- pareto
    pk = "campaign" if "campaign" in cmap else ("channel" if "channel" in cmap else None)
    if pk:
        A["pareto"] = pareto(rows, pk, "revenue" if K["revenue"] else "clicks")

    # --- korelasi
    if A.get("time"):
        keys = [k for k in NUMERIC if any(A["time"]["series"].get(k, []))]
        cs = []
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                r = corr(A["time"]["series"][a], A["time"]["series"][b])
                if not math.isnan(r):
                    cs.append({"a": a, "b": b, "r": r0(r)})
        A["correlations"] = sorted(cs, key=lambda d: -abs(d["r"]))[:8]

    # --- skor kesehatan marketing 0-100
    score = 0
    score += min(30, K["roas"] / 4 * 30) if K["roas"] else 0
    score += min(25, K["ctr"] / 2 * 25) if K["ctr"] else 0
    score += min(25, K["cvr"] / 3 * 25) if K["cvr"] else 0
    score += 20 if (A.get("trend") or {}).get("direction") == "up" else 8
    A["health_score"] = round(score, 1)

    A["insights"] = build_insights(A, currency)
    A["recommendations"] = [i["action"] for i in A["insights"] if i.get("action")]
    return A


def to_markdown(A: Dict[str, Any], lang: str = "id") -> str:
    import i18n
    _t = lambda key: i18n.t(key, lang)
    cur = A["meta"]["currency"]
    k = A["kpi"]
    L: List[str] = []
    L.append(f"# Laporan Analisa Marketing — {A['meta']['source']}")
    L.append(f"\n_Dibuat: {A['meta']['generated_at']} · {A['meta']['rows']} baris · "
             f"kolom terpetakan: {', '.join(A['meta']['columns_mapped'].keys())}_\n")
    L.append(f"**Marketing Health Score: {A['health_score']}/100**\n")
    L.append("## 1. " + _t("rep_kpi") + "\n")
    L.append("| Metrik | Nilai | Metrik | Nilai |")
    L.append("|---|---|---|---|")
    pairs = [("Impresi", f"{k['impressions']:,.0f}"), ("Klik", f"{k['clicks']:,.0f}"),
             ("CTR", f"{k['ctr']:.2f}%"), ("CPC", f"{cur}{k['cpc']:,.0f}"),
             ("Spend", f"{cur}{k['spend']:,.0f}"), ("CPM", f"{cur}{k['cpm']:,.0f}"),
             ("Konversi", f"{k['conversions']:,.0f}"), ("CVR", f"{k['cvr']:.2f}%"),
             ("CPA", f"{cur}{k['cpa']:,.0f}"), ("Revenue", f"{cur}{k['revenue']:,.0f}"),
             ("ROAS", f"{k['roas']:.2f}x"), ("AOV", f"{cur}{k['aov']:,.0f}"),
             ("Profit", f"{cur}{k['profit']:,.0f}"), ("Margin", f"{k['margin']:.1f}%")]
    for i in range(0, len(pairs), 2):
        a = pairs[i]
        b = pairs[i + 1] if i + 1 < len(pairs) else ("", "")
        L.append(f"| {a[0]} | {a[1]} | {b[0]} | {b[1]} |")

    if A.get("by_channel"):
        L.append("\n## 2. " + _t("rep_channel") + "\n")
        L.append(f"| Channel | Spend | Revenue | ROAS | CTR | CVR | CPA | Share Rev |")
        L.append("|---|---|---|---|---|---|---|---|")
        for c in A["by_channel"]:
            x = c["kpi"]
            L.append(f"| {c['name']} | {cur}{x['spend']:,.0f} | {cur}{x['revenue']:,.0f} | "
                     f"{x['roas']:.2f}x | {x['ctr']:.2f}% | {x['cvr']:.2f}% | {cur}{x['cpa']:,.0f} | "
                     f"{c['share_revenue']:.1f}% |")
    if A.get("by_campaign"):
        L.append("\n## 3. " + _t("rep_campaign") + "\n")
        L.append("| Kampanye | Spend | Revenue | ROAS | Konversi | CPA |")
        L.append("|---|---|---|---|---|---|")
        for c in A["by_campaign"][:10]:
            x = c["kpi"]
            L.append(f"| {c['name']} | {cur}{x['spend']:,.0f} | {cur}{x['revenue']:,.0f} | "
                     f"{x['roas']:.2f}x | {x['conversions']:,.0f} | {cur}{x['cpa']:,.0f} |")
    if A.get("trend"):
        t = A["trend"]
        L.append("\n## 4. " + _t("rep_trend") + "\n")
        L.append(f"- Arah tren: **{t['direction'].upper()}** (slope revenue {t['slope_revenue']:+,.0f}/hari, "
                 f"R² {t['r2_revenue']:.2f})")
        L.append(f"- Perubahan awal→akhir periode: **{t['growth_pct_period']:+.1f}%**")
        if A.get("time"):
            L.append(f"- Rentang data: {A['time']['labels'][0]} → {A['time']['labels'][-1]} "
                     f"({A['time']['span_days']} hari)")
        if A.get("forecast"):
            f = A["forecast"]
            L.append(f"- Proyeksi {f['horizon']} hari ke depan ({f['method']}): " +
                     ", ".join(f"{l} = {cur}{v:,.0f}" for l, v in zip(f["labels"], f["revenue"])))
    if A.get("anomalies"):
        L.append("\n## 5. " + _t("rep_anom") + "\n")
        L.append("| Tanggal | Nilai | Deviasi | z-score | Arah |")
        L.append("|---|---|---|---|---|")
        for a in A["anomalies"][:8]:
            L.append(f"| {a['label']} | {a['value']:,.0f} | {a['deviation_pct']:+.1f}% | "
                     f"{a['z']} | {a['direction']} |")
    if A.get("pareto"):
        L.append("\n## 6. " + _t("rep_pareto") + "\n")
        L.append(f"_{A['pareto']['concentration']['note']}_\n")
        L.append("| Item | Nilai | Share | Kumulatif |")
        L.append("|---|---|---|---|")
        for p in A["pareto"]["items"]:
            L.append(f"| {p['name']} | {p['value']:,.0f} | {p['share']:.1f}% | {p['cumulative']:.1f}% |")
    if A.get("by_weekday"):
        L.append("\n## 7. " + _t("rep_week") + "\n")
        L.append(" | ".join(f"{d['label']} {d['share']:.0f}%" for d in A["by_weekday"]))
    L.append("\n## 8. " + _t("rep_ins") + "\n")
    for i, ins in enumerate(A["insights"], 1):
        icon = {"good": "✅", "warn": "⚠️", "bad": "⛔", "info": "ℹ️"}.get(ins["severity"], "ℹ️")
        L.append(f"{i}. {icon} **{ins['title']}** — {ins['detail']}")
        if ins.get("action"):
            L.append(f"   → _Aksi: {ins['action']}_")
    if A.get("correlations"):
        L.append("\n## 9. " + _t("rep_corr") + "\n")
        L.append("| A | B | r | Interpretasi |")
        L.append("|---|---|---|---|")
        for c in A["correlations"]:
            s = "kuat" if abs(c["r"]) >= 0.7 else ("sedang" if abs(c["r"]) >= 0.4 else "lemah")
            L.append(f"| {c['a']} | {c['b']} | {c['r']:+.2f} | {s} "
                     f"{'positif' if c['r'] > 0 else 'negatif'} |")
    L.append("\n---\n_Dihasilkan oleh DAN · sub-skill Marketing Data Analyst. "
             "Angka dibulatkan; korelasi ≠ kausalitas._")
    return "\n".join(L)


def self_test() -> int:
    """Uji cepat parser angka & tanggal. Jalankan: python3 dan_analytics.py --test"""
    global NUM_LOCALE
    NUM_LOCALE = "auto"
    cases = [
        ("1234", 1234.0), ("1.234.567", 1234567.0), ("1,234,567", 1234567.0),
        ("1.234,56", 1234.56), ("1,234.56", 1234.56), ("Rp 14.397.036", 14397036.0),
        ("Rp1.500.000", 1500000.0), ("12,5%", 0.125), ("3.4 jt", 3400000.0),
        ("12K", 12000.0), ("2,5 miliar", 2500000000.0), ("1.5", 1.5), ("0", 0.0),
        ("14.397", 14397.0), ("-", None), ("N/A", None), ("", None),
        ("$1,200.50", 1200.50), ("1.2M", 1200000.0),
        ("103,241", 103241.0), ("12,5", 12.5), ("1.234,5", 1234.5),
        ("Rp1.500", 1500.0), ("1,234.5", 1234.5),
    ]
    fails = 0
    for raw, want in cases:
        got = parse_number(raw)
        ok = (got is None and want is None) or (
            got is not None and want is not None and abs(got - want) < max(0.01, abs(want) * 1e-9))
        print(("  ok  " if ok else "  FAIL") + f"  {raw!r:22} -> {got!r:16} (expect {want!r})")
        fails += 0 if ok else 1
    d = parse_date("2026-09-16")
    print(("  ok  " if d and d.year == 2026 else "  FAIL") + f"  parse_date('2026-09-16') -> {d}")
    print(f"\n[DAN] self-test: {len(cases) + 1 - fails}/{len(cases) + 1} lulus")
    return 1 if fails else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    ap = argparse.ArgumentParser(description="DAN · Marketing Data Analyst")
    ap.add_argument("csv", help="path file CSV/XLSX")
    ap.add_argument("--out", default=os.path.join(root, "deliverables", "analysis.json"))
    ap.add_argument("--report", default=os.path.join(root, "deliverables", "analysis.md"))
    ap.add_argument("--summary-csv", default="")
    ap.add_argument("--currency", default="Rp")
    ap.add_argument("--forecast", type=int, default=3)
    ap.add_argument("--num-locale", default="auto", choices=["auto", "id", "en"],
                    help="cara membaca pemisah angka yang ambigu (default: auto)")
    ap.add_argument("--test", action="store_true", help="jalankan self-test parser lalu keluar")
    ap.add_argument("--lang", default="id", choices=["id", "en", "zh"])
    a = ap.parse_args(argv)

    global NUM_LOCALE
    NUM_LOCALE = a.num_locale
    if a.test:
        return self_test()

    A = analyze(a.csv, currency=a.currency, forecast_n=a.forecast)
    for p in (a.out, a.report):
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(A, f, ensure_ascii=False, indent=2, default=str)
    md = to_markdown(A, a.lang)
    with open(a.report, "w", encoding="utf-8") as f:
        f.write(md)
    if a.summary_csv:
        os.makedirs(os.path.dirname(os.path.abspath(a.summary_csv)), exist_ok=True)
        with open(a.summary_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if A.get("by_channel"):
                w.writerow(["channel", "spend", "revenue", "roas", "ctr", "cvr", "cpa", "share_revenue"])
                for c in A["by_channel"]:
                    x = c["kpi"]
                    w.writerow([c["name"], x["spend"], x["revenue"], x["roas"], x["ctr"],
                                x["cvr"], x["cpa"], c["share_revenue"]])
    print(f"[DAN] rows={A['meta']['rows']}  ROAS={A['kpi']['roas']:.2f}x  "
          f"CTR={A['kpi']['ctr']:.2f}%  health={A['health_score']}/100")
    print(f"[DAN] json   -> {a.out}")
    print(f"[DAN] report -> {a.report}")
    if a.summary_csv:
        print(f"[DAN] csv    -> {a.summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
