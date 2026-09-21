#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
crisis_sim.py — Stress-test rencana: simulasi krisis dengan dampak TERUKUR +
rencana respons terurut (0–24 jam, 24–72 jam, minggu ke-2).

Skenario:
  A budget_cut   : budget iklan dipotong 50% mendadak
  B channel_dead : channel penyumbang revenue terbesar mati total
  C stock_out    : stok produk utama habis 3 minggu
  D reputation   : komplain viral / isu kepercayaan

Untuk A–C dampak dihitung dari data (share revenue channel, ROAS blend, AOV, stok);
untuk D dampak kualitatif dengan indikator pemantau. Setiap skenario memberi:
angka terpapar, respons ber-fase dengan pemilik, dan indikator pemulihan.
Kami TIDAK memprediksi masa depan — ini latihan kesiapan, bukan ramalan.

PAKAI
  python3 crisis_sim.py --analysis analysis.json --stok 4000 \
      --out deliverables/crisis_playbook.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import svg_charts as sc  # noqa: E402


def rupiah(v: float) -> str:
    return f"Rp{sc.fmt_num(v, 'id')}"


def build(A: Dict[str, Any], stok: float, cut: float = 50.0) -> List[Dict[str, Any]]:
    k = A.get("kpi", {})
    ch = sorted(A.get("by_channel", []) or [], key=lambda c: -c["kpi"]["revenue"])
    rev, spend, aov = k.get("revenue", 0), k.get("spend", 0), k.get("aov", 0)
    out: List[Dict[str, Any]] = []

    # A. budget cut: potong dari channel paling tidak efisien dulu
    target_cut = spend * cut / 100
    lost = 0.0
    remaining = target_cut
    plan_cut = []
    for c in reversed(ch):
        if remaining <= 0:
            break
        take = min(c["kpi"]["spend"], remaining)
        lost += take * c["kpi"]["roas"]
        remaining -= take
        plan_cut.append((c["name"], take))
    out.append({
        "id": "A", "nama": f"Pemotongan budget {cut:.0f}%",
        "dampak": f"Revenue berisiko {rupiah(lost)} per periode bila dipotong acak; "
                  f"bila dipotong dari channel paling efisien, kehilangan bisa 2–3× lipat.",
        "angka": {"budget_dipotong": target_cut, "revenue_berisiko": lost,
                  "roas_blend": k.get("roas", 0)},
        "respons": [
            ("0–24 jam", "Bekukan semua eksperimen; hanya pertahankan kampanye ROAS ≥ target",
             "PMO Lead"),
            ("0–24 jam", "Hitung ulang break-even per channel;umumkan urutan pemotongan",
             "Analyst"),
            ("24–72 jam", f"Eksekusi pemotongan berurutan dari: "
                          + ", ".join(f"{n} ({rupiah(t)})" for n, t in plan_cut[:3]),
             "Ops-Finance"),
            ("Minggu 2", "Pindahkan sisa budget ke 2 channel ROAS tertinggi; uji kreatif murah",
             "Creative + Analyst"),
        ],
        "pemulihan": ["ROAS blend kembali ≥ target", "CPA stabil ≤ ambang 2 minggu beruntun"],
    })

    # B. channel mati
    if ch:
        top = ch[0]
        share = top["share_revenue"]
        next_best = ch[1] if len(ch) > 1 else None
        # saturasi: channel tujuan tidak bisa menyerap semua budget pada ROAS sama
        absorb = min(top["kpi"]["spend"] * 0.5, next_best["kpi"]["spend"] * 0.3) \
            if next_best else 0.0
        recover = absorb * (next_best["kpi"]["roas"] if next_best else 0) * 0.35
        out.append({
            "id": "B", "nama": f"Channel utama mati ({top['name']})",
            "dampak": f"{share:.0f}% revenue ({rupiah(top['kpi']['revenue'])}) terpapar; "
                      f"pemulihan realistis {rupiah(recover)} via "
                      f"{next_best['name'] if next_best else 'kanal lain'} — dibatasi "
                      f"saturasi (channel tujuan hanya menyerap sebagian budget pada "
                      f"ROAS menurun).",
            "angka": {"share_revenue": share, "revenue_terpapar": top["kpi"]["revenue"],
                      "pemulihan_estimasi": recover},
            "respons": [
                ("0–24 jam", "Konfirmasi penyebab (platform vs internal); dokumentasikan",
                 "Ops-Finance"),
                ("0–24 jam", "Alihkan 50% budget channel mati ke 2 channel terbaik (damp 0,7)",
                 "PMO Lead"),
                ("24–72 jam", "Naikkan frekuensi kanal organik + WA/email ke basis member",
                 "Creative"),
                ("Minggu 2", "Negosiasi pemulihan akun ATAU bangun kanal pengganti permanen",
                 "Owner"),
            ],
            "pemulihan": [f"Share {top['name']} turun <20% portofolio",
                          "Revenue total ≥80% baseline dalam 4 minggu"],
        })

    # C. stok habis
    cap_rev = stok * aov
    weeks = 3
    out.append({
        "id": "C", "nama": f"Stok habis {weeks} minggu",
        "dampak": f"Maksimum revenue tertagih {rupiah(cap_rev)} ({stok:,.0f} unit × AOV "
                  f"{rupiah(aov)}); iklan yang jalan di atas kapasitas = bakar budget.",
        "angka": {"stok_unit": stok, "revenue_cap": cap_rev,
                  "spend_mubazir_estimasi": max(0.0, spend - cap_rev / max(0.1, k.get("roas", 1)))},
        "respons": [
            ("0–24 jam", "Turunkan budget ke level yang sesuai kapasitas stok (jangan nol: "
                         "pertahankan brand search)", "PMO Lead"),
            ("0–24 jam", "Aktifkan waitlist/pre-order dengan insentif", "Creative"),
            ("24–72 jam", "Geser iklan ke produk pengganti/stok sehat", "Analyst"),
            ("Minggu 2", "Sinkronkan forecast stok ↔ budget mingguan (aturan baru)",
             "Ops-Finance"),
        ],
        "pemulihan": ["Rasio spend:kapasitas ≤ break-even", "Waitlist ≥30% permintaan tertahan"],
    })

    # D. reputasi
    out.append({
        "id": "D", "nama": "Komplain viral / isu kepercayaan",
        "dampak": "Kualitatif: kepercayaan & CVR menurun sebelum revenue terlihat; "
                  "biaya akuisisi naik karena audiens dingin menolak.",
        "angka": {"pantau": ["sentimen harian", "CVR", "CPA", "refund rate", "mention volume"]},
        "respons": [
            ("0–24 jam", "Satu suara resmi: akui masalah, sebut tindakan, beri tenggat",
             "Owner"),
            ("0–24 jam", "Hentikan semua iklan hard-sell; ganti ke pesan pelayanan",
             "PMO Lead"),
            ("24–72 jam", "Tim respons khusus balas 100% komplain publik <4 jam", "Creative"),
            ("Minggu 2", "Publikasikan perbaikan terukur (angka sebelum-sesudah)", "Owner"),
        ],
        "pemulihan": ["Sentimen netral-positif ≥70%", "CVR kembali ≥90% baseline"],
    })
    return out


def to_markdown(scen: List[Dict[str, Any]], A: Dict[str, Any]) -> str:
    L = ["# Crisis Playbook — simulasi terukur", "",
         f"_Basis data: {A.get('meta', {}).get('source', 'analysis.json')} · "
         f"revenue {rupiah(A.get('kpi', {}).get('revenue', 0))} · ROAS "
         f"{A.get('kpi', {}).get('roas', 0):.2f}x. Ini latihan kesiapan, bukan ramalan._", ""]
    for s in scen:
        L += [f"## Skenario {s['id']} — {s['nama']}", "", f"**Dampak:** {s['dampak']}", ""]
        if "angka" in s and isinstance(s["angka"], dict):
            L += ["**Angka kunci:**"]
            for kk, vv in s["angka"].items():
                if isinstance(vv, list):
                    L.append(f"- {kk}: " + ", ".join(vv))
                elif isinstance(vv, float) and vv > 1000:
                    L.append(f"- {kk}: {rupiah(vv)}")
                else:
                    L.append(f"- {kk}: {vv}")
            L.append("")
        L += ["**Respons terurut:**", "", "| Fase | Tindakan | Pemilik |", "|---|---|---|"]
        for f, t, p in s["respons"]:
            L.append(f"| {f} | {t} | {p} |")
        L += ["", "**Indikator pemulihan:** " + " · ".join(s["pemulihan"]), ""]
    L += ["---", "_DAN · crisis_sim. Jalankan ulang tiap kuartal atau saat struktur "
                  "channel/stok berubah._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · crisis simulation")
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--stok", type=float, default=3000)
    ap.add_argument("--cut", type=float, default=50)
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables",
                                                   "crisis_playbook.md"))
    a = ap.parse_args(argv)
    A = json.load(open(a.analysis, encoding="utf-8"))
    scen = build(A, a.stok, a.cut)
    md = to_markdown(scen, A)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(md)
    json.dump(scen, open(os.path.splitext(a.out)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"[DAN] crisis playbook: {len(scen)} skenario -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
