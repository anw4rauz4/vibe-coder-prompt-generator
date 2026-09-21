#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt_lab.py — Sub-skill 10 · Prompt Engineering: lint, skor, perbaiki, & varian.

Memperlakukan prompt sebagai ARTIFAK yang bisa di-QA, bukan teks sekali tulis:
  lint     -> checklist elemen (peran, konteks, tugas, kendala, format keluaran,
              contoh, pembatas, larangan, kriteria sukses) + skor 0-100 + masalah
  improve  -> kerangka ulang prompt yang memenuhi elemen yang hilang
  variants -> n varian pembingkaian (role-first, constraint-first, few-shot, CoT)

PAKAI
  python3 prompt_lab.py lint --text "buatkan laporan penjualan"
  python3 prompt_lab.py improve --file prompt.txt --out prompt_baru.md
  python3 prompt_lab.py variants --text "..." --n 3
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple

CHECKS: List[Tuple[str, str, str, int]] = [
    # (kunci, nama, cara deteksi, bobot)
    ("role", "Peran/persona", r"(?i)\b(kamu|anda|you|act as|bertindak|sebagai)\b.*\b(ahli|expert|specialist|profesional|professional|assistant|asisten)\b", 10),
    ("audience", "Audiens/pengguna hasil", r"(?i)\b(untuk|for)\b.*\b(pembaca|audience|audiens|manajer|manager|pemimpin|client|klien|tim|team)\b", 8),
    ("task", "Tugas eksplisit (kata kerja)", r"(?i)\b(buat|buatkan|create|make|tulis|write|analisa|analyze|hitung|compute|ringkas|summarize|review|susun|draft)\b", 12),
    ("context", "Konteks/data masukan", r"(?i)\b(berdasarkan|based on|data|file|csv|json|lampiran|attached|berikut|following)\b", 10),
    ("constraints", "Kendala/batasan", r"(?i)\b(maksimal|max|minimum|min|tidak boleh|don'?t|jangan|hindari|avoid|hanya|only|batas|limit)\b", 10),
    ("format", "Format keluaran", r"(?i)\b(format|tabel|table|markdown|json|poin|bullet|daftar|list|paragraf|paragraph|slide|html|csv)\b", 12),
    ("length", "Panjang/ukuran", r"(?i)\b(\d+\s*(kata|words|kalimat|sentences|baris|lines|poin|points|karakter|characters|slide|halaman|pages))\b", 6),
    ("examples", "Contoh (few-shot)", r"(?i)\b(contoh|example|misal|e\.g\.|seperti berikut|such as)\s*[:\"]", 8),
    ("delimiters", "Pembatas input", r"(```|\"\"\"|<|\[|###|---)", 6),
    ("success", "Kriteria sukses/verifikasi", r"(?i)\b(pastikan|verify|check|kriteria|criteria|valid|uji|test|semua|every)\b", 8),
    ("negatives", "Larangan jelas", r"(?i)\b(jangan|don'?t|do not|hindari|avoid|tanpa|without)\b", 5),
    ("output_lang", "Bahasa keluaran", r"(?i)\b(bahasa|language|indonesia|english|inggris)\b", 5),
]

AMBIGU = [r"(?i)\bdsb\b", r"(?i)\betc\.?", r"(?i)\bsekitar\b(?!\s*\d)", r"(?i)\bkira-kira\b",
          r"(?i)\bsomething\b", r"(?i)\bbagus\b(?!\s*(dalam|dengan|untuk))"]


def lint(prompt: str) -> Dict[str, Any]:
    found, missing = [], []
    score = 0
    for key, name, rx, w in CHECKS:
        if re.search(rx, prompt):
            found.append({"key": key, "name": name, "weight": w})
            score += w
        else:
            missing.append({"key": key, "name": name, "weight": w})
    amb = [a for a in AMBIGU if re.search(a, prompt)]
    if amb:
        score -= 5 * len(amb)
    if len(prompt) < 40:
        score -= 10
        missing.append({"key": "detail", "name": "Terlalu pendek (<40 karakter)", "weight": 10})
    score = max(0, min(100, score))
    grade = ("A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "D")
    return {"score": score, "grade": grade, "present": found, "missing": missing,
            "ambiguous": amb, "chars": len(prompt),
            "advice": _advice(missing, amb)}


def _advice(missing: List[Dict], amb: List[str]) -> List[str]:
    out = []
    prio = {"task": "Mulai dengan kata kerja tugas yang spesifik (buat/analisa/ringkas).",
            "format": "Sebutkan format keluaran eksplisit (tabel/markdown/json/poin).",
            "context": "Rujuk data/masukan konkret (file, periode, angka).",
            "constraints": "Tambahkan batasan (maksimal N, jangan X).",
            "role": "Beri peran: 'Bertindaklah sebagai analis marketing senior…'",
            "success": "Tambahkan kriteria sukses: 'Pastikan setiap angka punya satuan & periode.'",
            "examples": "Sertakan 1 contoh keluaran yang diharapkan.",
            "length": "Sebutkan panjang target (mis. maksimal 150 kata).",
            "delimiters": "Apit data masukan dengan pembatas (``` atau ###).",
            "audience": "Sebutkan siapa pembaca hasilnya.",
            "negatives": "Sebutkan larangan eksplisit untuk mencegah hal tak diinginkan.",
            "output_lang": "Tegaskan bahasa keluaran.",
            "detail": "Perpanjang prompt dengan konteks & kendala; prompt <40 karakter hampir selalu under-specified."}
    for m in sorted(missing, key=lambda x: -x["weight"]):
        if m["key"] in prio:
            out.append(prio[m["key"]])
    for a in amb:
        out.append(f"Hindari kata ambigu {a.replace('(?i)', '')} — ganti dengan angka/batasan pasti.")
    return out


SKELETON = """{role}

KONTEKS:
{context}

TUGAS:
{task}

KENDALA:
- {constraint1}
- {constraint2}

FORMAT KELUARAN:
{format}

KRITERIA SUKSES:
- {success1}

LARANGAN:
- {negative1}
"""


def improve(prompt: str) -> str:
    L = lint(prompt)
    first = prompt.strip().split("\n")[0]
    role = ("Bertindaklah sebagai spesialis yang relevan dengan tugas berikut."
            if not any(c["key"] == "role" for c in L["present"]) else first)
    ctx = ("Data/masukan: <tempel di sini> (sebutkan sumber & periode)."
           if not any(c["key"] == "context" for c in L["present"]) else "")
    task = first if any(c["key"] == "task" for c in L["present"]) else \
        f"Laksanakan tugas berikut dengan teliti: {first}"
    fmt = ("Markdown dengan tabel untuk angka dan daftar poin untuk rekomendasi."
           if not any(c["key"] == "format" for c in L["present"]) else "")
    return SKELETON.format(
        role=role,
        context=ctx or "Gunakan hanya data yang diberikan; tandai `asumsi:` bila terpaksa.",
        task=task,
        constraint1="Maksimal 400 kata kecuali diminta lain.",
        constraint2="Setiap angka wajib punya satuan dan periode.",
        format=fmt or "Markdown; tabel untuk metrik, poin untuk aksi.",
        success1="Semua klaim numerik dapat ditelusuri ke masukan.",
        negative1="Jangan mengarang data atau sumber yang tidak ada.",
    ) + f"\n<!-- skor awal: {L['score']}/100 ({L['grade']}) · elemen hilang: " \
        + ", ".join(m["name"] for m in L["missing"][:6]) + " -->\n"


def variants(prompt: str, n: int = 3) -> List[Dict[str, str]]:
    p = prompt.strip()
    pool = [
        ("role-first", f"Bertindaklah sebagai pakar terdepan di bidang ini. {p}"),
        ("constraint-first", f"Kendala ketat: jawaban harus terverifikasi & ringkas. {p}"),
        ("few-shot", f"{p}\n\nContoh keluaran yang baik:\n```\n<isi 1 contoh nyata>\n```"),
        ("chain-of-thought", f"{p}\n\nBerpikirlah langkah-demi-langkah terlebih dahulu, "
                             f"lalu berikan jawaban final setelah heading '## Jawaban'."),
        ("audience-first", f"Hasil ini akan dibaca pimpinan yang hanya punya 2 menit. {p}"),
        ("counterfactual", f"{p}\n\nSebelum menjawab, sebutkan 2 cara jawaban ini bisa "
                           f"menyesatkan, lalu hindari keduanya."),
    ]
    return [{"style": s, "prompt": t} for s, t in pool[:max(1, min(n, len(pool)))]]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · prompt engineering lab")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("lint", "improve", "variants"):
        p = sub.add_parser(name)
        p.add_argument("--text", default="")
        p.add_argument("--file", default="")
        p.add_argument("--out", default="")
        p.add_argument("--n", type=int, default=3)
    a = ap.parse_args(argv)
    prompt = a.text or (open(a.file, encoding="utf-8").read() if a.file else "")
    if not prompt:
        print("[DAN] butuh --text atau --file")
        return 2
    if a.cmd == "lint":
        L = lint(prompt)
        print(f"[DAN] skor {L['score']}/100 ({L['grade']}) · {len(L['present'])} elemen ada · "
              f"{len(L['missing'])} hilang")
        for m in L["missing"]:
            print(f"   - hilang: {m['name']} (bobot {m['weight']})")
        for adv in L["advice"][:6]:
            print("   * ", adv)
        if a.out:
            os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
            json.dump(L, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return 0
    if a.cmd == "improve":
        out = improve(prompt)
        if a.out:
            os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
            open(a.out, "w", encoding="utf-8").write(out)
        print(out)
        return 0
    vs = variants(prompt, a.n)
    for v in vs:
        print(f"\n--- varian: {v['style']} ---\n{v['prompt']}")
    if a.out:
        json.dump(vs, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
