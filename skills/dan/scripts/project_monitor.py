#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_monitor.py — Tools Monitoring / Tracking / Progress Proyek (sub-skill DAN #07).

Zero-dependency (stdlib). Membaca `projects.json` (lihat templates/projects.example.json),
lalu menghitung kesehatan proyek secara obyektif:

  PER TUGAS   : planned progress (linear dari tanggal), variance (pp), SPI analog,
                hari terlambat, status RAG, deteksi stalled (dari riwayat update)
  PER PROYEK  : weighted % complete, variance, RAG, Earned Value (EV/CPI/EAC),
                forecast tanggal selesai, beban per owner
  PORTOFOLIO  : ringkasan on-track / at-risk / overdue, matriks risiko, burndown

SUB-PERINTAH
  report   projects.json            → report.md + report.json + dashboard.html
  status   projects.json            → tabel ringkas ke stdout
  apply    projects.json update.json→ terapkan form terisi (progress/monitoring/controlling)
                                      → projects_updated.json + riwayat
  coach    projects.json            → coach.md (pesan motivator per owner berdasar data)
  forms    --out forms.html         → form interaktif (monitoring/controlling/progress)

CONTOH
  python3 project_monitor.py report ../templates/projects.example.json
  python3 project_monitor.py apply projects.json update.json
  python3 project_monitor.py coach projects.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import svg_charts as sc  # noqa: E402

RAG_ORDER = {"good": 0, "warn": 1, "bad": 2}
RAG_LABEL = {"good": "On-track", "warn": "Waspada", "bad": "Kritis"}


# --------------------------------------------------------------------- util

def d(v: Any) -> Optional[datetime]:
    return sc._pm_date(v)


def today_of(meta: Dict[str, Any]) -> datetime:
    return d(meta.get("today")) or datetime.now()


def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def planned_progress(task: Dict[str, Any], now: datetime) -> float:
    """Progres yang SEHARUSNYA tercapai hari ini (interpolasi linear start→end)."""
    if task.get("planned_progress") is not None:
        return clamp(float(task["planned_progress"]))
    st, en = d(task.get("start")), d(task.get("end") or task.get("start"))
    if not st or not en or en <= st:
        return 100.0 if (task.get("progress") or 0) >= 100 else (100.0 if en and now > en else 0.0)
    frac = (now - st).days / (en - st).days
    return clamp(frac * 100)


def task_rag(task: Dict[str, Any], now: datetime) -> Tuple[str, float, float, int]:
    """-> (rag, planned, actual, overdue_days)"""
    act = clamp(float(task.get("progress", 0) or 0))
    plan = planned_progress(task, now)
    st, en = d(task.get("start")), d(task.get("end") or task.get("start"))
    overdue = max(0, (now - en).days) if (en and act < 100 and now > en) else 0
    if act >= 100:
        return "good", plan, act, 0
    var = act - plan
    if overdue > 3 or var < -20:
        rag = "bad"
    elif overdue > 0 or var < -5 or str(task.get("status", "")).lower() in ("blocked", "stalled", "risiko"):
        rag = "warn"
    else:
        rag = "good"
    return rag, plan, act, overdue


def spi(plan: float, act: float) -> float:
    return (act / plan) if plan > 0 else (1.0 if act >= 100 else 0.0)


def history_of(hist: List[Dict[str, Any]], project: str, task: str) -> List[Dict[str, Any]]:
    return [h for h in hist
            if h.get("form") == "progress" and h.get("project") == project
            and str(h.get("task")) == str(task)]


def is_stalled(hist: List[Dict[str, Any]], project: str, task: str, now: datetime,
               days: int = 7) -> bool:
    """Stalled = ada ≥2 update berurutan dengan progres sama, atau tanpa update > `days`."""
    hs = sorted(history_of(hist, project, task), key=lambda h: str(h.get("date")))
    if len(hs) >= 2:
        last, prev = hs[-1], hs[-2]
        same = float(last.get("progress", -1)) == float(prev.get("progress", -1))
        dt = (d(last.get("date")) - d(prev.get("date"))).days if d(last.get("date")) and d(prev.get("date")) else 0
        if same and dt >= 3:
            return True
    if hs:
        last_dt = d(hs[-1].get("date"))
        if last_dt and (now - last_dt).days > days:
            return True
    return False


# --------------------------------------------------------------------- compute

def compute(doc: Dict[str, Any]) -> Dict[str, Any]:
    meta = doc.get("meta", {})
    now = today_of(meta)
    cur = meta.get("currency", "Rp")
    hist = doc.get("history", []) or []
    projects_out, portfolio = [], {"projects": 0, "tasks": 0, "done": 0, "on_track": 0,
                                   "warn": 0, "bad": 0, "overdue": 0, "stalled": 0,
                                   "budget_planned": 0.0, "budget_actual": 0.0,
                                   "owners": defaultdict(lambda: {"tasks": 0, "weight": 0.0,
                                                                  "bad": 0, "warn": 0})}
    for p in doc.get("projects", []):
        tasks_out = []
        wsum = sum(float(t.get("weight", 1) or 1) for t in p.get("tasks", [])) or 1.0
        w_act = w_plan = 0.0
        for t in p.get("tasks", []):
            rag, plan, act, over = task_rag(t, now)
            stalled = is_stalled(hist, p.get("id", ""), t.get("id", t.get("name", "")), now)
            w = float(t.get("weight", 1) or 1)
            w_act += w * act
            w_plan += w * plan
            portfolio["tasks"] += 1
            portfolio["done"] += 1 if act >= 100 else 0
            portfolio["on_track"] += 1 if rag == "good" else 0
            portfolio["warn"] += 1 if rag == "warn" else 0
            portfolio["bad"] += 1 if rag == "bad" else 0
            portfolio["overdue"] += 1 if over else 0
            portfolio["stalled"] += 1 if stalled else 0
            own = t.get("owner", "(tanpa owner)")
            ob = portfolio["owners"][own]
            ob["tasks"] += 1
            ob["weight"] += w
            ob[rag if rag != "good" else "good_count"] = ob.get(rag if rag != "good" else "good_count", 0) + (1 if rag != "good" else 0)
            tasks_out.append({
                "id": t.get("id", t.get("name")), "name": t.get("name", t.get("id")),
                "owner": own, "start": t.get("start"), "end": t.get("end"),
                "planned": round(plan, 1), "actual": round(act, 1),
                "variance": round(act - plan, 1), "spi": round(spi(plan, act), 2),
                "overdue_days": over, "rag": rag, "stalled": stalled,
                "weight": w, "status": t.get("status", ""),
                "blockers": t.get("blockers", []) or [], "notes": t.get("notes", ""),
            })
        p_act = w_act / wsum
        p_plan = w_plan / wsum
        p_var = p_act - p_plan
        p_rag = "bad" if p_var < -20 else ("warn" if p_var < -5 else "good")
        if any(t["rag"] == "bad" for t in tasks_out):
            p_rag = "bad" if p_var < -10 else "warn"

        # Earned value (analog): EV = BAC * %complete ; CPI = EV/AC ; EAC = BAC/CPI
        bac = float(p.get("budget_planned", 0) or 0)
        ac = float(p.get("budget_actual", 0) or 0)
        ev = bac * p_act / 100
        cpi = (ev / ac) if ac > 0 else None
        eac = (bac / cpi) if cpi else None
        portfolio["budget_planned"] += bac
        portfolio["budget_actual"] += ac

        # forecast selesai: laju = progres / hari terlewani
        st, en = d(p.get("start")), d(p.get("end"))
        elapsed = max(1, (now - st).days) if st else 1
        rate = p_act / elapsed                       # % per hari
        remaining = 100 - p_act
        eta_days = int(remaining / rate) if rate > 0 else None
        forecast_end = (now + timedelta(days=eta_days)) if eta_days is not None else None
        slip = (forecast_end - en).days if (forecast_end and en) else None

        projects_out.append({
            "id": p.get("id", ""), "name": p.get("name", ""), "owner": p.get("owner", ""),
            "start": p.get("start"), "end": p.get("end"), "goal": p.get("goal", ""),
            "progress": round(p_act, 1), "planned": round(p_plan, 1),
            "variance": round(p_var, 1), "rag": p_rag,
            "budget_planned": bac, "budget_actual": ac,
            "budget_used_pct": round(ac / bac * 100, 1) if bac else None,
            "ev": round(ev, 0), "cpi": round(cpi, 2) if cpi else None,
            "eac": round(eac, 0) if eac else None,
            "forecast_end": forecast_end.strftime("%Y-%m-%d") if forecast_end else None,
            "slip_days": slip, "tasks": tasks_out,
            "kpi": p.get("kpi", []) or [],
            "risks": p.get("risks", []) or [],
            "actions": p.get("actions", []) or [],
        })
    projects_out.sort(key=lambda x: RAG_ORDER[x["rag"]], reverse=True)
    portfolio["projects"] = len(projects_out)
    portfolio["owners"] = {k: {kk: (round(vv, 1) if isinstance(vv, float) else vv)
                               for kk, vv in v.items()}
                           for k, v in portfolio["owners"].items()}

    return {"meta": {**meta, "today": now.strftime("%Y-%m-%d"), "currency": cur},
            "projects": projects_out, "portfolio": portfolio,
            "insights": _insights(projects_out, portfolio, now, cur),
            "coach": coach_messages(projects_out, now)}


def _insights(P: List[Dict[str, Any]], port: Dict[str, Any], now: datetime,
              cur: str) -> List[Dict[str, str]]:
    ins = []
    if port["bad"]:
        worst = [t for p in P for t in p["tasks"] if t["rag"] == "bad"]
        worst.sort(key=lambda t: t["variance"])
        t = worst[0]
        ins.append({"title": f"{port['bad']} tugas kritis; terparah “{t['name']}” ({t['variance']:+.0f} pp)",
                    "detail": f"Progres {t['actual']:.0f}% dari rencana {t['planned']:.0f}%"
                              + (f", terlambat {t['overdue_days']} hari." if t["overdue_days"] else "."),
                    "severity": "bad",
                    "action": f"Escalate ke owner {t['owner']} hari ini: pecah jadi tugas ≤2 hari "
                              f"atau tambah sumber daya; isi form controlling bila akar masalah struktural."})
    if port["stalled"]:
        names = [f"{t['name']} ({p['id']})" for p in P for t in p["tasks"] if t["stalled"]][:4]
        ins.append({"title": f"{port['stalled']} tugas stalled (tidak ada kemajuan)",
                    "detail": "Tanpa perubahan progres pada update terakhir: " + ", ".join(names),
                    "severity": "warn",
                    "action": "Cek blocker di form progress; bila blocker eksternal >3 hari, "
                              "ambil alih koordinasi atau turunkan scope tugas tersebut."})
    slip = [p for p in P if p.get("slip_days") and p["slip_days"] > 0]
    if slip:
        p = max(slip, key=lambda x: x["slip_days"])
        ins.append({"title": f"Proyeksi mundur {p['slip_days']} hari — {p['name']}",
                    "detail": f"Forecast selesai {p['forecast_end']} vs rencana {p['end']} "
                              f"(laju saat ini {p['progress'] / max(1, (now - (d(p['start']) or now)).days):.2f}%/hari).",
                    "severity": "warn",
                    "action": "Pilih satu: tambah resource, kurangi scope, atau geser deadline "
                              "dan komunikasikan ke stakeholder minggu ini."})
    over_budget = [p for p in P if p.get("cpi") and p["cpi"] < 1]
    if over_budget:
        p = over_budget[0]
        ins.append({"title": f"Biaya melebihi nilai kerja (CPI {p['cpi']:.2f}) — {p['name']}",
                    "detail": f"Terpakai {cur}{p['budget_actual']:,.0f} untuk kerja senilai "
                              f"{cur}{p['ev']:,.0f}. EAC {cur}{p['eac']:,.0f} vs budget "
                              f"{cur}{p['budget_planned']:,.0f}.",
                    "severity": "warn" if p["cpi"] > 0.85 else "bad",
                    "action": "Bekukan pengeluaran non-kritis; review vendor & scope sebelum "
                              "approve budget tambahan."})
    good = [p for p in P if p["rag"] == "good"]
    if good:
        p = good[0]
        ins.append({"title": f"{len(good)} proyek on-track; terbaik “{p['name']}” ({p['progress']:.0f}%)",
                    "detail": f"Variance {p['variance']:+.1f} pp terhadap rencana.",
                    "severity": "good",
                    "action": "Dokumentasikan cara kerjanya (ritme, template, owner) agar bisa "
                              "direplikasi ke proyek yang kritis."})
    risks = [r for p in P for r in p["risks"]]
    if risks:
        hi = sorted(risks, key=lambda r: -(float(r.get("prob", 1)) * float(r.get("impact", 1))))[0]
        score = float(hi.get("prob", 1)) * float(hi.get("impact", 1))
        ins.append({"title": f"Risiko tertinggi: skor {score:.0f} — {hi.get('desc', '')[:60]}",
                    "detail": f"Probabilitas {hi.get('prob')} × dampak {hi.get('impact')}. "
                              f"Mitigasi saat ini: {hi.get('mitigation', '-')}",
                    "severity": "bad" if score >= 12 else ("warn" if score >= 6 else "info"),
                    "action": f"Pastikan mitigasi punya owner ({hi.get('owner', '?')}) dan tanggal; "
                              f"bahas di review mingguan sampai skor < 6."})
    return ins


# --------------------------------------------------------------------- coach (motivator expert)

def coach_messages(P: List[Dict[str, Any]], now: datetime) -> List[Dict[str, Any]]:
    """Pesan motivator per owner, DIBANGUN DARI DATA (bukan kata penyemangat kosong)."""
    by_owner: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in P:
        for t in p["tasks"]:
            by_owner[t["owner"]].append({**t, "project": p["name"], "pid": p["id"]})
    out = []
    for owner, tasks in sorted(by_owner.items()):
        done = [t for t in tasks if t["actual"] >= 100]
        bad = [t for t in tasks if t["rag"] == "bad"]
        warn = [t for t in tasks if t["rag"] == "warn"]
        stalled = [t for t in tasks if t["stalled"]]
        avg = sum(t["actual"] for t in tasks) / len(tasks)
        wins = sum(1 for t in tasks if t["variance"] >= 0)
        if not (bad or warn or stalled):
            tone, msg = "apresiasi", (
                f"{owner}, semua tugasmu on-track ({len(done)}/{len(tasks)} selesai, rata-rata "
                f"{avg:.0f}%). Itu hasil ritme yang rapi, bukan keberuntungan.")
            step = "Tulis satu hal yang membuat ritme ini bekerja, supaya bisa kamu ulangi di proyek berikutnya."
        elif bad:
            t = bad[0]
            tone = "reframing + langkah kecil"
            msg = (f"{owner}, aku lihat “{t['name']}” di {t['actual']:.0f}% dari rencana "
                   f"{t['planned']:.0f}%. Wajar terasa berat — tapi perhatikan: kamu sudah "
                   f"menyelesaikan {len(done)} tugas lain di portofolio ini, dan {wins} dari "
                   f"{len(tasks)} tugasmu tidak minus. Masalahnya bukan kemampuanmu, tapi "
                   f"ukuran tugas ini yang terlalu besar untuk satu langkah.")
            step = (f"15 menit ke depan: buka “{t['name']}” dan tulis 3 potongan terkecil yang "
                    f"bisa selesai hari ini. Kerjakan potongan pertama saja.")
        elif stalled:
            t = stalled[0]
            tone = "memecah kelumpuhan"
            msg = (f"{owner}, “{t['name']}” belum bergerak sejak update terakhir. Biasanya ini "
                   f"bukan malas — ada blocker yang belum terucapkan atau tugas yang kabur batasnya.")
            step = (f"Sebutkan SATU hal yang menghalangi “{t['name']}” di form progress hari ini. "
                    f"Kalau blocker eksternal, tandai siapa yang harus dihubungi — lalu hubungi.")
        else:
            t = warn[0]
            tone = "fokus"
            msg = (f"{owner}, “{t['name']}” selisih {abs(t['variance']):.0f} poin dari rencana. "
                   f"Masih bisa dikejar minggu ini tanpa lembur kalau fokusnya satu.")
            step = f"Pilih satu tugas prioritas besok pagi: “{t['name']}”. Tunda yang lain 24 jam."
        out.append({"owner": owner, "tone": tone, "message": msg, "step_15min": step,
                    "facts": {"tasks": len(tasks), "done": len(done), "bad": len(bad),
                              "warn": len(warn), "stalled": len(stalled),
                              "avg_progress": round(avg, 1)}})
    return out


# --------------------------------------------------------------------- charts / dashboard

def build_dashboard_spec(A: Dict[str, Any]) -> Dict[str, Any]:
    meta, P, port = A["meta"], A["projects"], A["portfolio"]
    cur = meta.get("currency", "Rp")
    now = d(meta["today"]) or datetime.now()

    gantt_tasks = []
    for p in P:
        for t in p["tasks"]:
            gantt_tasks.append({"name": f"{t['name']}", "start": t["start"], "end": t["end"],
                                "progress": t["actual"], "rag": t["rag"], "owner": t["owner"]})
    prog_items = [{"label": p["name"][:24], "value": p["progress"], "target": p["planned"],
                   "rag": p["rag"]} for p in P]

    # burn-up: planned vs actual kumulatif portofolio per minggu
    labels, plan_s, act_s = [], [], []
    if P:
        st = min([d(p["start"]) for p in P if d(p["start"])], default=now - timedelta(days=30))
        en = max([d(p["end"]) for p in P if d(p["end"])], default=now)
        weeks = max(2, ((en - st).days // 7) + 1)
        for w in range(weeks + 1):
            day = st + timedelta(days=w * 7)
            if day > now + timedelta(days=1):
                break
            labels.append(day.strftime("%d/%m"))
            pa = aa = 0.0
            for p in P:
                for t in p["tasks"]:
                    wgt = t["weight"]
                    ts, te = d(t["start"]), d(t["end"])
                    if ts and te and te > ts:
                        pa += wgt * clamp((day - ts).days / (te - ts).days * 100)
                    hs = [h for h in (A.get("history") or [])]
                    aa += wgt * _actual_at(t, hs, p["id"], day)
            tot = sum(t["weight"] for p in P for t in p["tasks"]) or 1
            plan_s.append(round(pa / tot, 1))
            act_s.append(round(aa / tot, 1))

    # matriks risiko prob × impact
    rm = [[0] * 5 for _ in range(5)]
    for p in P:
        for r in p["risks"]:
            pr = int(clamp(float(r.get("prob", 1)), 1, 5)) - 1
            im = int(clamp(float(r.get("impact", 1)), 1, 5)) - 1
            rm[im][pr] += 1
    risk_rows = ["Dampak 5", "Dampak 4", "Dampak 3", "Dampak 2", "Dampak 1"][::-1]
    matrix = [rm[4 - i] for i in range(5)]

    owner_items = [{"label": o, "value": v["weight"], } for o, v in
                   sorted(port["owners"].items(), key=lambda kv: -kv[1]["weight"])]

    sections: List[Dict[str, Any]] = [
        {"type": "kpi", "items": [
            {"label": "Proyek", "value": port["projects"], "format": "number"},
            {"label": "Progres rata-rata",
             "value": f"{sum(p['progress'] for p in P) / max(1, len(P)):.0f}%",
             "delta": (sum(p['progress'] for p in P) / max(1, len(P)) -
                       sum(p['planned'] for p in P) / max(1, len(P))), "delta_suffix": " pp"},
            {"label": "On-track", "value": port["on_track"], "format": "number", "color": "#34D399"},
            {"label": "Waspada", "value": port["warn"], "format": "number", "color": "#FBBF24"},
            {"label": "Kritis", "value": port["bad"], "format": "number", "color": "#FB7185"},
            {"label": "Terlambat", "value": port["overdue"], "format": "number", "color": "#FB7185"},
            {"label": "Stalled", "value": port["stalled"], "format": "number", "color": "#FBBF24"},
            {"label": "Budget terpakai",
             "value": f"{port['budget_actual'] / max(1, port['budget_planned']) * 100:.0f}%",
             "color": "#38BDF8"},
        ]},
        {"type": "chart", "chart": "gantt", "span": 8, "title": "Timeline & Tracking Tugas",
         "subtitle": f"per {meta['today']} · warna = status RAG · angka = progres aktual",
         "width": 900, "height": max(180, 40 + len(gantt_tasks) * 30),
         "data": gantt_tasks, "options": {"today": meta["today"]},
         "note": "Garis putus = hari ini. Berlian = milestone."},
        {"type": "chart", "chart": "progress", "span": 4, "title": "Progres vs Rencana",
         "subtitle": "bar = aktual · garis tegak = rencana hari ini",
         "width": 520, "height": max(140, 40 + len(prog_items) * 34), "data": prog_items},
    ]
    if labels:
        sections.append({"type": "chart", "chart": "line", "span": 6,
                         "title": "Burn-up Portofolio (planned vs actual)",
                         "width": 640, "height": 340,
                         "data": {"labels": labels, "series": {"Rencana": plan_s, "Aktual": act_s}},
                         "note": "Satuan % bobot tugas kumulatif. Aktual di bawah rencana = perlu intervensi."})
    sections += [
        {"type": "chart", "chart": "heatmap", "span": 6, "title": "Matriks Risiko (probabilitas × dampak)",
         "subtitle": "jumlah risiko per sel", "width": 620, "height": 340,
         "data": {"rows": risk_rows, "cols": ["P1", "P2", "P3", "P4", "P5"], "matrix": matrix},
         "note": "Sel kanan-atas (prob tinggi × dampak tinggi) wajib punya mitigasi ber-owner."},
        {"type": "chart", "chart": "hbar", "span": 6, "title": "Beban Kerja per Owner (bobot tugas)",
         "width": 620, "height": 340, "data": [(o["label"], o["value"]) for o in owner_items],
         "note": "Owner dengan beban tertinggi + tugas kritis = kandidat burnout; seimbangkan."},
    ]
    rows = "".join(
        f'<tr><td>{sc.esc(t["name"])}</td><td>{sc.esc(t["owner"])}</td>'
        f'<td class="n">{t["planned"]:.0f}%</td><td class="n">{t["actual"]:.0f}%</td>'
        f'<td class="n">{t["variance"]:+.0f}</td><td class="n">{t["spi"]:.2f}</td>'
        f'<td class="n">{t["overdue_days"] or "—"}</td>'
        f'<td>{RAG_LABEL[t["rag"]]}{" · stalled" if t["stalled"] else ""}</td></tr>'
        for p in P for t in sorted(p["tasks"], key=lambda x: x["variance"])[:25])
    sections.append({"type": "html", "span": 12, "html":
                     f'<div style="padding:6px 8px"><div style="font-size:15px;font-weight:700;'
                     f'margin-bottom:10px">Tracking Tugas (urut variance terburuk)</div>'
                     f'<table><thead><tr><th>Tugas</th><th>Owner</th><th class="n">Rencana</th>'
                     f'<th class="n">Aktual</th><th class="n">Var (pp)</th><th class="n">SPI</th>'
                     f'<th class="n">Telat (hari)</th><th>Status</th></tr></thead>'
                     f'<tbody>{rows}</tbody></table></div>',
                     "note": "SPI = aktual ÷ rencana. <0,9 = perlu perhatian; <0,75 = intervensi."})
    acts = [a for p in P for a in p["actions"]]
    if acts:
        arows = "".join(
            f'<tr><td>{sc.esc(a.get("issue", ""))}</td><td>{sc.esc(a.get("action", ""))}</td>'
            f'<td>{sc.esc(a.get("owner", ""))}</td><td>{sc.esc(a.get("due", ""))}</td>'
            f'<td>{sc.esc(a.get("status", ""))}</td></tr>' for a in acts)
        sections.append({"type": "html", "span": 12, "html":
                         f'<div style="padding:6px 8px"><div style="font-size:15px;font-weight:700;'
                         f'margin-bottom:10px">Tindakan Korektif (form controlling)</div>'
                         f'<table><thead><tr><th>Masalah</th><th>Tindakan</th><th>Owner</th>'
                         f'<th>Tenggat</th><th>Status</th></tr></thead><tbody>{arows}</tbody></table></div>'})
    sections.append({"type": "insights", "items": A["insights"]})
    if A["coach"]:
        c = A["coach"][0]
        sections.append({"type": "recommendations",
                         "items": [f"[Coach untuk {c['owner']}] {c['step_15min']}"] +
                                  [f"[Coach untuk {x['owner']}] {x['step_15min']}"
                                   for x in A["coach"][1:5]]})
    return {
        "title": meta.get("name", "Dashboard Monitoring Proyek"),
        "subtitle": (f"Per {meta['today']} · {port['projects']} proyek · {port['tasks']} tugas · "
                     f"{port['on_track']} on-track / {port['warn']} waspada / {port['bad']} kritis · "
                     f"disusun oleh DAN · Project Monitoring & Controlling"),
        "theme": meta.get("theme", "dan"), "locale": "id", "currency": cur,
        "badge": {"value": f"{sum(p['progress'] for p in P) / max(1, len(P)):.0f}",
                  "label": "% selesai"},
        "chips": [f"Per {meta['today']}", f"{port['overdue']} terlambat",
                  f"{port['stalled']} stalled",
                  f"Budget {cur}{port['budget_actual'] / max(1, port['budget_planned']) * 100:.0f}% terpakai"],
        "sections": sections,
        "footer": ("Metode: planned progress = interpolasi linear start→end · variance = aktual − "
                   "rencana (pp) · SPI = aktual ÷ rencana · RAG: baik bila var ≥ −5 · "
                   "waspada bila −20 ≤ var < −5 atau terlambat ≤3 hari · "
                   "kritis bila var < −20 atau terlambat >3 hari · "
                   "EV = budget × %selesai, CPI = EV ÷ biaya aktual, EAC = budget ÷ CPI · "
                   "stalled = tanpa kemajuan pada update terakhir. · DAN · PMO + Motivator Expert"),
    }


def _actual_at(t: Dict[str, Any], hist: List[Dict[str, Any]], pid: str,
               day: datetime) -> float:
    """Progres aktual tugas pada suatu tanggal: pakai riwayat bila ada, else linear."""
    hs = sorted([h for h in hist if h.get("form") == "progress"
                 and h.get("project") == pid and str(h.get("task")) == str(t["id"])],
                key=lambda h: str(h.get("date")))
    val = 0.0
    for h in hs:
        hd = d(h.get("date"))
        if hd and hd <= day:
            val = float(h.get("progress", val) or 0)
    if not hs:
        ts, te = d(t["start"]), d(t["end"])
        if ts and te and te > ts:
            val = clamp((day - ts).days / (te - ts).days * 100)
    return val


# --------------------------------------------------------------------- apply form

def apply_updates(doc: Dict[str, Any], updates: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Terapkan record form terisi ke dokumen proyek."""
    doc = json.loads(json.dumps(doc))                      # deep copy
    doc.setdefault("history", [])
    now = today_of(doc.get("meta", {}))
    idx = {(p.get("id"), str(t.get("id", t.get("name")))): t
           for p in doc.get("projects", []) for t in p.get("tasks", [])}
    pidx = {p.get("id"): p for p in doc.get("projects", [])}
    applied = 0
    for u in updates:
        f = u.get("form")
        pid = u.get("project")
        doc["history"].append({**u, "applied_at": now.isoformat(timespec="seconds")})
        if f == "progress":
            t = idx.get((pid, str(u.get("task"))))
            if t is None:
                continue
            if u.get("progress") is not None:
                t["progress"] = clamp(float(u["progress"]))
            if u.get("effort_actual") is not None:
                t["effort_actual"] = float(u["effort_actual"])
            if u.get("blockers") is not None:
                t["blockers"] = u["blockers"]
            if u.get("notes"):
                t["notes"] = u["notes"]
            if u.get("status"):
                t["status"] = u["status"]
            if float(t.get("progress", 0)) >= 100:
                t["status"] = "done"
            applied += 1
        elif f == "monitoring":
            p = pidx.get(pid)
            if p is None:
                continue
            if u.get("kpi"):
                p["kpi"] = u["kpi"]
            if u.get("risks") is not None:
                p["risks"] = u["risks"]
            if u.get("budget_actual") is not None:
                p["budget_actual"] = float(u["budget_actual"])
            if u.get("summary"):
                p.setdefault("log", []).append({"date": u.get("date"), "summary": u["summary"],
                                                "rag": u.get("rag")})
            applied += 1
        elif f == "controlling":
            p = pidx.get(pid)
            if p is None:
                continue
            p.setdefault("actions", []).append({
                "id": u.get("id") or f"CA{len(p.get('actions', [])) + 1}",
                "issue": u.get("issue", ""), "root_cause": u.get("root_cause", ""),
                "variance": u.get("variance", {}), "action": u.get("corrective_action", ""),
                "preventive": u.get("preventive", ""), "owner": u.get("owner", ""),
                "due": u.get("due", ""), "status": u.get("status", "open")})
            applied += 1
    return {"doc": doc, "applied": applied}


# --------------------------------------------------------------------- report

def to_markdown(A: Dict[str, Any]) -> str:
    meta, P, port = A["meta"], A["projects"], A["portfolio"]
    cur = meta.get("currency", "Rp")
    L = [f"# Laporan Monitoring Proyek — {meta.get('name', '')}", "",
         f"**Per {meta['today']}** · {port['projects']} proyek · {port['tasks']} tugas  ",
         f"Status: **{port['on_track']} on-track · {port['warn']} waspada · {port['bad']} kritis** · "
         f"{port['overdue']} terlambat · {port['stalled']} stalled · "
         f"budget terpakai {port['budget_actual'] / max(1, port['budget_planned']) * 100:.0f}%", "",
         "## 1. Ringkasan per Proyek", "",
         "| Proyek | Owner | Rencana | Aktual | Var | RAG | Forecast | Slip | CPI | Budget terpakai |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for p in P:
        used = f"{p['budget_used_pct']:.0f}%" if p['budget_used_pct'] is not None else "—"
        slip = f"{p['slip_days']}h" if p['slip_days'] else "—"
        cpi = p['cpi'] if p['cpi'] else "—"
        L.append(f"| {p['name']} | {p['owner']} | {p['planned']:.0f}% | {p['progress']:.0f}% | "
                 f"{p['variance']:+.0f} | {RAG_LABEL[p['rag']]} | {p['forecast_end'] or '—'} | "
                 f"{slip} | {cpi} | {used} |")
    L += ["", "## 2. Tracking Tugas", "",
          "| Proyek | Tugas | Owner | Rencana | Aktual | Var | SPI | Telat | Status | Blocker |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for p in P:
        for t in sorted(p["tasks"], key=lambda x: x["variance"]):
            L.append(f"| {p['id']} | {t['name']} | {t['owner']} | {t['planned']:.0f}% | "
                     f"{t['actual']:.0f}% | {t['variance']:+.0f} | {t['spi']:.2f} | "
                     f"{t['overdue_days'] or '—'} | {RAG_LABEL[t['rag']]}{' +stalled' if t['stalled'] else ''} | "
                     f"{'; '.join(t['blockers']) or '—'} |")
    L += ["", "## 3. Beban per Owner", "", "| Owner | Tugas | Bobot | Kritis/Waspada |", "|---|---|---|---|"]
    for o, v in sorted(port["owners"].items(), key=lambda kv: -kv[1]["weight"]):
        L.append(f"| {o} | {v['tasks']} | {v['weight']:.0f} | {v.get('bad', 0)}/{v.get('warn', 0)} |")
    L += ["", "## 4. Insight & Tindakan", ""]
    for i, ins in enumerate(A["insights"], 1):
        icon = {"good": "✅", "warn": "⚠️", "bad": "⛔"}.get(ins.get("severity", "info"), "ℹ️")
        L.append(f"{i}. {icon} **{ins['title']}** — {ins['detail']}")
        if ins.get("action"):
            L.append(f"   → _Aksi: {ins['action']}_")
    L += ["", "## 5. Catatan Coach (Motivator Expert)", ""]
    for c in A["coach"]:
        L.append(f"### {c['owner']}  _(nada: {c['tone']})_")
        L.append(f"> {c['message']}")
        L.append(f"**Langkah 15 menit:** {c['step_15min']}")
        f = c["facts"]
        L.append(f"_Fakta: {f['tasks']} tugas · {f['done']} selesai · {f['bad']} kritis · "
                 f"{f['stalled']} stalled · rata-rata {f['avg_progress']}%_\n")
    L += ["", "---",
          "_DAN · Project Monitoring & Controlling + Motivator Expert. Planned progress = "
          "interpolasi linear; variance dalam poin persentase; SPI = aktual ÷ rencana._"]
    return "\n".join(L)


# --------------------------------------------------------------------- main

def _load(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv: Optional[Sequence[str]] = None) -> int:
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · Project Monitoring / Tracking / Progress")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_rep = sub.add_parser("report", help="hitung + tulis laporan & dashboard")
    p_rep.add_argument("projects")
    p_rep.add_argument("--out-dir", default=dl)
    p_rep.add_argument("--theme", default="")

    p_st = sub.add_parser("status", help="tabel ringkas ke stdout")
    p_st.add_argument("projects")

    p_ap = sub.add_parser("apply", help="terapkan update dari form terisi")
    p_ap.add_argument("projects")
    p_ap.add_argument("updates")
    p_ap.add_argument("--out", default="")

    p_co = sub.add_parser("coach", help="pesan motivator per owner")
    p_co.add_argument("projects")
    p_co.add_argument("--out", default="")

    a = ap.parse_args(argv)

    if a.cmd == "status":
        A = compute(_load(a.projects))
        for p in A["projects"]:
            print(f"[{RAG_LABEL[p['rag']]:8}] {p['name']:34} plan {p['planned']:5.1f}%  "
                  f"aktual {p['progress']:5.1f}%  var {p['variance']:+6.1f}  "
                  f"forecast {p['forecast_end'] or '-'}")
        for p in A["projects"]:
            for t in p["tasks"]:
                flag = {"good": "  ", "warn": "! ", "bad": "X "}[t["rag"]]
                print(f"   {flag}{t['name']:30} {t['owner']:10} {t['actual']:5.1f}% "
                      f"(plan {t['planned']:5.1f}%) {t['overdue_days'] or ''}"
                      f"{' STALLED' if t['stalled'] else ''}")
        return 0

    if a.cmd == "apply":
        doc = _load(a.projects)
        up = _load(a.updates)
        up = up if isinstance(up, list) else up.get("updates", [])
        res = apply_updates(doc, up)
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.projects)),
                                    "projects_updated.json")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(res["doc"], f, ensure_ascii=False, indent=2)
        print(f"[DAN] {res['applied']}/{len(up)} update diterapkan -> {out}")
        return 0

    doc = _load(a.projects)
    A = compute(doc)

    if a.cmd == "coach":
        out = a.out or os.path.join(dl, "coach.md")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        lines = ["# Catatan Coach — per Owner", "", f"_Per {A['meta']['today']} · "
                 f"pesan dibangun dari data monitoring, bukan kata penyemangat kosong._", ""]
        for c in A["coach"]:
            lines += [f"## {c['owner']}  _(nada: {c['tone']})_", "", f"> {c['message']}", "",
                      f"**Langkah 15 menit:** {c['step_15min']}", "",
                      f"Fakta: {c['facts']['tasks']} tugas · {c['facts']['done']} selesai · "
                      f"{c['facts']['bad']} kritis · {c['facts']['warn']} waspada · "
                      f"{c['facts']['stalled']} stalled · rata-rata {c['facts']['avg_progress']}%", ""]
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"[DAN] {len(A['coach'])} pesan coach -> {out}")
        return 0

    # report
    os.makedirs(a.out_dir, exist_ok=True)
    base = os.path.join(a.out_dir, "project_report")
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(A, f, ensure_ascii=False, indent=2)
    with open(base + ".md", "w", encoding="utf-8") as f:
        f.write(to_markdown(A))
    import make_infographic as mi
    spec = build_dashboard_spec(A)
    if a.theme:
        spec["theme"] = a.theme
    html = mi.to_html(mi.build_spec(spec), spec.get("theme", "dan"), "a3")
    with open(os.path.join(a.out_dir, "project_dashboard.html"), "w", encoding="utf-8") as f:
        f.write(html)
    port = A["portfolio"]
    print(f"[DAN] {port['projects']} proyek / {port['tasks']} tugas | "
          f"{port['on_track']} on-track, {port['warn']} waspada, {port['bad']} kritis, "
          f"{port['overdue']} terlambat, {port['stalled']} stalled")
    print(f"[DAN] -> {base}.md\n[DAN] -> {base}.json\n[DAN] -> "
          f"{os.path.join(a.out_dir, 'project_dashboard.html')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
