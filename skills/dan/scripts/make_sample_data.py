#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_sample_data.py — Membuat dataset demo marketing yang realistis untuk menguji skill DAN.

  python3 make_sample_data.py            # -> <root>/data/sample_campaign.csv
  python3 make_sample_data.py --days 120 --seed 3 --out ../../../../data/x.csv

Struktur kolom sengaja pakai campuran istilah ID/EN untuk menguji auto-mapping
kolom di dan_analytics.py.
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import random
from datetime import datetime, timedelta

#        ctr%   cvr%   cpc     aov      growth/hari  bobot volume
CHANNELS = {
    "Instagram":   (1.85, 2.6, 3200, 185000, 1.006, 1.00),
    "TikTok":      (2.40, 1.9, 1800, 132000, 1.014, 1.15),
    "Google Ads":  (3.10, 4.2, 6500, 268000, 1.004, 0.55),
    "YouTube":     (0.95, 1.4, 2400, 210000, 1.002, 0.35),
    "Email":       (4.60, 5.1, 1200, 240000, 1.001, 0.20),
    "Marketplace": (2.10, 6.4, 1200, 155000, 1.009, 0.70),
}

CAMPAIGNS = {
    "Instagram": ["IG-Prospecting-Video", "IG-Retargeting-Carousel", "IG-Brand-Awareness"],
    "TikTok": ["TT-Spark-Ads-KOL", "TT-Non-Branded-UGC", "TT-Live-Shopping"],
    "Google Ads": ["GAD-Search-Brand", "GAD-Search-NonBrand", "GAD-PMax-Catalog"],
    "YouTube": ["YT-Instream-Skippable", "YT-Shorts-Bumper"],
    "Email": ["EM-Newsletter-Mingguan", "EM-Abandoned-Cart", "EM-Winback-90d"],
    "Marketplace": ["MP-Flash-Sale", "MP-Sponsored-Product", "MP-Affiliate-KOL"],
}


def main(argv=None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=os.path.join(root, "data", "sample_campaign.csv"))
    a = ap.parse_args(argv)
    rnd = random.Random(a.seed)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    start = datetime.now() - timedelta(days=a.days - 1)
    rows = []
    for d in range(a.days):
        day = start + timedelta(days=d)
        weekend = 1.28 if day.weekday() >= 5 else 1.0
        payday = 1.35 if day.day in (1, 2, 25, 26, 27) else 1.0
        mega = 2.4 if (day.day == 9 and day.month % 2 == 0) else 1.0   # tanggal kembar
        for ch, (ctr, cvr, cpc, aov, trend, weight) in CHANNELS.items():
            for camp in CAMPAIGNS[ch]:
                base = rnd.uniform(90_000, 420_000) * weight * (trend ** d)
                imp = base * weekend * payday * mega * rnd.uniform(0.82, 1.18)
                clk = imp * (ctr / 100) * rnd.uniform(0.8, 1.2)
                conv = clk * (cvr / 100) * rnd.uniform(0.75, 1.3)
                spend = clk * cpc * rnd.uniform(0.85, 1.15)
                rev = conv * aov * rnd.uniform(0.85, 1.2)
                eng = imp * rnd.uniform(0.02, 0.07)
                rows.append({
                    "tanggal": day.strftime("%Y-%m-%d"),
                    "channel": ch,
                    "campaign": camp,
                    "tayangan": round(imp),
                    "klik": round(clk),
                    # format Indonesia (titik = ribuan) untuk menguji parser
                    "biaya": f"{round(spend):,}".replace(",", "."),
                    "konversi": round(conv, 2),
                    "pendapatan": round(rev),
                    "engagement": round(eng),
                })
    # sisipkan 2 anomali untuk menguji deteksi
    if rows:
        rows[len(rows) // 3]["pendapatan"] = round(rows[len(rows) // 3]["pendapatan"] * 4.2)
        rows[int(len(rows) * 0.72)]["klik"] = round(rows[int(len(rows) * 0.72)]["klik"] * 0.08)

    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[DAN] {len(rows)} baris -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
