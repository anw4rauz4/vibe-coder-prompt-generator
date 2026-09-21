#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cost_router.py — Router biaya: tugas mana ke model tier mana, dan kapan turun tier.

Prinsip: hemat kuota tanpa menurunkan mutu hasil yang BERISIKO.
  tier FREE  : tugas mekanis (format, ringkas data yang sudah ada, lint, terjemahan
               label, draf pertama) — mutu dijaga oleh ENGINE, bukan oleh model.
  tier MID   : analisa & produksi artefak (engine DAN + model untuk narasi pendek).
  tier STRONG: narasi berdampak tinggi (laporan klien final, komunikasi krisis,
               strategi baru, kode kompleks) — jangan diturunkan saat kuota tipis;
               lebih baik tunda atau pangkas lingkup.

Aturan saat kuota hampir habis (ditampilkan otomatis):
  1) turunkan hanya tugas FREE/MID; 2) ganti "model menulis" jadi "engine menghitung,
  model merapikan ≤120 kata"; 3) matikan konteks panjang (baca per-section);
  4) tunda tugas STRONG daripada menurunkannya ke model lemah.

PAKAI
  python3 cost_router.py "buatkan ringkasan weekly untuk tim"
  python3 cost_router.py "tulis laporan final untuk klien soal krisis reputasi" --kuota tipis
"""
from __future__ import annotations

import argparse
import re
import sys

FREE_RX = re.compile(r"(?i)\b(ringkas|format|rapikan|terjemah|label|judul|caption|"
                     r"draf|daftar|tabel|konversi satuan|lint)\b")
MID_RX = re.compile(r"(?i)\b(analisa|analisis|infografik|dashboard|storyboard|denah|"
                    r"monitor|simulasi|stack|prompt|report internal)\b")
STRONG_RX = re.compile(r"(?i)\b(klien final|krisis|strategi baru|negosiasi|putuskan|"
                       r"PHK|harga naik|permintaan maaf|investor)\b")
LONG_RX = re.compile(r"(?i)\b(semua dokumen|seluruh repo|semua laporan|gabungkan semua)\b")

HEMAT = [
    "Turunkan tugas FREE/MID ke model gratis; biarkan engine DAN yang menghitung.",
    "Batasi narasi model ≤120 kata; detail angka dari analysis.json, bukan dari model.",
    "Baca konteks per-section (grep/sed), jangan cat file utuh ke percakapan.",
    "Pakai ulang artefak sesi ini (analysis.json, infografik) — jangan hitung ulang.",
    "Tunda tugas STRONG daripada menurunkannya ke model lemah; risiko mutu terlalu tinggi.",
]


def route(task: str) -> dict:
    tier = "FREE" if FREE_RX.search(task) else "MID"
    if MID_RX.search(task):
        tier = "MID"
    if STRONG_RX.search(task):
        tier = "STRONG"
    alasan = []
    if FREE_RX.search(task):
        alasan.append("mekanis: mutu dijaga engine, model hanya merapikan")
    if MID_RX.search(task):
        alasan.append("produksi artefak: engine menghitung, model menulis pendek")
    if STRONG_RX.search(task):
        alasan.append("berdampak tinggi: jangan diturunkan tier-nya")
    if LONG_RX.search(task):
        alasan.append("permintaan konteks besar: pecah jadi beberapa panggilan kecil")
    return {"tier": tier, "alasan": alasan or ["default: mulai dari MID, naik hanya bila perlu"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · cost router")
    ap.add_argument("task")
    ap.add_argument("--kuota", default="normal", choices=["normal", "tipis"])
    a = ap.parse_args(argv)
    r = route(a.task)
    print(f"[DAN] tier: {r['tier']}")
    for x in r["alasan"]:
        print("   -", x)
    if a.kuota == "tipis":
        print("[DAN] kuota tipis — terapkan urutan hemat:")
        for i, h in enumerate(HEMAT, 1):
            print(f"   {i}. {h}")
        if r["tier"] == "STRONG":
            print("[DAN] PERINGATAN: tugas ini STRONG. Lebih baik tunda/pangkas lingkup "
                  "daripada memakai model lemah.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
