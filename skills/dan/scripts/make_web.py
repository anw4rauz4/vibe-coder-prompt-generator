#!/usr/bin/env python3
"""make_web.py — Website hub DAN: agent + 21 sub-skill + tools interaktif + engine.

Menghasilkan SATU file HTML self-contained (CSS/JS inline, tanpa CDN/network) di
deliverables/dan-web/index.html. Data (skills, engines, adapters, changelog, QA)
dibaca langsung dari paket sehingga situs selalu sinkron dengan isi repo.

Pakai:  python3 make_web.py [--outdir DIR]
Lokal:  python3 serve.py 8686   →  http://localhost:8686/deliverables/dan-web/
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAKET = os.path.dirname(HERE)                 # .../skills/dan
ROOT = os.path.dirname(os.path.dirname(PAKET))  # .../home/user
DELIV = os.path.join(ROOT, "deliverables")


# ---------------------------------------------------------------- kumpul data
def _front(t: str, key: str) -> str:
    m = re.search(r"^%s:\s*>-\n((?:\s+.*\n)+)" % key, t, re.M)
    if m:
        return " ".join(x.strip() for x in m.group(1).splitlines())
    m = re.search(r"^%s:\s*(.+)$" % key, t, re.M)
    return m.group(1).strip() if m else ""


def _potong(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= n:
        return s
    cut = s[:n].rsplit(" ", 1)[0]
    return cut + "…"


def kumpul_skills() -> list:
    out = []
    d = os.path.join(PAKET, "skills")
    for nama in sorted(os.listdir(d)):
        p = os.path.join(d, nama, "SKILL.md")
        if not os.path.isdir(os.path.join(d, nama)) or not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        no = nama.split("-", 1)[0]
        judul = nama.split("-", 1)[1].replace("-", " ").title() if "-" in nama else nama
        out.append({
            "no": no, "dir": nama, "judul": judul,
            "desc": _potong(_front(t, "description"), 170),
            "grup": "Inti Marketing & Desain" if int(no) <= 9 else "AI Skills 2027",
            "path": "skills/%s/SKILL.md" % nama,
        })
    return out


def kumpul_engines() -> list:
    out = []
    for f in sorted(os.listdir(HERE)):
        if not f.endswith(".py") or f.startswith("_") or f in ("make_web.py", "serve.py"):
            continue
        try:
            doc = ast.get_docstring(ast.parse(open(os.path.join(HERE, f), encoding="utf-8").read()))
        except SyntaxError:
            doc = ""
        baris = (doc or "").strip().splitlines()
        desc = _potong(baris[0] if baris else "", 110)
        desc = re.sub(r"^%s\s*[—-]\s*" % re.escape(f), "", desc)
        out.append({"file": f, "desc": desc or "(tanpa deskripsi)"})
    return out


def kumpul_adapters() -> list:
    d = os.path.join(ROOT, "adapters")
    if not os.path.isdir(d):
        return []
    out = [x for x in sorted(os.listdir(d)) if os.path.isdir(os.path.join(d, x))]
    if os.path.exists(os.path.join(d, "SYSTEM_PROMPT.txt")):
        out.append("system-prompt")
    return out


def kumpul_changelog(n: int = 4) -> list:
    p = os.path.join(PAKET, "CHANGELOG.md")
    if not os.path.exists(p):
        return []
    t = open(p, encoding="utf-8").read()
    blok = re.split(r"^## ", t, flags=re.M)[1:]
    out = []
    for b in blok[-n:]:
        head = b.splitlines()[0]
        m = re.match(r"([\d.]+)\s*[—-]\s*(.+)", head)
        isi = [re.sub(r"^-\s*", "", x).strip() for x in b.splitlines()[1:] if x.strip().startswith("-")]
        out.append({"versi": m.group(1) if m else head, "tgl": m.group(2).strip() if m else "",
                    "isi": isi[:8]})
    return list(reversed(out))


def kumpul_qa(n: int = 5) -> list:
    p = os.path.join(PAKET, "qa_history.jsonl")
    if not os.path.exists(p):
        return []
    rows = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]
    return rows[-n:][::-1]


def kumpul_unduhan() -> list:
    out = []
    for pola, label in ((r"dan-skill-([\d.]+)\.zip", "Paket skill (import ke runtime AI)"),
                        (r"dan-offline-([\d.]+)\.zip", "Bundle offline total"),):
        cands = [f for f in os.listdir(DELIV) if re.fullmatch(pola, f)] if os.path.isdir(DELIV) else []
        if cands:
            f = sorted(cands, key=lambda x: [int(i) for i in re.search(r"[\d.]+", x).group(0).split(".") if i])[-1]
            out.append({"file": f, "label": label,
                        "kb": os.path.getsize(os.path.join(DELIV, f)) // 1024})
    pyz = os.path.join(DELIV, "dan.pyz")
    if os.path.exists(pyz):
        out.append({"file": "dan.pyz", "label": "Semua engine dalam 1 file executable",
                    "kb": os.path.getsize(pyz) // 1024})
    return out


def kumpul_data() -> dict:
    skills = kumpul_skills()
    engines = kumpul_engines()
    qa = kumpul_qa()
    ch = kumpul_changelog()
    versi = ch[0]["versi"] if ch else "0"
    return {
        "versi": versi,
        "dibuat": _dt.date.today().isoformat(),
        "skills": skills,
        "engines": engines,
        "adapters": kumpul_adapters(),
        "changelog": ch,
        "qa": qa,
        "unduhan": kumpul_unduhan(),
        "stat": {
            "skills": len(skills), "engines": len(engines),
            "adapters": len(kumpul_adapters()),
            "tests": qa[0]["tests_pass"] if qa else 0,
            "fail": qa[0]["tests_fail"] if qa else 0,
        },
    }


# ------------------------------------------------------------------- template
CSS = """
:root{--bg:#0b0e17;--bg2:#111627;--card:#151b2e;--line:#232b45;--tx:#e8ecf8;--mut:#8b94b5;
--ac:#6d5df6;--ac2:#00d4ff;--ok:#2ecc8f;--warn:#f5b942;--bad:#ff5d6c;--mono:ui-monospace,'Cascadia Code',Consolas,monospace}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--tx);font:15px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}
a{color:var(--ac2);text-decoration:none}
header{position:sticky;top:0;z-index:9;background:rgba(11,14,23,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.hd{max-width:1100px;margin:auto;display:flex;align-items:center;gap:14px;padding:10px 18px;flex-wrap:wrap}
.logo{display:flex;align-items:center;gap:9px;font-weight:800;font-size:17px;letter-spacing:.4px}
.nav{display:flex;gap:2px;flex-wrap:wrap;margin-left:auto}
.nav a{color:var(--mut);padding:7px 12px;border-radius:8px;font-weight:600;font-size:13.5px}
.nav a:hover{color:var(--tx);background:var(--bg2)}
.nav a.on{color:#fff;background:linear-gradient(120deg,var(--ac),#4a7cf7)}
main{max-width:1100px;margin:auto;padding:26px 18px 70px}
.hero{padding:46px 0 26px;text-align:center}
.hero h1{font-size:clamp(28px,5vw,44px);font-weight:900;line-height:1.12;
background:linear-gradient(120deg,#fff 30%,var(--ac2) 70%,var(--ac));-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{color:var(--mut);max-width:680px;margin:14px auto 0;font-size:16px}
.chips{display:flex;gap:9px;justify-content:center;flex-wrap:wrap;margin-top:22px}
.chip{background:var(--card);border:1px solid var(--line);border-radius:99px;padding:7px 15px;font-size:13px;color:var(--mut)}
.chip b{color:var(--tx);font-size:14px}
h2.sec{font-size:22px;margin:34px 0 6px;font-weight:800}
p.sub{color:var(--mut);margin-bottom:16px}
.grid{display:grid;gap:12px}
.g2{grid-template-columns:repeat(auto-fill,minmax(320px,1fr))}
.g3{grid-template-columns:repeat(auto-fill,minmax(250px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px}
.card h3{font-size:15.5px;margin-bottom:6px;display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.card p{color:var(--mut);font-size:13.5px}
.badge{font-size:10.5px;font-weight:800;border-radius:6px;padding:2px 7px;letter-spacing:.5px}
.bno{background:linear-gradient(120deg,var(--ac),#4a7cf7);color:#fff}
.bgrup{background:var(--bg2);color:var(--ac2);border:1px solid var(--line)}
.path{font-family:var(--mono);font-size:11px;color:var(--mut);margin-top:9px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
button{cursor:pointer;border:0;border-radius:8px;font:600 13px system-ui;padding:7px 13px}
.btn{background:var(--bg2);color:var(--tx);border:1px solid var(--line)}
.btn:hover{border-color:var(--ac)}
.bpri{background:linear-gradient(120deg,var(--ac),#4a7cf7);color:#fff}
.copy{background:var(--bg2);color:var(--ac2);border:1px solid var(--line);padding:3px 9px;font-size:11.5px}
pre.cmd{background:#0d1120;border:1px solid var(--line);border-radius:10px;padding:13px 15px;overflow:auto;
font:12.5px/1.7 var(--mono);color:#c9d4f5;position:relative}
pre.cmd .c{color:#5c678d}
input,textarea,select{background:#0d1120;border:1px solid var(--line);color:var(--tx);border-radius:8px;
padding:8px 11px;font:13.5px system-ui;width:100%}
input:focus,textarea:focus{outline:1px solid var(--ac)}
label{font-size:12px;color:var(--mut);font-weight:600;display:block;margin:9px 0 4px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.kv{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px dashed var(--line);font-size:13.5px}
.kv:last-child{border:0}
.kv b{font-family:var(--mono);font-size:14px}
.rag{font-size:11px;font-weight:800;border-radius:6px;padding:2px 8px;margin-left:8px}
.rag.g{background:rgba(46,204,143,.15);color:var(--ok)}
.rag.y{background:rgba(245,185,66,.15);color:var(--warn)}
.rag.r{background:rgba(255,93,108,.15);color:var(--bad)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:var(--mut);text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.6px;padding:8px 10px;border-bottom:1px solid var(--line)}
td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
td .f{font-family:var(--mono);color:var(--ac2);font-size:12.5px}
.tabs-ad{display:flex;gap:8px;flex-wrap:wrap}
.ad{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 14px;font-size:13px;font-weight:600}
.ok{color:var(--ok)}.bad{color:var(--bad)}.mut{color:var(--mut)}
.warnbox{background:rgba(245,185,66,.08);border:1px solid rgba(245,185,66,.35);border-radius:10px;padding:11px 14px;font-size:13px;color:var(--warn);margin-top:12px}
.rules{counter-reset:r;display:grid;gap:8px}
.rules div{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px 10px 44px;position:relative;font-size:13.5px;color:var(--mut)}
.rules div:before{counter-increment:r;content:counter(r);position:absolute;left:13px;top:10px;width:21px;height:21px;
border-radius:7px;background:linear-gradient(120deg,var(--ac),#4a7cf7);color:#fff;font-weight:800;font-size:12px;display:flex;align-items:center;justify-content:center}
.rel{border-left:3px solid var(--ac);padding-left:16px;margin-bottom:20px}
.rel h3{font-size:16px}.rel .tgl{color:var(--mut);font-size:12px;margin-bottom:6px}
.rel li{font-size:13.5px;color:var(--mut);margin-left:18px}
.toolout{background:#0d1120;border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:12px;min-height:44px}
.search{max-width:340px;margin-bottom:14px}
footer{border-top:1px solid var(--line);padding:20px;text-align:center;color:var(--mut);font-size:12.5px}
@media(max-width:640px){.row{grid-template-columns:1fr}}
"""

HTML = """<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DAN — Hub Agent &amp; Skills AI</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%236d5df6'/%3E%3Ctext x='32' y='44' font-size='30' font-weight='900' text-anchor='middle' fill='white' font-family='Arial'%3ED%3C/text%3E%3C/svg%3E">
<style>__CSS__</style>
</head>
<body>
<header><div class="hd">
<div class="logo"><svg width="30" height="30" viewBox="0 0 64 64"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6d5df6"/><stop offset="1" stop-color="#00d4ff"/></linearGradient></defs><rect width="64" height="64" rx="14" fill="url(#g)"/><text x="32" y="44" font-size="30" font-weight="900" text-anchor="middle" fill="#fff" font-family="Arial">D</text></svg>
DAN <span class="badge bgrup" id="versi-chip"></span></div>
<nav class="nav">
<a href="#/beranda">Beranda</a><a href="#/skills">Skills</a><a href="#/tools">Tools</a>
<a href="#/mesin">Mesin</a><a href="#/pasang">Pasang</a><a href="#/unduh">Unduh</a><a href="#/rilis">Rilis</a>
</nav></div></header>
<main>

<section id="tab-beranda">
<div class="hero">
<h1>Satu Agent. 21 Keahlian.<br>Zero Dependency.</h1>
<p>DAN adalah paket Agent Skill plug-and-play untuk marketing end-to-end, PMO, arsitektur
software &amp; bangunan, dan 12 skill AI esensial — berjalan di Claude, Cursor, ChatGPT, Gemini,
Copilot, dan runtime lain lewat MCP. Semua engine Python stdlib; semua artefak self-contained.</p>
<div class="chips" id="stat-chips"></div>
<div style="margin-top:24px;display:flex;gap:10px;justify-content:center;flex-wrap:wrap">
<a href="#/skills"><button class="bpri">Jelajahi 21 Skills →</button></a>
<a href="#/tools"><button class="btn">Coba Tools Interaktif</button></a>
</div></div>
<h2 class="sec">Mulai cepat</h2>
<p class="sub">Lima perintah untuk memakai DAN dari terminal mana pun.</p>
<pre class="cmd" id="quickstart"></pre>
<h2 class="sec">Enam aturan inti</h2>
<div class="rules">
<div>Data dulu; angka tertelusur atau ditandai <code>asumsi:</code>.</div>
<div>Tiap temuan = 1 aksi terukur + pemilik + tenggat.</div>
<div>Deliverable self-contained (SVG/CSS inline, tanpa CDN).</div>
<div>QA sebelum serahkan: <code>_test_all.py</code> 0 gagal · <code>_check_refs.py</code> 0 hilang.</div>
<div>Disiplin konteks: baca per-section, pakai ulang hasil hitungan.</div>
<div>Tutup dengan 2–3 langkah berikutnya.</div>
</div>
</section>

<section id="tab-skills" style="display:none">
<h2 class="sec">21 Sub-Skill</h2>
<p class="sub">01–09 inti marketing/desain/PMO/arsitektur · 10–21 “12 AI Skills You Need to Master Before 2027”. Klik salin untuk menyalin path SKILL.md.</p>
<input class="search" id="sk-q" placeholder="Cari skill… (mis. rag, video, pmo)">
<div class="grid g2" id="sk-list"></div>
</section>

<section id="tab-tools" style="display:none">
<h2 class="sec">Tools Interaktif</h2>
<p class="sub">Versi mini dari engine DAN yang jalan langsung di browser — tanpa server, tanpa data dikirim ke mana pun. Format angka Indonesia (<code>1.234.567</code>).</p>
<div class="grid g2">

<div class="card"><h3>💰 Kalkulator KPI Marketing</h3>
<p class="mut" style="font-size:12.5px">CTR · CPC · CPM · CVR · CPA · ROAS · AOV</p>
<div class="row">
<div><label>Impresi</label><input id="k-imp" value="250000"></div>
<div><label>Klik</label><input id="k-klik" value="4500"></div>
<div><label>Biaya iklan (Rp)</label><input id="k-biaya" value="7500000"></div>
<div><label>Konversi</label><input id="k-konv" value="180"></div>
</div>
<label>Omset dari iklan (Rp)</label><input id="k-omset" value="26000000">
<div class="toolout" id="k-out"></div></div>

<div class="card"><h3>📊 Format Rupiah &amp; Singkatan</h3>
<p class="mut" style="font-size:12.5px">Angka mentah → format Indonesia + singkatan rb/jt/M/T</p>
<label>Angka (boleh 1500000 atau 1.500.000)</label><input id="f-in" value="106760000">
<div class="toolout" id="f-out"></div></div>

<div class="card"><h3>⚖️ Break-Even Point</h3>
<div class="row">
<div><label>Biaya tetap / bulan (Rp)</label><input id="b-fc" value="45000000"></div>
<div><label>Harga jual / unit (Rp)</label><input id="b-p" value="25000"></div>
</div>
<label>Biaya variabel / unit (Rp)</label><input id="b-vc" value="14000">
<div class="toolout" id="b-out"></div></div>

<div class="card"><h3>🎯 Alokator Budget per ROAS</h3>
<p class="mut" style="font-size:12.5px">Budget dibagi proporsional ROAS tiap channel + proyeksi omset.</p>
<label>Total budget (Rp)</label><input id="a-total" value="50000000">
<div id="a-rows"></div>
<div style="margin-top:9px"><button class="btn" id="a-add">+ Tambah channel</button></div>
<div class="toolout" id="a-out"></div></div>

<div class="card"><h3>✍️ Pemeriksa Narasi (mini narrative_check)</h3>
<p class="mut" style="font-size:12.5px">Menandai superlatif tanpa pembanding &amp; proyeksi tanpa ±/estimasi.</p>
<label>Teks laporan</label>
<textarea id="n-in" rows="5">Penjualan kami terbaik di industri. Proyeksi Q4 mencapai Rp2,1 M. Tim Kalbe turun 19,5% YoY (asumsi: data By Team).</textarea>
<div class="toolout" id="n-out"></div></div>

<div class="card"><h3>🧪 Prompt Lint (mini prompt_lab)</h3>
<p class="mut" style="font-size:12.5px">Skor kelengkapan 7 elemen prompt.</p>
<label>Prompt kamu</label>
<textarea id="p-in" rows="5">Anda adalah analis marketing senior. Konteks: distributor FMCG, audiens manajemen. Buat ringkasan pencapaian YTD. Jangan pakai jargon. Format: tabel + 3 bullet. Bahasa Indonesia.</textarea>
<div class="toolout" id="p-out"></div></div>

<div class="card"><h3>📦 SCD Checker (Stock Cover Days)</h3>
<p class="mut" style="font-size:12.5px">Hari tahan stok · status RAG · saran order. Satuan bebas (pcs atau Rp) asal konsisten.</p>
<div class="row">
<div><label>Stok saat ini</label><input id="s-stok" value="9200"></div>
<div><label>Rata-rata penjualan / hari</label><input id="s-jual" value="1000"></div>
</div>
<div class="row">
<div><label>Target SCD (hari)</label><input id="s-target" value="30"></div>
<div><label>Safety stock (hari)</label><input id="s-ss" value="7"></div>
</div>
<div class="toolout" id="s-out"></div></div>

<div class="card"><h3>📈 Proyeksi Musiman (sisa tahun)</h3>
<p class="mut" style="font-size:12.5px">Sisa bulan = periode sama tahun lalu × (1+growth YoY), selalu dengan rentang ± (aturan kejujuran narasi).</p>
<div class="row">
<div><label>YTD tahun ini (Rp)</label><input id="m-ytd" value="106760000"></div>
<div><label>YTD tahun lalu (Rp)</label><input id="m-ly" value="112380000"></div>
</div>
<div class="row">
<div><label>Sisa bulan tahun lalu (Rp)</label><input id="m-rest" value="61000000"></div>
<div><label>Ketidakpastian ± (%)</label><input id="m-u" value="8"></div>
</div>
<label>Target setahun penuh (Rp)</label><input id="m-target" value="185000000">
<div class="toolout" id="m-out"></div></div>

</div>
</section>

<section id="tab-mesin" style="display:none">
<h2 class="sec">Mesin / Engine CLI</h2>
<p class="sub">Semua Python stdlib di <code>skills/dan/scripts/</code>. Gerbang tunggal: <code>dan.py</code>.</p>
<input class="search" id="en-q" placeholder="Cari engine… (mis. rag, weekly, xlsx)">
<div class="card" style="padding:6px 10px"><table><thead><tr><th>File</th><th>Fungsi</th><th></th></tr></thead><tbody id="en-list"></tbody></table></div>
</section>

<section id="tab-pasang" style="display:none">
<h2 class="sec">Pemasangan Lintas AI</h2>
<p class="sub">Plug-and-play ke 12+ runtime lewat <code>make_adapters.py</code>, atau sebagai server MCP (10 tool).</p>
<div class="tabs-ad" id="ad-list"></div>
<h2 class="sec">Perintah</h2>
<pre class="cmd" id="pasang-cmd"></pre>
<div class="warnbox">Situs ini satu file HTML statis — bisa dibuka langsung, di-serve dengan <code>serve.py</code>, atau dipublikasi <b>gratis</b> ke GitHub Pages: <code>dan.py deploy</code> (panduan: <code>DEPLOY-GITHUB.md</code>).</div>
</section>

<section id="tab-unduh" style="display:none">
<h2 class="sec">Unduh</h2>
<p class="sub">Artefak rilis di <code>deliverables/</code>. Tautan aktif saat situs di-serve lewat <code>serve.py</code> (lihat tab Pasang).</p>
<div class="grid g3" id="dl-list"></div>
</section>

<section id="tab-rilis" style="display:none">
<h2 class="sec">Rilis &amp; Riwayat QA</h2>
<p class="sub">Rilis dijaga 8 gerbang (test · cases · refs · adapters · sec · package · digest · health).</p>
<div class="card" style="padding:6px 10px;margin-bottom:22px"><table><thead><tr><th>Waktu</th><th>Versi</th><th>Test lulus</th><th>Gagal</th><th>Refs hilang</th><th>File</th></tr></thead><tbody id="qa-list"></tbody></table></div>
<div id="rel-list"></div>
</section>

</main>
<footer>DAN v__VERSI__ · dibangun __TGL__ oleh <b>make_web.py</b> · zero-dependency, satu file, tanpa tracker</footer>
<script>
const D = __DATA__;
__JS__
</script>
</body>
</html>
"""

JS = r"""
'use strict';
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const TABS=['beranda','skills','tools','mesin','pasang','unduh','rilis'];
function show(t){ if(!TABS.includes(t))t='beranda';
 TABS.forEach(id=>{$('tab-'+id).style.display=id===t?'':'none';});
 document.querySelectorAll('.nav a').forEach(a=>a.classList.toggle('on',a.getAttribute('href')==='#/'+t));
 window.scrollTo(0,0);}
window.addEventListener('hashchange',()=>show((location.hash||'#/beranda').slice(2)));

function num(v){v=String(v==null?'':v).trim();if(!v)return 0;
 if(v.indexOf(',')>=0&&v.indexOf('.')>=0)v=v.replace(/\./g,'').replace(',','.');
 else if(v.indexOf(',')>=0)v=v.replace(',','.');
 const n=parseFloat(v);return isFinite(n)?n:0;}
function fmt(n,d){d=d||0;return n.toLocaleString('id-ID',{minimumFractionDigits:d,maximumFractionDigits:d});}
function rp(n){return 'Rp'+fmt(Math.round(n));}
function short(n){const a=Math.abs(n);
 if(a>=1e12)return fmt(n/1e12,2)+' T'; if(a>=1e9)return fmt(n/1e9,2)+' M';
 if(a>=1e6)return fmt(n/1e6,2)+' jt'; if(a>=1e3)return fmt(n/1e3,1)+' rb'; return fmt(n);}
function rag(v,g,y,inv){const good=inv?v<=g:v>=g,mid=inv?v<=y:v>=y;
 return '<span class="rag '+(good?'g':mid?'y':'r')+'">'+(good?'BAGUS':mid?'WASPADA':'KRITIS')+'</span>';}
function kv(k,v,extra){return '<div class="kv"><span>'+k+'</span><b>'+v+(extra||'')+'</b></div>';}

/* ---------- salin ---------- */
document.addEventListener('click',e=>{const b=e.target.closest('.copy');if(!b)return;
 const t=b.dataset.copy||'';
 (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>{
  b.textContent='✓ tersalin';setTimeout(()=>b.textContent='salin',1200);
 }).catch(()=>{const ta=document.createElement('textarea');ta.value=t;document.body.appendChild(ta);
  ta.select();try{document.execCommand('copy');b.textContent='✓ tersalin';setTimeout(()=>b.textContent='salin',1200);}catch(_){}
  document.body.removeChild(ta);});});

/* ---------- beranda ---------- */
$('versi-chip').textContent='v'+D.versi;
const S=D.stat;
$('stat-chips').innerHTML=[
 ['Sub-skill',S.skills],['Engine CLI',S.engines],['Adapter runtime',S.adapters],
 ['Test QA',S.tests+' lulus'],['Gagal',S.fail],['Dependensi','0']
].map(c=>'<span class="chip"><b>'+c[1]+'</b> '+c[0]+'</span>').join('');
$('quickstart').innerHTML=
 '<span class="c"># 1 · pasang ke runtime (Claude Code contoh)</span>\ncp -r skills/dan ~/.claude/skills/\n\n'+
 '<span class="c"># 2 · hasilkan adapter untuk 12 runtime AI</span>\npython3 skills/dan/scripts/make_adapters.py --all\n\n'+
 '<span class="c"># 3 · cek kesehatan paket</span>\npython3 skills/dan/scripts/dan.py doctor --full\n\n'+
 '<span class="c"># 4 · analisa workbook business-plan klien</span>\npython3 skills/dan/scripts/plan_analyst.py --file data.xlsx --outdir deliverables/klien\n\n'+
 '<span class="c"># 5 · jalankan situs ini</span>\npython3 skills/dan/scripts/serve.py 8686';

/* ---------- skills ---------- */
function skillsInit(){
 const wrap=document.createElement('div');wrap.id='sk-wrap';
 $('sk-list').replaceWith(wrap);
 const rerender=()=>{const q=($('sk-q').value||'').toLowerCase();
  const card=s=>'<div class="card"><h3><span class="badge bno">'+s.no+'</span>'+esc(s.judul)+'</h3>'+
   '<p>'+esc(s.desc)+'</p><div class="path"><code>'+esc(s.path)+'</code>'+
   '<button class="copy" data-copy="'+esc(s.path)+'">salin</button></div></div>';
  const filt=s=>!q||s.judul.toLowerCase().includes(q)||s.desc.toLowerCase().includes(q)||s.dir.includes(q);
  let h='';
  [['Inti Marketing & Desain',s=>s.grup.startsWith('Inti')],['AI Skills 2027',s=>!s.grup.startsWith('Inti')]].forEach(g=>{
   const xs=D.skills.filter(g[1]).filter(filt); if(!xs.length)return;
   h+='<h2 class="sec" style="font-size:16px;margin:18px 0 10px">'+g[0]+' <span class="mut">('+xs.length+')</span></h2>'+
      '<div class="grid g2">'+xs.map(card).join('')+'</div>';});
  wrap.innerHTML=h||'<p class="mut">Tidak ada skill yang cocok.</p>';};
 $('sk-q').addEventListener('input',rerender); rerender();}

/* ---------- engines ---------- */
function enginesInit(){
 const tb=$('en-list');
 const rerender=()=>{const q=($('en-q').value||'').toLowerCase();
  tb.innerHTML=D.engines.filter(e=>!q||e.file.toLowerCase().includes(q)||e.desc.toLowerCase().includes(q))
   .map(e=>'<tr><td class="f">'+esc(e.file)+'</td><td class="mut">'+esc(e.desc)+'</td>'+
    '<td><button class="copy" data-copy="python3 skills/dan/scripts/'+esc(e.file)+' --help">salin cmd</button></td></tr>').join('');};
 $('en-q').addEventListener('input',rerender); rerender();}

/* ---------- tools: KPI ---------- */
function kpi(){const imp=num($('k-imp').value),klik=num($('k-klik').value),by=num($('k-biaya').value),
 konv=num($('k-konv').value),om=num($('k-omset').value);
 if(imp<=0||klik<=0){$('k-out').innerHTML='<span class="mut">Isi impresi &amp; klik.</span>';return;}
 const roas=by>0?om/by:0;
 $('k-out').innerHTML=
  kv('CTR',fmt(klik/imp*100,2)+' %')+
  kv('CPC',rp(by/klik))+
  kv('CPM',rp(by/imp*1000))+
  kv('CVR',konv>0?fmt(konv/klik*100,2)+' %':'—')+
  kv('CPA',konv>0?rp(by/konv):'—')+
  kv('AOV',konv>0?rp(om/konv):'—')+
  kv('ROAS',fmt(roas,2)+'×',rag(roas,3,1.5));}
['k-imp','k-klik','k-biaya','k-konv','k-omset'].forEach(i=>$(i).addEventListener('input',kpi));

/* ---------- tools: format ---------- */
function fmtTool(){const n=num($('f-in').value);
 $('f-out').innerHTML=kv('Format ID',fmt(n))+kv('Rupiah',rp(n))+kv('Singkatan',short(n))+
  kv('Untuk JSON',String(Math.round(n*100)/100));}
$('f-in').addEventListener('input',fmtTool);

/* ---------- tools: BEP ---------- */
function bep2(){const fc=num($('b-fc').value),p=num($('b-p').value),vc=num($('b-vc').value);
 if(p<=vc){$('b-out').innerHTML='<span class="bad">Harga jual harus &gt; biaya variabel (margin negatif).</span>';return;}
 const u=fc/(p-vc);
 $('b-out').innerHTML=kv('Margin / unit',rp(p-vc)+' · '+fmt((p-vc)/p*100,1)+' %')+
  kv('BEP unit',fmt(Math.ceil(u))+' unit/bln')+
  kv('BEP omset',rp(Math.ceil(u)*p)+'/bln')+
  kv('BEP harian','± '+fmt(Math.ceil(u/26))+' unit (26 hari kerja)');}
['b-fc','b-p','b-vc'].forEach(i=>$(i).addEventListener('input',bep2));

/* ---------- tools: alokator ---------- */
let CH=[{n:'Meta Ads',r:3.2},{n:'Google Ads',r:2.4},{n:'TikTok Ads',r:2.8},{n:'KOL',r:1.9}];
function drawRows(){$('a-rows').innerHTML='<table><thead><tr><th>Channel</th><th style="width:90px">ROAS</th><th style="width:36px"></th></tr></thead><tbody>'+
 CH.map((c,i)=>'<tr><td><input data-i="'+i+'" data-k="n" value="'+esc(c.n)+'"></td>'+
 '<td><input data-i="'+i+'" data-k="r" value="'+c.r+'"></td>'+
 '<td><button class="btn" style="padding:3px 9px" data-del="'+i+'">✕</button></td></tr>').join('')+'</tbody></table>';}
function alok(){const t=num($('a-total').value),tot=CH.reduce((s,c)=>s+Math.max(0,num(c.r)),0);
 if(tot<=0){$('a-out').innerHTML='<span class="mut">Isi minimal satu ROAS &gt; 0.</span>';return;}
 let proy=0;
 const rows=CH.map(c=>{const r=Math.max(0,num(c.r)),al=t*r/tot;proy+=al*r;
  return '<div class="kv"><span>'+esc(c.n)+' · '+fmt(r,1)+'×</span><b>'+rp(al)+'</b></div>';}).join('');
 $('a-out').innerHTML=rows+kv('Proyeksi omset','± '+rp(proy)+' <span class="mut">(estimasi linier)</span>');}
$('a-rows').addEventListener('input',e=>{const i=+e.target.dataset.i,k=e.target.dataset.k;
 if(k){CH[i][k]=k==='n'?e.target.value:num(e.target.value);alok();}});
$('a-rows').addEventListener('click',e=>{const d=e.target.dataset.del;
 if(d!=null){CH.splice(+d,1);drawRows();alok();}});
$('a-add').addEventListener('click',()=>{CH.push({n:'Channel baru',r:2});drawRows();alok();});
$('a-total').addEventListener('input',alok);

/* ---------- tools: narasi ---------- */
function narasi(){const t=$('n-in').value.split('\n');let sk=100,h='';
 t.forEach((ln,i)=>{if(!ln.trim())return;const no=i+1;
  if(/\b(terbaik|terbesar|tercepat|termurah|tertinggi|paling\s+\w+|nomor\s*satu|no\.?\s*1)\b/i.test(ln)
     && !/\b(vs\.?|versus|dibanding|lebih\s+\w+\s+dari)/i.test(ln)){
    sk-=15;h+='<div class="kv"><span class="bad">L'+no+' · superlatif tanpa pembanding</span><b style="font-size:11.5px;font-weight:400">'+esc(ln.slice(0,70))+'</b></div>';}
  if(/(proyeksi|forecast|diperkirakan|akan\s+mencapai)/i.test(ln)&&/\d/.test(ln)
     && !/(±|rentang|estimasi|perkiraan|kisaran)/i.test(ln)){
    sk-=12;h+='<div class="kv"><span class="bad">L'+no+' · proyeksi tanpa ±/rentang</span><b style="font-size:11.5px;font-weight:400">'+esc(ln.slice(0,70))+'</b></div>';}
  if(/\d+[.,]?\d*\s*(%|jt|M\b)/.test(ln)&&!/(asumsi|sumber|data|yoy|ytd|vs\.?|dibanding)/i.test(ln)){
    sk-=6;h+='<div class="kv"><span style="color:var(--warn)">L'+no+' · angka tanpa penanda sumber</span><b style="font-size:11.5px;font-weight:400">'+esc(ln.slice(0,70))+'</b></div>';}});
 sk=Math.max(0,sk);
 const r=sk>=90?'g':sk>=70?'y':'r';
 $('n-out').innerHTML=kv('Skor narasi',sk+'/100 <span class="rag '+r+'">'+(sk>=90?'LAYAK':sk>=70?'REVISI':'TOLAK')+'</span>')+(h||'<p class="mut ok" style="margin-top:6px">✓ Tidak ada pelanggaran terdeteksi.</p>');}
$('n-in').addEventListener('input',narasi);

/* ---------- tools: prompt lint ---------- */
const ELEM=[
 ['Peran',/(act as|berperan|anda (adalah|ialah)|kamu (adalah|ialah)|sebagai (seorang|seorang)?\s*\w+)/i,'Tambahkan: "Anda adalah <peran> senior."'],
 ['Konteks',/(konteks|latar|situasi|audiens|pembaca|untuk (tim|klien|manajemen|pemilik))/i,'Tambahkan latar bisnis & audiens.'],
 ['Tugas',/(buat|tulis|analisa|analisis|ringkas|hasilkan|susun|hitung|beri(kan)?|rekomendasi)/i,'Nyatakan kata kerja tugas yang jelas.'],
 ['Kendala',/(jangan|hindari|batasan|maksimal|minimum|wajib|harus|tanpa)/i,'Tambahkan batasan/larangan.'],
 ['Format',/(format|json|tabel|markdown|bullet|poin|csv|slide|heading)/i,'Sebutkan format keluaran.'],
 ['Contoh',/(contoh|example|misal)/i,'Berikan 1 contoh (few-shot) bila bisa.'],
 ['Bahasa',/(bahasa|indonesia|inggris|english)/i,'Kunci bahasa keluaran.']];
function plint(){const t=$('p-in').value;let n=0,h='';
 ELEM.forEach(e=>{const ok=e[1].test(t);if(ok)n++;
  h+='<div class="kv"><span>'+(ok?'<span class="ok">✓</span>':'<span class="bad">✗</span>')+' '+e[0]+'</span>'+
   '<b style="font-size:11.5px;font-weight:400;color:var(--mut)">'+(ok?'ada':esc(e[2]))+'</b></div>';});
 const sk=Math.round(n/ELEM.length*100),r=sk>=85?'g':sk>=55?'y':'r';
 $('p-out').innerHTML=kv('Skor prompt',sk+'/100 <span class="rag '+r+'">'+(sk>=85?'SIAP':sk>=55?'PERBAIKI':'LEMAH')+'</span>')+h;}
$('p-in').addEventListener('input',plint);

/* ---------- tools: SCD ---------- */
function scd(){const stok=num($('s-stok').value),jual=num($('s-jual').value),
 tg=num($('s-target').value),ss=Math.max(0,num($('s-ss').value));
 if(jual<=0){$('s-out').innerHTML='<span class="mut">Isi rata-rata penjualan/hari (&gt;0).</span>';return;}
 const d=stok/jual,r=tg>0?d/tg:0;
 const st=r<0.6?['r','RISIKO HABIS']:r<=1.3?['g','SEHAT']:['y','OVERSTOCK'];
 const order=Math.max(0,Math.ceil((tg+ss-d)*jual));
 const cap=Math.max(0,(d-tg)*jual);
 $('s-out').innerHTML=
  kv('Cover stok',fmt(d,1)+' hari <span class="rag '+st[0]+'">'+st[1]+'</span>')+
  (tg>0?kv('Vs target',fmt(r*100,0)+' % dari '+fmt(tg)+' hari'):'')+
  kv('Stok habis dalam',stok>0?'± '+fmt(Math.floor(d))+' hari':'sudah kosong')+
  kv('Saran order',order>0?fmt(order)+' unit (ke target+safety '+fmt(tg+ss)+' hari)':'tahan order — stok cukup')+
  (cap>0?kv('Kelebihan vs target','± '+fmt(cap)+' unit setara penjualan harian'):'');}
['s-stok','s-jual','s-target','s-ss'].forEach(i=>$(i).addEventListener('input',scd));

/* ---------- tools: proyeksi musiman ---------- */
function musim(){const ytd=num($('m-ytd').value),ly=num($('m-ly').value),rest=num($('m-rest').value),
 u=Math.max(0,num($('m-u').value))/100,tg=num($('m-target').value);
 if(ly<=0){$('m-out').innerHTML='<span class="mut">Isi YTD tahun lalu (&gt;0).</span>';return;}
 const g=ytd/ly-1,pr=rest*(1+g),fy=ytd+pr;
 const lo=fy*(1-u),hi=fy*(1+u),ach=tg>0?fy/tg*100:0;
 const rc=ach>=100?'g':ach>=85?'y':'r';
 $('m-out').innerHTML=
  kv('Growth YTD YoY',(g>=0?'+':'−')+fmt(Math.abs(g)*100,1)+' %',rag(g,0,-0.1))+
  kv('Proyeksi sisa bulan',rp(pr))+
  kv('Proyeksi setahun',rp(fy)+' <span class="mut" style="font-weight:400">(±'+fmt(u*100,0)+'%: '+short(lo)+' – '+short(hi)+')</span>')+
  (tg>0?kv('Vs target setahun',fmt(ach,1)+' % <span class="rag '+rc+'">'+(ach>=100?'ON TRACK':ach>=85?'WASPADA':'MELESET')+'</span> · gap '+rp(fy-tg)):'')+
  '<p class="mut" style="font-size:11.5px;margin-top:6px">asumsi: pola musim tahun ini = tahun lalu. Tulis proyeksi selalu dengan rentang ±.</p>';}
['m-ytd','m-ly','m-rest','m-u','m-target'].forEach(i=>$(i).addEventListener('input',musim));

/* ---------- pasang / unduh / rilis ---------- */
$('ad-list').innerHTML=D.adapters.map(a=>'<span class="ad">'+esc(a)+'</span>').join('');
$('pasang-cmd').innerHTML=
 '<span class="c"># Adapter semua runtime → /adapters</span>\npython3 skills/dan/scripts/make_adapters.py --all\n\n'+
 '<span class="c"># Server MCP (10 tool) — pasang di Claude Desktop/Cursor:</span>\n'+
 '<span class="c">#   command: python3, args: [/path/to/skills/dan/scripts/mcp_server.py]</span>\npython3 skills/dan/scripts/mcp_server.py\n\n'+
 '<span class="c"># Uji integrasi MCP end-to-end</span>\npython3 skills/dan/scripts/mcp_smoke.py\n\n'+
 '<span class="c"># Bundle offline untuk mesin tanpa internet</span>\npython3 skills/dan/scripts/make_bundle.py\n\n'+
 '<span class="c"># Publikasi ke GitHub Pages — 100% GRATIS (lihat DEPLOY-GITHUB.md)</span>\npython3 skills/dan/scripts/publish_gh.py prepare --out site';
$('dl-list').innerHTML=D.unduhan.map(u=>'<div class="card"><h3>📦 '+esc(u.file)+'</h3><p>'+esc(u.label)+
 ' · '+fmt(u.kb)+' KB</p><div style="margin-top:10px"><a href="../'+encodeURIComponent(u.file)+'" download><button class="bpri">Unduh</button></a></div></div>').join('')||
 '<p class="mut">Belum ada artefak rilis.</p>';
$('qa-list').innerHTML=D.qa.map(q=>'<tr><td class="mut">'+esc((q.ts||'').replace('T',' ').slice(0,16))+'</td><td><b>'+esc(q.version)+'</b></td>'+
 '<td class="ok">'+q.tests_pass+'</td><td class="'+(q.tests_fail?'bad':'ok')+'">'+q.tests_fail+'</td><td>'+q.refs_missing+'</td><td class="mut">'+q.files+'</td></tr>').join('');
$('rel-list').innerHTML=D.changelog.map(c=>'<div class="rel"><h3>v'+esc(c.versi)+'</h3><div class="tgl">'+esc(c.tgl)+'</div><ul>'+
 c.isi.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></div>').join('');

/* ---------- init ---------- */
skillsInit();enginesInit();kpi();fmtTool();bep2();drawRows();alok();narasi();plint();scd();musim();
show((location.hash||'#/beranda').slice(2));
"""


def bangun(outdir: str | None = None) -> dict:
    outdir = outdir or os.path.join(DELIV, "dan-web")
    os.makedirs(outdir, exist_ok=True)
    data = kumpul_data()
    blob = json.dumps(data, ensure_ascii=True).replace("</", "<\\/")
    html = (HTML.replace("__CSS__", CSS)
                .replace("__JS__", JS)
                .replace("__DATA__", blob)
                .replace("__VERSI__", data["versi"])
                .replace("__TGL__", data["dibuat"]))
    p = os.path.join(outdir, "index.html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    return {"path": p, "bytes": os.path.getsize(p), "stat": data["stat"], "versi": data["versi"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", default="")
    a = ap.parse_args(argv)
    r = bangun(a.outdir or None)
    print("✓ Situs DAN: %s (%d KB) · %d skills · %d engines · v%s"
          % (r["path"], r["bytes"] // 1024, r["stat"]["skills"], r["stat"]["engines"], r["versi"]))
    print("  serve: python3 %s 8686 → http://localhost:8686/deliverables/dan-web/"
          % os.path.join(HERE, "serve.py"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
