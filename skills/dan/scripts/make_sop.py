#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_sop.py — SOP / runbook operasional tim: siapa menjalankan apa, kapan, dan
bagaimana eskalasinya. Dibangkitkan dari kemampuan nyata paket (perintah sebenarnya),
bukan dokumen kosong.

Isi: cadence harian/mingguan/bulanan/kuartalan (langkah + perintah + durasi),
matriks RACI per aktivitas, aturan eskalasi, dan checklist "definisi selesai".

PAKAI
  python3 make_sop.py --tim "PMO Lead,Analyst,Creative,Ops-Finance,Owner" \
      --out deliverables/sop_tim.md
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))

CADENCE = [
    ("Harian (5–10 menit)", [
        ("Cek angka kemarin: spend, ROAS, CPA vs ambang", "dan_analytics / dashboard ads",
         "Analyst"),
        ("Jalankan PMO guard pada projects terbaru", "python3 …/pmo_guard.py projects.json",
         "PMO Lead"),
        ("Tandai tugas kritis/stalled baru ke pemiliknya", "weekly_summary / guard report",
         "PMO Lead"),
    ]),
    ("Mingguan (60–90 menit)", [
        ("Kumpulkan update form dari seluruh pemilik tugas", "forms.html (progress)",
         "Semua pemilik tugas"),
        ("Jalankan ritme mingguan lengkap", "python3 …/weekly.py --projects … --channel …",
         "PMO Lead"),
        ("Review burn-up & diff antar-minggu", "burnup.html + weekly_diff",  "PMO Lead"),
        ("Putuskan 3 keputusan minggu ini (realokasi/uji/tenggat)", "weekly_summary §keputusan",
         "Owner + PMO Lead"),
        ("Periksa kualitas narasi laporan sebelum dibagikan", "narrative_trend + narrative_check",
         "Analyst"),
    ]),
    ("Bulanan (2–3 jam)", [
        ("Review strategi: channel mix, budget 70/20/10, harga", "strategy-brief + budget_sim",
         "Owner + PMO Lead"),
        ("Audit klaim angka pada semua laporan klien", "claim_audit per laporan", "Analyst"),
        ("Kesehatan paket & regresi QA", "dan.py doctor --full", "PMO Lead"),
        ("Refresh knowledge: digest rilis + catatan pelajaran", "make_digest + notes",
         "Semua"),
    ]),
    ("Kuartalan (setengah hari)", [
        ("Kursus internal / onboarding anggota baru", "kursus/README.md", "PMO Lead"),
        ("Audit posisi & diferensiasi", "perceptual map + STP (sub-skill 02)", "Owner"),
        ("Uji ulang asumsi model (damp, cv, break-even)", "budget_sim + metric-library",
         "Analyst + Ops-Finance"),
    ]),
]

RACI_DEFAULT = [
    ("Ritme mingguan (weekly.py)", "PMO Lead", "Analyst+Creative", "Ops-Finance", "Owner"),
    ("Realokasi budget", "Owner", "PMO Lead+Analyst", "Ops-Finance", "-"),
    ("Konten & kreatif", "Creative", "Analyst", "PMO Lead", "Owner"),
    ("Laporan klien", "Analyst", "PMO Lead", "Owner", "-"),
    ("Guard & eskalasi", "PMO Lead", "-", "Owner", "-"),
    ("Keamanan data & secret", "Ops-Finance", "PMO Lead", "-", "Owner"),
]

ESCALATION = [
    ("Tugas kritis >3 hari tanpa tindakan", "PMO Lead → Owner", "1×24 jam",
     "pecah tugas / tambah resource / turunkan scope"),
    ("ROAS channel < break-even 2 minggu", "Analyst → Owner", "1×7 hari",
     "uji ulang kreatif/audiens atau hentikan channel"),
    ("CPI < 0,85 (biaya melebihi nilai kerja)", "Ops-Finance → Owner", "1×7 hari",
     "bekukan pengeluaran non-kritis"),
    ("Kebocoran data / secret tercecer", "Ops-Finance → Owner", "SEGERA (<4 jam)",
     "rotasi kunci, tarik akses, insiden report"),
    ("Krisis reputasi / komplain viral", "PMO Lead → Owner", "SEGERA (<4 jam)",
     "jalankan crisis_sim.py skenario D"),
]

DONE = [
    "Setiap angka di laporan punya sumber atau ditandai `asumsi:`",
    "Setiap temuan punya 1 aksi + pemilik + tenggat",
    "Guard bersih ATAU pelanggaran punya tindakan open ber-owner",
    "Narasi lolos narrative_check (skor ≥88) sebelum dikirim keluar",
    "Rilis paket lewat `release.py` (gate QA tidak dilompati)",
    "Secret hanya di environment; tidak ada di file/repo/chat",
]


def build(tim: List[str]) -> str:
    L = ["# SOP / Runbook Operasional Tim", "",
         f"**Peran terlibat:** {', '.join(tim)}", "",
         "Dokumen ini dibangkitkan dari perintah nyata paket DAN — jalankan persis, "
         "jangan improvisasi tanpa mencatat perubahan.", ""]
    for name, items in CADENCE:
        L += [f"## {name}", "", "| Aktivitas | Alat/perintah | Penanggung jawab |",
              "|---|---|---|"]
        for act, tool, pic in items:
            L.append(f"| {act} | `{tool}` | {pic} |")
        L.append("")
    L += ["## Matriks RACI", "",
          "| Aktivitas | Responsible | Accountable | Consulted | Informed |",
          "|---|---|---|---|---|"]
    for a, r, ac, c, i in RACI_DEFAULT:
        L.append(f"| {a} | {r} | {ac} | {c} | {i} |")
    L += ["", "## Aturan eskalasi", "",
          "| Pemicu | Jalur | SLA | Tindakan default |", "|---|---|---|---|"]
    for p, j, sla, t in ESCALATION:
        L.append(f"| {p} | {j} | {sla} | {t} |")
    L += ["", "## Definisi selesai (definition of done)", ""]
    L += [f"- [ ] {d}" for d in DONE]
    L += ["", "---", "_DAN · make_sop. Tinjau ulang SOP tiap kuartal atau saat tool berubah._"]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · SOP/runbook generator")
    ap.add_argument("--tim", default="PMO Lead,Analyst,Creative,Ops-Finance,Owner")
    ap.add_argument("--out", default=os.path.join(ROOT, "deliverables", "sop_tim.md"))
    a = ap.parse_args(argv)
    md = build([x.strip() for x in a.tim.split(",") if x.strip()])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(md)
    print(f"[DAN] SOP -> {a.out} ({len(md.splitlines())} baris)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
