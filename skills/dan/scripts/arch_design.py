#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arch_design.py — Agent Arsitektur Bangunan (sub-skill DAN #09), "SketchUp dalam SVG".

Membaca `building.json` (lihat templates/building.example.json) lalu menghasilkan,
tanpa dependensi apa pun:

  2D  : denah tiap lantai (shelf-packing ruangan + dinding + dimensi + arah utara)
        tampak depan (elevasi) dengan bukaan per ruang
  3D  : massa isometrik per lantai, berwarna per fungsi ruang (painter's algorithm)
  DOC : laporan = program ruang, kepatuhan KDB/KLB, RAB, jadwal material,
        daftar gambar (set 2D & 3D), tahapan konstruksi + durasi,
        prompt render interior & eksterior (siap untuk sub-skill 04 / image gen)

PAKAI
  python3 arch_design.py ../templates/building.example.json
  python3 arch_design.py building.json --out-dir ../../../deliverables --scale 26
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import svg_charts as sc  # noqa: E402

COS30, SIN30 = math.cos(math.radians(30)), math.sin(math.radians(30))

FUNCTION_COLORS = {"living": 0, "private": 1, "service": 4, "wet": 3, "circulation": 5}
FUNCTION_LABEL = {"living": "Ruang hidup", "private": "Privat", "service": "Servis",
                  "wet": "Basah", "circulation": "Sirkulasi"}

# harga satuan bawaan (Rp/m2) — ganti lewat building.json["cost"]
DEFAULT_COST = {"structure_per_m2": 3_500_000, "finish_per_m2": 2_500_000,
                "mep_per_m2": 1_200_000, "other_pct": 10}

MATERIAL_BY_FUNCTION = {
    "living":  "lantai: granit 60x60 / vinyl SPC · dinding: cat emulsi · plafond: gypsum + cat",
    "private": "lantai: vinyl SPC / parket · dinding: cat emulsi · plafond: gypsum",
    "service": "lantai: keramik kasar anti-slip · dinding: keramik setinggi 1,5 m · plafond: gypsum tahan lembap",
    "wet":     "lantai: keramik anti-slip R10 · dinding: keramik full height · slope 1% ke floor drain",
    "circulation": "lantai: granit / keramik · dinding: cat · plafond: gypsum",
}

DRAWING_SET = [
    ("A-001", "Cover & daftar gambar", "2D"),
    ("A-002", "Site plan + KDB/KLB", "2D"),
    ("A-101", "Denah lantai 1..n", "2D"),
    ("A-201", "Tampak depan / belakang / kiri / kanan", "2D"),
    ("A-301", "Potongan A-A & B-B", "2D"),
    ("A-401", "Rencana pola lantai & plafond", "2D"),
    ("A-501", "Detail kusen, tangga, kamar mandi", "2D"),
    ("A-601", "Rencana pintu & jendela (schedule)", "2D"),
    ("S-101", "Rencana pondasi & struktur", "2D"),
    ("M/E-101", "Rencana plumbing & electrical", "2D"),
    ("3D-01", "Massing isometrik", "3D"),
    ("3D-02", "Render eksterior (2 angle)", "3D"),
    ("3D-03", "Render interior ruang utama", "3D"),
]

CONSTRUCTION_STAGES = [
    ("Pekerjaan persiapan & pengukuran", 2, "bowplank, mobilisasi, pagar proyek"),
    ("Pondasi & struktur bawah", 4, "galian, pondasi, sloof"),
    ("Struktur atas per lantai", 3, "kolom, balok, pelat (per lantai)"),
    ("Dinding & plesteran", 4, "bata/batako, plester, aci"),
    ("Atap & penutup", 3, "rangka, penutup, talang"),
    ("MEP kasar", 3, "pipa, conduit, titik listrik & air"),
    ("Kusen, pintu, jendela", 2, "pemasangan frame & daun"),
    ("Finishing lantai & dinding", 4, "keramik/granit, cat, plafond"),
    ("MEP akhir & sanitary", 2, "fixture, lampu, saklar, testing"),
    ("Pembersihan & serah terima", 1, "cleaning, punch list, handover"),
]


# --------------------------------------------------------------------- layout 2D

def layout_floor(rooms: Sequence[Dict[str, Any]], floor_width: float,
                 wall: float = 0.15) -> Tuple[List[Dict[str, Any]], float, float]:
    """Shelf-packing sederhana: urutkan berdasarkan depth menurun, isi baris kiri→kanan."""
    rs = sorted(rooms, key=lambda r: -(float(r.get("d", 3))))
    rows: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = []
    cur_w = 0.0
    for r in rs:
        w, dd = float(r.get("w", 3)), float(r.get("d", 3))
        need = w + (wall if cur else 0)
        if cur and cur_w + need > floor_width:
            rows.append(cur)
            cur, cur_w = [], 0.0
            need = w
        cur.append({**r, "w": w, "d": dd, "x": cur_w, "row": len(rows)})
        cur_w += need
    if cur:
        rows.append(cur)
    y = 0.0
    placed = []
    row_depths = []
    for ri, row in enumerate(rows):
        rd = max(r["d"] for r in row)
        row_depths.append(rd)
        for r in row:
            placed.append({**r, "x": r["x"], "y": y})
        y += rd + wall
    # bounding box diambil dari posisi aktual (bukan penjumlahan teoritis)
    bw = max((r["x"] + r["w"] for r in placed), default=0.0)
    bd = max((r["y"] + r["d"] for r in placed), default=0.0)
    return placed, round(bw, 2), round(bd, 2)


# --------------------------------------------------------------------- compute

def compute(doc: Dict[str, Any], scale: float) -> Dict[str, Any]:
    meta = doc.get("meta", {})
    cur = meta.get("currency", "Rp")
    site = doc.get("site", {}) or {}
    site_area = float(site.get("width", 0) or 0) * float(site.get("length", 0) or 0)
    floor_width = float(site.get("build_width") or site.get("width", 10) or 10) - 1.0
    cost = {**DEFAULT_COST, **(doc.get("cost", {}) or {})}

    floors_out = []
    total_built = total_program = 0.0
    z = 0.0
    for fi, fl in enumerate(doc.get("floors", [])):
        rooms = fl.get("rooms", [])
        placed, bw, bd = layout_floor(rooms, floor_width)
        prog = sum(r["w"] * r["d"] for r in placed)
        built = bw * bd
        circ = built - prog
        h = float(fl.get("height", 3.0))
        for r in placed:
            r["area"] = round(r["w"] * r["d"], 2)
            r["z"] = z
            r["floor"] = fi
        floors_out.append({"index": fi, "name": fl.get("name", f"Lantai {fi + 1}"),
                           "height": h, "z": z, "rooms": placed,
                           "width": bw, "depth": bd,
                           "program_area": round(prog, 2), "built_area": round(built, 2),
                           "circulation_area": round(circ, 2),
                           "circulation_pct": round(circ / built * 100, 1) if built else 0})
        total_program += prog
        total_built += built
        z += h

    kdb = (floors_out[0]["built_area"] / site_area * 100) if site_area and floors_out else 0
    klb = (total_built / site_area * 100) if site_area else 0
    kdb_max = float(site.get("kdb_max", 0.6)) * 100
    klb_max = float(site.get("klb_max", 1.2)) * 100

    sub = total_built * (cost["structure_per_m2"] + cost["finish_per_m2"] + cost["mep_per_m2"])
    other = sub * cost["other_pct"] / 100
    total = sub + other
    rab = [
        {"item": "Struktur (pondasi, kolom, balok, pelat)",
         "vol": round(total_built, 1), "unit": "m2", "price": cost["structure_per_m2"],
         "amount": round(total_built * cost["structure_per_m2"])},
        {"item": "Finishing (lantai, dinding, plafond, kusen)",
         "vol": round(total_built, 1), "unit": "m2", "price": cost["finish_per_m2"],
         "amount": round(total_built * cost["finish_per_m2"])},
        {"item": "MEP (plumbing, electrical, sanitary)",
         "vol": round(total_built, 1), "unit": "m2", "price": cost["mep_per_m2"],
         "amount": round(total_built * cost["mep_per_m2"])},
        {"item": f"Biaya lain-lain ({cost['other_pct']}%)",
         "vol": 1, "unit": "ls", "price": round(other), "amount": round(other)},
    ]
    weeks = sum(d for _, d, _ in CONSTRUCTION_STAGES)
    # penyesuaian durasi theo luas (heuristik): +1 minggu tiap 100 m2 di atas 100 m2
    extra = max(0, int((total_built - 100) // 100))
    weeks += extra

    prompts = _render_prompts(doc, floors_out)
    return {"meta": {**meta, "currency": cur}, "site": site, "floors": floors_out,
            "scale_px_per_m": scale,
            "totals": {"program_area": round(total_program, 2),
                       "built_area": round(total_built, 2),
                       "circulation_pct": round((total_built - total_program) / total_built * 100, 1)
                       if total_built else 0,
                       "rooms": sum(len(f["rooms"]) for f in floors_out)},
            "compliance": {"site_area": site_area, "kdb": round(kdb, 1), "kdb_max": kdb_max,
                           "kdb_ok": kdb <= kdb_max, "klb": round(klb, 1), "klb_max": klb_max,
                           "klb_ok": klb <= klb_max},
            "cost": cost, "rab": rab, "rab_total": round(total),
            "schedule_weeks": weeks,
            "stages": [{"name": n, "weeks": d, "note": t} for n, d, t in CONSTRUCTION_STAGES],
            "prompts": prompts}


# --------------------------------------------------------------------- SVG 2D denah

def _shell_svg(w: int, h: int, inner: str, th: Dict[str, Any]) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" font-family="{sc.FONT}">'
            f'<rect width="{w}" height="{h}" fill="{th["bg"]}"/>{inner}</svg>')


def floorplan_svg(fl: Dict[str, Any], th_name: str, scale: float,
                  north: bool = True) -> str:
    th = sc.theme(th_name)
    S = scale
    pad = 70
    W = int(fl["width"] * S + pad * 2)
    H = int(fl["depth"] * S + pad * 2 + 30)
    g = [f'<text x="{pad}" y="34" fill="{th["text"]}" font-size="18" font-weight="800">'
         f'{sc.esc(fl["name"])} — DENAH</text>',
         f'<text x="{pad}" y="52" fill="{th["muted"]}" font-size="11.5">'
         f'{fl["width"]:.2f} m × {fl["depth"]:.2f} m · luas terbangun {fl["built_area"]:.1f} m² · '
         f'sirkulasi {fl["circulation_pct"]:.0f}%</text>']
    ox, oy = pad, pad
    # dinding luar
    g.append(f'<rect x="{ox - 6}" y="{oy - 6}" width="{fl["width"] * S + 12}" '
             f'height="{fl["depth"] * S + 12}" fill="none" stroke="{th["text"]}" stroke-width="5"/>')
    for r in fl["rooms"]:
        x, y = ox + r["x"] * S, oy + r["y"] * S
        w, d = r["w"] * S, r["d"] * S
        col = th["series"][FUNCTION_COLORS.get(r.get("function", "living"), 0)
                           % len(th["series"])]
        g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{d}" fill="{col}" '
                 f'fill-opacity="0.20" stroke="{col}" stroke-width="2"/>')
        cx, cy = x + w / 2, y + d / 2
        name = sc.esc(r.get("name", ""))
        lines = sc._wrap(name, max(6, int(w / 7)))[:2]
        for i, ln in enumerate(lines):
            g.append(f'<text x="{cx}" y="{cy - 4 + i * 13}" fill="{th["text"]}" font-size="11" '
                     f'text-anchor="middle">{ln}</text>')
        g.append(f'<text x="{cx}" y="{cy + 12 + (len(lines) - 1) * 13}" fill="{th["muted"]}" '
                 f'font-size="10" text-anchor="middle">{r["area"]:.1f} m²</text>')
    # dimensi keseluruhan
    yb = oy + fl["depth"] * S + 26
    g.append(f'<line x1="{ox}" y1="{yb}" x2="{ox + fl["width"] * S}" y2="{yb}" '
             f'stroke="{th["muted"]}" stroke-width="1"/>')
    g.append(f'<text x="{ox + fl["width"] * S / 2}" y="{yb + 16}" fill="{th["muted"]}" '
             f'font-size="11" text-anchor="middle">{fl["width"]:.2f} m</text>')
    xr = ox + fl["width"] * S + 24
    g.append(f'<line x1="{xr}" y1="{oy}" x2="{xr}" y2="{oy + fl["depth"] * S}" '
             f'stroke="{th["muted"]}" stroke-width="1"/>')
    g.append(f'<text x="{xr + 14}" y="{oy + fl["depth"] * S / 2}" fill="{th["muted"]}" '
             f'font-size="11" text-anchor="middle" '
             f'transform="rotate(90 {xr + 14} {oy + fl["depth"] * S / 2})">{fl["depth"]:.2f} m</text>')
    if north:
        nx, ny = W - 46, 60
        g.append(f'<path d="M {nx} {ny - 16} L {nx + 8} {ny + 8} L {nx} {ny + 2} '
                 f'L {nx - 8} {ny + 8} Z" fill="{th["accent"]}"/>')
        g.append(f'<text x="{nx}" y="{ny + 22}" fill="{th["muted"]}" font-size="10" '
                 f'text-anchor="middle">U</text>')
    # skala bar
    g.append(f'<rect x="{pad}" y="{H - 22}" width="{S}" height="5" fill="{th["text"]}"/>')
    g.append(f'<rect x="{pad + S}" y="{H - 22}" width="{S}" height="5" fill="{th["muted"]}"/>')
    g.append(f'<text x="{pad + 2 * S + 8}" y="{H - 16}" fill="{th["muted"]}" font-size="10">0 – 2 m</text>')
    return _shell_svg(W, H, "".join(g), th)


# --------------------------------------------------------------------- SVG 3D isometrik

def iso(u: float, v: float, z: float, S: float, ox: float, oy: float) -> Tuple[float, float]:
    return (ox + (u - v) * COS30 * S, oy + (u + v) * SIN30 * S - z * S)


def _shade(hexc: str, f: float) -> str:
    c = [max(0, min(255, int(int(hexc[i:i + 2], 16) * f))) for i in (1, 3, 5)]
    return "#{:02X}{:02X}{:02X}".format(*c)


def isometric_svg(A: Dict[str, Any], th_name: str, scale: float) -> str:
    th = sc.theme(th_name)
    S = scale * 0.8
    tot_w = max(f["width"] for f in A["floors"])
    tot_d = max(f["depth"] for f in A["floors"])
    tot_h = sum(f["height"] for f in A["floors"])
    W = int((tot_w + tot_d) * COS30 * S + 120)
    H = int((tot_w + tot_d) * SIN30 * S + tot_h * S + 140)
    ox, oy = W / 2, 90
    g = [f'<text x="30" y="34" fill="{th["text"]}" font-size="18" font-weight="800">'
         f'{sc.esc(A["meta"].get("name", "Massing"))} — MASSA 3D ISOMETRIK</text>',
         f'<text x="30" y="52" fill="{th["muted"]}" font-size="11.5">'
         f'{len(A["floors"])} lantai · tinggi {tot_h:.1f} m · luas terbangun '
         f'{A["totals"]["built_area"]:.0f} m²</text>']
    boxes = []
    for fl in A["floors"]:
        for r in fl["rooms"]:
            boxes.append((r, fl))
    boxes.sort(key=lambda b: (b[0]["z"], b[0]["x"] + b[0]["y"]))
    for r, fl in boxes:
        u, v, z = r["x"], r["y"], r["z"]
        w, d, h = r["w"], r["d"], fl["height"] * 0.92
        base = th["series"][FUNCTION_COLORS.get(r.get("function", "living"), 0)
                            % len(th["series"])]
        top = _shade(base, 1.0)
        sa = _shade(base, 0.72)
        sb = _shade(base, 0.52)
        t = [iso(u, v, z + h, S, ox, oy), iso(u + w, v, z + h, S, ox, oy),
             iso(u + w, v + d, z + h, S, ox, oy), iso(u, v + d, z + h, S, ox, oy)]
        fa = [iso(u, v + d, z, S, ox, oy), iso(u + w, v + d, z, S, ox, oy),
              iso(u + w, v + d, z + h, S, ox, oy), iso(u, v + d, z + h, S, ox, oy)]
        fb = [iso(u + w, v, z, S, ox, oy), iso(u + w, v + d, z, S, ox, oy),
              iso(u + w, v + d, z + h, S, ox, oy), iso(u + w, v, z + h, S, ox, oy)]
        pts = lambda P: " ".join(f"{x:.1f},{y:.1f}" for x, y in P)
        g.append(f'<polygon points="{pts(fa)}" fill="{sa}" stroke="{th["bg"]}" stroke-width="0.6"/>')
        g.append(f'<polygon points="{pts(fb)}" fill="{sb}" stroke="{th["bg"]}" stroke-width="0.6"/>')
        g.append(f'<polygon points="{pts(t)}" fill="{top}" fill-opacity="0.95" '
                 f'stroke="{th["bg"]}" stroke-width="0.6"/>')
    # legenda fungsi (wrap otomatis agar tidak meluber pada kanvas sempit)
    items = [(lab, th["series"][FUNCTION_COLORS[fn] % len(th["series"])])
             for fn, lab in FUNCTION_LABEL.items()]
    rows: List[List[Tuple[str, str]]] = [[]]
    x = 30
    for lab, col in items:
        w_item = 15 + len(lab) * 6.5 + 22
        if x + w_item > W - 20 and rows[-1]:
            rows.append([])
            x = 30
        rows[-1].append((lab, col))
        x += w_item
    H += (len(rows) - 1) * 18
    ly = H - 26 - (len(rows) - 1) * 18
    for r_i, row in enumerate(rows):
        lx = 30
        yy = ly + r_i * 18
        for lab, col in row:
            g.append(f'<rect x="{lx}" y="{yy - 9}" width="10" height="10" rx="2" fill="{col}"/>')
            g.append(f'<text x="{lx + 15}" y="{yy}" fill="{th["muted"]}" '
                     f'font-size="10.5">{lab}</text>')
            lx += 15 + len(lab) * 6.5 + 22
    return _shell_svg(W, H, "".join(g), th)


# --------------------------------------------------------------------- SVG tampak

def elevation_svg(A: Dict[str, Any], th_name: str, scale: float) -> str:
    th = sc.theme(th_name)
    S = scale * 0.7
    w = max(f["width"] for f in A["floors"])
    h = sum(f["height"] for f in A["floors"])
    pad = 70
    W = int(w * S + pad * 2)
    H = int(h * S + pad + 90)
    g = [f'<text x="{pad}" y="34" fill="{th["text"]}" font-size="18" font-weight="800">'
         f'TAMPAK DEPAN</text>',
         f'<text x="{pad}" y="52" fill="{th["muted"]}" font-size="11.5">'
         f'lebar {w:.2f} m · tinggi {h:.1f} m</text>']
    gy = H - 60
    y = gy
    for fl in A["floors"]:
        y -= fl["height"] * S
        g.append(f'<rect x="{pad}" y="{y}" width="{fl["width"] * S}" '
                 f'height="{fl["height"] * S}" fill="{th["panel"]}" stroke="{th["text"]}" '
                 f'stroke-width="2"/>')
        front = [r for r in fl["rooms"] if r["y"] == 0]
        for r in front:
            rx = pad + r["x"] * S
            rw = r["w"] * S
            if r.get("function") == "service" and fl["index"] == 0:
                # pintu/garasi
                g.append(f'<rect x="{rx + rw * 0.2:.1f}" y="{y + fl["height"] * S - 42:.1f}" '
                         f'width="{rw * 0.6:.1f}" height="42" fill="{th["grid"]}" '
                         f'stroke="{th["muted"]}" stroke-width="1.5"/>')
            elif r.get("function") != "wet":
                wy = y + fl["height"] * S * 0.32
                g.append(f'<rect x="{rx + rw * 0.18:.1f}" y="{wy:.1f}" width="{rw * 0.64:.1f}" '
                         f'height="{fl["height"] * S * 0.42:.1f}" fill="{th["accent"]}" '
                         f'fill-opacity="0.35" stroke="{th["accent"]}" stroke-width="1.5"/>')
                g.append(f'<line x1="{rx + rw * 0.5:.1f}" y1="{wy:.1f}" x2="{rx + rw * 0.5:.1f}" '
                         f'y2="{wy + fl["height"] * S * 0.42:.1f}" stroke="{th["accent"]}" '
                         f'stroke-width="1"/>')
    # atap
    g.append(f'<path d="M {pad - 10} {y} L {pad + w * S / 2} {y - 26} '
             f'L {pad + w * S + 10} {y} Z" fill="{th["grid"]}" stroke="{th["text"]}" '
             f'stroke-width="2"/>')
    # tanah
    g.append(f'<line x1="{pad - 30}" y1="{gy}" x2="{pad + w * S + 30}" y2="{gy}" '
             f'stroke="{th["text"]}" stroke-width="3"/>')
    for i in range(0, int(w) + 2, 1):
        xx = pad - 26 + i * S
        if xx < pad + w * S + 30:
            g.append(f'<line x1="{xx:.1f}" y1="{gy}" x2="{xx - 6:.1f}" y2="{gy + 7}" '
                     f'stroke="{th["muted"]}" stroke-width="1"/>')
    return _shell_svg(W, H, "".join(g), th)


# --------------------------------------------------------------------- prompts render

def _render_prompts(doc: Dict[str, Any], floors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    style = doc.get("meta", {}).get("style", "modern tropis")
    out: Dict[str, List[Dict[str, str]]] = {"interior": [], "exterior": []}
    for fl in floors:
        for r in fl["rooms"]:
            if r.get("function") in ("living", "private") and len(out["interior"]) < 6:
                out["interior"].append({
                    "room": f'{fl["name"]} · {r["name"]}',
                    "prompt": (f"Interior render of {r['name'].lower()} ({r['area']:.1f} sqm), "
                               f"{style} style. Wide-angle 24mm eye-level shot, "
                               f"{MATERIAL_BY_FUNCTION.get(r['function'], '')}. "
                               f"Soft daylight from large window, warm neutral palette, "
                               f"minimalist furniture, photorealistic, 8K, 16:9, "
                               f"no text, no watermark, no people")})
    out["exterior"].append({
        "room": "Fasad depan",
        "prompt": (f"Exterior architectural render of a {len(floors)}-storey {style} house, "
                   f"front facade, two-point perspective at street level, "
                   f"tropical landscaping, overcast soft light, photorealistic, 8K, 16:9, "
                   f"no text, no watermark")})
    out["exterior"].append({
        "room": "Angle taman/sisi",
        "prompt": (f"Exterior render of a {len(floors)}-storey {style} house from garden side, "
                   f"golden hour, lush tropical plants foreground, warm interior lights on, "
                   f"photorealistic, 8K, 16:9, no text, no watermark")})
    return out


# --------------------------------------------------------------------- report

def to_markdown(A: Dict[str, Any]) -> str:
    m, cur = A["meta"], A["meta"].get("currency", "Rp")
    t, comp = A["totals"], A["compliance"]
    L = [f"# Laporan Arsitektur — {m.get('name', '')}", "",
         f"_Gaya: {m.get('style', '-')} · {len(A['floors'])} lantai · "
         f"{t['rooms']} ruang · disusun oleh DAN · Architectural Design_", "",
         "## 1. Program Ruang", "",
         "| Lantai | Ruang | Fungsi | Lebar | Dalam | Luas |", "|---|---|---|---|---|---|"]
    for fl in A["floors"]:
        for r in fl["rooms"]:
            L.append(f"| {fl['name']} | {r['name']} | {FUNCTION_LABEL.get(r.get('function'), '-')} | "
                     f"{r['w']:.2f} | {r['d']:.2f} | {r['area']:.1f} m² |")
    L += ["", "| Lantai | Luas program | Luas terbangun | Sirkulasi | Tinggi |",
          "|---|---|---|---|---|"]
    for fl in A["floors"]:
        L.append(f"| {fl['name']} | {fl['program_area']:.1f} m² | {fl['built_area']:.1f} m² | "
                 f"{fl['circulation_pct']:.0f}% | {fl['height']:.1f} m |")
    L += ["", f"**Total:** program {t['program_area']:.1f} m² · terbangun "
              f"{t['built_area']:.1f} m² · sirkulasi {t['circulation_pct']:.0f}%", "",
          "## 2. Kepatuhan terhadap Site", "",
          "| Indikator | Nilai | Batas | Status |", "|---|---|---|---|",
          f"| Luas lahan | {comp['site_area']:.0f} m² | — | — |",
          f"| KDB (lantai dasar) | {comp['kdb']:.1f}% | {comp['kdb_max']:.0f}% | "
          f"{'✔ aman' if comp['kdb_ok'] else '⛔ melebihi'} |",
          f"| KLB (total) | {comp['klb']:.1f}% | {comp['klb_max']:.0f}% | "
          f"{'✔ aman' if comp['klb_ok'] else '⛔ melebihi'} |", "",
          "## 3. Rencana Anggaran Biaya (estimasi)", "",
          "| Item | Vol | Sat | Harga satuan | Jumlah |", "|---|---|---|---|---|"]
    for r in A["rab"]:
        L.append(f"| {r['item']} | {r['vol']:,.0f} | {r['unit']} | {cur}{r['price']:,.0f} | "
                 f"{cur}{r['amount']:,.0f} |")
    L += ["", f"**Total estimasi: {cur}{A['rab_total']:,.0f}**  "
              f"(≈ {cur}{A['rab_total'] / max(1, t['built_area']):,.0f}/m²)", "",
          "> Estimasi kelas konsep (±25%). Wajib diverifikasi dengan harga lokal & "
          "gambar kerja sebelum tender.", "",
          "## 4. Jadwal Material per Fungsi Ruang", "", "| Fungsi | Spesifikasi bawaan |", "|---|---|"]
    for fn, lab in FUNCTION_LABEL.items():
        L.append(f"| {lab} | {MATERIAL_BY_FUNCTION[fn]} |")
    L += ["", "## 5. Daftar Gambar (set 2D & 3D)", "", "| Kode | Gambar | Jenis |", "|---|---|---|"]
    for c, n, k in DRAWING_SET:
        L.append(f"| {c} | {n} | {k} |")
    L += ["", f"## 6. Tahapan Konsumsi/Konstruksi (±{A['schedule_weeks']} minggu)", "",
          "| # | Tahap | Durasi (minggu) | Catatan |", "|---|---|---|---|"]
    for i, s in enumerate(A["stages"], 1):
        L.append(f"| {i} | {s['name']} | {s['weeks']} | {s['note']} |")
    L += ["", "## 7. Prompt Render (untuk sub-skill 04 / image generator)", ""]
    L += ["### Interior"]
    for p in A["prompts"]["interior"]:
        L.append(f"- **{p['room']}** — `{p['prompt']}`")
    L += ["### Eksterior"]
    for p in A["prompts"]["exterior"]:
        L.append(f"- **{p['room']}** — `{p['prompt']}`")
    L += ["", "---", "_DAN · Architectural Design. Denah memakai shelf-packing skematik "
          "(tahap konsep), bukan gambar kerja berskala sertifikasi._"]
    return "\n".join(L)


# --------------------------------------------------------------------- main

def main(argv: Optional[Sequence[str]] = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · Architectural Design (2D/3D/konstruksi)")
    ap.add_argument("building")
    ap.add_argument("--out-dir", default=dl)
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    ap.add_argument("--scale", type=float, default=26, help="px per meter untuk denah")
    ap.add_argument("--stem", default="arch_",
                    help="prefix nama file keluaran (mis. kafe_) agar multi-kasus tidak tertimpa")
    a = ap.parse_args(argv)

    with open(a.building, encoding="utf-8") as f:
        doc = json.load(f)
    A = compute(doc, a.scale)
    os.makedirs(a.out_dir, exist_ok=True)
    stem = a.stem
    with open(os.path.join(a.out_dir, stem + "report.md"), "w", encoding="utf-8") as f:
        f.write(to_markdown(A))
    with open(os.path.join(a.out_dir, stem + "report.json"), "w", encoding="utf-8") as f:
        json.dump(A, f, ensure_ascii=False, indent=2)
    for fl in A["floors"]:
        p = os.path.join(a.out_dir, f"{stem}denah_L{fl['index'] + 1}.svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(floorplan_svg(fl, a.theme, a.scale))
    with open(os.path.join(a.out_dir, stem + "massing_3d.svg"), "w", encoding="utf-8") as f:
        f.write(isometric_svg(A, a.theme, a.scale))
    with open(os.path.join(a.out_dir, stem + "tampak_depan.svg"), "w", encoding="utf-8") as f:
        f.write(elevation_svg(A, a.theme, a.scale))
    t = A["totals"]
    print(f"[DAN] {len(A['floors'])} lantai · {t['rooms']} ruang · "
          f"terbangun {t['built_area']:.0f} m² · KDB {A['compliance']['kdb']:.0f}% · "
          f"RAB {A['meta']['currency']}{A['rab_total']:,.0f} · ±{A['schedule_weeks']} minggu")
    print(f"[DAN] -> {a.out_dir}/{stem}report.md / denah_L*.svg / massing_3d.svg / tampak_depan.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
