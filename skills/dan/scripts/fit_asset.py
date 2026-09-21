#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fit_asset.py — Sesuaikan aset gambar ke rasio platform (sub-skill DAN #04).

MASALAH YANG DISELESAIKAN:
  Generator gambar AI sering mengabaikan permintaan rasio di dalam prompt.
  Storyboard meminta 9:16 (1080x1920) tapi hasilnya 1:1 (2048x2048).
  Mengunggah asset yang salah rasio = terpotong otomatis oleh platform.

SOLUSI:
  crop cerdas (mempertahankan subjek) atau pad (tanpa memotong), lalu resize
  ke ukuran standar platform.

PAKAI:
  python3 fit_asset.py gambar.png                       # auto: pakai rasio dari brief
  python3 fit_asset.py gambar.png --ratio 9:16 --focus center
  python3 fit_asset.py gambar.png --ratio 4:5 --mode pad --bg "#F5F1E8"
  python3 fit_asset.py gambar.png --ratio 16:9 --size 1920x1080 --out hero.jpg

Butuh Pillow:  pip install Pillow
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Optional, Tuple

try:
    from PIL import Image
except ImportError:                                     # pragma: no cover
    sys.exit("[DAN] Butuh Pillow:  pip install Pillow")

# rasio -> ukuran standar platform (px)
PRESETS = {
    "9:16":  (1080, 1920),   # TikTok, Reels, Shorts, Story
    "4:5":   (1080, 1350),   # feed Instagram portrait, carousel
    "1:1":   (1080, 1080),   # feed square
    "16:9":  (1920, 1080),   # YouTube, thumbnail, presentasi
    "3:4":   (1080, 1440),   # Pinterest
    "1.91:1": (1200, 628),   # OG image / link preview
    "2:3":   (1000, 1500),   # poster
}


def parse_ratio(s: str) -> Tuple[float, float]:
    if ":" in s:
        a, b = s.split(":", 1)
        return float(a), float(b)
    v = float(s)
    return v, 1.0


def parse_size(s: Optional[str]) -> Optional[Tuple[int, int]]:
    if not s:
        return None
    a, b = s.lower().replace(" ", "").split("x", 1)
    return int(a), int(b)


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def fit(img: Image.Image, rw: float, rh: float, mode: str = "crop",
        focus: str = "center", bg: str = "#FFFFFF",
        size: Optional[Tuple[int, int]] = None) -> Image.Image:
    """Crop/pad gambar ke rasio rw:rh, lalu resize ke `size` (atau preset)."""
    target = rw / rh
    w, h = img.size
    cur = w / h

    if abs(cur - target) < 0.005:
        out = img
    elif mode == "pad" or cur < target:
        # gambar lebih tinggi dari target -> perlu tambah lebar (pad)
        # atau lebih lebar -> tambah tinggi. Hitung kanvas baru.
        if mode == "pad" and cur > target:
            new_h = int(round(w / target))
            canvas = Image.new("RGB", (w, new_h), hex_to_rgb(bg))
            off = _offset(focus, new_h, h, axis="v")
            canvas.paste(img, (0, off))
            out = canvas
        else:
            new_w = int(round(h * target))
            canvas = Image.new("RGB", (new_w, h), hex_to_rgb(bg))
            canvas.paste(img, ((new_w - w) // 2, 0))
            out = canvas
    else:
        # crop: buang kelebihan
        if cur > target:
            new_w = int(round(h * target))
            left = (w - new_w) // 2                    # crop tengah secara horizontal
            box = (left, 0, left + new_w, h)
        else:
            new_h = int(round(w / target))
            top = _offset(focus, h, new_h, axis="v")
            box = (0, top, w, top + new_h)
        out = img.crop(box)

    if size is None:
        size = _preset_for(target)
    out = out.convert("RGB") if out.mode not in ("RGB", "RGBA") else out
    return out.resize(size, Image.LANCZOS)


def _offset(focus: str, total: int, keep: int, axis: str = "v") -> int:
    extra = max(0, total - keep)
    return {"top": 0, "center": extra // 2, "bottom": extra}.get(focus, extra // 2)


def _preset_for(target: float) -> Tuple[int, int]:
    best = min(PRESETS.items(), key=lambda kv: abs(kv[1][0] / kv[1][1] - target))
    return best[1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · sesuaikan aset ke rasio platform")
    ap.add_argument("image")
    ap.add_argument("--ratio", default="9:16", help="9:16 | 4:5 | 1:1 | 16:9 | 3:4 | 1.91:1 | 2:3 | angka")
    ap.add_argument("--mode", default="crop", choices=["crop", "pad"])
    ap.add_argument("--focus", default="center", choices=["top", "center", "bottom"],
                    help="bagian yang dipertahankan saat crop vertikal")
    ap.add_argument("--bg", default="#FFFFFF", help="warna latar untuk mode pad (HEX)")
    ap.add_argument("--size", default="", help="ukuran keluaran eksplisit, mis. 1080x1920")
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)

    img = Image.open(a.image)
    rw, rh = parse_ratio(a.ratio)
    size = parse_size(a.size) or PRESETS.get(a.ratio.strip())
    out = fit(img, rw, rh, mode=a.mode, focus=a.focus, bg=a.bg, size=size)

    dst = a.out
    if not dst:
        base, ext = os.path.splitext(a.image)
        safe = a.ratio.replace(":", "x").replace(".", "_")
        dst = f"{base}_{safe}{ext if ext.lower() in ('.png', '.jpg', '.jpeg', '.webp') else '.png'}"
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
    out.save(dst, fmt.get(os.path.splitext(dst)[1].lstrip(".").lower(), "PNG"),
             quality=92, optimize=True)
    print(f"[DAN] {img.size[0]}x{img.size[1]} (rasio {img.size[0] / img.size[1]:.3f}) "
          f"-> {out.size[0]}x{out.size[1]} (rasio {out.size[0] / out.size[1]:.3f})")
    print(f"[DAN] mode={a.mode} focus={a.focus} -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
