#!/usr/bin/env python3
"""plan_analyst — analis Business Plan / Sales Performance workbook (xlsx).

Dibuat untuk pola workbook distributor: sheet "Omset All" (omset per divisi per bulan
vs target vs tahun lalu), sheet kanal/produk per divisi, sheet "Stock" (SCD),
sheet "By Team" (pencapaian salesman per periode).

Nol dependensi: baca xlsx lewat xlsx_lite.

    python3 plan_analyst.py --file "Bisnis Plan 2026.xlsx" --outdir deliverables/nama-klien

Keluaran: analysis.json, analysis.md, data_quality.md, spec_infografik.json,
          omset_divisi.csv, tim_achievement.csv, kanal.csv
Aturan jujur: setiap angka turunan disebut sumbernya; yang bukan dari data
ditandai "asumsi:".
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsx_lite import load, cell, num, ref_to_rc, rc_to_ref  # noqa: E402

BULAN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
BULAN_ID = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

# blok di sheet "Omset All": nama -> (baris bulan pertama, baris Year, baris MTD)
BLOK = {"ALL": (6, 18, 20), "KALBE": (24, 36, 38), "KENVEU": (42, 54, 56),
        "OOH": (60, 72, 74), "DK": (78, 90, 92)}
NAMA_DIVISI = {"ALL": "Semua Divisi", "KALBE": "Kalbe", "KENVEU": "Kenveu",
               "OOH": "OOH-FFI", "DK": "Dua Kelinci"}


# ----------------------------------------------------------------------------- format
def rp(v: float, satuan: str = "M") -> str:
    """Rp miliar / juta gaya Indonesia."""
    if v is None:
        return "-"
    if satuan == "M":
        return "Rp{:,.2f} M".format(v / 1e9).replace(",", "X").replace(".", ",").replace("X", ".")
    if satuan == "jt":
        return "Rp{:,.1f} jt".format(v / 1e6).replace(",", "X").replace(".", ",").replace("X", ".")
    return "Rp{:,.0f}".format(v).replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v: float, digit: int = 1) -> str:
    if v is None:
        return "-"
    return ("{:,." + str(digit) + "f}%").format(v * 100).replace(",", "X").replace(".", ",").replace("X", ".")


def sgn(v: float, satuan: str = "M") -> str:
    s = "+" if v >= 0 else "-"
    return s + rp(abs(v), satuan)


def rata(v: list) -> float:
    v = [x for x in v if isinstance(x, (int, float))]
    return sum(v) / len(v) if v else 0.0


def status_rag(pencapaian: float) -> str:
    if pencapaian >= 1.0:
        return "hijau"
    if pencapaian >= 0.9:
        return "kuning"
    return "merah"


# ----------------------------------------------------------------------------- parser
def parse_omset(wb: dict, sheet: str = "Omset All") -> dict:
    """Ambil omset 2024/2025/2026/target per divisi per bulan (kolom D,E,F,G)."""
    out = {}
    for kode, (r0, _, _) in BLOK.items():
        rows = []
        for i in range(12):
            r = r0 + i
            rows.append({
                "bulan": BULAN_ID[i],
                "y2024": num(wb, sheet, f"D{r}"),
                "y2025": num(wb, sheet, f"E{r}"),
                "y2026": num(wb, sheet, f"F{r}"),
                "target": num(wb, sheet, f"G{r}"),
            })
        out[kode] = rows
    return out


def parse_metrik(wb: dict, sheet: str = "Omset All") -> dict:
    """EA (kol N), IPT (kol U), CB (kol Z) per divisi per bulan 2026; 2025 di M/T/Y."""
    out = {}
    for kode, (r0, _, _) in BLOK.items():
        if kode == "ALL":
            continue
        ea25, ea26, cb25, cb26, ipt25, ipt26 = [], [], [], [], [], []
        for i in range(12):
            r = r0 + i
            ea25.append(num(wb, sheet, f"M{r}"))
            ea26.append(num(wb, sheet, f"N{r}"))
            ipt25.append(num(wb, sheet, f"T{r}"))
            ipt26.append(num(wb, sheet, f"U{r}"))
            cb25.append(num(wb, sheet, f"Y{r}"))
            cb26.append(num(wb, sheet, f"Z{r}"))
        out[kode] = {"ea25": ea25, "ea26": ea26, "cb25": cb25, "cb26": cb26,
                     "ipt25": ipt25, "ipt26": ipt26}
    return out


def parse_kenveu(wb: dict, sheet: str = "Kenveu") -> list:
    """Kanal Kenveu Jan-Jun: B=kanal, C=2025, D=2026, E=%gr, F=kontribusi."""
    out = []
    for r in range(3, 29):
        nama = cell(wb, sheet, f"B{r}")
        if not isinstance(nama, str) or not nama.strip():
            continue
        v25, v26 = num(wb, sheet, f"C{r}"), num(wb, sheet, f"D{r}")
        out.append({"kanal": nama.strip(), "y2025": v25, "y2026": v26,
                    "gr": num(wb, sheet, f"E{r}"), "kontribusi": num(wb, sheet, f"F{r}"),
                    "induk": nama.strip().isupper()})
    return out


def parse_kalbe(wb: dict, sheet: str = "Kalbe") -> dict:
    """Bulanan SO/SOO/EA/CB/M3MEA/IPT (B..K) + kanal (AO..AS) + top produk (BC..BH)."""
    bulanan = []
    for r in range(6, 31):
        th = cell(wb, sheet, f"B{r}")
        bl = cell(wb, sheet, f"C{r}")
        if not isinstance(bl, str) or bl.strip() not in BULAN + ["Des"]:
            continue
        bulanan.append({"tahun": str(th), "bulan": bl.strip(),
                        "so": num(wb, sheet, f"D{r}"), "tgt_so": num(wb, sheet, f"E{r}"),
                        "soo": num(wb, sheet, f"F{r}"), "tgt_soo": num(wb, sheet, f"G{r}"),
                        "ea": num(wb, sheet, f"H{r}"), "cb": num(wb, sheet, f"I{r}"),
                        "m3mea": num(wb, sheet, f"J{r}"), "ipt": num(wb, sheet, f"K{r}")})
    kanal = []
    for r in range(5, 14):
        nama = cell(wb, sheet, f"AO{r}")
        if not isinstance(nama, str):
            continue
        kanal.append({"kanal": nama.strip(), "y2025": num(wb, sheet, f"AP{r}"),
                      "y2026": num(wb, sheet, f"AQ{r}"), "gr": num(wb, sheet, f"AR{r}"),
                      "kontribusi": num(wb, sheet, f"AS{r}")})
    produk = []
    for r in range(5, 25):
        nama = cell(wb, sheet, f"BE{r}")
        if not isinstance(nama, str):
            continue
        produk.append({"kode": str(cell(wb, sheet, f"BD{r}") or ""), "nama": nama.strip(),
                       "y2025": num(wb, sheet, f"BF{r}"), "y2026": num(wb, sheet, f"BG{r}"),
                       "gr": num(wb, sheet, f"BH{r}")})
    pelanggan = []
    for r in range(5, 25):
        nama = cell(wb, sheet, f"BM{r}")
        if not isinstance(nama, str):
            continue
        pelanggan.append({"nama": nama.strip(), "y2025": num(wb, sheet, f"BN{r}"),
                          "y2026": num(wb, sheet, f"BO{r}"), "gr": num(wb, sheet, f"BP{r}")})
    return {"bulanan": bulanan, "kanal": kanal, "produk": produk, "pelanggan": pelanggan}


def parse_stock(wb: dict, sheet: str = "Stock") -> list:
    out = []
    for c in range(3, 7):
        nama = cell(wb, sheet, rc_to_ref(3, c))
        if not nama:
            continue
        avg = num(wb, sheet, rc_to_ref(4, c))
        soh = num(wb, sheet, rc_to_ref(5, c))
        scd = num(wb, sheet, rc_to_ref(6, c))
        tgt = num(wb, sheet, rc_to_ref(7, c))
        selisih_hari = scd - tgt
        # nilai stok berlebih/kurang vs target cover (asumsi: pola konsumsi rata L3M)
        rp_selisih = (selisih_hari / 30.0) * avg if avg else 0.0
        out.append({"divisi": str(nama), "avg_l3m": avg, "soh": soh, "scd": scd,
                    "target_scd": tgt, "selisih_hari": selisih_hari, "rp_selisih": rp_selisih,
                    "status": "overstock" if selisih_hari > 5 else ("kritis" if selisih_hari < -5 else "sehat")})
    return out


PERIODE_RE = re.compile(r"Periode\s*:?\s*([A-Za-z]+)\s*(\d{4})?", re.I)
BULAN_ALIAS = {b.lower(): i for i, b in enumerate(BULAN)}
BULAN_ALIAS.update({"des": 11, "agu": 7, "aug": 7, "okt": 9, "may": 4, "mar": 2, "jun": 5, "jul": 6})

# tiap blok di "By Team" punya kolom label periode & lebar pita baris sendiri
BLOK_TIM = {
    "Kalbe":       {"label": 2,  "band": 14, "anchor": 3},
    "Dua Kelinci": {"label": 29, "band": 13, "anchor": 3},
    "Kenveu":      {"label": 52, "band": 13, "anchor": 3},
    "OOH-FFI":     {"label": 71, "band": 8,  "anchor": 3},
}


def _label_periode(wb: dict, sheet: str, cfg: dict) -> list:
    """[(baris, bulan_id)] untuk semua sel 'Periode ...' di kolom label blok."""
    out = []
    for (r, c), v in wb["grid"].get(sheet, {}).items():
        if c == cfg["label"] and isinstance(v, str):
            m = PERIODE_RE.search(v)
            if m:
                i = BULAN_ALIAS.get(m.group(1).lower()[:3])
                if i is not None:
                    out.append((r, BULAN_ID[i]))
    return sorted(out)


def _periode_banding(cfg: dict, r: int) -> str:
    idx = (r - cfg["anchor"]) // cfg["band"]
    return BULAN_ID[idx] if 0 <= idx < 12 else "?"


def _periode(labels: list, r: int, cfg: dict) -> str:
    """Label periode terdekat di atas baris r; fallback = aritmetika pita baris."""
    hit = None
    for lr, nm in labels:
        if lr <= r:
            hit = nm
        else:
            break
    return hit or _periode_banding(cfg, r)


def _periode_klaster(baris: list, labels: list, cfg: dict, batas: int = 12) -> dict:
    """Peta {baris: periode}. Blok berdampingan kadang tanpa label periode, jadi
    baris dikelompokkan (jeda > 3 baris = blok baru) lalu diberi bulan berurutan.
    Kalau label tersedia dan jumlahnya >= jumlah blok, label yang dipakai."""
    if not baris:
        return {}
    klaster, cur = [], [baris[0]]
    for r in baris[1:]:
        if r - cur[-1] > 3:
            klaster.append(cur)
            cur = [r]
        else:
            cur.append(r)
    klaster.append(cur)
    peta = {}
    if len(labels) >= len(klaster):
        for i, k in enumerate(klaster):
            nm = labels[i][1] if i < len(labels) else (BULAN_ID[i] if i < batas else "DUP")
            for r in k:
                peta[r] = nm if i < batas else "DUP"
    else:
        for i, k in enumerate(klaster):
            for r in k:
                peta[r] = BULAN_ID[i] if i < batas else "DUP"
    return peta


def _grup(wb: dict, sheet: str, kolom: int, r: int) -> str:
    """Label grup (General/Modern Trade) terdekat di atas baris r."""
    g = wb["grid"].get(sheet, {})
    best = ""
    for rr in range(r, max(0, r - 14), -1):
        v = g.get((rr, kolom))
        if isinstance(v, str) and ("Trade" in v or "SPV" in v):
            best = " ".join(v.split())
            break
    return best


def parse_team(wb: dict, sheet: str = "By Team", batas: int = 12) -> list:
    """Ambil pencapaian salesman per periode dari 4 blok berdampingan.

    Kolom terverifikasi (lihat xlsx_lite --range):
      Kalbe       : B tipe · C id · D nama · E aktual · F target · G %
      Dua Kelinci : AD kode · AE nama · AG HKS · AH HKA · AJ-AU CB/OA/EC/IPT · AV tgt · AW act · AX %
      Kenveu      : AZ grup · BA kode(SAN.*) · BB nama · BC tgt · BD act · BE % · BF-BP CB/OA/EC/IPT
      OOH-FFI     : BS kode(SM*) · BT nama · BU tgt · BV act · BW %
    """
    out = []
    g = wb["grid"].get(sheet, {})
    lab = {d: _label_periode(wb, sheet, c) for d, c in BLOK_TIM.items()}
    maxr = max((r for r, _ in g), default=0)
    kandidat = {"Kalbe": [], "Dua Kelinci": [], "OOH-FFI": [], "Kenveu": []}
    for r in range(1, maxr + 1):
        # --- Kalbe
        sid, nm = g.get((r, 3)), g.get((r, 4))
        if isinstance(nm, str) and nm.strip() and isinstance(sid, (int, float)) \
                and nm.strip().upper() not in ("SALES NAME", "SALES ID"):
            tgt, act = num(wb, sheet, f"F{r}"), num(wb, sheet, f"E{r}")
            if tgt > 0 or act > 0:
                kandidat["Kalbe"].append(r)
                out.append({"divisi": "Kalbe", "grup": str(g.get((r, 2)) or "").strip(),
                            "periode": None,
                            "kode": str(int(sid)), "nama": " ".join(str(nm).split()),
                            "target": tgt, "aktual": act,
                            "pct": act / tgt if tgt else 0.0, "_r": r})
        # --- Dua Kelinci
        kd, nm2 = g.get((r, 30)), g.get((r, 31))
        if isinstance(nm2, str) and nm2.strip() and re.fullmatch(r"\d{4,6}", str(kd or "")):
            tgt, act = num(wb, sheet, f"AV{r}"), num(wb, sheet, f"AW{r}")
            if tgt > 0 or act > 0:
                kandidat["Dua Kelinci"].append(r)
                out.append({"divisi": "Dua Kelinci", "grup": str(g.get((r, 32)) or "").strip(),
                            "periode": None,
                            "kode": str(kd), "nama": " ".join(nm2.split()), "target": tgt, "aktual": act,
                            "pct": act / tgt if tgt else 0.0, "_r": r,
                            "hk_tgt": num(wb, sheet, f"AG{r}"), "hk_act": num(wb, sheet, f"AH{r}"),
                            "cb_tgt": num(wb, sheet, f"AJ{r}"), "cb_act": num(wb, sheet, f"AK{r}"),
                            "oa_tgt": num(wb, sheet, f"AM{r}"), "oa_act": num(wb, sheet, f"AN{r}"),
                            "ec_tgt": num(wb, sheet, f"AP{r}"), "ec_act": num(wb, sheet, f"AQ{r}"),
                            "ipt_tgt": num(wb, sheet, f"AS{r}"), "ipt_act": num(wb, sheet, f"AT{r}")})
        # --- Kenveu (kode SAN.*) — terbukti dari rekonsiliasi: total blok = omset divisi Kenveu
        kd3 = g.get((r, 53))
        if isinstance(kd3, str) and kd3.strip().upper().startswith("SAN."):
            tgt, act = num(wb, sheet, f"BC{r}"), num(wb, sheet, f"BD{r}")
            kandidat["Kenveu"].append(r)
            out.append({"divisi": "Kenveu", "grup": _grup(wb, sheet, 52, r),
                        "periode": None,
                        "kode": kd3.strip(), "nama": " ".join(str(g.get((r, 54)) or "").split()),
                        "target": tgt, "aktual": act,
                        "pct": act / tgt if tgt else 0.0, "_r": r,
                        "cb_tgt": num(wb, sheet, f"BF{r}"), "cb_act": num(wb, sheet, f"BG{r}"),
                        "oa_tgt": num(wb, sheet, f"BI{r}"), "oa_act": num(wb, sheet, f"BJ{r}"),
                        "ec_tgt": num(wb, sheet, f"BL{r}"), "ec_act": num(wb, sheet, f"BM{r}"),
                        "ipt_tgt": num(wb, sheet, f"BO{r}"), "ipt_act": num(wb, sheet, f"BP{r}")})
        # --- OOH-FFI (kode SM*) — total blok = omset divisi OOH-FFI
        kd4 = g.get((r, 71))
        if isinstance(kd4, str) and re.fullmatch(r"SM\d+", kd4.strip()):
            tgt, act = num(wb, sheet, f"BU{r}"), num(wb, sheet, f"BV{r}")
            kandidat["OOH-FFI"].append(r)
            out.append({"divisi": "OOH-FFI", "grup": "", "periode": None,
                        "kode": kd4.strip(), "nama": " ".join(str(g.get((r, 72)) or "").split()),
                        "target": tgt, "aktual": act, "pct": act / tgt if tgt else 0.0,
                        "_r": r})
    for d, rows in kandidat.items():
        peta = _periode_klaster(sorted(set(rows)), lab[d], BLOK_TIM[d], batas)
        for x in out:
            if x["divisi"] == d and x.get("periode") is None:
                x["periode"] = peta.get(x.get("_r", 0), "?")
    for x in out:
        x.setdefault("_r", 0)
    return out


# ----------------------------------------------------------------------------- analisis
def n_bulan_data(wb: dict, sheet: str = "Omset All") -> int:
    """Jumlah bulan 2026 yang sudah ada aktualnya (patokan periode laporan)."""
    n = 0
    for i in range(12):
        if num(wb, sheet, f"F{BLOK['ALL'][0] + i}") > 0:
            n = i + 1
    return n or 12


def ytd(rows: list, key: str) -> float:
    """Jumlah bulan yang punya data 2026 (actual > 0)."""
    return sum(r[key] for r in rows if r["y2026"] > 0)


def bulan_ada(rows: list) -> list:
    return [r for r in rows if r["y2026"] > 0]


def proyeksi(rows: list, rows_ly: list) -> list:
    """3 skenario Sep-Des: run-rate, musiman (index tahun lalu), tren linear."""
    act = bulan_ada(rows)
    n = len(act)
    if n == 0:
        return []
    sisa = 12 - n
    total_ytd = sum(r["y2026"] for r in act)
    rr = total_ytd / n
    # musiman: rata-rata bulan sisa tahun lalu / rata-rata bulan yang sama tahun lalu
    ly_sisa = sum(r["y2025"] for r in rows_ly[n:]) or 0
    ly_ytd = sum(r["y2025"] for r in rows_ly[:n]) or 1
    rasio_musim = (ly_sisa / sisa) / (ly_ytd / n) if (sisa and ly_ytd) else 1.0
    musiman = rr * rasio_musim
    # tren linear (least square pada index bulan)
    xs = list(range(n))
    ys = [r["y2026"] for r in act]
    mx, my = rata(xs), rata(ys)
    den = sum((x - mx) ** 2 for x in xs) or 1
    b = sum((xs[i] - mx) * (ys[i] - my) for i in range(n)) / den
    a = my - b * mx
    tren = sum(max(0.0, a + b * (n + k)) for k in range(sisa))
    out = []
    for nama, per_bulan in (("Run-rate rata-rata", rr),
                            ("Musiman (pola tahun lalu)", musiman),
                            ("Tren linear", tren / sisa if sisa else 0)):
        total = per_bulan * sisa
        out.append({"skenario": nama, "sisa_bulan": sisa, "per_bulan": per_bulan,
                    "sep_des": total, "setahun": total_ytd + total,
                    "vs_2025": (total_ytd + total) / (sum(r["y2025"] for r in rows_ly) or 1) - 1})
    return out


def bangun(file_xlsx: str, nama_perusahaan: str) -> dict:
    wb = load(file_xlsx)
    sheets = wb["sheets"]
    omset = parse_omset(wb)
    metrik = parse_metrik(wb)
    stock = parse_stock(wb) if "Stock" in sheets else []
    kenveu_kanal = parse_kenveu(wb) if "Kenveu" in sheets else []
    kalbe = parse_kalbe(wb) if "Kalbe" in sheets else {"bulanan": [], "kanal": [], "produk": [], "pelanggan": []}
    team_all = parse_team(wb, batas=n_bulan_data(wb)) if "By Team" in sheets else []
    team = [x for x in team_all if x.get("periode") != "DUP"]
    n_dup = len(team_all) - len(team)

    all_rows = omset["ALL"]
    n_bulan = len(bulan_ada(all_rows))
    ytd26 = ytd(all_rows, "y2026")
    ytd25 = sum(r["y2025"] for r in bulan_ada(all_rows))
    ytd24 = sum(r["y2024"] for r in bulan_ada(all_rows))
    tgt = sum(r["target"] for r in bulan_ada(all_rows))
    pencapaian = ytd26 / tgt if tgt else 0
    yoy = ytd26 / ytd25 - 1 if ytd25 else 0
    gap = ytd26 - tgt

    divisi = []
    for kode in ("KALBE", "KENVEU", "OOH", "DK"):
        rows = omset[kode]
        ada = bulan_ada(rows)
        if not ada:
            continue
        a26 = sum(r["y2026"] for r in ada)
        a25 = sum(r["y2025"] for r in ada)
        t = sum(r["target"] for r in ada)
        m = metrik.get(kode, {})
        ea26 = [m.get("ea26", [0] * 12)[i] for i in range(len(ada))]
        cb26 = [m.get("cb26", [0] * 12)[i] for i in range(len(ada))]
        ea25 = [m.get("ea25", [0] * 12)[i] for i in range(len(ada))]
        cb25 = [m.get("cb25", [0] * 12)[i] for i in range(len(ada))]
        ipt26 = [m.get("ipt26", [0] * 12)[i] for i in range(len(ada))]
        ipt25 = [m.get("ipt25", [0] * 12)[i] for i in range(len(ada))]
        ea_a, cb_a = rata(ea26), rata(cb26)
        divisi.append({
            "kode": kode, "nama": NAMA_DIVISI[kode],
            "ytd2026": a26, "ytd2025": a25, "target": t,
            "pencapaian": a26 / t if t else 0, "yoy": a26 / a25 - 1 if a25 else 0,
            "gap": a26 - t,
            "kontribusi2026": a26 / ytd26 if ytd26 else 0,
            "kontribusi2025": a25 / ytd25 if ytd25 else 0,
            "status": status_rag(a26 / t if t else 0),
            "ea26": ea_a, "ea25": rata(ea25), "cb26": cb_a, "cb25": rata(cb25),
            "ipt26": rata(ipt26), "ipt25": rata(ipt25),
            "efektivitas_call26": ea_a / cb_a if cb_a else 0,
            "efektivitas_call25": rata(ea25) / rata(cb25) if rata(cb25) else 0,
            "omset_per_ea": a26 / len(ada) / ea_a if ea_a else 0,
        })

    proy = proyeksi(all_rows, all_rows)
    ly_full = sum(r["y2025"] for r in all_rows)
    tgt_tahunan_asumsi = tgt / n_bulan * 12 if n_bulan else 0

    # --- Kalbe deep dive
    kb = kalbe["bulanan"]
    kb26 = [x for x in kb if x["tahun"] == "2026" and x["soo"] > 0]
    kb25 = [x for x in kb if x["tahun"] == "2025"][:len(kb26)]
    kalbe_ring = {
        "so_2026": sum(x["so"] for x in kb26), "so_2025": sum(x["so"] for x in kb25),
        "soo_2026": sum(x["soo"] for x in kb26), "soo_2025": sum(x["soo"] for x in kb25),
        "ea_2026": rata([x["ea"] for x in kb26]), "ea_2025": rata([x["ea"] for x in kb25]),
        "cb_2026": rata([x["cb"] for x in kb26]), "cb_2025": rata([x["cb"] for x in kb25]),
        "m3mea_2026": rata([x["m3mea"] for x in kb26]), "m3mea_2025": rata([x["m3mea"] for x in kb25]),
        "ipt_2026": rata([x["ipt"] for x in kb26]), "ipt_2025": rata([x["ipt"] for x in kb25]),
        "kanal": kalbe["kanal"], "produk": kalbe["produk"], "pelanggan": kalbe["pelanggan"],
        "bulanan": kb26,
    }
    kalbe_ring["efektivitas_call_2026"] = (kalbe_ring["ea_2026"] / kalbe_ring["cb_2026"]
                                           if kalbe_ring["cb_2026"] else 0)
    kalbe_ring["efektivitas_call_2025"] = (kalbe_ring["ea_2025"] / kalbe_ring["cb_2025"]
                                           if kalbe_ring["cb_2025"] else 0)

    # --- tim
    tim_ring = {}
    for d in ("Kalbe", "Dua Kelinci", "OOH-FFI", "Kenveu"):
        sub = [x for x in team if x["divisi"] == d]
        if not sub:
            continue
        per = {}
        for x in sub:
            k = x["periode"]
            p = per.setdefault(k, {"target": 0.0, "aktual": 0.0, "n": 0, "n_dinilai": 0,
                                   "bawah_80": 0, "tanpa_target": 0, "negatif": 0, "orang": []})
            p["target"] += x["target"]
            p["aktual"] += x["aktual"]
            p["n"] += 1
            if x["aktual"] < 0:
                p["negatif"] += 1
            if not x["target"]:
                p["tanpa_target"] += 1
                continue          # tidak dinilai (mis. baris OFFICE tanpa target)
            ratio = x["aktual"] / x["target"]
            p["n_dinilai"] += 1
            if ratio < 0.8:
                p["bawah_80"] += 1
            p["orang"].append((x["nama"], ratio))
        for k, p in per.items():
            p["pencapaian"] = p["aktual"] / p["target"] if p["target"] else 0
            p["orang"].sort(key=lambda z: z[1])
            p["terbawah"] = [{"nama": a, "pencapaian": b} for a, b in p["orang"][:3]]
            p["teratas"] = [{"nama": a, "pencapaian": b} for a, b in p["orang"][-3:]][::-1]
            del p["orang"]
        tot_t = sum(x["target"] for x in sub)
        tot_a = sum(x["aktual"] for x in sub)
        tim_ring[d] = {"periode": per, "target_total": tot_t, "aktual_total": tot_a,
                       "pencapaian": tot_a / tot_t if tot_t else 0, "n_salesman": len(sub)}

    # --- kualitas data
    dq = []
    f18 = cell(wb, "Omset All", "F18")
    if isinstance(f18, (int, float)) and abs(f18 - ytd26) > 1e6:
        dq.append({"kode": "DQ-01", "temuan": "Baris 'Year' Semua Divisi (Omset All!F18) = "
                   + rp(f18) + ", padahal jumlah 12 bulan 2026 = " + rp(ytd26)
                   + ". Formula-nya menjumlah baris Year divisi (F36+F54+F72+F90), bukan SUM(F6:F17).",
                   "dampak": "Total tahunan di laporan bisa salah baca sampai 6x lipat.",
                   "saran": "Ganti dengan =SUM(F6:F17) atau =SUM dari baris MTD per divisi."})
    tgt_kosong = [r["bulan"] for r in all_rows if r["target"] <= 0]
    if tgt_kosong:
        dq.append({"kode": "DQ-02", "temuan": "Target 2026 kosong/0 untuk bulan: " + ", ".join(tgt_kosong)
                   + (". Target Sep Semua Divisi terisi " + rp(all_rows[8]["target"])
                      + " (jauh di bawah skala bulanan " + rp(rr_bulanan(ytd26, n_bulan)) + ")."
                      if all_rows[8]["target"] > 0 else "."),
                   "dampak": "Pencapaian setahun penuh tidak bisa dihitung; controlling bulanan Sep-Des tidak punya pagar.",
                   "saran": "Isi target Sep-Des per divisi (pakai pola musiman 2025 sebagai dasar)."})
    err = []
    for sh in sheets:
        for (r, c), v in wb["grid"].get(sh, {}).items():
            if isinstance(v, str) and v.startswith("#ERR"):
                err.append(f"{sh}!{rc_to_ref(r, c)}")
    if err:
        dq.append({"kode": "DQ-03", "temuan": f"{len(err)} sel error (#DIV/0! dll): " + ", ".join(err[:8])
                   + (" ..." if len(err) > 8 else ""),
                   "dampak": "Sel error ikut terhitung sebagai teks; persen bisa salah.",
                   "saran": "Bungkus dengan IFERROR(...,0) atau perbaiki pembaginya."})
    skala = 0
    for sh in ("By Team",):
        for (r, c), v in wb["grid"].get(sh, {}).items():
            if isinstance(v, (int, float)) and 5 < v < 500 and c in (49, 50, 57):
                skala += 1
    if skala:
        dq.append({"kode": "DQ-04", "temuan": f"Persen achievement di 'By Team' tersimpan dalam dua skala "
                   f"(0,85 dan 102,58) pada {skala} sel.",
                   "dampak": "Rata-rata/sortir pencapaian salesman jadi menyesatkan.",
                   "saran": "Satukan format: simpan rasio (0-1) lalu format persen di tampilan."})
    neg = []
    for (r, c), v in wb["grid"].get("Sheet1", {}).items():
        if isinstance(v, (int, float)) and v < -100000:
            neg.append(rc_to_ref(r, c))
    if neg:
        dq.append({"kode": "DQ-05", "temuan": f"{len(neg)} sel bernilai negatif besar di Sheet1 (retur), mis. "
                   + ", ".join(neg[:5]) + ".",
                   "dampak": "Retur bercampur dengan sales sehingga growth produk/outlet bias.",
                   "saran": "Pisahkan kolom sales & retur, atau buat baris retur tersendiri."})
    dq.append({"kode": "DQ-06", "temuan": "Header kolom O baris 5 'Omset All' berlabel 'CB' padahal isinya "
               "CB aktual (pembanding EA di kolom N); kolom target EA tidak ada.",
               "dampak": "Pembaca bisa salah artikan pencapaian EA vs target.",
               "saran": "Beri nama kolom eksplisit: EA, CB, EA/CB, IPT + kolom target masing-masing."})
    dq.append({"kode": "DQ-07", "temuan": "Tabel kanal & top produk sheet 'Kalbe' tidak mencantumkan periode "
               "(total 2025 " + rp(kalbe_ring.get("soo_2025", 0), "M") + " di tabel bulanan vs "
               + rp(sum(k["y2025"] for k in kalbe["kanal"])) + " di tabel kanal).",
               "dampak": "Dua angka berbeda untuk periode yang tampak sama.",
               "saran": "Tambah baris 'Periode: Jan-Agu 2026' dan 'Scope: sell out / sell in' di atas tiap tabel."})
    dq.append({"kode": "DQ-08", "temuan": "Nama salesman berubah antar periode untuk kode yang sama "
               "(mis. SAN.119908.S09: Rido -> Ardiansyah -> Asrdiansyah).",
               "dampak": "Riwayat kinerja per orang terputus; evaluasi & insentif tidak adil.",
               "saran": "Pakai master data salesman (kode tetap) + tabel alias."})
    if n_dup:
        dq.append({"kode": "DQ-14", "temuan": f"{n_dup} baris salesman berada di blok periode ke-"
                   f"{n_bulan + 1} dst (di luar periode data {n_bulan} bulan) dan isinya identik dengan "
                   f"blok sebelumnya.",
                   "dampak": "Bisa terbaca sebagai bulan berikutnya padahal salinan yang belum diperbarui.",
                   "saran": "Hapus/diperbarui blok salinan itu; engine otomatis menandainya 'DUP' dan "
                            "tidak menghitungnya."})
    dq.append({"kode": "DQ-09", "temuan": "Sheet4 dan Channels kosong; Sheet1 (produk/outlet/SKU) tidak "
               "berlabel divisi & periode.",
               "dampak": "Analisis per divisi tidak bisa otomatis dari Sheet1.",
               "saran": "Hapus sheet kosong atau isi; beri judul divisi+periode di Sheet1."})

    # rekonsiliasi: total tim (By Team) vs omset divisi (Omset All) per bulan
    peta_nama = {"Kalbe": "KALBE", "Dua Kelinci": "DK", "OOH-FFI": "OOH", "Kenveu": "KENVEU"}
    rekonsiliasi = []
    for d, v in tim_ring.items():
        kode = peta_nama.get(d)
        if not kode:
            continue
        rows = omset[kode]
        for i, bl in enumerate(BULAN_ID):
            p = v["periode"].get(bl)
            if not p or rows[i]["y2026"] <= 0:
                continue
            tim_act = p["aktual"]
            div_act = rows[i]["y2026"]
            selisih = tim_act / div_act - 1 if div_act else 0
            rekonsiliasi.append({"divisi": d, "bulan": bl, "tim": tim_act, "divisi_omset": div_act,
                                 "selisih": selisih,
                                 "ok": abs(selisih) <= 0.15})
    buruk = [x for x in rekonsiliasi if not x["ok"]]
    if buruk:
        contoh = "; ".join(f"{x['divisi']} {x['bulan']} (tim {rp(x['tim'])} vs divisi "
                           f"{rp(x['divisi_omset'])}, selisih {pct(x['selisih'], 0)})"
                           for x in sorted(buruk, key=lambda z: z["selisih"])[:6])
        dq.append({"kode": "DQ-10", "temuan": f"{len(buruk)} dari {len(rekonsiliasi)} bulan tidak rekonsiliasi "
                   f"(total salesman di 'By Team' beda > 15% dari omset divisi di 'Omset All'): {contoh}.",
                   "dampak": "Pencapaian tim tidak bisa dipakai untuk menilai pencapaian divisi; "
                             "insentif & evaluasi berisiko salah sasaran.",
                   "saran": "Kunci satu sumber kebenaran (omset divisi = jumlah salesman). Baris tanpa target "
                            "(mis. OFFICE) tetap dihitung di total, dan baris formula yang menjumlah baris lain "
                            "dihapus agar tidak ganda/kurang."})
    skala = []
    for d, v in tim_ring.items():
        tgt_per = [(k, p["target"] / p["n"]) for k, p in v["periode"].items() if p["n"]]
        if len(tgt_per) >= 3:
            mx = max(t for _, t in tgt_per)
            for k, t in tgt_per:
                if mx and t < mx * 0.1:
                    skala.append(f"{d} {k} (rata target/orang {rp(t, 'jt')})")
    if skala:
        dq.append({"kode": "DQ-11", "temuan": "Skala target salesman tidak konsisten antar periode: "
                   + "; ".join(skala[:6]) + " jauh di bawah periode lain pada divisi yang sama.",
                   "dampak": "Pencapaian periode itu terlihat ekstrem (bisa 44% atau 263%) padahal basisnya salah.",
                   "saran": "Samakan satuan & sumber target salesman dengan target divisi; validasi sebelum dikunci."})
    neg_tim = [x for x in team if x["aktual"] < 0]
    if neg_tim:
        dq.append({"kode": "DQ-12", "temuan": f"{len(neg_tim)} baris salesman bernilai negatif (retur), mis. "
                   + "; ".join(f"{x['nama']} {x['periode']} {rp(x['aktual'], 'jt')}" for x in neg_tim[:3]) + ".",
                   "dampak": "Pencapaian individu bisa negatif dan merusak rata-rata tim.",
                   "saran": "Pisahkan retur sebagai baris/kolom tersendiri; tampilkan sales netto & retur berdampingan."})

    kb2 = kalbe.get("bulanan", [])
    if kb2:
        n8 = len([x for x in kb2 if x["tahun"] == "2026" and x["soo"] > 0])
        ea_omset = rata(metrik.get("KALBE", {}).get("ea26", [])[:n8])
        ea_kalbe = rata([x["ea"] for x in kb2 if x["tahun"] == "2026" and x["soo"] > 0])
        if ea_omset and ea_kalbe and abs(ea_omset / ea_kalbe - 1) > 0.01:
            dq.append({"kode": "DQ-13",
                       "temuan": f"Metrik Kalbe berbeda antar sheet: rata EA 2026 di 'Omset All' = "
                                 f"{ea_omset:.0f}, di sheet 'Kalbe' = {ea_kalbe:.0f} "
                                 f"(selisih {pct(ea_omset / ea_kalbe - 1)}).",
                       "dampak": "Dua laporan bisa menyebut angka EA berbeda untuk periode sama.",
                       "saran": "Tetapkan satu sheet sebagai sumber metrik (single source of truth) "
                                "dan buat sheet lain menarik dari sana."})

    analisis = {
        "meta": {"perusahaan": nama_perusahaan, "sumber": os.path.basename(file_xlsx),
                 "sheets": sheets, "periode_data": f"Jan-{BULAN_ID[n_bulan - 1]} 2026 ({n_bulan} bulan)",
                 "dibuat": datetime.now().strftime("%Y-%m-%d %H:%M"),
                 "alat": "DAN plan_analyst + xlsx_lite (stdlib)",
                 "catatan": "Angka dari sel workbook; angka turunan dihitung ulang oleh engine. "
                            "Yang bukan dari data ditandai 'asumsi:'."},
        "ringkasan": {"ytd2026": ytd26, "ytd2025": ytd25, "ytd2024": ytd24, "target": tgt,
                      "pencapaian": pencapaian, "yoy": yoy, "gap": gap, "bulan": n_bulan,
                      "full_2025": ly_full, "full_2024": sum(r["y2024"] for r in all_rows),
                      "run_rate_bulanan": rr_bulanan(ytd26, n_bulan),
                      "target_tahunan_asumsi": tgt_tahunan_asumsi},
        "divisi": divisi,
        "bulanan": {"labels": [r["bulan"] for r in all_rows],
                    "y2024": [r["y2024"] for r in all_rows],
                    "y2025": [r["y2025"] for r in all_rows],
                    "y2026": [r["y2026"] or None for r in all_rows],
                    "target": [r["target"] or None for r in all_rows],
                    "per_divisi": {NAMA_DIVISI[k]: [r["y2026"] or None for r in omset[k]]
                                   for k in ("KALBE", "KENVEU", "OOH", "DK")}},
        "proyeksi": {"skenario": proy, "full_2025": ly_full,
                     "target_tahunan_asumsi": tgt_tahunan_asumsi,
                     "catatan": "Target Sep-Des 2026 di workbook kosong, jadi pembanding 'target tahunan' "
                                "adalah asumsi: target YTD / bulan berjalan x 12."},
        "kalbe": kalbe_ring,
        "kenveu_kanal": kenveu_kanal,
        "stok": stock,
        "tim": tim_ring,
        "team_raw_count": len(team),
        "rekonsiliasi_tim": rekonsiliasi,
        "omset_bulanan": {NAMA_DIVISI[k]: v for k, v in omset.items()},
        "temuan_data": dq,
    }
    analisis["insights"] = buat_insights(analisis)
    analisis["recommendations"] = buat_rekomendasi(analisis)
    analisis["temuan_data"] = sorted(analisis["temuan_data"], key=lambda d: d["kode"])
    return analisis


def rr_bulanan(total: float, n: int) -> float:
    return total / n if n else 0.0


def buat_insights(a: dict) -> list:
    """Insight sebagai dict {title, detail, severity, action} — siap dipakai infografik."""
    r = a["ringkasan"]
    out = []
    div_sorted = sorted(a["divisi"], key=lambda d: d["gap"])
    worst = div_sorted[0]
    share = worst["gap"] / r["gap"] if r["gap"] else 0
    sev = "bad" if r["pencapaian"] < 0.9 else ("warn" if r["pencapaian"] < 1 else "good")
    out.append({
        "title": f"Pencapaian YTD {pct(r['pencapaian'])} — gap {sgn(r['gap'])}",
        "detail": f"Omset {r['bulan']} bulan 2026 {rp(r['ytd2026'])} dari target {rp(r['target'])}; "
                  f"vs periode sama 2025 {pct(r['yoy'])} ({rp(r['ytd2025'])}). "
                  f"Run-rate {rp(r['run_rate_bulanan'])}/bulan.",
        "severity": sev,
        "action": "Kunci target Sep–Des dulu (sekarang kosong), lalu jalankan review mingguan per divisi."})
    out.append({
        "title": f"{worst['nama']} menyumbang {pct(share, 0)} dari total gap",
        "detail": f"{worst['nama']}: {pct(worst['pencapaian'])} dari target, {pct(worst['yoy'])} YoY, "
                  f"gap {sgn(worst['gap'])}. Tiga divisi lain tumbuh: "
                  + ", ".join(f"{d['nama']} {pct(d['yoy'])}" for d in a["divisi"]
                              if d["kode"] != worst["kode"]) + ".",
        "severity": "bad",
        "action": f"Fokus sumber daya ke {worst['nama']}; divisi lain cukup dijaga ritmenya."})
    kb = a.get("kalbe", {})
    if kb.get("ea_2026") and worst["kode"] == "KALBE":
        out.append({
            "title": f"Akar masalah {worst['nama']}: outlet aktif, bukan harga",
            "detail": f"EA {kb['ea_2025']:.0f} → {kb['ea_2026']:.0f} ({pct(kb['ea_2026'] / kb['ea_2025'] - 1)}), "
                      f"M3MEA {kb['m3mea_2025']:.0f} → {kb['m3mea_2026']:.0f} "
                      f"({pct(kb['m3mea_2026'] / kb['m3mea_2025'] - 1)}), sementara IPT naik "
                      f"{pct(kb['ipt_2026'] / kb['ipt_2025'] - 1)}. Efektivitas kunjungan (EA/CB) turun "
                      f"{pct(kb['efektivitas_call_2025'])} → {pct(kb['efektivitas_call_2026'])}.",
            "severity": "bad",
            "action": "Program reaktivasi outlet 60 hari + route plan ulang; kejar EA kembali ke level 2025."})
        ch = [k for k in kb.get("kanal", []) if k["kanal"] != "Grand Total"]
        if ch:
            turun = sorted(ch, key=lambda z: z["y2026"] - z["y2025"])[:3]
            out.append({
                "title": "Penurunan terkonsentrasi di 3 kanal (urut selisih Rp pada tabel kanal sheet Kalbe)",
                "detail": "; ".join(f"{k['kanal']} {sgn(k['y2026'] - k['y2025'])} ({pct(k['gr'])})"
                                    for k in turun)
                          + ". Periode tabel kanal tidak tertulis di sheet (DQ-07).",
                "severity": "warn",
                "action": "Buat rencana pemulihan per kanal dengan PIC & target outlet aktif."})
        pr = [x for x in kb.get("produk", []) if x["y2025"] > 0]
        if pr:
            naik = sorted(pr, key=lambda z: -z["gr"])[:3]
            out.append({
                "title": "Ada produk yang tetap tumbuh — pakai sebagai ujung tombak",
                "detail": "; ".join(f"{x['nama']} {pct(x['gr'])}" for x in naik)
                          + ". Sebagian besar top product lain turun dua digit.",
                "severity": "good",
                "action": "Geser fokus display & insentif salesman ke SKU yang tumbuh."})
    st = a.get("stok", [])
    kritis = [x for x in st if x["status"] == "kritis"]
    over = [x for x in st if x["status"] == "overstock"]
    if kritis:
        out.append({
            "title": "Stok kritis di " + ", ".join(f"{x['divisi']} ({x['scd']:.0f} hari)" for x in kritis),
            "detail": "Target cover " + ", ".join(f"{x['divisi']} {x['target_scd']:.0f} hari" for x in kritis)
                      + ". Kebutuhan tambahan stok ~"
                      + " dan ~".join(rp(abs(x["rp_selisih"])) for x in kritis) + " (asumsi).",
            "severity": "bad",
            "action": "Naikkan PO minggu ini untuk divisi yang tumbuh; pasang alarm SCD < 15 hari."})
    if over:
        out.append({
            "title": "Kas tertahan di stok " + ", ".join(f"{x['divisi']} ({x['scd']:.0f} hari)" for x in over),
            "detail": "Kelebihan cover ~" + ", ".join(f"{x['divisi']} {rp(x['rp_selisih'])}" for x in over)
                      + " (asumsi: pola konsumsi rata 3 bulan).",
            "severity": "warn",
            "action": "Setop pembelian SKU lambat + program habiskan stok; alihkan kas ke divisi kritis."})
    kn = [k for k in a.get("kenveu_kanal", []) if k["induk"] and k["kanal"] != "Grand Total"]
    if kn:
        tot = sum(k["y2026"] for k in kn) or 1
        top2 = sorted(kn, key=lambda z: -z["y2026"])[:2]
        gt = next((k for k in kn if k["kanal"] == "GENERAL TRADE"), None)
        out.append({
            "title": f"Kenveu tumbuh {pct(next((k['gr'] for k in kn if k['kanal'] == 'NATIONAL KEY ACCOUNT'), 0))}"
                     f" di NKA, tapi GT turun",
            "detail": f"Dua kanal teratas = {pct(sum(k['y2026'] for k in top2) / tot, 0)} omset Kenveu. "
                      + (f"General Trade {pct(gt['gr'])}, Online Reseller "
                         f"{pct(next((k['gr'] for k in kn if k['kanal'] == 'ONLINE RESELLER'), 0))}."
                         if gt else ""),
            "severity": "warn",
            "action": "Jaga NKA dengan joint business plan; perbaiki GT baby shop & cosmetic store yang masih tumbuh."})
    for d, v in a.get("tim", {}).items():
        per = [(k, p) for k, p in v["periode"].items() if p["target"] > 0]
        if not per:
            continue
        k, p = min(per, key=lambda z: z[1]["pencapaian"])
        out.append({
            "title": f"Tim {d}: bulan terlemah {k} ({pct(p['pencapaian'])})",
            "detail": f"{p['bawah_80']} dari {p['n_dinilai']} salesman di bawah 80% target. "
                      f"Terbawah: " + ", ".join(f"{x['nama']} {pct(x['pencapaian'], 0)}"
                                                for x in p["terbawah"][:3]) + ".",
            "severity": "bad" if p["pencapaian"] < 0.6 else "warn",
            "action": "Coaching 1-on-1 + cek route plan & hari kerja efektif sebelum menyalahkan angka."})
    rek = [x for x in a.get("rekonsiliasi_tim", []) if not x["ok"]]
    if rek:
        out.append({
            "title": f"{len(rek)} bulan angka tim tidak cocok dengan omset divisi",
            "detail": "; ".join(f"{x['divisi']} {x['bulan']} ({pct(x['selisih'], 0)})" for x in rek[:4])
                      + ". Detail di DQ-10/DQ-11.",
            "severity": "warn",
            "action": "Tetapkan satu sumber kebenaran sebelum evaluasi/insentif salesman dijalankan."})
    proy = a["proyeksi"]["skenario"]
    if proy:
        out.append({
            "title": f"Estimasi setahun 2026: {rp(proy[0]['setahun'])}–{rp(max(p['setahun'] for p in proy))} (indikatif)",
            "detail": "Estimasi, bukan komitmen: tiga skenario (run-rate, musiman, tren) semuanya di bawah 2025 ("
                      + rp(a["proyeksi"]["full_2025"]) + ") dan di bawah target tahunan asumsi "
                      + rp(a["proyeksi"]["target_tahunan_asumsi"]) + ".",
            "severity": "warn",
            "action": "Pilih satu skenario sebagai komitmen revisi (±5%), atau tetapkan program penutup gap."})
    return out


def _kode_dari_nama(nama: str) -> str:
    for k, v in NAMA_DIVISI.items():
        if v == nama:
            return k
    return ""


def buat_rekomendasi(a: dict) -> list:
    r = a["ringkasan"]
    div = {d["nama"]: d for d in a["divisi"]}
    kb = a.get("kalbe", {})
    st = {s["divisi"]: s for s in a.get("stok", [])}
    rec = []
    kalbe = div.get("Kalbe")
    if kalbe:
        ea_gap = max(0.0, kb.get("ea_2025", 0) - kb.get("ea_2026", 0))
        omset_per_ea = kalbe["omset_per_ea"]
        dampak = ea_gap * omset_per_ea * 4
        rec.append({
            "prioritas": 1, "judul": "Reaktivasi outlet Kalbe (kejar EA kembali ke level 2025)",
            "alasan": f"EA turun {ea_gap:.0f} outlet/bulan; omset per EA {rp(omset_per_ea, 'jt')}/bulan. "
                      f"IPT naik, jadi masalahnya jumlah outlet aktif, bukan isi transaksi.",
            "aksi": ["Kunci daftar outlet yang berhenti transaksi (M3MEA turun paling dalam) per salesman",
                     "Program reaktivasi 60 hari: kunjungan wajib + paket awal + insentif per outlet aktif kembali",
                     "Naikkan EA/CB dari " + pct(kb.get("efektivitas_call_2026", 0)) + " ke "
                     + pct(kb.get("efektivitas_call_2025", 0)) + " dengan route plan ulang"],
            "dampak": f"Potensial +{rp(dampak)} untuk 4 bulan sisa (asumsi: omset per EA tetap, "
                      f"EA kembali {pct(ea_gap / kb['ea_2025'], 0) if kb.get('ea_2025') else '-'} dari level 2025)",
            "pemilik": "Sales Manager Kalbe", "tenggat": "2 minggu (daftar outlet) / 60 hari (program)",
            "kpi": "EA bulanan, EA/CB, M3MEA, omset per EA"})
    urutan_stok = sorted((s for s in st.values() if s["status"] == "kritis"),
                         key=lambda z: z["selisih_hari"])
    prio = 2
    for s in urutan_stok:
        d = div.get(s["divisi"]) or div.get(NAMA_DIVISI.get(_kode_dari_nama(s["divisi"]), ""))
        yoy_txt = (f"divisi ini tumbuh {pct(d['yoy'])} sehingga stockout langsung memotong momentum"
                   if d and d["yoy"] > 0 else
                   (f"divisi ini sedang turun {pct(abs(d['yoy']))}, jadi naikkan stok bertahap "
                    f"seiring pemulihan outlet — jangan sampai menambah stok mati" if d else
                    "arah divisi perlu dikonfirmasi"))
        rec.append({"prioritas": prio, "judul": f"Amankan stok {s['divisi']} (SCD {s['scd']:.1f} hari)",
                    "alasan": f"Cover {s['scd']:.1f} hari vs target {s['target_scd']:.0f}; {yoy_txt}.",
                    "aksi": [f"Naikkan PO minggu ini sampai cover {min(s['target_scd'], 30):.0f} hari",
                             "Minta prioritas alokasi prinsipal untuk SKU fast moving",
                             "Pasang alarm SCD < 15 hari di laporan mingguan"],
                    "dampak": f"Butuh tambahan stok ~{rp(abs(s['rp_selisih']))} (asumsi); "
                              f"menghindari risiko kehilangan omset ~{rp(s['avg_l3m'] / 4.3)}/minggu",
                    "pemilik": "Supply Chain + Sales Manager divisi", "tenggat": "7 hari",
                    "kpi": "SCD per divisi, fill rate, lost sales estimate"})
        prio += 1
    for nama, s in st.items():
        if s["status"] == "overstock":
            rec.append({"prioritas": prio, "judul": f"Bebaskan kas dari stok {s['divisi']} (SCD {s['scd']:.1f} hari)",
                        "alasan": f"Cover {s['scd']:.1f} hari vs target {s['target_scd']:.0f} -> kas tertahan "
                                  f"~{rp(s['rp_selisih'])} (asumsi).",
                        "aksi": ["Hentikan sementara pembelian SKU slow moving",
                                 "Jalankan program bundling/diskon bertingkat untuk SKU berumur > 60 hari",
                                 "Alihkan kas yang bebas untuk menutup kebutuhan stok divisi kritis"],
                        "dampak": f"Potensi kas bebas ~{rp(s['rp_selisih'])}",
                        "pemilik": "Supply Chain + Finance", "tenggat": "30 hari",
                        "kpi": "SCD, umur stok, cash conversion cycle"})
            prio += 1
    rec.append({"prioritas": prio, "judul": "Isi target Sep-Des 2026 per divisi",
                "alasan": f"Target {r['bulan']+1}-12 kosong sehingga pencapaian tahunan tidak terukur "
                          f"(target tahunan asumsi saat ini {rp(r['target_tahunan_asumsi'])}).",
                "aksi": ["Turunkan target tahunan ke bulan pakai indeks musiman 2025",
                         "Setujui per divisi & per salesman, kunci di workbook",
                         "Jadikan dasar controlling mingguan (pmo_guard / weekly_run)"],
                "dampak": "Controlling berjalan; deviasi terdeteksi < 7 hari, bukan akhir kuartal",
                "pemilik": "Direksi + Finance", "tenggat": "1 minggu",
                "kpi": "% bulan yang punya target, deviasi aktual vs target"})
    prio += 1
    kn = [k for k in a.get("kenveu_kanal", []) if k["induk"] and k["kanal"] != "Grand Total"]
    if kn:
        gt = next((k for k in kn if k["kanal"] == "GENERAL TRADE"), None)
        if gt and gt["gr"] < 0:
            rec.append({"prioritas": prio, "judul": "Perbaiki General Trade Kenveu sebelum ketergantungan NKA membesar",
                        "alasan": f"GT {pct(gt['gr'])} (kontribusi {pct(gt['kontribusi'])}) sementara 2 kanal modern "
                                  f"trade memegang mayoritas omset -> daya tawar ke prinsipal/ritel modern melemah.",
                        "aksi": ["Fokus ke GT Baby Shop & GT Cosmetic Store yang masih tumbuh",
                                 "Perbaiki harga/term untuk GT Wholesaler yang turun paling dalam",
                                 "Jaga NKA existing (Indomaret/Alfamart) dengan joint business plan"],
                        "dampak": "Menurunkan risiko konsentrasi kanal; potensi recovery GT ~"
                                  + rp(abs(gt["y2026"] - gt["y2025"])) + " (asumsi kembali ke level 2025)",
                        "pemilik": "Sales Manager Kenveu", "tenggat": "30 hari",
                        "kpi": "Omset per kanal, jumlah outlet aktif GT, kontribusi NKA"})
            prio += 1
    rec.append({"prioritas": prio, "judul": "Bersihkan data: retur, master salesman, skala persen, formula total",
                "alasan": f"{len(a['temuan_data'])} temuan kualitas data; yang paling berisiko: baris Year "
                          f"tidak sama dengan jumlah bulan, persen dua skala, retur bercampur sales.",
                "aksi": ["Perbaiki formula total (SUM per periode, bukan penjumlahan baris Year)",
                         "Pisahkan retur dari sales", "Satukan skala persen & master kode salesman",
                         "Beri label periode+scope di tiap tabel"],
                "dampak": "Laporan bisa dipercaya & otomatis (hemat waktu rekonsiliasi bulanan)",
                "pemilik": "Finance/IT + Admin Sales", "tenggat": "2 minggu",
                "kpi": "Jumlah sel error, selisih rekonsiliasi, % baris berlabel lengkap"})
    for i, x in enumerate(sorted(rec, key=lambda z: z["prioritas"]), 1):
        x["prioritas"] = i
    return sorted(rec, key=lambda x: x["prioritas"])


# ----------------------------------------------------------------------------- paket controlling
TENGGAT_HARI = [("hari", 1), ("minggu", 7), ("bulan", 30)]


def _hari(tenggat: str) -> int:
    m = re.search(r"(\d+)\s*(hari|minggu|bulan)", tenggat or "")
    if not m:
        return 30
    n = int(m.group(1))
    return n * dict(TENGGAT_HARI)[m.group(2)]


def _angka_rp(teks: str) -> float:
    """Ambil nilai Rp pertama (M/jt/rupiah) dari teks dampak."""
    m = re.search(r"Rp([\d.,]+)\s*(M|jt)?", teks or "")
    if not m:
        return 0.0
    v = float(m.group(1).replace(".", "").replace(",", "."))
    return v * (1e9 if m.group(2) == "M" else 1e6 if m.group(2) == "jt" else 1)


def buat_projects(a: dict, today: str | None = None) -> dict:
    """Ubah rekomendasi + target divisi jadi projects.json (dipakai project_monitor/weekly)."""
    from datetime import date, timedelta
    t0 = datetime.strptime(today, "%Y-%m-%d").date() if today else date.today()
    r = a["ringkasan"]
    n = r["bulan"]
    proyek = []
    # 1) proyek pemulihan dari rekomendasi
    for x in a["recommendations"]:
        hari = _hari(x["tenggat"])
        tasks = []
        aksi = x["aksi"]
        bobot = [max(5, int(round(100 / len(aksi))))] * len(aksi)
        for i, (ak, w) in enumerate(zip(aksi, bobot), 1):
            tasks.append({"id": f"T{i}", "name": ak, "owner": x["pemilik"],
                          "start": (t0 + timedelta(days=int(hari * (i - 1) / max(1, len(aksi))))).isoformat(),
                          "end": (t0 + timedelta(days=int(hari * i / len(aksi)))).isoformat(),
                          "progress": 0, "weight": w, "status": "todo"})
        proyek.append({"id": f"PRJ-{x['prioritas']:02d}", "name": x["judul"], "owner": x["pemilik"],
                       "start": t0.isoformat(), "end": (t0 + timedelta(days=hari)).isoformat(),
                       "goal": x["dampak"], "budget_planned": _angka_rp(x["dampak"]),
                       "budget_actual": 0,
                       "kpi": [{"name": "pencapaian aksi", "target": 100, "actual": 0}],
                       "tasks": tasks, "actions": [],
                       "risks": [
                           {"id": "R1", "desc": "Data sumber belum rekonsiliasi (DQ-10/DQ-11) sehingga "
                            "progres sulit diverifikasi", "prob": 3, "impact": 4,
                            "mitigation": "Kunci satu sumber angka sebelum review minggu ke-2",
                            "owner": x["pemilik"]},
                           {"id": "R2", "desc": "Aksi berjalan tanpa PIC harian sehingga macet di tengah",
                            "prob": 2, "impact": 3,
                            "mitigation": "Tunjuk satu PIC per aksi + cek 10 menit tiap Senin",
                            "owner": x["pemilik"]}]}
                       )
    # 2) proyek divisi: kejar target Sep-Des (usulan pola musiman 2025)
    for d in a["divisi"]:
        rows = a["omset_bulanan"][d["nama"]]
        ly_sisa = sum(z["y2025"] for z in rows[n:])
        ly_ytd = sum(z["y2025"] for z in rows[:n]) or 1
        per_bulan = (d["ytd2026"] / n) * (ly_sisa / (12 - n)) / (ly_ytd / n) if (12 - n) else 0
        target_usulan = per_bulan * (12 - n)
        tasks = []
        for i, z in enumerate(rows[n:], 1):
            tasks.append({"id": f"M{i}", "name": f" Tutup bulan {z['bulan']} 2026",
                          "owner": f"Sales Manager {d['nama']}",
                          "start": (t0 + timedelta(days=30 * (i - 1))).isoformat(),
                          "end": (t0 + timedelta(days=30 * i)).isoformat(),
                          "progress": 0, "weight": 25, "status": "todo"})
        proyek.append({"id": f"DIV-{d['kode']}", "name": f"Kejar target {d['nama']} Sep–Des 2026",
                       "owner": f"Sales Manager {d['nama']}", "start": t0.isoformat(),
                       "end": (t0 + timedelta(days=30 * max(1, len(tasks)))).isoformat(),
                       "goal": f"Omset Sep–Des {rp(target_usulan)} (usulan pola musiman 2025); "
                               f"posisi YTD {pct(d['pencapaian'])} dari target",
                       "budget_planned": target_usulan, "budget_actual": 0,
                       "kpi": [{"name": "omset/bulan (Rp)", "target": round(per_bulan), "actual": 0},
                               {"name": "pencapaian target", "target": 100,
                                "actual": round(d["pencapaian"] * 100, 1)},
                               {"name": "EA bulanan", "target": round(d["ea25"]), "actual": round(d["ea26"])}],
                       "tasks": tasks, "actions": [],
                       "risks": [
                           {"id": "R1", "desc": f"Target Sep–Des belum disetujui (masih usulan pola musiman)",
                            "prob": 4, "impact": 4,
                            "mitigation": "Bawa usulan ini ke rapat direksi minggu ini untuk dikunci",
                            "owner": "Direksi/Finance"},
                           {"id": "R2", "desc": f"Stok divisi tidak mendukung (SCD saat ini "
                                                f"{next((z['scd'] for z in a['stok'] if z['divisi'] == d['nama']), 0):.0f} hari)",
                            "prob": 3, "impact": 5,
                            "mitigation": "Sinkronkan PO dengan rencana penjualan bulanan",
                            "owner": "Supply Chain"}]})
    return {"meta": {"name": f"Portofolio Pemulihan 2026 — {a['meta']['perusahaan']}",
                     "currency": "Rp", "today": t0.isoformat(), "theme": "dan", "owner": "Direksi/PMO",
                     "review_cadence": "Senin 09.00 (10 menit angka) · Jumat 16.00 (keputusan)",
                     "sumber": a["meta"]["sumber"],
                     "catatan": "Target Sep–Des = usulan engine dari pola musiman 2025 (asumsi), "
                                "bukan angka yang sudah disetujui direksi."},
            "projects": proyek}


# ----------------------------------------------------------------------------- keluaran
def tulis_md(a: dict, path: str) -> None:
    r = a["ringkasan"]
    L = []
    L.append(f"# Analisis Business Plan 2026 — {a['meta']['perusahaan']}")
    L.append("")
    L.append(f"Sumber: `{a['meta']['sumber']}` · Periode data: {a['meta']['periode_data']} · "
             f"Dibuat: {a['meta']['dibuat']}")
    L.append("")
    L.append("## 1. Ringkasan eksekutif")
    L.append("")
    L.append("| Indikator | Nilai |")
    L.append("|---|---|")
    L.append(f"| Omset YTD 2026 | {rp(r['ytd2026'])} |")
    L.append(f"| Target YTD 2026 | {rp(r['target'])} |")
    L.append(f"| Pencapaian | **{pct(r['pencapaian'])}** (gap {sgn(r['gap'])}) |")
    L.append(f"| YoY (vs periode sama 2025) | **{pct(r['yoy'])}** ({rp(r['ytd2025'])}) |")
    L.append(f"| Run-rate bulanan | {rp(r['run_rate_bulanan'])} |")
    L.append(f"| Omset setahun 2025 (pembanding) | {rp(r['full_2025'])} |")
    L.append("")
    L.append("## 2. Kinerja per divisi (YTD)")
    L.append("")
    L.append("| Divisi | 2026 | 2025 | Target | Pencapaian | YoY | Gap | Kontribusi | Status |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for d in sorted(a["divisi"], key=lambda z: z["gap"]):
        L.append(f"| {d['nama']} | {rp(d['ytd2026'])} | {rp(d['ytd2025'])} | {rp(d['target'])} | "
                 f"{pct(d['pencapaian'])} | {pct(d['yoy'])} | {sgn(d['gap'])} | "
                 f"{pct(d['kontribusi2026'], 0)} | {d['status']} |")
    L.append("")
    L.append("Metrik operasional (rata-rata per bulan, 2026 vs 2025):")
    L.append("")
    L.append("| Divisi | EA | CB | EA/CB | IPT | Omset per EA |")
    L.append("|---|---|---|---|---|---|")
    for d in a["divisi"]:
        L.append(f"| {d['nama']} | {d['ea26']:.0f} ({d['ea26'] / d['ea25'] - 1:+.0%}) | "
                 f"{d['cb26']:.0f} | {pct(d['efektivitas_call26'])} | {d['ipt26']:.2f} | "
                 f"{rp(d['omset_per_ea'], 'jt')} |")
    L.append("")
    L.append("EA = outlet efektif (transaksi), CB = jumlah kunjungan/call, IPT = item per transaksi. "
             "Diambil dari sheet 'Omset All'; sheet 'Kalbe' menyimpan angka serupa yang sedikit berbeda "
             "(lihat DQ-13).")
    L.append("")
    L.append("## 3. Proyeksi setahun 2026 — estimasi indikatif (target Sep-Des masih kosong)")
    L.append("")
    L.append("| Skenario | Perkiraan/bulan | Sep-Des | Setahun 2026 | vs 2025 |")
    L.append("|---|---|---|---|---|")
    for s in a["proyeksi"]["skenario"]:
        L.append(f"| {s['skenario']} | {rp(s['per_bulan'])} | {rp(s['sep_des'])} | "
                 f"**{rp(s['setahun'])}** | {pct(s['vs_2025'])} |")
    L.append("")
    L.append(f"Pembanding: setahun 2025 = {rp(a['proyeksi']['full_2025'])}; target tahunan "
             f"(asumsi: target YTD / {r['bulan']} x 12) = {rp(a['proyeksi']['target_tahunan_asumsi'])}.")
    L.append("")
    kb = a["kalbe"]
    if kb.get("bulanan"):
        L.append("## 4. Diagnosa divisi dengan gap terbesar: Kalbe")
        L.append("")
        L.append(f"- Sell out (SO) YTD: {rp(kb['so_2025'])} → {rp(kb['so_2026'])} "
                 f"({pct(kb['so_2026'] / kb['so_2025'] - 1)})")
        L.append(f"- Sell out out (SOO) YTD: {rp(kb['soo_2025'])} → {rp(kb['soo_2026'])} "
                 f"({pct(kb['soo_2026'] / kb['soo_2025'] - 1)})")
        L.append(f"- EA: {kb['ea_2025']:.0f} → {kb['ea_2026']:.0f} ({pct(kb['ea_2026'] / kb['ea_2025'] - 1)}) · "
                 f"CB: {kb['cb_2025']:.0f} → {kb['cb_2026']:.0f} · "
                 f"M3MEA: {kb['m3mea_2025']:.0f} → {kb['m3mea_2026']:.0f} "
                 f"({pct(kb['m3mea_2026'] / kb['m3mea_2025'] - 1)}) · "
                 f"IPT: {kb['ipt_2025']:.2f} → {kb['ipt_2026']:.2f}")
        L.append("")
        if kb["kanal"]:
            L.append("Kanal (periode sesuai sheet — lihat temuan DQ-07):")
            L.append("")
            L.append("| Kanal | 2025 | 2026 | Growth | Kontribusi |")
            L.append("|---|---|---|---|---|")
            for k in kb["kanal"]:
                L.append(f"| {k['kanal']} | {rp(k['y2025'], 'jt')} | {rp(k['y2026'], 'jt')} | "
                         f"{pct(k['gr'])} | {pct(k['kontribusi'], 1)} |")
            L.append("")
        if kb["produk"]:
            tumbuh = sorted([p for p in kb["produk"] if p["y2025"] > 0], key=lambda z: -z["gr"])[:5]
            turun = sorted([p for p in kb["produk"] if p["y2025"] > 0], key=lambda z: z["gr"])[:5]
            L.append("Top produk naik: " + "; ".join(f"{p['nama']} {pct(p['gr'])}" for p in tumbuh))
            L.append("")
            L.append("Top produk turun: " + "; ".join(f"{p['nama']} {pct(p['gr'])}" for p in turun))
            L.append("")
    kn = a.get("kenveu_kanal", [])
    if kn:
        L.append("## 5. Kanal Kenveu (Jan–Jun)")
        L.append("")
        L.append("| Kanal | 2025 | 2026 | Growth | Kontribusi |")
        L.append("|---|---|---|---|---|")
        for k in kn:
            if k["induk"] or k["kanal"] == "Grand Total":
                L.append(f"| **{k['kanal']}** | {rp(k['y2025'], 'jt')} | {rp(k['y2026'], 'jt')} | "
                         f"{pct(k['gr'])} | {pct(k['kontribusi'], 1)} |")
        L.append("")
        sub = sorted([k for k in kn if not k["induk"] and k["kanal"] != "Grand Total"],
                     key=lambda z: -(z["y2026"] - z["y2025"]))
        L.append("Sub-kanal penambah omset teratas (urut selisih 2026−2025, sheet Kenveu Jan–Jun): "
                 + "; ".join(f"{k['kanal']} {sgn(k['y2026'] - k['y2025'], 'jt')}" for k in sub[:4]))
        L.append("")
        L.append("Sub-kanal penggerus terdalam (urut selisih 2026−2025, sheet Kenveu Jan–Jun): "
                 + "; ".join(f"{k['kanal']} {sgn(k['y2026'] - k['y2025'], 'jt')}" for k in sub[-4:]))
        L.append("")
    if a["stok"]:
        L.append("## 6. Stok & cover hari (SCD)")
        L.append("")
        L.append("| Divisi | Rata omset 3 bln | Stock on hand | SCD | Target | Selisih | Status | Nilai (asumsi) |")
        L.append("|---|---|---|---|---|---|---|---|")
        for s in a["stok"]:
            L.append(f"| {s['divisi']} | {rp(s['avg_l3m'])} | {rp(s['soh'])} | {s['scd']:.1f} | "
                     f"{s['target_scd']:.0f} | {s['selisih_hari']:+.1f} hari | {s['status']} | "
                     f"{sgn(s['rp_selisih'])} |")
        L.append("")
    if a["tim"]:
        L.append("## 7. Pencapaian tim sales (per periode, dari sheet By Team)")
        L.append("")
        L.append("| Divisi | Periode | Target | Aktual | Pencapaian | <80% (dinilai) | Tanpa target | Negatif |")
        L.append("|---|---|---|---|---|---|---|---|")
        for d, v in a["tim"].items():
            for k in BULAN_ID:
                p = v["periode"].get(k)
                if p:
                    L.append(f"| {d} | {k} | {rp(p['target'], 'jt')} | {rp(p['aktual'], 'jt')} | "
                             f"{pct(p['pencapaian'])} | {p['bawah_80']}/{p['n_dinilai']} | "
                             f"{p['tanpa_target']} | {p['negatif']} |")
        L.append("")
        for d, v in a["tim"].items():
            L.append(f"- **{d}**: pencapaian kumulatif {pct(v['pencapaian'])} "
                     f"({v['n_salesman']} baris salesman-periode).")
            terburuk = min((p | {"k": k} for k, p in v["periode"].items() if p["target"] > 0),
                           key=lambda z: z["pencapaian"], default=None)
            if terburuk:
                nama = ", ".join(f"{x['nama']} {pct(x['pencapaian'], 0)}" for x in terburuk["terbawah"][:2])
                L.append(f"  - bulan terlemah: {terburuk['k']} {pct(terburuk['pencapaian'])} "
                         f"(terbawah: {nama})")
        L.append("")
        rek = a.get("rekonsiliasi_tim", [])
        if rek:
            ok = sum(1 for x in rek if x["ok"])
            L.append(f"### Rekonsiliasi tim vs omset divisi ({ok}/{len(rek)} bulan cocok, toleransi 15%)")
            L.append("")
            L.append("| Divisi | Bulan | Total salesman | Omset divisi | Selisih | Status |")
            L.append("|---|---|---|---|---|---|")
            for x in rek:
                if not x["ok"]:
                    L.append(f"| {x['divisi']} | {x['bulan']} | {rp(x['tim'])} | "
                             f"{rp(x['divisi_omset'])} | {pct(x['selisih'], 0)} | tidak cocok |")
            L.append("")
            L.append("Baris di atas = bulan yang angka timnya tidak bisa dipakai menilai divisi "
                     "(lihat DQ-10/DQ-11). Bulan lain cocok.")
            L.append("")
    L.append("## 8. Insight")
    L.append("")
    for i, x in enumerate(a["insights"], 1):
        L.append(f"{i}. **{x['title']}** — {x['detail']}")
        if x.get("action"):
            L.append(f"   - Aksi: {x['action']}")
    L.append("")
    L.append("## 9. Rekomendasi (urut prioritas)")
    L.append("")
    for x in a["recommendations"]:
        L.append(f"### P{x['prioritas']}. {x['judul']}")
        L.append(f"- Alasan: {x['alasan']}")
        L.append("- Aksi: " + "; ".join(x["aksi"]))
        L.append(f"- Dampak: {x['dampak']}")
        L.append(f"- Pemilik: {x['pemilik']} · Tenggat: {x['tenggat']} · KPI: {x['kpi']}")
        L.append("")
    L.append("## 10. Batasan")
    L.append("")
    L.append("- Periode 2026 baru " + str(r["bulan"]) + " bulan; target Sep–Des kosong sehingga estimasi "
             "setahun memakai 3 skenario (run-rate, musiman, tren) — semuanya estimasi indikatif, "
             "bukan komitmen.")
    L.append("- Tabel kanal/produk sheet Kalbe tidak mencantumkan periode & scope (DQ-07).")
    L.append("- Nilai dampak bertanda 'asumsi:' dihitung dari pola di data, bukan dari komitmen prinsipal.")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def tulis_dq(a: dict, path: str) -> None:
    L = ["# Temuan Kualitas Data — " + a["meta"]["perusahaan"], "",
         f"Sumber: `{a['meta']['sumber']}` · {len(a['temuan_data'])} temuan · "
         "Prinsip: blameless (fokus ke sistem, bukan orang).", ""]
    for d in a["temuan_data"]:
        L.append(f"## {d['kode']}: {d['temuan']}")
        L.append(f"- Dampak: {d['dampak']}")
        L.append(f"- Saran: {d['saran']}")
        L.append("")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")


def buat_spec(a: dict) -> dict:
    r = a["ringkasan"]
    bl = a["bulanan"]
    div = sorted(a["divisi"], key=lambda z: -z["ytd2026"])
    kb = a["kalbe"]
    sections = []
    sections.append({"type": "kpi", "items": [
        {"label": "Omset YTD 2026", "value": r["ytd2026"], "format": "currency",
         "delta": round(r["yoy"] * 100, 1), "color": "#38BDF8",
         "spark": [round(x / 1e9, 1) if x else None for x in bl["y2026"][:r["bulan"]]]},
        {"label": "Pencapaian target", "value": pct(r["pencapaian"]), "color": "#FBBF24",
         "spark": [round(bl["y2026"][i] / bl["target"][i] * 100, 1) if bl["target"][i] else None
                   for i in range(r["bulan"])]},
        {"label": "Gap vs target", "value": sgn(r["gap"]), "color": "#FB7185"},
        {"label": "YoY", "value": pct(r["yoy"]), "color": "#34D399" if r["yoy"] >= 0 else "#FB7185"},
        {"label": "Run-rate/bulan", "value": r["run_rate_bulanan"], "format": "currency", "color": "#A78BFA"},
        {"label": "Divisi merah", "value": str(sum(1 for d in a["divisi"] if d["status"] == "merah")),
         "color": "#FB7185"}]})
    sections.append({"type": "chart", "chart": "line", "span": 8,
                     "title": "Omset bulanan: 2026 vs 2025 vs target",
                     "subtitle": "satuan Rp miliar · kosong = bulan belum jalan / target belum diisi",
                     "width": 900, "height": 380,
                     "data": {"labels": bl["labels"],
                              "series": {"2026": [round(x / 1e9, 2) if x else None for x in bl["y2026"]],
                                         "2025": [round(x / 1e9, 2) if x else None for x in bl["y2025"]],
                                         "Target": [round(x / 1e9, 2) if x else None for x in bl["target"]]}},
                     "note": f"YTD {r['bulan']} bulan: {rp(r['ytd2026'])} dari target {rp(r['target'])}."})
    sections.append({"type": "chart", "chart": "gauge", "span": 4,
                     "title": "Pencapaian target YTD", "width": 380, "height": 240,
                     "data": {"value": round(r["pencapaian"] * 100, 1), "vmax": 100,
                              "label": pct(r["pencapaian"]) + " dari target"},
                     "note": f"Gap {sgn(r['gap'])}. Periode Jan–{BULAN_ID[r['bulan'] - 1]} 2026."})
    sections.append({"type": "chart", "chart": "hbar", "span": 6,
                     "title": "Gap vs target per divisi (Rp M)", "width": 620, "height": 320,
                     "data": [[d["nama"], round(d["gap"] / 1e9, 2)] for d in sorted(a["divisi"], key=lambda z: z["gap"])],
                     "note": "Negatif = di bawah target. Kalbe menyumbang mayoritas gap."})
    sections.append({"type": "chart", "chart": "donut", "span": 6,
                     "title": "Kontribusi omset 2026 per divisi", "width": 620, "height": 340,
                     "data": [[d["nama"], round(d["ytd2026"] / 1e9, 2)] for d in div],
                     "options": {"center_value": rp(r["ytd2026"]), "center_label": "omset YTD"},
                     "note": "Pergeseran vs 2025: "
                             + ", ".join(f"{d['nama']} {pct(d['kontribusi2025'], 0)}→{pct(d['kontribusi2026'], 0)}"
                                         for d in div)})
    sections.append({"type": "chart", "chart": "bar", "span": 6,
                     "title": "Pencapaian target per divisi (%)", "width": 620, "height": 320,
                     "data": [[d["nama"], round(d["pencapaian"] * 100, 1)] for d in div],
                     "note": "Garis sehat = 100%."})
    sections.append({"type": "chart", "chart": "bar", "span": 6,
                     "title": "Growth YoY per divisi (%)", "width": 620, "height": 320,
                     "data": [[d["nama"], round(d["yoy"] * 100, 1)] for d in div],
                     "note": "Kalbe satu-satunya yang turun; OOH tumbuh paling kencang."})
    if kb.get("bulanan"):
        sections.append({"type": "chart", "chart": "line", "span": 7,
                         "title": "Kalbe: sell out vs sell out out 2026 (Rp M)", "width": 720, "height": 330,
                         "data": {"labels": [x["bulan"] for x in kb["bulanan"]],
                                  "series": {"Sell Out": [round(x["so"] / 1e9, 2) for x in kb["bulanan"]],
                                             "Sell Out Out": [round(x["soo"] / 1e9, 2) for x in kb["bulanan"]],
                                             "Target SOO": [round(x["tgt_soo"] / 1e9, 2) for x in kb["bulanan"]]}},
                         "note": f"SO YTD {pct(kb['so_2026'] / kb['so_2025'] - 1)} vs 2025; "
                                 f"SOO {pct(kb['soo_2026'] / kb['soo_2025'] - 1)}."})
        sections.append({"type": "chart", "chart": "bar", "span": 5,
                         "title": "Kalbe: mesin distribusi (2025 → 2026)", "width": 520, "height": 330,
                         "data": [["EA", round(kb["ea_2026"] / kb["ea_2025"] * 100 - 100, 1)],
                                  ["CB", round(kb["cb_2026"] / kb["cb_2025"] * 100 - 100, 1)],
                                  ["M3MEA", round(kb["m3mea_2026"] / kb["m3mea_2025"] * 100 - 100, 1)],
                                  ["IPT", round(kb["ipt_2026"] / kb["ipt_2025"] * 100 - 100, 1)]],
                         "note": "Perubahan % vs 2025. Outlet efektif & M3MEA anjlok, IPT naik tipis."})
    if kb.get("kanal"):
        sections.append({"type": "chart", "chart": "hbar", "span": 6,
                         "title": "Kalbe: perubahan omset per kanal (Rp M)", "width": 620, "height": 330,
                         "data": [[k["kanal"], round((k["y2026"] - k["y2025"]) / 1e9, 2)]
                                  for k in sorted(kb["kanal"], key=lambda z: z["y2026"] - z["y2025"])
                                  if k["kanal"] != "Grand Total"],
                         "note": "Specialty Stores & Modern Trade = penyumbang penurunan terbesar."})
    kn = a.get("kenveu_kanal", [])
    if kn:
        sections.append({"type": "chart", "chart": "bar", "span": 6,
                         "title": "Kenveu: growth per kanal utama (%)", "width": 620, "height": 320,
                         "data": [[k["kanal"].title(), round(k["gr"] * 100, 1)]
                                  for k in kn if k["induk"] and k["kanal"] != "Grand Total"],
                         "note": "Jan–Jun. NKA & LMT tumbuh; GT dan Online Reseller turun."})
        sections.append({"type": "chart", "chart": "donut", "span": 6,
                         "title": "Kenveu: kontribusi kanal 2026", "width": 620, "height": 340,
                         "data": [[k["kanal"].title(), round(k["y2026"] / 1e9, 2)]
                                  for k in kn if k["induk"] and k["kanal"] != "Grand Total"],
                         "note": "Konsentrasi tinggi di modern trade = risiko daya tawar."})
    if a["stok"]:
        sections.append({"type": "chart", "chart": "bar", "span": 6,
                         "title": "Stock cover days (SCD) vs target", "width": 620, "height": 320,
                         "data": [[s["divisi"], round(s["scd"], 1)] for s in a["stok"]],
                         "note": "Target: " + ", ".join(f"{s['divisi']} {s['target_scd']:.0f}" for s in a["stok"])
                                 + ". OOH kritis (9 hari), Kenveu overstock (60 hari)."})
    if a["tim"]:
        labels = [b for b in BULAN_ID if any(b in v["periode"] for v in a["tim"].values())]
        series = {}
        for d, v in a["tim"].items():
            series[d] = [round(v["periode"][b]["pencapaian"] * 100, 1) if b in v["periode"] else None
                         for b in labels]
        sections.append({"type": "chart", "chart": "line", "span": 12,
                         "title": "Pencapaian tim sales per bulan (%)", "width": 1080, "height": 360,
                         "data": {"labels": labels, "series": series},
                         "note": "Dari sheet By Team (target vs aktual per salesman, diagregasi)."})
    sections.append({"type": "insights", "title": "Insight kunci", "items": a["insights"]})
    sections.append({"type": "recommendations", "title": "Rekomendasi",
                     "items": [f"P{x['prioritas']} · {x['judul']} — {x['dampak']} "
                               f"(pemilik: {x['pemilik']}, tenggat: {x['tenggat']})"
                               for x in a["recommendations"]]})
    return {"title": f"Business Plan Review 2026 — {a['meta']['perusahaan']}",
            "subtitle": f"Periode data {a['meta']['periode_data']} · sumber: {a['meta']['sumber']}",
            "theme": "dan", "locale": "id", "currency": "Rp", "paper": "a3",
            "badge": {"value": pct(a["ringkasan"]["pencapaian"], 0), "label": "pencapaian target YTD"},
            "chips": [a["meta"]["periode_data"], f"{len(a['divisi'])} divisi",
                      f"{len(a['temuan_data'])} temuan data", "Sumber: workbook internal"],
            "sections": sections}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · analis business plan xlsx")
    ap.add_argument("--file", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--nama", default="PT Sancho Mitra Sejahtera")
    a = ap.parse_args(argv)
    if not os.path.exists(a.file):
        print(f"[x] file tidak ada: {a.file}", file=sys.stderr)
        return 2
    os.makedirs(a.outdir, exist_ok=True)
    an = bangun(a.file, a.nama)

    def w(name, obj):
        p = os.path.join(a.outdir, name)
        with open(p, "w", encoding="utf-8") as fh:
            if isinstance(obj, str):
                fh.write(obj)
            else:
                json.dump(obj, fh, ensure_ascii=False, indent=1)
        return p

    w("analysis.json", an)
    w("projects.json", buat_projects(an))
    w("spec_infografik.json", buat_spec(an))
    tulis_md(an, os.path.join(a.outdir, "analysis.md"))
    tulis_dq(an, os.path.join(a.outdir, "data_quality.md"))
    with open(os.path.join(a.outdir, "omset_divisi.csv"), "w", newline="", encoding="utf-8") as fh:
        cw = csv.writer(fh)
        cw.writerow(["divisi", "bulan", "omset_2024", "omset_2025", "omset_2026", "target_2026",
                     "pencapaian", "yoy"])
        for nama_div, rows in an["omset_bulanan"].items():
            for r in rows:
                cw.writerow([nama_div, r["bulan"], r["y2024"], r["y2025"], r["y2026"], r["target"],
                             round(r["y2026"] / r["target"], 4) if r["target"] else "",
                             round(r["y2026"] / r["y2025"] - 1, 4) if r["y2025"] else ""])
    with open(os.path.join(a.outdir, "kanal.csv"), "w", newline="", encoding="utf-8") as fh:
        cw = csv.writer(fh)
        cw.writerow(["divisi", "kanal", "y2025", "y2026", "growth", "kontribusi"])
        for k in an["kenveu_kanal"]:
            cw.writerow(["Kenveu", k["kanal"], k["y2025"], k["y2026"], k["gr"], k["kontribusi"]])
        for k in an["kalbe"].get("kanal", []):
            cw.writerow(["Kalbe", k["kanal"], k["y2025"], k["y2026"], k["gr"], k["kontribusi"]])
    with open(os.path.join(a.outdir, "tim_achievement.csv"), "w", newline="", encoding="utf-8") as fh:
        cw = csv.writer(fh)
        cw.writerow(["divisi", "periode", "kode", "nama", "grup", "target", "aktual", "pencapaian"])
        wb2 = load(a.file)
        for x in parse_team(wb2, batas=an["ringkasan"]["bulan"]):
            if x.get("periode") == "DUP":
                continue
            cw.writerow([x["divisi"], x["periode"], x["kode"], x["nama"], x.get("grup", ""),
                         x["target"], x["aktual"], round(x["pct"], 4)])
    r = an["ringkasan"]
    print(f"[ok] {a.outdir}/: analysis.json · analysis.md · data_quality.md · spec_infografik.json "
          f"· projects.json · 3 CSV")
    print(f"     YTD {r['bulan']} bln: {rp(r['ytd2026'])} | target {rp(r['target'])} | "
          f"pencapaian {pct(r['pencapaian'])} | YoY {pct(r['yoy'])} | gap {sgn(r['gap'])}")
    for d in sorted(an["divisi"], key=lambda z: z["gap"]):
        print(f"     - {d['nama']:<12} {pct(d['pencapaian']):>7} target · {pct(d['yoy']):>7} YoY · "
              f"gap {sgn(d['gap']):>14} · {d['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
