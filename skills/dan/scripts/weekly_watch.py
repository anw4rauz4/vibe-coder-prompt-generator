#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly_watch.py — Watchdog mingguan: rilis-mode dry + deteksi drift + notifikasi.

Dirancang untuk cron Senin pagi. Melakukan:
  1. release.py --dry-run          (pastikan pipeline rilis masih utuh)
  2. pkg_health                    (skor kesehatan paket dari riwayat QA)
  3. pmo_guard pada projects.json  (drift eksekusi: tugas kritis tanpa tindakan)
  4. bandingkan 2 entri qa_history terakhir (drift paket: test turun / refs naik)
Bila ada drift → render notifikasi (channel pilihan) dan exit 1 (sinyal untuk cron/CI).
Bila sehat → exit 0 tanpa ribut.

CRON:
  0 7 * * 1 cd /path/skills/dan/scripts && python3 weekly_watch.py \
      --projects /path/projects.json --channel slack >> /path/watch.log 2>&1
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)


def drift_paket() -> List[str]:
    hist_p = os.path.join(ROOT, "skills", "dan", "qa_history.jsonl")
    if not os.path.exists(hist_p):
        return []
    hist = [json.loads(ln) for ln in open(hist_p, encoding="utf-8") if ln.strip()]
    if len(hist) < 2:
        return []
    a, b = hist[-2], hist[-1]
    msgs = []
    if (b.get("tests_pass", 0) < a.get("tests_pass", 0)):
        msgs.append(f"test lulus turun {a['tests_pass']} → {b['tests_pass']}")
    if (b.get("tests_fail", 0) > a.get("tests_fail", 0)):
        msgs.append(f"test gagal naik {a['tests_fail']} → {b['tests_fail']}")
    if (b.get("refs_missing", 0) > a.get("refs_missing", 0)):
        msgs.append(f"refs hilang naik {a['refs_missing']} → {b['refs_missing']}")
    return msgs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DAN · weekly watchdog")
    ap.add_argument("--projects", default="")
    ap.add_argument("--channel", default="stdout",
                    choices=["telegram", "slack", "email", "stdout"])
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "deliverables"))
    a = ap.parse_args(argv)

    import release as rel
    import pkg_health as ph
    import pmo_guard as pg
    import notify as nf
    import project_monitor as pm

    problems: List[str] = []
    rc = rel.main(["--version", "watch", "--dry-run"])
    if rc:
        problems.append("release dry-run gagal")
    hist = ph.load()
    score = ph.score(hist[-1]) if hist else 0
    if hist and score < 100:
        problems.append(f"skor kesehatan paket {score}/100")
    if a.projects and os.path.exists(a.projects):
        doc = json.load(open(a.projects, encoding="utf-8"))
        A = pm.compute(doc)
        viol = pg.evaluate(doc, A)
        nh = sum(1 for v in viol if v["severity"] == "high")
        if nh:
            problems.append(f"PMO guard: {nh} tugas kritis/stalled tanpa tindakan")
    problems += drift_paket()
    try:
        import narrative_trend as nt
        dlx = a.out_dir
        rcn = nt.main(["--dir", dlx, "--out", os.path.join(dlx, "narrative_trend.html")])
        if rcn:
            problems.append("narrative trend gagal mengevaluasi laporan")
    except Exception as e:                                   # pragma: no cover
        print("   ! narrative_trend:", e)

    if problems:
        msg = ("⚠️ WATCHDOG DAN menemukan drift:\n- " + "\n- ".join(problems) +
               "\nAksi: jalankan `dan.py doctor --full` lalu perbaiki sebelum rilis berikutnya.")
        if a.channel != "stdout":
            p = nf.build_payload(json.load(open(a.projects, encoding="utf-8")), None) \
                if a.projects and os.path.exists(a.projects) else None
            out = os.path.join(a.out_dir, f"notif_watchdog_{a.channel}.txt")
            body = nf.render(p, a.channel) if p else msg
            body += "\n\n" + msg
            os.makedirs(a.out_dir, exist_ok=True)
            open(out, "w", encoding="utf-8").write(body)
            print(f"[DAN] watchdog: DRIFT -> {out}")
        else:
            print(msg)
        return 1
    print(f"[DAN] watchdog: SEHAT (skor paket {score}/100, guard bersih)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
