#!/usr/bin/env python3
"""Audit referensi silang: pastikan setiap path/nama file yang disebut di dokumen benar-benar ada."""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PKG = os.path.join(ROOT, "skills", "dan")

# pola: nama file ber-ekstensi, dan path relatif yang disebut dalam backtick/markdown.
# (?![\w]) memastikan ekstensi benar-benar berakhir di situ — tanpa ini,
# "rnd.shuffle" terbaca sebagai "rnd.sh" dan "caption.short" sebagai "caption.sh".
PAT = re.compile(
    r"(?:`|\(|\s|^|>)([\w./\-]+\.(?:md|py|json|csv|svg|html|txt|srt|sh|xlsx))(?![\w])"
)
SKIP = {".srt", ".xlsx"}          # disebut sebagai contoh format, bukan file konkret
GENERIC = {  # nama generik/placeholder yang jelas bukan path nyata di paket
    "file.csv", "data.csv", "x.csv", "a.csv", "relasi.csv", "summary.csv",
    "jaringan.json", "net.json", "file.json", "spec.json", "data.json",
    "data-spec.json", "chart.svg", "a.svg", "a.json", "a.md", "poster.svg",
    "q3.html", "brief.json", "storyboard-brief.json", "master.ai", "print.pdf",
    "web.svg", "index.html", "package.json", "requirements.txt",
    "analysis.json", "analysis.md", "summary_channel.csv", "infographic.html",
    "infographic_poster.svg", "chart_gallery.html", "graph.json", "graph.svg",
    "graph.md",
    # nama keluaran/placeholder pada contoh perintah (dibuat saat runtime, bukan file paket)
    "projects.json", "projects_updated.json", "batch.json", "update.json",
    "report.md", "report.json", "dashboard.html", "forms.html", "coach.md",
    "gambar.png", "asset.png", "relasi.csv", "session_log.jsonl", "404.html",
    "deploy-pages.yml",
    # keluaran engine xlsx/business-plan (dibuat saat runtime di folder keluaran)
    "omset_divisi.csv", "tim_achievement.csv", "kanal.csv", "stock.csv",
    "data_quality.md", "spec_infografik.json", "plan.xlsx", "mini.xlsx",
    "building.json", "massing_3d.svg", "tampak_depan.svg", "denah_L1.svg",
    # nama historis/placeholder yang sengaja disebut di dokumen
    "svg_charts.py", "berkas_ini.json", "out.md", "nota.md",
    "queue.json", "tr.json", "weekly_summary_en.md",
    # placeholder contoh pada docstring/dokumen engine AI 10-21
    "prompt.txt", "prompt_baru.md", "p.txt", "p_baru.md", "wf.json", "workflow.json",
    "workflow_run.json", "spec_asisten.json", "spec_agent.json", "system_prompt.md",
    "tools_manifest.json", "eval_set.json", "README_assistant.md", "diff.md",
    "report_lalu.json", "report_sekarang.json", "rag_index.json", "llm_obs_report.md", "digest.md", "digest_v2.md",
    "mcp.json", "claude_desktop_config.json", "out.json", "run_log.json",
    "INSTALL-OFFLINE.md", "manifest-bundle.json", "b.md",
    "deck_pimpinan.pdf.html",
    "narrative_weekly.md", "notif_slack.txt", "review_infografik.json",
    "_review.html", "arch.json",
}


def walk(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != "__pycache__"]
        for f in fn:
            if f.endswith((".md", ".py", ".json")):
                yield os.path.join(dp, f)


def candidates(text):
    out = set()
    for m in PAT.finditer(text):
        p = m.group(1)
        base = os.path.basename(p)
        if base in GENERIC or any(p.endswith(s) for s in SKIP):
            continue
        if p.startswith(".") or p.startswith(("http://", "https://")):
            continue          # daftar format seperti ".ai/.svg" bukan path
        out.add(p)
    return out


def main():
    # kumpulkan semua nama file yang benar-benar ada di workspace
    existing = set()
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in ("__pycache__", ".git")]
        for f in fn:
            existing.add(f)
            existing.add(os.path.relpath(os.path.join(dp, f), PKG).replace(os.sep, "/"))
            existing.add(os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, "/"))

    missing = []
    checked = 0
    for path in sorted(walk(PKG)):
        rel = os.path.relpath(path, ROOT)
        text = open(path, encoding="utf-8").read()
        for ref in sorted(candidates(text)):
            base = os.path.basename(ref)
            checked += 1
            # terima bila nama file-nya ada di mana pun, atau path relatifnya resolve
            hit = (ref in existing) or (base in existing) or \
                os.path.exists(os.path.join(PKG, ref)) or \
                os.path.exists(os.path.join(ROOT, ref)) or \
                os.path.exists(os.path.join(os.path.dirname(path), ref))
            if not hit:
                missing.append((rel, ref))

    print(f"referensi diperiksa : {checked}")
    print(f"referensi hilang    : {len(missing)}")
    for rel, ref in missing:
        print(f"  ✗ {rel:58} -> {ref}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
