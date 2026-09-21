#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
notify.py — Notifikasi ritme mingguan yang mengisi dirinya sendiri.

Merangkai pesan dari: weekly summary (angka + 3 keputusan), status PMO guard,
dan diff mingguan bila ada — lalu merender ke format channel:
  telegram | slack | email | stdout
TANPA mengirim apa pun (tidak ada jaringan/secret di engine): keluaran berupa berkas
pesan + contoh perintah kirim (curl) dengan placeholder token yang Anda isi sendiri.

PAKAI
  python3 notify.py --projects projects.json --updates batch.json \
      --channel slack --out deliverables/notif_slack.txt
  python3 notify.py --projects projects.json --channel telegram --print-curl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import project_monitor as pm   # noqa: E402
import weekly_run as wr        # noqa: E402
import pmo_guard as pg         # noqa: E402

ICON = {"good": "🟢", "warn": "🟡", "bad": "🔴"}


def build_payload(doc: Dict[str, Any], updates: Optional[List[Dict]],
                  lang: str = "id") -> Dict[str, Any]:
    if updates:
        doc = pm.apply_updates(doc, updates)["doc"]
    A = pm.compute(doc)
    viol = pg.evaluate(doc, A)
    n_high = sum(1 for v in viol if v["severity"] == "high")
    decs = wr.pick_decisions(A, None)[:3]
    focus = wr.pick_focus(A)[:3]
    po = A["portfolio"]
    return {
        "title": f"Ringkasan mingguan — {A['meta'].get('name', 'Portofolio')}",
        "period": A["meta"].get("today", ""),
        "status": "🔴 PERLU TINDAKAN" if n_high else "🟢 TERKENDALI",
        "guard": {"high": n_high,
                  "warn": sum(1 for v in viol if v["severity"] == "warn"),
                  "top": viol[:3]},
        "numbers": [
            f"{po['on_track']}/{po['tasks']} tugas on-track",
            f"{po['bad']} kritis · {po['stalled']} stalled · {po['overdue']} terlambat",
            f"budget terpakai {po['budget_actual'] / max(1, po['budget_planned']) * 100:.0f}%",
        ],
        "projects": [{"name": p["name"], "progress": p["progress"], "planned": p["planned"],
                      "rag": p["rag"]} for p in A["projects"]],
        "decisions": decs, "focus": focus, "lang": lang,
    }


def render(p: Dict[str, Any], channel: str) -> str:
    if channel == "slack":
        L = [f"*{p['title']}* — {p['period']}  •  status: {p['status']}", ""]
        L += [f"• {n}" for n in p["numbers"]]
        L += ["", "*Proyek:*"]
        L += [f"• {ICON[x['rag']]} {x['name']}: {x['progress']:.0f}% "
              f"(rencana {x['planned']:.0f}%)" for x in p["projects"]]
        L += ["", "*Keputusan minggu ini:*"]
        L += [f"{i}. {d['keputusan']} → _{d['aksi'][:90]}_" for i, d in enumerate(p["decisions"], 1)]
        if p["guard"]["high"]:
            L += ["", f":warning: PMO guard: {p['guard']['high']} temuan high — "
                      + "; ".join(v["message"][:70] for v in p["guard"]["top"])]
        return "\n".join(L)
    if channel == "telegram":
        L = [f"<b>{p['title']}</b> — {p['period']}", f"Status: {p['status']}", ""]
        L += [f"• {n}" for n in p["numbers"]]
        L += ["", "<b>Proyek:</b>"]
        L += [f"• {ICON[x['rag']]} {x['name']}: {x['progress']:.0f}% "
              f"(rencana {x['planned']:.0f}%)" for x in p["projects"]]
        L += ["", "<b>Keputusan:</b>"]
        L += [f"{i}. {d['keputusan']}" for i, d in enumerate(p["decisions"], 1)]
        if p["guard"]["high"]:
            L += ["", f"⚠️ Guard: {p['guard']['high']} temuan high"]
        return "\n".join(L)
    if channel == "email":
        rows = "".join(f"<tr><td>{ICON[x['rag']]}</td><td>{x['name']}</td>"
                       f"<td>{x['progress']:.0f}%</td><td>{x['planned']:.0f}%</td></tr>"
                       for x in p["projects"])
        dec = "".join(f"<li><b>{d['keputusan']}</b><br><small>{d['aksi'][:140]}</small></li>"
                      for d in p["decisions"])
        return (f"Subject: {p['title']} ({p['period']}) — {p['status']}\n\n"
                f"<html><body style='font-family:sans-serif'>"
                f"<h2>{p['title']}</h2><p>Status: <b>{p['status']}</b></p><ul>"
                + "".join(f"<li>{n}</li>" for n in p["numbers"]) +
                f"</ul><table border=1 cellpadding=6><tr><th></th><th>Proyek</th>"
                f"<th>Progres</th><th>Rencana</th></tr>{rows}</table>"
                f"<h3>Keputusan minggu ini</h3><ol>{dec}</ol>"
                f"<p><small>Dikirim otomatis oleh DAN notify.py · guard high: "
                f"{p['guard']['high']}</small></p></body></html>")
    # stdout / plain
    L = [p["title"], f"periode {p['period']} · status {p['status']}", ""]
    L += [f"- {n}" for n in p["numbers"]]
    L += ["", "Proyek:"]
    L += [f"  {ICON[x['rag']]} {x['name']}: {x['progress']:.0f}% (rencana {x['planned']:.0f}%)"
          for x in p["projects"]]
    L += ["", "Keputusan minggu ini:"]
    L += [f"  {i}. {d['keputusan']} | aksi: {d['aksi'][:100]}"
          for i, d in enumerate(p["decisions"], 1)]
    L += ["", "Fokus eksekusi:"]
    L += [f"  - {f['task']} ({f['owner']}) var {f['variance']:+.0f}" for f in p["focus"]]
    L += ["", f"PMO guard: {p['guard']['high']} high / {p['guard']['warn']} warn"]
    return "\n".join(L)


CURL = {
    "telegram": 'curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" '
                '-d chat_id=<CHAT_ID> -d parse_mode=HTML --data-urlencode text=@<FILE>',
    "slack": 'curl -s -X POST <SLACK_WEBHOOK_URL> -H \'content-type: application/json\' '
             '-d \'{"text": $(python3 -c "import json,sys;print(json.dumps(open(sys.argv[1]).read()))" <FILE>)}\'',
    "email": '# kirim via SMTP internal Anda; isi berkas sudah berupa email siap kirim',
}


def send(channel: str, msg: str) -> int:
    """Kirim SUNGGUHAN hanya bila kredensial ada di environment (tidak pernah disimpan)."""
    if channel == "telegram":
        tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
        if not (tok and chat):
            print("[DAN] kirim dibatalkan: set TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID "
                  "di environment (jangan di file).")
            return 2
        data = json.dumps({"chat_id": chat, "parse_mode": "HTML", "text": msg}
                          ).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendMessage", data=data,
            headers={"Content-Type": "application/json"})
    elif channel == "slack":
        url = os.environ.get("SLACK_WEBHOOK_URL")
        if not url:
            print("[DAN] kirim dibatalkan: set SLACK_WEBHOOK_URL di environment.")
            return 2
        data = json.dumps({"text": msg}).encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json"})
    elif channel == "email":
        host, port = os.environ.get("SMTP_HOST"), os.environ.get("SMTP_PORT", "587")
        user, pw = os.environ.get("SMTP_USER"), os.environ.get("SMTP_PASS")
        frm, to = os.environ.get("MAIL_FROM"), os.environ.get("MAIL_TO")
        if not (host and frm and to):
            print("[DAN] kirim dibatalkan: set SMTP_HOST, MAIL_FROM, MAIL_TO "
                  "(+ SMTP_USER/SMTP_PASS bila perlu) di environment.")
            return 2
        import smtplib
        from email.mime.text import MIMEText
        m = MIMEText(msg, "html" if "<html" in msg else "plain", "utf-8")
        m["Subject"] = msg.splitlines()[0].replace("Subject: ", "")[:120]
        m["From"], m["To"] = frm, to
        with smtplib.SMTP(host, int(port)) as srv:
            srv.starttls()
            if user and pw:
                srv.login(user, pw)
            srv.sendmail(frm, [to], m.as_string())
        print("[DAN] email terkirim ke", to)
        return 0
    else:
        print("[DAN] channel stdout tidak mengirim apa pun.")
        return 0
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"[DAN] terkirim via {channel} (HTTP {r.status})")
            return 0
    except Exception as e:
        print(f"[DAN] gagal kirim via {channel}: {e}")
        return 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · weekly notification builder")
    ap.add_argument("--projects", required=True)
    ap.add_argument("--updates", default="")
    ap.add_argument("--channel", default="stdout",
                    choices=["telegram", "slack", "email", "stdout"])
    ap.add_argument("--lang", default="id")
    ap.add_argument("--out", default="")
    ap.add_argument("--print-curl", action="store_true")
    ap.add_argument("--send", action="store_true",
                    help="kirim sungguhan; kredensial HANYA dari environment")
    a = ap.parse_args(argv)
    doc = json.load(open(a.projects, encoding="utf-8"))
    ups = None
    if a.updates and os.path.exists(a.updates):
        u = json.load(open(a.updates, encoding="utf-8"))
        ups = u if isinstance(u, list) else u.get("updates", [])
    p = build_payload(doc, ups, a.lang)
    msg = render(p, a.channel)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        open(a.out, "w", encoding="utf-8").write(msg)
        print(f"[DAN] notif {a.channel} -> {a.out} ({len(msg)} karakter)")
    else:
        print(msg)
    if a.print_curl:
        print("\n[DAN] contoh kirim (isi secret Anda sendiri):")
        print("   ", CURL.get(a.channel, "-"))
    if a.send:
        return send(a.channel, msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
