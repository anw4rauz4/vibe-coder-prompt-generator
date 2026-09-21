#!/usr/bin/env python3
"""Cek tata letak: pastikan tidak ada elemen yang keluar dari viewBox SVG."""
import re
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"


def check(svg_text: str, name: str) -> int:
    root = ET.fromstring(svg_text)
    W = float(root.get("width"))
    H = float(root.get("height"))
    bad = 0
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag == "text":
            x = float(el.get("x", 0))
            y = float(el.get("y", 0))
            if not (-2 <= x <= W + 2 and -2 <= y <= H + 2):
                bad += 1
                print(f"  [{name}] TEXT di luar kanvas: ({x:.0f},{y:.0f}) vs {W:.0f}x{H:.0f} "
                      f"-> {el.text!r}")
        elif tag in ("rect", "circle"):
            if tag == "rect":
                x, y = float(el.get("x", 0)), float(el.get("y", 0))
                w, h = float(el.get("width", 0)), float(el.get("height", 0))
            else:
                r = float(el.get("r", 0))
                x, y = float(el.get("cx", 0)) - r, float(el.get("cy", 0)) - r
                w = h = 2 * r
            if x < -2 or y < -2 or x + w > W + 2 or y + h > H + 2:
                bad += 1
                print(f"  [{name}] {tag.upper()} overflow: x={x:.0f} y={y:.0f} "
                      f"w={w:.0f} h={h:.0f} vs {W:.0f}x{H:.0f}")
    print(f"{'OK  ' if not bad else 'WARN'} {name}: {W:.0f}x{H:.0f}, {bad} masalah")
    return bad


def main():
    path = sys.argv[1]
    h = open(path, encoding="utf-8").read()
    svgs = re.findall(r"<svg.*?</svg>", h, re.S)
    total = 0
    for i, s in enumerate(svgs):
        m = re.search(r'font-weight="700"[^>]*>([^<]{3,60})<', s)
        nm = (m.group(1)[:34] if m else f"svg#{i}").strip()
        try:
            total += check(s, nm)
        except ET.ParseError as e:
            print(f"  PARSE ERROR #{i}: {e}")
            total += 1
    print(f"\nTotal masalah tata letak: {total} pada {len(svgs)} svg")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
