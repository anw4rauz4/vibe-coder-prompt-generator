#!/usr/bin/env python3
"""Validasi SVG hasil paket svg_charts — dipakai saat development skill DAN."""
import re
import sys
import xml.etree.ElementTree as ET

path = sys.argv[1] if len(sys.argv) > 1 else "deliverables/chart_gallery.html"
h = open(path, encoding="utf-8").read()
svgs = re.findall(r"<svg.*?</svg>", h, re.S)
ok = 0
for i, s in enumerate(svgs):
    try:
        ET.fromstring(s)
        ok += 1
    except Exception as e:
        col = getattr(e, "position", (0, 0))[1]
        print(f"[INVALID #{i}] {e}")
        print("   near:", s[max(0, col - 90):col + 90].replace("\n", " "))
print(f"valid {ok}/{len(svgs)} | {round(len(h)/1024,1)} KB")
