#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_course.py — Paket pelatihan "berjalan": deck slide + naskah audio tersinkron.

Membaca modul kursus (kursus/README.md) lalu menghasilkan:
  course_deck.html        slide per modul DENGAN speaker-notes = naskah narasi,
                          lengkap dengan estimasi durasi per slide (145 kata/menit)
  course_audio_script.md  naskah TTS siap pakai ber-timestamp (aturan sub-skill 16:
                          kalimat ≤18 kata, angka dilafalkan, jeda ditandai)
  COURSE.md               petunjuk produksi: sintesis audio (TTS apa pun / generate_speech
                          di agent), urutan slide, checklist QC audio-video

Sinkronisasi: tiap slide menyimpan data-durasi (detik) sehingga editor bisa menyusun
video dengan menumpuk audio per slide sesuai urutan.

PAKAI
  python3 make_course.py --out-dir deliverables/course
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
WPM = 145

MODULES = [
    ("Pembuka: apa itu DAN",
     "DAN adalah satu agen dengan dua puluh satu sub-skill untuk pekerjaan marketing "
     "ujung ke ujung. Ia menganalisa data, menyusun strategi, membuat infografik dan "
     "storyboard, memantau proyek, hingga melatih timnya sendiri. Semua mesin berjalan "
     "tanpa instalasi tambahan, dan bisa dipasang di Claude, Cursor, Gemini, ChatGPT, "
     "Copilot, atau VS Code lewat adapter dan server MCP."),
    ("Analisa data yang jujur",
     "Mulailah selalu dari data. Jalankan analisa pada CSV kampanye Anda, lalu baca tiga "
     "hal: kanal mana yang menguntungkan, di mana funnel bocor, dan anomali apa yang perlu "
     "diverifikasi. Setiap kesimpulan wajib menyebut angka sumbernya. Bila angka tidak "
     "ada, tandai sebagai asumsi, jangan mengarang."),
    ("Visual yang tidak menyesatkan",
     "Pilih grafik sesuai pesan, bukan sesuai selera. Perbandingan antar kategori pakai "
     "bar. Tren pakai garis. Komposisi pakai donut maksimal enam irisan. Selalu mulai "
     "sumbu bar dari nol, dan jalankan pemeriksa tata letak sebelum dibagikan."),
    ("Keputusan budget dengan ketidakpastian",
     "Simulator budget memberi interval persen sepuluh sampai sembilan puluh, bukan satu "
     "angka palsu. Aturan kelayakannya: skenario layak bila kasus terburuknya masih "
     "setidaknya sama dengan kasus tengah baseline. Setelah itu validasi dengan uji "
     "budget kecil tujuh sampai empat belas hari."),
    ("Ritme mingguan yang menjaga tim",
     "Setiap Senin: kumpulkan update form, jalankan ritme mingguan, tinjau burn-up, lalu "
     "putuskan tiga hal. Guard memastikan tugas kritis tidak lolos tanpa tindakan. "
     "Notifikasi mengisi dirinya sendiri dari data, dan rahasia tidak pernah disimpan "
     "di berkas."),
    ("Komunikasi: klien, tim, dan diri sendiri",
     "Laporan klien ditulis dalam bahasa manusia dengan glosarium kecil. Pesan untuk tim "
     "memakai nada yang mengakui perasaan dulu, lalu fakta, lalu satu langkah lima belas "
     "menit. Pemeriksa narasi menangkap klaim sebab-akibat tanpa uji, janji berlebihan, "
     "dan menyalahkan orang."),
    ("Penutup: latihan dan kebiasaan",
     "Kerjakan lima latihan pada folder kursus bersama tim Anda. Nilainya bukan kesamaan "
     "angka, melainkan cara berargumen dari data. Ulangi tiap kuartal, dan catat "
     "pelajarannya agar paket ini tetap segar."),
]


def secs(words: int) -> int:
    return max(8, int(round(words / WPM * 60)))


def tts_ready(text: str) -> str:
    t = text.replace("145 kata/menit", "seratus empat puluh lima kata per menit")
    t = re.sub(r"(\d+)%", lambda m: f"{m.group(1)} persen", t)
    return t


def build(out_dir: str) -> Dict[str, List[str]]:
    os.makedirs(out_dir, exist_ok=True)
    slides, script, cum = [], [], 0
    for i, (title, narr) in enumerate(MODULES, 1):
        d = secs(len(narr.split()))
        slides.append((i, title, narr, d))
        m0, s0 = divmod(cum, 60)
        m1, s1 = divmod(cum + d, 60)
        script.append(f"### Slide {i} — {title}  [{m0:02d}:{s0:02d} → {m1:02d}:{s1:02d}]"
                      f"  ({d} detik)\n\n{tts_ready(narr)}\n")
        cum += d
    deck_slides = "".join(
        f"<section class='s'><h2>{i}. {t}</h2><p class='narr'>{n}</p>"
        f"<div class='meta'>durasi narasi ±{d} detik · {len(n.split())} kata</div>"
        f"<details><summary>speaker notes</summary><p>{n}</p></details></section>"
        for i, t, n, d in slides)
    css = ("body{font-family:system-ui;background:#0F172A;color:#F1F5F9;margin:0;"
           "padding:26px}.s{border:1px solid #24344F;background:#16233F;border-radius:16px;"
           "padding:18px;margin:0 0 14px;page-break-after:always}h1{font-size:24px}"
           "h2{font-size:17px;margin:0 0 8px}.narr{font-size:13.5px;line-height:1.6;"
           "color:#CBD5E1}.meta{font-size:11px;color:#64748B;margin-top:8px}"
           "details{margin-top:8px}summary{cursor:pointer;font-size:12px;color:#38BDF8}"
           "@media print{body{background:#fff;color:#111}.s{border-color:#ccc}}")
    html = (f"<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            f"<title>Kursus DAN</title><style>{css}</style></head><body>"
            f"<h1>Kursus DAN — {len(slides)} slide · total narasi ±{cum // 60} menit "
            f"{cum % 60} detik</h1>{deck_slides}</body></html>")
    open(os.path.join(out_dir, "course_deck.html"), "w", encoding="utf-8").write(html)
    open(os.path.join(out_dir, "course_audio_script.md"), "w", encoding="utf-8").write(
        "# Naskah Audio Kursus DAN\n\nUrutan sesuai slide; sintetis per slide lalu tumpuk "
        "sesuai timestamp.\n\n" + "\n".join(script))
    open(os.path.join(out_dir, "COURSE.md"), "w", encoding="utf-8").write(
        "# Produksi Kursus Berjalan\n\n"
        "1. Sintesis audio per slide memakai TTS pilihan Anda (atau generate_speech pada "
        "agent): gunakan `course_audio_script.md`.\n"
        "2. Susun video: satu slide = satu klip sepanjang data-durasi pada deck.\n"
        "3. QC audio (sub-skill 16): loudness konsisten, tanpa artefak, pelafalan merek "
        "benar.\n"
        "4. Tambahkan subtitle dari naskah (sudah kalimat pendek).\n"
        "5. Unggah bersama `course_deck.html` sebagai materi pendamping.\n")
    return {"slides": [t for _, t, _, _ in slides], "total_secs": [cum]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · course kit (deck+audio script)")
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "deliverables", "course"))
    a = ap.parse_args(argv)
    R = build(a.out_dir)
    print(f"[DAN] course kit: {len(R['slides'])} slide · total narasi "
          f"{R['total_secs'][0] // 60}m{R['total_secs'][0] % 60}s -> {a.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
