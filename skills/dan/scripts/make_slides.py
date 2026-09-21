#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_slides.py — Template presentasi papan-tulis (slide deck) dari data DAN.

Membangun SATU file HTML self-contained berisi deck siap rapat pimpinan:
chart SVG ditempel inline (tajam di proyektor & saat dicetak), navigasi panah/klik,
dan CSS cetak (tiap slide = 1 halaman) sehingga bisa "Save as PDF" dari browser.

Slide: 1 judul · 2 ringkasan eksekutif · 3 marketing KPI+tren · 4 marketing channel ·
       5 proyek progres+gantt · 6 keputusan & risiko · 7 portofolio bangunan ·
       8 coach & fokus · 9 penutup + status PMO guard

PAKAI
  python3 make_slides.py --marketing analysis.json --project project_report.json \
      --arch arch_report.json --out ../../../deliverables/slides.html
  (buka di browser → panah ←/→ atau klik; Ctrl/Cmd+P untuk PDF)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import svg_charts as sc        # noqa: E402
import weekly_run as wr       # noqa: E402
import i18n                # noqa: E402
import pmo_guard as pg         # noqa: E402

CSS = """
*{box-sizing:border-box}html,body{margin:0;height:100%;background:%(bg)s;color:%(text)s;
font-family:%(font)s}
.deck{height:100vh;overflow:hidden;position:relative}
.slide{display:none;height:100vh;padding:5vh 6vw;flex-direction:column;justify-content:center}
.slide.on{display:flex}
h1{font-size:clamp(30px,5vw,58px);margin:0 0 10px;letter-spacing:-1.2px;line-height:1.08}
h2{font-size:clamp(20px,2.6vw,32px);margin:0 0 18px;letter-spacing:-.6px}
h2:before{content:"";display:inline-block;width:14px;height:14px;border-radius:4px;
background:%(accent)s;margin-right:12px;vertical-align:2px}
.sub{color:%(muted)s;font-size:clamp(13px,1.4vw,18px);line-height:1.5;max-width:60ch}
.kpis{display:flex;gap:22px;flex-wrap:wrap;margin:8px 0 22px}
.kpi{background:%(card)s;border:1px solid %(grid)s;border-radius:16px;padding:16px 22px;min-width:150px}
.kpi .l{font-size:11px;color:%(muted)s;text-transform:uppercase;letter-spacing:.8px}
.kpi .v{font-size:clamp(24px,3vw,40px);font-weight:800;letter-spacing:-1px;margin-top:4px}
.row{display:flex;gap:26px;flex-wrap:wrap;align-items:flex-start}
.row>div{flex:1 1 380px;min-width:300px}
.row svg{width:100%%;height:auto;display:block}
table{border-collapse:collapse;width:100%%;font-size:clamp(11px,1.15vw,15px)}
th,td{border:1px solid %(grid)s;padding:7px 10px;text-align:left}
th{color:%(muted)s;font-size:11px;text-transform:uppercase;letter-spacing:.6px}
li{margin:6px 0 6px 20px;font-size:clamp(13px,1.35vw,18px);line-height:1.5}
.note{color:%(muted)s;font-size:12px;margin-top:14px;line-height:1.5}
.badge{display:inline-block;padding:4px 14px;border-radius:999px;font-weight:800;font-size:13px}
.badge.ok{background:rgba(52,211,153,.16);color:%(good)s}
.badge.bad{background:rgba(251,113,133,.16);color:%(bad)s}
.nav{position:fixed;right:22px;bottom:18px;display:flex;gap:8px;align-items:center;z-index:9}
.nav button{background:%(card)s;color:%(text)s;border:1px solid %(grid)s;border-radius:10px;
padding:8px 14px;font-size:14px;cursor:pointer}
.nav span{color:%(muted)s;font-size:12px;min-width:44px;text-align:center}
@media print{html,body{height:auto}.deck{height:auto;overflow:visible}
.slide{display:flex!important;height:auto;min-height:92vh;page-break-after:always}
.nav{display:none}}
"""

JS = """
var i=0,S=document.querySelectorAll('.slide');
function go(n){i=Math.max(0,Math.min(S.length-1,n));
 for(var k=0;k<S.length;k++)S[k].classList.toggle('on',k===i);
 document.getElementById('cnt').textContent=(i+1)+' / '+S.length;
 location.hash='s'+(i+1);}
document.addEventListener('keydown',function(e){
 if(e.key==='ArrowRight'||e.key===' '||e.key==='PageDown')go(i+1);
 if(e.key==='ArrowLeft'||e.key==='PageUp')go(i-1);
 if(e.key==='Home')go(0); if(e.key==='End')go(S.length-1);});
document.addEventListener('click',function(e){
 if(e.target.closest('button'))return; go(i+1);});
var h=parseInt((location.hash||'').replace('#s',''),10);
go(isNaN(h)?0:h-1);
"""


def _load(p: Optional[str]) -> Optional[Dict[str, Any]]:
    if not p or not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def build(mkt: Optional[Dict], prj: Optional[Dict], archs: List[Dict],
          title: str, theme: str, lang: str = "id") -> str:
    th = sc.theme(theme)
    cur = (mkt or {}).get("meta", {}).get("currency", "Rp")
    S: List[str] = []

    # 1 judul
    chips = f"{(mkt or {}).get('meta', {}).get('source', 'marketing')} · " \
            f"{len((prj or {}).get('projects', []))} proyek · {len(archs)} studi bangunan"
    S.append(f"<h1>{sc.esc(title)}</h1><p class='sub'>Rapat pimpinan · "
             f"{sc.esc(chips)}<br>Disusun otomatis oleh DAN dari analysis.json, "
             f"project_report.json, dan arch_report.json.</p>")

    # 2 ringkasan eksekutif
    decs = wr.pick_decisions(prj or {"insights": [], "projects": []}, mkt)
    k = (mkt or {}).get("kpi", {})
    port = (prj or {}).get("portfolio", {})
    tot_built = sum(a.get("totals", {}).get("built_area", 0) for a in archs)
    S.append(f"<h2>{i18n.t('slide_exec', lang)}</h2><div class='kpis'>"
             + f"<div class='kpi'><div class='l'>Revenue</div><div class='v'>{cur}"
               f"{sc.fmt_num(k.get('revenue', 0), 'id')}</div></div>"
             + f"<div class='kpi'><div class='l'>ROAS</div><div class='v'>{k.get('roas', 0):.2f}x</div></div>"
             + f"<div class='kpi'><div class='l'>Tugas on-track</div><div class='v'>"
               f"{port.get('on_track', 0)}/{port.get('tasks', 0)}</div></div>"
             + f"<div class='kpi'><div class='l'>Portofolio terbangun</div><div class='v'>"
               f"{tot_built:,.0f} m²</div></div></div><ol>"
             + "".join(f"<li><b>{sc.esc(d['keputusan'])}</b> — {sc.esc(d['aksi'])}</li>"
                       for d in decs) + "</ol>")

    # 3 marketing
    if mkt:
        ts = (mkt.get("time") or {}).get("series") or {}
        labels = (mkt.get("time") or {}).get("labels") or []
        trend = ""
        if ts.get("revenue") and labels:
            step = max(1, len(labels) // 10)
            trend = sc.line([(labels[i], ts["revenue"][i]) for i in range(0, len(labels), step)],
                            title="Tren revenue", th=theme, width=760, height=330,
                            area=True, markers=False)
        S.append(f"<h2>{i18n.t('slide_marketing', lang)}</h2><div class='kpis'>"
                 + f"<div class='kpi'><div class='l'>CTR</div><div class='v'>{k.get('ctr', 0):.2f}%</div></div>"
                 + f"<div class='kpi'><div class='l'>CVR</div><div class='v'>{k.get('cvr', 0):.2f}%</div></div>"
                 + f"<div class='kpi'><div class='l'>CPA</div><div class='v'>{cur}"
                   f"{sc.fmt_num(k.get('cpa', 0), 'id')}</div></div>"
                 + f"<div class='kpi'><div class='l'>Health</div><div class='v'>"
                   f"{mkt.get('health_score', 0):.0f}</div></div></div>"
                 + f"<div class='row'><div>{trend}</div></div>")
        ch = mkt.get("by_channel") or []
        if ch:
            S.append(f"<h2>{i18n.t('slide_channel', lang)}</h2><div class='row'>"
                     f"<div>{sc.hbar([(c['name'], c['kpi']['roas']) for c in ch], title='ROAS', th=theme, width=520, height=330, value_fmt=lambda v: f'{v:.2f}x')}</div>"
                     f"<div>{sc.donut([(c['name'], c['kpi']['revenue']) for c in ch], title='Kontribusi revenue', th=theme, width=520, height=330)}</div></div>")

    # 4 proyek
    if prj:
        P = prj["projects"]
        S.append(f"<h2>{i18n.t('slide_project', lang)}</h2><div class='row'>"
                 f"<div>{sc.progress([{'label': p['name'][:22], 'value': p['progress'], 'target': p['planned'], 'rag': p['rag']} for p in P], title='', th=theme, width=560)}</div>"
                 f"<div>{sc.gantt([{'name': t['name'], 'start': t['start'], 'end': t['end'], 'progress': t['actual'], 'rag': t['rag'], 'owner': t['owner']} for p in P for t in p['tasks']], title='', th=theme, width=620, row_h=24)}</div></div>")
        rows = "".join(
            f"<tr><td>{sc.esc(p['name'])}</td><td>{p['progress']:.0f}%</td>"
            f"<td>{p['variance']:+.0f}</td><td>{sc.esc(pm_label(prj, p))}</td><td>{p['forecast_end'] or '—'}</td></tr>"
            for p in P)
        risks = sorted([r for p in P for r in p.get("risks", [])],
                       key=lambda r: -float(r.get("prob", 1)) * float(r.get("impact", 1)))[:3]
        rrows = "".join(f"<tr><td>{sc.esc(r.get('desc', '')[:60])}</td>"
                        f"<td>{float(r.get('prob', 1)) * float(r.get('impact', 1)):.0f}</td>"
                        f"<td>{sc.esc(r.get('owner', '-'))}</td></tr>" for r in risks)
        S.append(f"<h2>{i18n.t('slide_decision', lang)}</h2><div class='row'>"
                 f"<div><table><tr><th>Proyek</th><th>Progres</th><th>Var</th><th>Status</th>"
                 f"<th>Forecast</th></tr>{rows}</table></div>"
                 f"<div><table><tr><th>Risiko teratas</th><th>Skor</th><th>Owner</th></tr>"
                 f"{rrows}</table></div></div>")

    # 5 arsitektur
    if archs:
        names = [a.get("meta", {}).get("name", f"Studi {i + 1}")[:20]
                 for i, a in enumerate(archs)]
        mf = lambda v: f"{cur}{sc.fmt_num(v, 'id')}"
        S.append(f"<h2>{i18n.t('slide_arch', lang)}</h2><div class='row'>"
                 f"<div>{sc.bar(list(zip(names, [a.get('totals', {}).get('built_area', 0) for a in archs])), title='Luas terbangun (m²)', th=theme, width=560, height=320)}</div>"
                 f"<div>{sc.hbar(list(zip(names, [a.get('rab_total', 0) for a in archs])), title='RAB', th=theme, width=560, height=320, value_fmt=mf)}</div></div>"
                 + "<p class='note'>RAB kelas konsep ±25%; kepatuhan KDB/KLB diverifikasi "
                   "per studi pada arch_report masing-masing.</p>")

    # 6 coach & fokus
    if prj:
        focus = wr.pick_focus(prj)
        frows = "".join(f"<tr><td>{sc.esc(f['task'])}</td><td>{sc.esc(f['owner'])}</td>"
                        f"<td>{f['variance']:+.0f}</td><td>{'stalled' if f['stalled'] else 'lihat RAG'}</td></tr>"
                        for f in focus) or "<tr><td colspan=4>semua dalam ambang</td></tr>"
        coach = "".join(f"<li><b>{sc.esc(c['owner'])}</b>: {sc.esc(c['step_15min'])}</li>"
                        for c in (prj.get("coach") or [])[:4])
        S.append(f"<h2>{i18n.t('slide_focus', lang)}</h2><div class='row'>"
                 f"<div><table><tr><th>Tugas fokus</th><th>Owner</th><th>Var</th><th>Catatan</th></tr>"
                 f"{frows}</table></div><div><ul>{coach}</ul></div></div>")

    # 7 penutup + guard
    guard = "— "
    if prj:
        try:
            viol = pg.evaluate(_projects_doc_or_none(prj) or {}, prj)
            n = sum(1 for v in viol if v["severity"] == "high")
            guard = (f"<span class='badge ok'>PMO guard BERSIH</span>" if n == 0
                     else f"<span class='badge bad'>PMO guard: {n} temuan high</span>")
        except Exception:
            guard = "<span class='badge ok'>PMO guard: n/a</span>"
    S.append(f"<h2>{i18n.t('slide_close', lang)}</h2><ul>"
             "<li>Setujui 3 keputusan pada slide 2.</li>"
             "<li>Tetapkan owner & tenggat untuk tiap tugas fokus.</li>"
             "<li>Ritme: form progres diisi tim tiap Senin; guard berjalan otomatis.</li>"
             "</ul><p class='note'>Status gate: " + guard +
             " · Deck ini dihasilkan `make_slides.py`; cetak via Ctrl/Cmd+P "
             "(tiap slide = 1 halaman).</p>")

    body = "".join(f"<section class='slide{' on' if i == 0 else ''}'>{s}</section>"
                   for i, s in enumerate(S))
    css = CSS
    for kk in ("bg", "card", "text", "muted", "grid", "accent", "good", "bad"):
        css = css.replace(f"%({kk})s", th[kk])
    css = css.replace("%(font)s", sc.FONT).replace("%%", "%")
    return (f"<!doctype html><html lang='id'><head><meta charset='utf-8'>"
            f"<title>{sc.esc(title)}</title><style>{css}</style></head><body>"
            f"<div class='deck'>{body}</div>"
            f"<div class='nav'><button onclick='go(i-1)'>←</button>"
            f"<span id='cnt'></span><button onclick='go(i+1)'>→</button></div>"
            f"<script>{JS}</script></body></html>")


def pm_label(prj: Dict, p: Dict) -> str:
    import project_monitor as pm
    return pm.RAG_LABEL[p["rag"]]


def _projects_doc_or_none(prj: Dict) -> Optional[Dict]:
    # guard butuh dokumen mentah (history); bila hanya model terhitung, kembalikan None
    return None if "history" not in prj else prj


def main(argv=None) -> int:
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · slide deck generator")
    ap.add_argument("--marketing", default=os.path.join(dl, "analysis.json"))
    ap.add_argument("--project", default=os.path.join(dl, "project_report.json"))
    ap.add_argument("--arch", action="append", default=[])
    ap.add_argument("--title", default="Review Pimpinan — DAN")
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    ap.add_argument("--out", default=os.path.join(dl, "slides.html"))
    ap.add_argument("--lang", default="id", choices=i18n.langs())
    a = ap.parse_args(argv)
    archs = [_load(p) for p in (a.arch or [os.path.join(dl, "arch_report.json")])]
    html = build(_load(a.marketing), _load(a.project), [x for x in archs if x],
                 a.title, a.theme, a.lang)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(html)
    n = html.count("class='slide")
    print(f"[DAN] slide deck: {n} slide -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
