"""Galeri contoh semua chart: python3 -m svg_charts."""
import os

from . import *
from .core import FONT

import os
demo = [
    bar([("Instagram", 4210), ("TikTok", 3180), ("YouTube", 1890), ("Google Ads", 2640),
         ("Email", 980)], title="Klik per Channel", subtitle="Q3 2026"),
    hbar([("Skincare", 82), ("Fashion", 64), ("F&B", 51), ("Elektronik", 38)],
         title="Kontribusi Revenue (%)"),
    line([(f"M{i}", v) for i, v in enumerate(
        [120, 180, 165, 240, 300, 285, 360, 420, 405, 510, 600, 690], 1)],
        title="Tren Leads", subtitle="12 bulan", area=True),
    donut([("Organik", 46), ("Berbayar", 31), ("Referral", 14), ("Email", 9)],
          title="Sumber Traffic", center_value="128rb", center_label="sesi/bulan"),
    funnel([("Impresi", 1_200_000), ("Klik", 84_000), ("ATC", 12_400),
            ("Checkout", 5_100), ("Purchase", 3_240)], title="Funnel Konversi"),
    radar({"Produk A": [8, 6, 9, 5, 7], "Produk B": [6, 9, 5, 8, 6]},
          ["Harga", "Kualitas", "Brand", "Distribusi", "Service"], title="Positioning"),
    scatter([(12, 3.1), (20, 4.4), (28, 5.0), (35, 6.8), (44, 7.2), (52, 9.1), (60, 9.4)],
            title="Spend vs ROAS", xlabel="Spend (jt)", ylabel="ROAS"),
    heatmap(["Sen", "Sel", "Rab", "Kam", "Jum", "Sab"],
            ["06", "09", "12", "15", "18", "21"],
            [[2, 5, 8, 6, 9, 4], [3, 6, 9, 7, 8, 5], [4, 7, 11, 9, 10, 6],
             [3, 8, 10, 8, 12, 7], [5, 9, 12, 10, 14, 9], [7, 6, 8, 6, 11, 10]],
            title="Jam Terbaik Posting (engagement)"),
    waterfall([("Awal", 100), ("Iklan", -22), ("Konten", -8), ("Tooling", -5),
               ("Revenue", 61), ("Net", 126)], title="Bridge Profit"),
    stacked_bar(["Q1", "Q2", "Q3", "Q4"],
                {"Organik": [30, 42, 55, 61], "Berbayar": [22, 28, 31, 44],
                 "Affiliate": [8, 11, 16, 21]}, title="Revenue per Kanal"),
    gauge(78, 100, "target 70%", title="Marketing Score"),
    network([{"id": a, "label": a, "group": i % 3, "value": v}
             for i, (a, v) in enumerate(
                 [("KOL-A", 9), ("KOL-B", 6), ("KOL-C", 8), ("Brand", 10),
                  ("KOL-D", 4), ("Komunitas", 7)])],
            [("Brand", "KOL-A", 5), ("Brand", "KOL-B", 3), ("KOL-A", "KOL-C", 4),
             ("KOL-B", "KOL-D", 2), ("KOL-C", "Komunitas", 3), ("Brand", "Komunitas", 2)],
            title="Jaringan Influencer", weighted=True),
]
here = os.path.dirname(os.path.abspath(__file__))
root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
out = os.path.join(root, "deliverables", "chart_gallery.html")
os.makedirs(os.path.dirname(out), exist_ok=True)
body = "".join(f'<div class="c">{s}</div>' for s in demo)
with open(out, "w", encoding="utf-8") as f:
    f.write(f"""<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>DAN · Galeri Chart</title><style>
body{{margin:0;background:#0B1220;color:#E2E8F0;font-family:{FONT};padding:28px}}
h1{{font-size:22px;margin:0 0 6px}}p{{color:#94A3B8;margin:0 0 22px;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:18px}}
.c{{background:#111C33;border:1px solid #24344F;border-radius:16px;padding:10px;overflow:hidden}}
svg{{width:100%;height:auto;display:block}}</style></head><body>
<h1>Galeri Chart — paket svg_charts (zero-dependency)</h1>
<p>16 tipe visualisasi yang tersedia untuk skill infografik DAN.</p>
<div class="grid">{body}</div></body></html>""")
print("OK ->", out)
