#!/usr/bin/env python3
"""xlsx_lite — pembaca .xlsx murni stdlib (tanpa openpyxl/pandas).

Kenapa: skill DAN harus jalan di mesin mana pun tanpa pip install.
Yang dibaca: nilai cache sel (hasil formula terakhir disimpan Excel) + teks formula.

Pakai sebagai modul:
    from xlsx_lite import load
    wb = load("file.xlsx")            # {'sheets': [...], 'grid': {sheet: {(r,c): val}}, 'formula': {...}}
    val = cell(wb, "Omset All", "F20")

Pakai sebagai CLI:
    python3 xlsx_lite.py --file data.xlsx --list
    python3 xlsx_lite.py --file data.xlsx --sheet Stock --csv stock.csv
    python3 xlsx_lite.py --file data.xlsx --sheet Omset All --range A5:I20
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PKGREL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

_REF = re.compile(r"^([A-Za-z]+)(\d+)$")


def ref_to_rc(ref: str) -> tuple[int, int]:
    """'C12' -> (row=12, col=3) 1-based."""
    m = _REF.match(ref.strip())
    if not m:
        raise ValueError(f"ref sel tidak valid: {ref!r}")
    col = 0
    for ch in m.group(1).upper():
        col = col * 26 + (ord(ch) - 64)
    return int(m.group(2)), col


def rc_to_ref(row: int, col: int) -> str:
    s = ""
    while col > 0:
        col, r = divmod(col - 1, 26)
        s = chr(65 + r) + s
    return f"{s}{row}"


def _shared_strings(z: zipfile.ZipFile) -> list[str]:
    out: list[str] = []
    try:
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    except KeyError:
        return out
    for si in root.findall(f"{NS}si"):
        parts = [t.text or "" for t in si.iter(f"{NS}t")]
        out.append("".join(parts))
    return out


def _sheet_paths(z: zipfile.ZipFile) -> list[tuple[str, str]]:
    """[(nama_sheet, path_dalam_zip)] urut sesuai workbook."""
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rid2target = {r.get("Id"): r.get("Target") for r in rels.findall(f"{PKGREL}Relationship")}
    out = []
    for sh in wb.find(f"{NS}sheets").findall(f"{NS}sheet"):
        rid = sh.get(f"{REL}id")
        tgt = rid2target.get(rid, "")
        if tgt.startswith("/"):
            path = tgt.lstrip("/")
        elif tgt.startswith("xl/"):
            path = tgt
        else:
            path = "xl/" + tgt
        out.append((sh.get("name") or "", path))
    return out


def _num(text: str):
    try:
        f = float(text)
    except (TypeError, ValueError):
        return text
    return int(f) if f.is_integer() and abs(f) < 1e15 else f


def load(path: str, keep_formula: bool = True) -> dict:
    """Baca workbook -> {'sheets', 'grid', 'formula', 'dims'}."""
    grid: dict[str, dict[tuple[int, int], object]] = {}
    formula: dict[str, dict[tuple[int, int], str]] = {}
    dims: dict[str, tuple[int, int]] = {}
    with zipfile.ZipFile(path) as z:
        sst = _shared_strings(z)
        for name, spath in _sheet_paths(z):
            cells: dict[tuple[int, int], object] = {}
            forms: dict[tuple[int, int], str] = {}
            maxr = maxc = 0
            try:
                data = z.read(spath)
            except KeyError:
                grid[name], formula[name], dims[name] = cells, forms, (0, 0)
                continue
            for _, el in ET.iterparse(_io(data), events=("end",)):
                if el.tag != f"{NS}c":
                    continue
                ref = el.get("r")
                if not ref:
                    el.clear()
                    continue
                r, c = ref_to_rc(ref)
                maxr, maxc = max(maxr, r), max(maxc, c)
                t = el.get("t")
                v = el.find(f"{NS}v")
                f = el.find(f"{NS}f")
                if keep_formula and f is not None and f.text:
                    forms[(r, c)] = f.text
                val = None
                if t == "inlineStr":
                    isel = el.find(f"{NS}is")
                    if isel is not None:
                        val = "".join(x.text or "" for x in isel.iter(f"{NS}t"))
                elif v is not None and v.text is not None:
                    if t == "s":
                        try:
                            val = sst[int(v.text)]
                        except (ValueError, IndexError):
                            val = v.text
                    elif t == "b":
                        val = v.text == "1"
                    elif t == "e":
                        val = f"#ERR:{v.text}"
                    elif t == "str":
                        val = v.text
                    else:
                        val = _num(v.text)
                if val is not None and val != "":
                    cells[(r, c)] = val
                el.clear()
            grid[name], formula[name], dims[name] = cells, forms, (maxr, maxc)
    return {"sheets": list(grid), "grid": grid, "formula": formula, "dims": dims}


def _io(data: bytes):
    import io

    return io.BytesIO(data)


def cell(wb: dict, sheet: str, ref: str, default=None):
    r, c = ref_to_rc(ref)
    return wb["grid"].get(sheet, {}).get((r, c), default)


def num(wb: dict, sheet: str, ref: str, default: float = 0.0) -> float:
    v = cell(wb, sheet, ref)
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    return default


def rows(wb: dict, sheet: str) -> list[list]:
    """Grid padat: list baris (index 0 = baris 1), sel kosong = None."""
    g = wb["grid"].get(sheet, {})
    if not g:
        return []
    maxr = max(r for r, _ in g)
    maxc = max(c for _, c in g)
    out = []
    for r in range(1, maxr + 1):
        out.append([g.get((r, c)) for c in range(1, maxc + 1)])
    return out


def to_csv(wb: dict, sheet: str, dest: str, r1: int = 1, r2: int | None = None,
           c1: int = 1, c2: int | None = None) -> int:
    g = wb["grid"].get(sheet, {})
    maxr = r2 or (max((r for r, _ in g), default=0))
    maxc = c2 or (max((c for _, c in g), default=0))
    n = 0
    with open(dest, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([""] + [rc_to_ref(r1, c) for c in range(c1, maxc + 1)])
        for r in range(r1, maxr + 1):
            row = [str(r)] + ["" if g.get((r, c)) is None else str(g.get((r, c)))
                              for c in range(c1, maxc + 1)]
            w.writerow(row)
            n += 1
    return n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Baca .xlsx tanpa dependensi")
    ap.add_argument("--file", required=True)
    ap.add_argument("--list", action="store_true", help="daftar sheet + dimensi")
    ap.add_argument("--sheet")
    ap.add_argument("--range", help="mis. A5:I20")
    ap.add_argument("--csv", help="tulis sheet ke CSV")
    ap.add_argument("--cell", help="mis. F20")
    ap.add_argument("--formula", action="store_true", help="tampilkan formula juga")
    ap.add_argument("--json", help="tulis grid sheet ke JSON")
    a = ap.parse_args(argv)
    wb = load(a.file, keep_formula=True)

    if a.list or not (a.sheet or a.csv or a.json):
        print(f"file: {a.file}")
        for s in wb["sheets"]:
            r, c = wb["dims"].get(s, (0, 0))
            n = len(wb["grid"].get(s, {}))
            print(f"  - {s:<22} {r:>4} baris x {c:>3} kolom   {n:>6} sel terisi")
        return 0

    sheet = a.sheet or wb["sheets"][0]
    if sheet not in wb["grid"]:
        print(f"[x] sheet tidak ada: {sheet}. Pilihan: {', '.join(wb['sheets'])}", file=sys.stderr)
        return 2

    r1 = c1 = 1
    r2 = c2 = None
    if a.range:
        m = re.match(r"^([A-Za-z]+\d+)(?::([A-Za-z]+\d+))?$", a.range.strip())
        if not m:
            print("[x] --range harus seperti A5 atau A5:I20", file=sys.stderr)
            return 2
        r1, c1 = ref_to_rc(m.group(1))
        if m.group(2):
            r2, c2 = ref_to_rc(m.group(2))
        else:
            r2, c2 = r1, c1

    if a.cell:
        v = cell(wb, sheet, a.cell)
        f = wb["formula"].get(sheet, {}).get(ref_to_rc(a.cell))
        print(f"{sheet}!{a.cell} = {v!r}")
        if f:
            print(f"  formula: ={f}")
        return 0

    if a.csv:
        n = to_csv(wb, sheet, a.csv, r1, r2, c1, c2)
        print(f"[ok] {n} baris -> {a.csv}")
        return 0

    if a.json:
        g = wb["grid"][sheet]
        payload = {rc_to_ref(r, c): v for (r, c), v in g.items()
                   if r2 is None or (r1 <= r <= r2 and c1 <= c <= c2)}
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=1)
        print(f"[ok] {len(payload)} sel -> {a.json}")
        return 0

    # cetak rentang
    g = wb["grid"][sheet]
    for r in range(r1, (r2 or r1) + 1):
        line = []
        for c in range(c1, (c2 or c1) + 1):
            v = g.get((r, c))
            if v is None:
                line.append("")
            elif isinstance(v, float):
                line.append(f"{v:,.2f}")
            else:
                line.append(str(v))
            if a.formula:
                f = wb["formula"].get(sheet, {}).get((r, c))
                if f:
                    line[-1] += f"  [={f}]"
        if any(x.strip() for x in line):
            print(f"{r:>4} | " + " | ".join(line))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
