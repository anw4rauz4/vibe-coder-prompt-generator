#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
storyboard.py — Kreator Video & Konten (sub-skill DAN #04).

Mengubah brief singkat menjadi paket produksi lengkap:
  * 5 varian hook (3 detik pertama)
  * shot list bertiming (tipe shot, gerakan kamera, visual, teks layar, VO, SFX)
  * prompt image-generation & video-generation per shot
  * caption + hashtag + CTA
  * file subtitle .srt
  * checklist produksi

PAKAI:
  python3 storyboard.py --product "Serum Vitamin C" --audience "wanita 25-34, kulit kusam" \
      --platform tiktok --duration 30 --structure hook_story_offer --goal konversi \
      --tone friendly --offer "Diskon 40% + gratis ongkir" --cta "Klik keranjang kuning"

  python3 storyboard.py --brief brief.json          # semua field dari JSON
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

# --------------------------------------------------------------------- presets

PLATFORMS: Dict[str, Dict[str, Any]] = {
    "tiktok": {"ratio": "9:16", "w": 1080, "h": 1920, "duration": 30, "max": 90,
               "safe": "teks utama di 25-75% tinggi frame; hindari 15% bawah (UI)",
               "style": "raw, handheld, cepat, subtitle besar, sound trending",
               "hook_window": 1.5},
    "reels": {"ratio": "9:16", "w": 1080, "h": 1920, "duration": 30, "max": 90,
              "safe": "hindari 20% bawah & 10% atas; teks tengah",
              "style": "estetik, transisi halus, warna hangat, subtitle rapi",
              "hook_window": 2.0},
    "shorts": {"ratio": "9:16", "w": 1080, "h": 1920, "duration": 45, "max": 180,
               "safe": "teks di 30-70% tinggi; judul terlihat di 3 detik pertama",
               "style": "padat, to the point, loop-friendly",
               "hook_window": 2.0},
    "youtube_ad": {"ratio": "16:9", "w": 1920, "h": 1080, "duration": 30, "max": 180,
                   "safe": "brand & CTA harus muncul sebelum detik ke-5 (skip button)",
                   "style": "sinematik, pencahayaan terkontrol, VO profesional",
                   "hook_window": 5.0},
    "longform": {"ratio": "16:9", "w": 1920, "h": 1080, "duration": 240, "max": 900,
                 "safe": "lower-third untuk nama/topik; chapter markers tiap 60-90 detik",
                 "style": "naratif, B-roll kaya, grafik pendukung",
                 "hook_window": 15.0},
    "carousel": {"ratio": "4:5", "w": 1080, "h": 1350, "duration": 0, "max": 0,
                 "safe": "slide 1 = hook, slide terakhir = CTA; 6-10 slide",
                 "style": "tipografi besar, 1 ide per slide, kontras tinggi",
                 "hook_window": 0},
}

# struktur naratif: (nama beat, bobot durasi, fungsi beat)
STRUCTURES: Dict[str, List[Dict[str, Any]]] = {
    "hook_story_offer": [
        {"beat": "Hook", "w": 0.10, "job": "hentikan scroll: klaim berani/pertanyaan/visual aneh"},
        {"beat": "Problem", "w": 0.15, "job": "sebut masalah yang dirasakan audiens, buat mereka mengangguk"},
        {"beat": "Story", "w": 0.30, "job": "cerita transformasi / bukti / behind the scene"},
        {"beat": "Offer", "w": 0.25, "job": "produk + benefit + penawaran spesifik"},
        {"beat": "Proof", "w": 0.10, "job": "testimoni, angka, review, sertifikasi"},
        {"beat": "CTA", "w": 0.10, "job": "satu perintah jelas + urgensi"},
    ],
    "aida": [
        {"beat": "Attention", "w": 0.12, "job": "visual/audio paling mencolok"},
        {"beat": "Interest", "w": 0.25, "job": "fakta menarik yang relevan dengan audiens"},
        {"beat": "Desire", "w": 0.33, "job": "buat mereka membayangkan hasilnya (before/after)"},
        {"beat": "Action", "w": 0.30, "job": "CTA + penawaran + urgensi"},
    ],
    "pas": [
        {"beat": "Problem", "w": 0.25, "job": "perbesar rasa sakit/masalah"},
        {"beat": "Agitate", "w": 0.30, "job": "konsekuensi kalau dibiarkan; sentuh emosi"},
        {"beat": "Solution", "w": 0.45, "job": "produk sebagai jalan keluar + bukti + CTA"},
    ],
    "before_after_bridge": [
        {"beat": "Before", "w": 0.30, "job": "kondisi awal yang relatable"},
        {"beat": "After", "w": 0.30, "job": "kondisi ideal — hasil yang diinginkan"},
        {"beat": "Bridge", "w": 0.40, "job": "produk/cara sebagai jembatan + CTA"},
    ],
    "listicle": [
        {"beat": "Hook", "w": 0.12, "job": "'3 kesalahan yang bikin X' — janji nilai"},
        {"beat": "Poin 1", "w": 0.22, "job": "kesalahan/tips pertama + contoh"},
        {"beat": "Poin 2", "w": 0.22, "job": "kedua + contoh"},
        {"beat": "Poin 3", "w": 0.22, "job": "ketiga + contoh (paling penting)"},
        {"beat": "CTA", "w": 0.22, "job": "rangkuman + ajakan follow/klik"},
    ],
    "testimonial": [
        {"beat": "Hook", "w": 0.10, "job": "hasil paling mengejutkan di depan"},
        {"beat": "Siapa saya", "w": 0.15, "job": "identitas + konteks agar relatable"},
        {"beat": "Masalah", "w": 0.20, "job": "skeptisisme awal / kegagalan sebelumnya"},
        {"beat": "Momen berubah", "w": 0.25, "job": "saat mencoba produk, apa yang terasa"},
        {"beat": "Hasil", "w": 0.20, "job": "angka/spesifik + perasaan"},
        {"beat": "CTA", "w": 0.10, "job": "ajakan + penawaran"},
    ],
    "demo_produk": [
        {"beat": "Hook", "w": 0.10, "job": "tunjukkan hasil akhir dulu (reverse reveal)"},
        {"beat": "Unboxing/Intro", "w": 0.15, "job": "produk & klaim utama"},
        {"beat": "Demo 1", "w": 0.22, "job": "fitur pertama, close-up pemakaian"},
        {"beat": "Demo 2", "w": 0.22, "job": "fitur pembeda vs kompetitor"},
        {"beat": "Hasil", "w": 0.21, "job": "before/after berdampingan"},
        {"beat": "CTA", "w": 0.10, "job": "harga, promo, cara beli"},
    ],
}

GOALS: Dict[str, Dict[str, str]] = {
    "konversi": {"cta_style": "langsung + urgensi", "metric": "CVR, CPA, ROAS"},
    "awareness": {"cta_style": "lembut, ajak follow/save", "metric": "reach, impressi, view 3s"},
    "engagement": {"cta_style": "pertanyaan & ajakan komentar", "metric": "komentar, share, save"},
    "traffic": {"cta_style": "arahkan ke link/bio", "metric": "CTR, sesi, bounce rate"},
    "retensi": {"cta_style": "loyalitas, program member", "metric": "repeat rate, LTV, churn"},
    "launching": {"cta_style": "pre-order & countdown", "metric": "pre-order, waitlist, hype"},
}

TONES = {
    "friendly": "santai, akrab, bahasa sehari-hari, emoji seperlunya",
    "profesional": "tegas, berbasis data, tanpa basa-basi",
    "lucu": "humor ringan, timing komedi, punchline di akhir beat",
    "inspiratif": "menggugah, kalimat pendek bernada naik, fokus pada kemungkinan",
    "edukatif": "jelas, bertahap, definisi singkat lalu contoh",
    "mewah": "elegan, hemat kata, jeda, fokus pada detail & kualitas",
    "urgensi": "cepat, padat, menekankan batas waktu & kelangkaan",
}

SHOT_TYPES = ["Extreme Close-Up", "Close-Up", "Medium Shot", "Medium Wide", "Wide Shot",
              "Over-the-shoulder", "Top-down/Flatlay", "POV", "Macro", "B-roll insert"]
CAMERA_MOVES = ["static tripod", "handheld subtle", "slow push-in", "pull-out reveal",
                "orbit 180°", "crane up", "whip pan", "tracking follow", "rack focus", "dolly zoom"]
TRANSITIONS = ["hard cut", "match cut", "whip pan", "morph cut", "light leak",
               "object wipe", "zoom punch", "J-cut audio", "L-cut audio"]

# Tata bahasa shot per beat: (tipe shot, gerakan kamera).
# Tanpa ini, prompt jadi tidak koheren — mis. "POV + dolly zoom" ditempel ke
# visual "hero shot produk". Shot type harus mengikuti maksud beat-nya.
BEAT_GRAMMAR: Dict[str, List[Tuple[str, str]]] = {
    "Hook": [("Close-Up", "slow push-in"), ("Extreme Close-Up", "static tripod"),
             ("Medium Shot", "handheld subtle")],
    "Attention": [("Medium Wide", "pull-out reveal"), ("Close-Up", "slow push-in")],
    "Problem": [("Medium Shot", "handheld subtle"), ("Close-Up", "slow push-in"),
                ("B-roll insert", "tracking follow")],
    "Agitate": [("Close-Up", "dolly zoom"), ("Extreme Close-Up", "static tripod"),
                ("B-roll insert", "handheld subtle")],
    "Interest": [("B-roll insert", "rack focus"), ("Medium Shot", "slow push-in")],
    "Story": [("Medium Shot", "handheld subtle"), ("Over-the-shoulder", "tracking follow"),
              ("Close-Up", "slow push-in")],
    "Momen berubah": [("Close-Up", "rack focus"), ("Medium Shot", "slow push-in")],
    "Siapa saya": [("Medium Shot", "static tripod"), ("Over-the-shoulder", "handheld subtle")],
    "Offer": [("Close-Up", "orbit 180°"), ("Top-down/Flatlay", "static tripod"),
              ("Macro", "slow push-in")],
    "Solution": [("Medium Shot", "static tripod"), ("Top-down/Flatlay", "slow push-in"),
                 ("Close-Up", "rack focus")],
    "Desire": [("Wide Shot", "crane up"), ("Close-Up", "slow push-in")],
    "Before": [("Medium Shot", "static tripod"), ("Close-Up", "handheld subtle")],
    "After": [("Medium Shot", "pull-out reveal"), ("Close-Up", "slow push-in")],
    "Bridge": [("Close-Up", "rack focus"), ("Medium Shot", "slow push-in")],
    "Proof": [("B-roll insert", "static tripod"), ("Medium Shot", "handheld subtle"),
              ("Close-Up", "slow push-in")],
    "Hasil": [("Close-Up", "slow push-in"), ("Medium Shot", "pull-out reveal")],
    "Poin 1": [("Medium Shot", "static tripod"), ("B-roll insert", "rack focus")],
    "Poin 2": [("Medium Shot", "static tripod"), ("B-roll insert", "rack focus")],
    "Poin 3": [("Close-Up", "slow push-in"), ("B-roll insert", "rack focus")],
    "CTA": [("Medium Shot", "static tripod"), ("Close-Up", "slow push-in")],
    "Action": [("Medium Shot", "static tripod"), ("Close-Up", "slow push-in")],
    "Unboxing/Intro": [("Top-down/Flatlay", "static tripod"), ("Close-Up", "orbit 180°")],
    "Demo 1": [("Macro", "rack focus"), ("Top-down/Flatlay", "static tripod")],
    "Demo 2": [("Extreme Close-Up", "slow push-in"), ("Over-the-shoulder", "tracking follow")],
}
_DEFAULT_GRAMMAR = [("Medium Shot", "static tripod"), ("Close-Up", "slow push-in"),
                    ("B-roll insert", "handheld subtle")]


def shot_grammar(beat: str, j: int) -> Tuple[str, str]:
    """Ambil (tipe shot, gerakan kamera) yang cocok untuk beat ini."""
    opts = BEAT_GRAMMAR.get(beat, _DEFAULT_GRAMMAR)
    return opts[j % len(opts)]



def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")[:60]


def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def wc_for(seconds: float, wpm: float = 145.0) -> int:
    """Perkiraan jumlah kata VO untuk durasi tertentu (ID ~145 kata/menit)."""
    return max(3, int(round(seconds / 60 * wpm)))


def fmt_tc(sec: float) -> str:
    ms = int(round((sec - int(sec)) * 1000))
    s = int(sec)
    return f"{s // 60:02d}:{s % 60:02d}:{ms // 10:02d}"


def srt_time(sec: float) -> str:
    ms = int(round((sec - int(sec)) * 1000))
    s = int(sec)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d},{ms:03d}"


# --------------------------------------------------------------------- generator

def make_hooks(b: Dict[str, Any]) -> List[Dict[str, str]]:
    p, aud = b["product"], b["audience"]
    prob = b.get("problem") or "masalah yang belum terselesaikan"
    res = b.get("result") or "hasil yang kamu inginkan"
    num = b.get("number") or 3
    return [
        {"type": "Pertanyaan menusuk",
         "text": f"Pernah ngerasa {prob} padahal udah coba semuanya?",
         "on_screen": f"Masih {prob}?"},
        {"type": "Klaim berani",
         "text": f"Aku bebas dari {prob} dalam {b.get('timeframe', '14 hari')} — ini caranya.",
         "on_screen": f"{str(b.get('timeframe', '14 HARI')).upper()} · TANPA {short(prob, 20).upper()}"},
        {"type": "Angka/list",
         "text": f"{num} kesalahan yang bikin {aud.split(',')[0]} gagal dapet {res}.",
         "on_screen": f"{num} KESALAHAN FATAL"},
        {"type": "Kontras visual",
         "text": f"Ini {res} — dan ini kondisi aku sebelumnya.",
         "on_screen": "SEBELUM ⇄ SESUDAH"},
        {"type": "Rahasia/insider",
         "text": f"Yang nggak diceritakan brand soal {p}… aku bongkar di sini.",
         "on_screen": "INI RAHASIA INDUSTRI"},
        {"type": "POV relatable",
         "text": f"POV: kamu {aud.split(',')[0]} dan baru nemu {p}.",
         "on_screen": "POV:"},
        {"type": "Urgensi",
         "text": f"Jangan beli {p} sebelum nonton ini sampai habis.",
         "on_screen": "TUNGGU! JANGAN BELI DULU"},
    ][:5]


def make_shots(b: Dict[str, Any]) -> List[Dict[str, Any]]:
    plat = PLATFORMS.get(b["platform"], PLATFORMS["tiktok"])
    total = float(b.get("duration") or plat["duration"] or 30)
    beats = STRUCTURES.get(b["structure"], STRUCTURES["hook_story_offer"])
    p, aud = b["product"], b["audience"]
    tone = TONES.get(b["tone"], TONES["friendly"])
    goal = GOALS.get(b["goal"], GOALS["konversi"])
    offer, cta = b.get("offer", ""), b.get("cta", "")
    shots: List[Dict[str, Any]] = []
    t = 0.0
    for i, bt in enumerate(beats):
        dur = round(total * bt["w"], 2)
        if i == len(beats) - 1:
            dur = round(total - t, 2)
        n_shot = 1 if dur < 3 else (2 if dur < 8 else 3)
        sub = dur / n_shot
        for j in range(n_shot):
            idx = len(shots) + 1
            st, cm = shot_grammar(bt["beat"], j)
            tr = TRANSITIONS[(idx + i) % len(TRANSITIONS)]
            vo = _vo_for(bt["beat"], b, sub, tone, variant=j + i)
            shots.append({
                "no": idx,
                "beat": bt["beat"],
                "job": bt["job"],
                "start": round(t + j * sub, 2),
                "end": round(t + (j + 1) * sub, 2),
                "duration": round(sub, 2),
                "shot_type": st,
                "camera": cm,
                "transition_in": tr if j == 0 else "hard cut",
                "visual": _visual_for(bt["beat"], j, b, st),
                "on_screen_text": _ost_for(bt["beat"], j, b),
                "vo": vo,
                "vo_words": wc_for(sub),
                "sfx": _sfx_for(bt["beat"], j),
                "b_roll": _broll_for(bt["beat"], b),
                "image_prompt": _img_prompt(b, bt["beat"], st, cm, j, plat),
                "video_prompt": _vid_prompt(b, bt["beat"], st, cm, sub, plat),
                "aspect": plat["ratio"],
            })
        t += dur
    return shots


def _vo_for(beat: str, b: Dict[str, Any], dur: float, tone: str, variant: int = 0) -> str:
    """Susun VO dari kalimat utuh yang muat budget kata (tidak memotong kalimat)."""
    p, aud = b["product"], b["audience"]
    aud_s = aud.split(",")[0].strip()
    prob = b.get("problem", "masalah ini")
    res = b.get("result", "hasilnya")
    target = wc_for(dur)
    bank = {
        "Hook": [f"Stop dulu — kalau kamu termasuk {aud_s}, ini penting banget.",
                 f"Aku nggak nyangka {p} bisa se-ngaruh ini ke {prob}.",
                 f"Beberapa detik ke depan bisa mengubah cara kamu mengatasi {prob}.",
                 f"Kalau kamu masih berjuang dengan {prob}, tonton sampai habis."],
        "Attention": [f"Perhatikan baik-baik, {prob} jauh lebih umum dari yang kamu kira.",
                      f"Ini bagian yang hampir semua orang lewatkan soal {prob}."],
        "Problem": [f"Kebanyakan {aud_s} stuck di {prob} bertahun-tahun.",
                    "Udah coba ini itu, tapi hasilnya tetap balik lagi.",
                    f"Aku pernah di titik paling capek: {prob} nggak kelar-kelar."],
        "Agitate": [f"Kalau dibiarkan, {prob} bikin {b.get('pain', 'waktu dan biaya makin terkuras')}.",
                    "Dan makin lama ditunda, makin susah diperbaiki.",
                    "Yang paling mahal bukan produknya, tapi waktu yang kebuang."],
        "Interest": [f"Faktanya, {b.get('fact', 'mayoritas orang salah di langkah pertama')}.",
                     "Ini bagian yang jarang dijelasin brand mana pun."],
        "Story": [f"Aku mulai pakai {p} karena penasaran, bukan karena iklan.",
                  "Minggu pertama belum kelihatan, minggu kedua mulai beda.",
                  f"Yang bikin aku lanjut: {b.get('usp', 'hasilnya konsisten')}.",
                  "Setiap malam aku pakai, dan aku catat perubahannya."],
        "Momen berubah": [f"Aku sempat skeptis, sampai akhirnya coba {p} sendiri.",
                          "Momen berubahnya waktu aku lihat hasil minggu kedua."],
        "Siapa saya": [f"Aku {b.get('persona', aud_s)}, dan ini pengalaman nyata.",
                       f"Sama kayak kamu, aku juga {aud_s} yang pengen hasil tanpa ribet."],
        "Offer": [f"{p} diformulasikan khusus untuk {aud_s}.",
                  f"Keunggulannya: {b.get('usp', 'hasil cepat dan aman')}.",
                  f"Sekarang lagi {b.get('offer', 'promo terbatas')}."],
        "Solution": [f"Solusinya {p}, dan ini cara pakainya biar maksimal.",
                     f"Hasilnya: {res} tanpa drama dan tanpa ribet."],
        "Desire": [f"Bayangkan {res} — tanpa harus mikirin {prob} lagi.",
                   "Rasanya ringan, percaya diri balik sendiri."],
        "Before": [f"Sebelumnya kondisi aku begini: {prob}."],
        "After": [f"Setelah rutin, hasilnya {res}."],
        "Bridge": [f"Jembatannya {p}, dan caranya sesimpel ini.",
                  f"{b.get('offer', 'Promonya terbatas')} — tinggal {b.get('cta', 'klik link di bio')}."],
        "Proof": [f"Bukan cuma aku: {b.get('proof', 'ribuan review bintang 5')}.",
                  "Hasil tiap orang beda, tapi polanya sama."],
        "Hasil": [f"Hasilnya kelihatan di minggu ke-{b.get('week', 2)}: {res}.",
                  "Aku foto tiap minggu, dan bedanya jelas kelihatan."],
        "Poin 1": ["Pertama, jangan pernah lewatin langkah dasar ini."],
        "Poin 2": ["Kedua, konsistensi selalu mengalahkan produk yang mahal."],
        "Poin 3": ["Ketiga, ini yang paling sering dilupakan orang."],
        "CTA": [f"{b.get('cta', 'Cek link di bio')} — {goal_cta(b)}.",
                "Kalau bermanfaat, save dulu biar nggak hilang."],
        "Action": [f"{b.get('cta', 'Klik sekarang')}, {goal_cta(b)}.",
                   "Aku taruh linknya di bio, langsung cek aja."],
        "Unboxing/Intro": [f"Ini {p}, dan klaim utamanya: {b.get('usp', res)}."],
        "Demo 1": ["Cara pakainya simpel banget, perhatikan langkah ini."],
        "Demo 2": ["Bedanya dengan produk lain ada tepat di bagian ini."],
    }
    opts = bank.get(beat, bank["CTA"])
    k = variant % len(opts)
    ordered = opts[k:] + opts[:k]
    out: List[str] = []
    n = 0
    for s in ordered:
        w = len(s.split())
        if out and n + w > target * 1.3:
            break
        out.append(s)
        n += w
        if n >= target:
            break
    return " ".join(out) or ordered[0]


def goal_cta(b: Dict[str, Any]) -> str:
    g = b.get("goal", "konversi")
    return {"konversi": "sebelum kehabisan", "awareness": "follow biar nggak ketinggalan",
            "engagement": "komen di bawah ya", "traffic": "linknya ada di bio",
            "retensi": "gabung member sekarang", "launching": "pre-order ditutup malam ini"
            }.get(g, "sekarang")


def _visual_for(beat: str, j: int, b: Dict[str, Any], st: str) -> str:
    p = b["product"]
    base = {
        "Hook": ["Talent menatap kamera, ekspresi serius, background kontras",
                 "Tangan menutup lensa lalu terbuka ke produk",
                 "Teks besar menutupi layar lalu tergeser"],
        "Attention": ["Zoom cepat ke objek utama", "Split screen dua kondisi"],
        "Problem": ["B-roll ekspresi frustrasi, cahaya redup",
                    "Tumpukan produk gagal di meja", "Scroll HP mencari solusi"],
        "Agitate": ["Time-lapse kalender/jam, warna makin gelap",
                    "Close-up ekspresi kecewa", "Grafik biaya menurun"],
        "Interest": ["Motion graphic angka/fakta muncul", "Insert close-up detail produk"],
        "Story": ["Montase pemakaian harian, cahaya natural pagi",
                  "Talent bercerita ke kamera, handheld", "Jurnal/catatan progres"],
        "Momen berubah": ["Unboxing produk, reveal perlahan", "Ekspresi berubah jadi penasaran"],
        "Siapa saya": ["Talent memperkenalkan diri, medium shot, background personal"],
        "Offer": ["Hero shot produk dengan lighting studio",
                  "3 benefit muncul bergantian dengan ikon", "Harga coret → harga promo"],
        "Solution": ["Demo pemakaian langkah demi langkah", "Produk + hasil berdampingan"],
        "Desire": ["Slow-motion hasil akhir, warna cerah", "Talent tersenyum puas"],
        "Before": ["Foto/video kondisi awal, tone dingin"],
        "After": ["Foto/video kondisi akhir, tone hangat, saturasi naik"],
        "Bridge": ["Animasi panah before→after", "Tangan mengambil produk, decisive"],
        "Proof": ["Screen record review bintang 5", "Testimoni user lain, split screen",
                  "Sertifikat/uji lab close-up"],
        "Hasil": ["Perbandingan berdampingan dengan tanggal", "Close-up hasil nyata"],
        "Poin 1": ["Teks '01' besar + demo singkat", "Insert tangan melakukan langkah"],
        "Poin 2": ["Teks '02' besar + demo singkat", "B-roll pendukung"],
        "Poin 3": ["Teks '03' besar + demo paling penting", "Close-up detail krusial"],
        "CTA": ["Produk + tombol/panah CTA animasi", "Talent menunjuk ke arah tombol",
                "End card logo + penawaran"],
        "Action": ["End card CTA besar + countdown", "Talent mengajak aksi langsung"],
        "Unboxing/Intro": ["Unboxing top-down, tangan rapi", "Produk berputar 360°"],
        "Demo 1": ["Macro pemakaian, fokus tekstur", "Top-down langkah 1"],
        "Demo 2": ["Perbandingan berdampingan dua produk", "Close-up fitur pembeda"],
    }.get(beat, ["Visual pendukung sesuai narasi"])
    return base[j % len(base)]


def short(s: str, n: int) -> str:
    """Potong teks di batas kata (bukan tengah kata) untuk teks layar."""
    s = str(s).strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(",.;:-") + "…"


def _ost_for(beat: str, j: int, b: Dict[str, Any]) -> str:
    p = b["product"]
    m = {
        "Hook": ["STOP SCROLL!", "INI PENTING", "3 DETIK AJA"],
        "Attention": ["PERHATIKAN INI"],
        "Problem": [short(b.get("problem", "masalah kamu"), 26).upper()],
        "Agitate": ["MAKIN LAMA MAKIN PARAH"],
        "Interest": [short(b.get("fact", "fakta menarik"), 28).upper()],
        "Story": ["CERITA AKU", "HARI 1 → HARI 14"],
        "Momen berubah": ["AWALNYA SKEPTIS"],
        "Siapa saya": [short(b.get("persona", "siapa aku"), 24).upper()],
        "Offer": [short(p, 24).upper(), short(b.get("offer", "promo terbatas"), 26).upper()],
        "Solution": [f"{short(p, 16).upper()} = SOLUSI"],
        "Desire": ["BAYANGIN INI…"],
        "Before": ["SEBELUM"],
        "After": ["SESUDAH"],
        "Bridge": ["CARANYA ↓"],
        "Proof": [short(b.get("proof", "4,9★ · 12.000+ review"), 28).upper()],
        "Hasil": [f"HASIL {b.get('week', 2)} MINGGU"],
        "Poin 1": ["01"], "Poin 2": ["02"], "Poin 3": ["03"],
        "CTA": [short(b.get("cta", "cek link di bio"), 28).upper()],
        "Action": [short(b.get("cta", "beli sekarang"), 26).upper()],
        "Unboxing/Intro": [short(p, 24).upper()],
        "Demo 1": ["LANGKAH 1"], "Demo 2": ["BEDANYA DI SINI"],
    }
    opts = m.get(beat, [""])
    return opts[j % len(opts)]


def _sfx_for(beat: str, j: int) -> str:
    m = {"Hook": "whoosh + boom impact, musik berhenti 0,3 detik",
         "Attention": "riser pendek, musik masuk di beat",
         "Problem": "musik minor, ambient low-pass",
         "Agitate": "detak jam / heartbeat, tensi naik",
         "Interest": "pop notification, musik mulai naik",
         "Story": "musik lo-fi hangat, volume -6 dB di bawah VO",
         "Momen berubah": "reverse cymbal menuju drop",
         "Siapa saya": "musik netral, ambient ringan",
         "Offer": "drop musik utama, cash register/ding untuk harga",
         "Solution": "musik upbeat, transisi naik",
         "Desire": "musik emosional, string pad",
         "Before": "musik redup/muted",
         "After": "musik cerah, uplifting swell",
         "Bridge": "build-up + snare roll",
         "Proof": "ding lembut tiap testimoni muncul",
         "Hasil": "sparkle/chime, musik klimaks",
         "Poin 1": "click + whoosh tiap poin", "Poin 2": "click + whoosh",
         "Poin 3": "click + whoosh paling keras",
         "CTA": "musik berhenti mendadak → 1 impact + silence 0,5 dtk",
         "Action": "impact final, musik fade 1 detik",
         "Unboxing/Intro": "suara kemasan/kertas ASMR",
         "Demo 1": "ASMR tekstur, musik -12 dB", "Demo 2": "comparison swish"}
    return m.get(beat, "musik latar -8 dB")


def _broll_for(beat: str, b: Dict[str, Any]) -> List[str]:
    p = b["product"]
    common = [f"Hero shot {p} di atas meja marmer, cahaya jendela pagi",
              f"Macro tekstur {p}, depth of field dangkal",
              f"Tangan memakai {p}, gerakan lambat",
              "Screen record testimoni/review",
              "Aktivitas sehari-hari audiens target (relatable)"]
    if beat in {"Proof", "Hasil"}:
        return ["Screen record review bintang 5", "Foto before/after bertanggal",
                "Close-up sertifikat/uji lab"]
    if beat in {"Offer", "CTA", "Action"}:
        return [f"Kemasan {p} + bonus di atas meja", "Tampilan harga promo (coret)",
                "Tombol/panah CTA animasi"]
    return common[:3]


# --------------------------------------------------------------------- prompts

STYLE = ("photorealistic, commercial product photography, 85mm lens, soft key light, "
         "shallow depth of field, clean negative space, high dynamic range, "
         "no text, no watermark, no logo artifacts")


def _img_prompt(b: Dict[str, Any], beat: str, st: str, cm: str, j: int,
                plat: Dict[str, Any]) -> str:
    subj = b.get("subject") or b["product"]
    setting = b.get("setting") or "studio minimal dengan latar netral"
    talent = b.get("talent") or "talent dewasa muda, ekspresi natural"
    palette = b.get("palette") or "palet hangat dengan aksen brand"
    neg = ("text, captions, subtitles, watermark, logo, extra fingers, deformed hands, "
           "blurry, oversaturated, cartoonish skin")
    return (f"{st}, {cm}. {subj} — {_visual_for(beat, j, b, st).lower()}. "
            f"Setting: {setting}. Talent: {talent}. Color: {palette}. {STYLE}. "
            f"Aspect {plat['ratio']} ({plat['w']}x{plat['h']}). Mood: {b['tone']}. "
            f"NEGATIVE: {neg}")


def _vid_prompt(b: Dict[str, Any], beat: str, st: str, cm: str, dur: float,
                plat: Dict[str, Any]) -> str:
    return (f"Shot {dur:.1f}s, {plat['ratio']}. {st}, camera: {cm}. "
            f"Aksi: {_visual_for(beat, 0, b, st).lower()}. "
            f"Gerakan natural, motion blur halus, pencahayaan {b.get('lighting', 'softbox')}. "
            f"Transisi keluar: {TRANSITIONS[(len(beat) + int(dur * 2)) % len(TRANSITIONS)]}. "
            f"Jangan ubah identitas produk/warna brand. Tanpa teks di dalam frame "
            f"(teks ditambahkan di editing).")


# --------------------------------------------------------------------- extras

def make_caption(b: Dict[str, Any], hooks: List[Dict[str, str]]) -> Dict[str, Any]:
    p, aud = b["product"], b["audience"]
    goal = GOALS.get(b["goal"], GOALS["konversi"])
    base = b.get("keywords") or [p.split()[0].lower(), "review", "rekomendasi"]
    tags = [f"#{slug(t).replace('-', '')}" for t in base] + \
           [f"#{slug(aud.split(',')[0]).replace('-', '')}", "#fyp", "#racun" + slug(p.split()[0]).replace("-", "")]
    seen, uniq = set(), []
    for t in tags:
        if t and t not in seen and len(t) > 2:
            seen.add(t)
            uniq.append(t)
    return {
        "short": f"{hooks[0]['text']} {b.get('offer', '')} {b.get('cta', '')}".strip(),
        "long": (f"{hooks[0]['text']}\n\n"
                 f"Kalau kamu {aud}, video ini buat kamu. "
                 f"{b.get('result', 'Hasilnya')} tanpa {b.get('problem', 'ribet')}.\n\n"
                 f"✨ Kenapa {p}:\n" +
                 "\n".join(f"• {u}" for u in (b.get("usp_list") or [b.get("usp", "hasil konsisten")])[:3]) +
                 f"\n\n🎁 {b.get('offer', '')}\n👉 {b.get('cta', 'Cek link di bio')}\n\n" +
                 " ".join(uniq[:14])),
        "hashtags": uniq[:18],
        "cta_style": goal["cta_style"],
        "kpi_to_watch": goal["metric"],
    }


def make_srt(shots: List[Dict[str, Any]]) -> str:
    out = []
    for i, s in enumerate(shots, 1):
        if not s.get("vo"):
            continue
        out.append(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n"
                   + "\n".join(_chunk(s["vo"], 42)) + "\n")
    return "\n".join(out)


def _chunk(text: str, n: int) -> List[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= n:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def make_checklist(b: Dict[str, Any], shots: List[Dict[str, Any]]) -> List[str]:
    plat = PLATFORMS.get(b["platform"], PLATFORMS["tiktok"])
    return [
        f"Pastikan hook muncul ≤ {plat['hook_window']} detik pertama (uji tanpa suara).",
        f"Safe area {plat['ratio']}: {plat['safe']}.",
        "Subtitle/CC aktif — 80%+ penonton menonton tanpa suara.",
        "Rekam VO terpisah di ruangan tenang; normalisasi -16 LUFS untuk mobile.",
        f"Siapkan 3 varian hook untuk A/B test ({len(shots)} shot sudah dibuat).",
        "Export master 1080p (minimum), bitrate ≥ 8 Mbps, H.264/H.265.",
        "Simpan proyek + aset mentah untuk iterasi berikutnya.",
        "Verifikasi klaim produk (izin edar/BPOM/halal) sebelum tayang.",
        "Tambahkan UTM di link CTA agar bisa diukur di dan_analytics.py.",
        "Setelah tayang 48 jam: tarik data → jalankan sub-skill #01 untuk evaluasi.",
    ]


# --------------------------------------------------------------------- render

def to_markdown(B: Dict[str, Any]) -> str:
    b = B["brief"]
    plat = PLATFORMS.get(b["platform"], PLATFORMS["tiktok"])
    L = [f"# Storyboard Video — {b['product']}", "",
         f"**Platform** {b['platform']} ({plat['ratio']}, {plat['w']}x{plat['h']}) · "
         f"**Durasi** {b['duration']}s · **Struktur** {b['structure']} · "
         f"**Goal** {b['goal']} · **Tone** {b['tone']}  ",
         f"**Audiens:** {b['audience']}  ",
         f"**Gaya platform:** {plat['style']}  ",
         f"**Safe area:** {plat['safe']}", "",
         "## 1. Varian Hook (pilih 1, uji sisanya)", ""]
    for i, h in enumerate(B["hooks"], 1):
        L.append(f"{i}. **[{h['type']}]** “{h['text']}”  \n   Teks layar: `{h['on_screen']}`")
    L += ["", "## 2. Shot List", "",
          "| # | Beat | Waktu | Dur | Shot / Kamera | Visual | Teks Layar | VO | SFX |",
          "|---|---|---|---|---|---|---|---|---|"]
    for s in B["shots"]:
        L.append(f"| {s['no']} | {s['beat']} | {s['start']:.1f}–{s['end']:.1f}s | {s['duration']:.1f}s | "
                 f"{s['shot_type']} / {s['camera']} | {s['visual']} | `{s['on_screen_text']}` | "
                 f"{s['vo']} | {s['sfx']} |")
    L += ["", "## 3. Prompt Generatif per Shot", ""]
    for s in B["shots"]:
        L.append(f"### Shot {s['no']} — {s['beat']} ({s['duration']:.1f}s)")
        L.append(f"- **Image prompt:** `{s['image_prompt']}`")
        L.append(f"- **Video prompt:** `{s['video_prompt']}`")
        L.append(f"- **B-roll:** " + "; ".join(s["b_roll"]))
        L.append("")
    L += ["## 4. Caption & Hashtag", "",
          f"**Versi pendek:** {B['caption']['short']}", "",
          "**Versi panjang:**", "", "```", B["caption"]["long"], "```", "",
          f"**Gaya CTA:** {B['caption']['cta_style']} · **KPI dipantau:** {B['caption']['kpi_to_watch']}",
          "", "## 5. Checklist Produksi", ""]
    L += [f"- [ ] {c}" for c in B["checklist"]]
    L += ["", "## 6. Catatan Sutradara", "",
          f"- Total {len(B['shots'])} shot untuk {b['duration']} detik → rata-rata "
          f"{b['duration'] / max(1, len(B['shots'])):.1f} detik/shot.",
          "- Tempo cepat = retensi tinggi, tapi beri 1 shot 'napas' (≥2,5 dtk) tiap 3-4 shot.",
          f"- Kecepatan bicara VO diasumsikan 145 kata/menit; kolom `vo_words` adalah target kata.",
          "- Uji pertama: tonton tanpa suara. Jika pesan tetap jelas, videonya kuat.",
          "", "---",
          f"_Dibuat oleh DAN · Image & Video Creator · {B['meta']['generated_at']}_"]
    return "\n".join(L)


def build(brief: Dict[str, Any]) -> Dict[str, Any]:
    plat = PLATFORMS.get(brief.get("platform", "tiktok"), PLATFORMS["tiktok"])
    b = {
        "product": brief.get("product", "Produk"),
        "audience": brief.get("audience", "audiens umum"),
        "platform": brief.get("platform", "tiktok"),
        "duration": min(float(brief.get("duration") or plat["duration"] or 30), plat["max"] or 9999),
        "structure": brief.get("structure", "hook_story_offer"),
        "goal": brief.get("goal", "konversi"),
        "tone": brief.get("tone", "friendly"),
        "offer": brief.get("offer", ""),
        "cta": brief.get("cta", "Cek link di bio"),
        "problem": brief.get("problem", ""),
        "result": brief.get("result", ""),
        "usp": brief.get("usp", ""),
        "usp_list": brief.get("usp_list"),
        "proof": brief.get("proof", ""),
        "fact": brief.get("fact", ""),
        "pain": brief.get("pain", ""),
        "persona": brief.get("persona", ""),
        "timeframe": brief.get("timeframe", "14 hari"),
        "week": brief.get("week", 2),
        "number": brief.get("number", 3),
        "setting": brief.get("setting", ""),
        "talent": brief.get("talent", ""),
        "palette": brief.get("palette", ""),
        "lighting": brief.get("lighting", "softbox"),
        "subject": brief.get("subject", ""),
        "keywords": brief.get("keywords"),
    }
    if b["structure"] not in STRUCTURES:
        b["structure"] = "hook_story_offer"
    hooks = make_hooks(b)
    shots = make_shots(b)
    out = {
        "meta": {"generated_at": datetime.now().isoformat(timespec="seconds"),
                 "engine": "DAN storyboard v1", "shots": len(shots),
                 "total_duration": round(sum(s["duration"] for s in shots), 2)},
        "brief": b, "hooks": hooks, "shots": shots,
        "caption": make_caption(b, hooks),
        "checklist": make_checklist(b, shots),
    }
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · Storyboard & Video Script")
    ap.add_argument("--brief", help="JSON berisi semua field brief")
    ap.add_argument("--product"); ap.add_argument("--audience"); ap.add_argument("--platform")
    ap.add_argument("--duration", type=float); ap.add_argument("--structure")
    ap.add_argument("--goal"); ap.add_argument("--tone"); ap.add_argument("--offer")
    ap.add_argument("--cta"); ap.add_argument("--problem"); ap.add_argument("--result")
    ap.add_argument("--usp"); ap.add_argument("--proof"); ap.add_argument("--setting")
    ap.add_argument("--out", default=""); ap.add_argument("--srt", default="")
    a = ap.parse_args(argv)

    brief: Dict[str, Any] = {}
    if a.brief:
        with open(a.brief, encoding="utf-8") as f:
            brief = json.load(f)
    for k in ("product", "audience", "platform", "duration", "structure", "goal", "tone",
              "offer", "cta", "problem", "result", "usp", "proof", "setting"):
        v = getattr(a, k, None)
        if v is not None:
            brief[k] = v
    if not brief.get("product"):
        ap.error("butuh --product atau --brief")

    B = build(brief)
    stem = slug(brief["product"]) or "storyboard"
    out = a.out or os.path.join(dl, f"storyboard_{stem}.md")
    js = os.path.splitext(out)[0] + ".json"
    srt = a.srt or os.path.splitext(out)[0] + ".srt"
    for p in (out, js, srt):
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(to_markdown(B))
    with open(js, "w", encoding="utf-8") as f:
        json.dump(B, f, ensure_ascii=False, indent=2)
    with open(srt, "w", encoding="utf-8") as f:
        f.write(make_srt(B["shots"]))
    print(f"[DAN] {B['meta']['shots']} shot · {B['meta']['total_duration']}s · "
          f"{brief.get('platform')} · {brief.get('structure')}")
    print(f"[DAN] -> {out}\n[DAN] -> {js}\n[DAN] -> {srt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
