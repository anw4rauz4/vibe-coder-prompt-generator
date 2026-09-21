#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
client_report.py — Laporan versi KLIEN: bahasa manusia, tanpa jargon.

Mengubah analysis.json (hasil dan_analytics.py) menjadi narasi yang bisa dikirim
ke pemilik bisnis/non-marketer: apa yang terjadi, apa artinya dalam rupiah,
dan langkah berikutnya — plus glosarium kecil. Semua angka tetap tertelusur
ke sumber (prinsip DAN) namun disajikan dengan pembanding yang mudah dicerna.

PAKAI
  python3 client_report.py --analysis analysis.json --out deliverables/laporan_klien.md
  python3 client_report.py --analysis analysis.json --nama "Kopi Enak" --period "Q3 2026"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import svg_charts as sc  # noqa: E402
import i18n  # noqa: E402

GLOS_EN = [
    ("Impressions", "how many times your ad appeared on a screen"),
    ("Clicks", "how many people were interested enough to tap the ad"),
    ("CTR", "of every 100 people who saw it, how many clicked"),
    ("Conversions", "how many people actually bought or signed up"),
    ("CPA", "what you pay to acquire one buyer"),
    ("ROAS", "how many rupiah of sales each Rp1 of ads returns"),
    ("AOV", "average value of one transaction"),
]

GLOS = [
    ("Impresi", "berapa kali iklan Anda ditampilkan di layar"),
    ("Klik", "berapa orang yang tertarik cukup untuk menyentuh iklan"),
    ("CTR", "dari 100 orang yang melihat, berapa yang klik"),
    ("Konversi", "berapa orang yang benar-benar membeli/daftar"),
    ("CPA", "biaya yang Anda bayar untuk mendapatkan satu pembeli"),
    ("ROAS", "setiap Rp1 iklan kembali jadi berapa rupiah penjualan"),
    ("AOV", "rata-rata nilai satu transaksi"),
]


def rupiah(v: float) -> str:
    return f"Rp{sc.fmt_num(v, 'id')}"


def build(A: Dict[str, Any], nama: str, period: str, lang: str = "id") -> str:
    t = lambda k: i18n.t(k, lang)
    ID = (lang == "id")
    k = A.get("kpi", {})
    ch = A.get("by_channel", []) or []
    cur_rev = k.get("revenue", 0)
    spend = k.get("spend", 0)
    profit = cur_rev - spend
    best = max(ch, key=lambda c: c["kpi"]["roas"]) if ch else None
    worst = min(ch, key=lambda c: c["kpi"]["roas"]) if ch else None
    conv = k.get("conversions", 0)
    clk = k.get("clicks", 0)

    if ID:
        lead = (f"**{t('cl_head')}:** Anda beriklan {rupiah(spend)} dan penjualan yang "
                f"tercatat {rupiah(cur_rev)}. Artinya setiap Rp1 iklan kembali menjadi "
                f"**Rp{k.get('roas', 0):.2f}**. Dari {sc.fmt_num(clk, 'id')} orang yang "
                f"klik, {sc.fmt_num(conv, 'id')} orang membeli.")
    else:
        lead = (f"**{t('cl_head')}:** You advertised {rupiah(spend)} and recorded sales of "
                f"{rupiah(cur_rev)}. Every Rp1 of ads returned **Rp{k.get('roas', 0):.2f}**. "
                f"Of {sc.fmt_num(clk, 'id')} people who clicked, "
                f"{sc.fmt_num(conv, 'id')} purchased.")
    L = [f"# {'Laporan' if ID else 'Report'} {nama} — {period}", "", lead, ""]

    L += [f"## {t('cl_happen')}", ""]
    std = ("standar industri sekitar 1–2, jadi posisi Anda "
           f"{'di atas' if k.get('ctr', 0) >= 2 else 'setara/di bawah'} standar"
           if ID else
           "industry benchmark is ~1–2, so you are "
           f"{'above' if k.get('ctr', 0) >= 2 else 'at/below'} benchmark")
    L.append(f"- {('Iklan Anda dilihat ' + sc.fmt_num(k.get('impressions', 0), 'id') + ' kali; ') if ID else ('Your ads were shown ' + sc.fmt_num(k.get('impressions', 0), 'id') + ' times; ')}"
             f"{k.get('ctr', 0):.2f} {'dari setiap 100 penonton tertarik mengklik (' if ID else 'of every 100 viewers clicked ('}"
             f"{std}).")
    L.append(f"- {('Dari yang klik, ' if ID else 'Of those clicks, ')}{k.get('cvr', 0):.2f}% "
             f"{('melanjutkan sampai membeli; biaya per satu pembeli ' if ID else 'went on to purchase; cost per buyer ')}"
             f"{rupiah(k.get('cpa', 0))} {('sementara rata-rata nilai transaksi ' if ID else 'while average order value is ')}"
             f"{rupiah(k.get('aov', 0))}.")
    if best and worst:
        if ID:
            L.append(f"- Kanal paling menguntungkan: **{best['name']}** (setiap Rp1 jadi "
                     f"Rp{best['kpi']['roas']:.2f}). Yang paling boros: **{worst['name']}** "
                     f"(Rp{worst['kpi']['roas']:.2f} kembali per Rp1).")
        else:
            L.append(f"- Most profitable channel: **{best['name']}** (each Rp1 returned "
                     f"Rp{best['kpi']['roas']:.2f}). Least efficient: **{worst['name']}** "
                     f"(Rp{worst['kpi']['roas']:.2f} back per Rp1).")

    L += ["", f"## {t('cl_mean')}", "",
          (f"- Selisih penjualan dikurangi biaya iklan = **{rupiah(profit)}** (belum termasuk "
           f"harga pokok produk & operasional)." if ID else
           f"- Sales minus ad spend = **{rupiah(profit)}** (before product cost & operations)."),
          (f"- Bila biaya per pembeli ({rupiah(k.get('cpa', 0))}) mendekati nilai transaksi "
           f"({rupiah(k.get('aov', 0))}), keuntungan tipis — prioritasnya memperbaiki halaman "
           f"penjualan, bukan menambah budget." if ID else
           f"- If cost per buyer ({rupiah(k.get('cpa', 0))}) approaches order value "
           f"({rupiah(k.get('aov', 0))}), margin is thin — fix the sales page first, "
           f"not the budget."),
          ("- Kanal yang mengembalikan >Rp3 per Rp1 aman untuk ditambah perlahan (naikkan "
           "±20% tiap beberapa hari, jangan langsung lipat ganda)." if ID else
           "- Channels returning >Rp3 per Rp1 can be scaled gradually (+20% every few days, "
           "never double at once)."), ""]

    L += [f"## {t('cl_next')}", ""]
    bn = best["name"] if best else "-"
    wn = worst["name"] if worst else "-"
    if best and worst:
        L.append("1. " + (f"Pindahkan sebagian budget dari {wn} ke {bn} dan uji 2 minggu."
                          if ID else
                          f"Shift part of the budget from {wn} to {bn} and test for 2 weeks."))
    else:
        L.append("1. " + ("Fokus pada kanal dengan data konversi terlengkap." if ID
                          else "Focus on the channel with the most complete conversion data."))
    L.append("2. " + ("Perbaiki halaman penjualan: percepat muat halaman, tampilkan ulasan "
                      "di bagian atas, sederhanakan formulir." if ID else
                      "Fix the sales page: faster load, reviews above the fold, shorter form."))
    L.append("3. " + ("Ulangi pengukuran minggu depan dengan cara sama agar perbandingan adil."
                      if ID else
                      "Re-measure next week the same way so comparisons stay fair."))
    L += [""]
    L += ["", f"## {t('cl_gloss')}", ""]
    G = GLOS if ID else [(a, b) for a, b in GLOS_EN]
    L += [f"- **{a}**: {b}" for a, b in G]
    L += ["", "---",
          (f"_Disusun otomatis dari data kampanye {period}. Angka dibulatkan; rincian "
           f"teknis tersedia pada laporan internal._" if ID else f"_{t('cl_footer')}_")]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · client-friendly report")
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--nama", default="Bisnis Anda")
    ap.add_argument("--period", default="periode ini")
    ap.add_argument("--out", default="")
    ap.add_argument("--lang", default="id", choices=["id", "en"])
    a = ap.parse_args(argv)
    A = json.load(open(a.analysis, encoding="utf-8"))
    md = build(A, a.nama, a.period, a.lang)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(md)
        print(f"[DAN] laporan klien -> {a.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
