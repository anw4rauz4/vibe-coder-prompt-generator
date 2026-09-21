#!/usr/bin/env python3
"""publish_gh.py — Publikasi web hub DAN ke GitHub Pages, 100% GRATIS.

Zero dependency (stdlib). Dua perintah:
  python3 publish_gh.py prepare [--out site]    → bangun folder siap push (+ site.zip)
  python3 publish_gh.py guide   [--repo U/N]    → cetak panduan GitHub gratis

Tanpa argumen = prepare + guide. Panduan lengkap: DEPLOY-GITHUB.md (root repo).
Opsi A (repo situs saja, manual) & opsi B (repo penuh + Actions deploy-pages.yml,
otomatis tiap push). Keduanya gratis: subdomain username.github.io, tanpa kartu kredit.
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PAKET = os.path.dirname(HERE)                    # .../skills/dan
ROOT = os.path.dirname(os.path.dirname(PAKET))   # root repo
DELIV = os.path.join(ROOT, "deliverables")

NOJEKYLL = ""
P404 = ("<!doctype html><html lang=id><meta charset=utf-8>"
        "<title>DAN Hub</title><meta http-equiv=refresh content='0; url=./index.html'>"
        "<body style='font-family:system-ui;padding:40px;text-align:center'>"
        "<p>Memuat… <a href='./index.html'>DAN Hub</a></p>")
SITE_README = """# DAN Web Hub (situs ter-generate)

Dibangun otomatis oleh `publish_gh.py prepare` dari repo utama (skills/dan).
Hosting gratis: GitHub Pages — jangan edit manual; ubah sumber lalu prepare ulang.
"""


def prepare(out: str | None = None) -> dict:
    """Bangun folder siap-push: index.html + files/ + .nojekyll + 404 + README + zip."""
    import make_web
    out = os.path.abspath(out or os.path.join(ROOT, "site"))
    if os.path.isdir(out):
        shutil.rmtree(out)
    r = make_web.bangun(out)

    # tautan unduhan di situs memakai "../<file>" (layout serve.py);
    # di Pages root, artefak hidup di files/ → patch href.
    idx = os.path.join(out, "index.html")
    html = open(idx, encoding="utf-8").read()
    html = html.replace('href="../', 'href="files/')
    with open(idx, "w", encoding="utf-8") as f:
        f.write(html)

    files = os.path.join(out, "files")
    os.makedirs(files, exist_ok=True)
    copied = []
    for u in make_web.kumpul_unduhan():
        src = os.path.join(DELIV, u["file"])
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(files, u["file"]))
            copied.append(u["file"])

    with open(os.path.join(out, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write(NOJEKYLL)
    with open(os.path.join(out, "404.html"), "w", encoding="utf-8") as f:
        f.write(P404)
    with open(os.path.join(out, "README.md"), "w", encoding="utf-8") as f:
        f.write(SITE_README)

    zip_path = shutil.make_archive(out, "zip", root_dir=out)
    return {"out": out, "index": r["path"], "bytes": r["bytes"],
            "versi": r["versi"], "files": copied, "zip": zip_path}


def guide_text(repo: str = "") -> str:
    r = repo or "USERNAME/dan-hub"
    user = r.split("/")[0] if "/" in r else "USERNAME"
    nama = r.split("/")[1] if "/" in r else "dan-hub"
    url = "https://%s.github.io/%s/" % (user.lower() if user != "USERNAME" else "USERNAME", nama)
    return f"""PANDUAN PUBLIKASI GRATIS — GitHub Pages (Rp0, tanpa kartu kredit)
================================================================
Yang gratis: akun GitHub Free · repo publik · hosting Pages (subdomain
{url if repo else 'username.github.io/…'} · ~1 GB) · GitHub Actions utk repo publik.
TIDAK perlu: domain berbayar, GitHub Pro, layanan pihak ketiga.

A) MANUAL — repo situs saja (paling sederhana)
   1. Siapkan folder situs:
        python3 skills/dan/scripts/publish_gh.py prepare --out site
   2. Buat repo PUBLIK kosong di github.com/new  (nama: {nama}, tanpa README)
   3. Push (butuh git):
        cd site && git init -b main && git add -A && git commit -m "DAN hub v"
        git remote add origin https://github.com/{r}.git && git push -u origin main
      TANPA git? buka repo → 'uploading an existing file' → unggah isi site.zip
      (dibuat otomatis di sebelah folder site/ oleh perintah prepare).
   4. Repo → Settings → Pages → 'Deploy from a branch' → branch main, folder / (root) → Save.
   5. Tunggu 1–2 menit → situs live di {url if repo else 'https://USERNAME.github.io/' + nama + '/'}

B) OTOMATIS — repo penuh + Actions (sekali setup, deploy tiap push)
   1. Push SELURUH proyek ini ke repo publik (mis. {r}).
   2. Repo → Settings → Pages → Build and deployment → Source: 'GitHub Actions'.
   3. Selesai — workflow .github/workflows/deploy-pages.yml membangun
      (publish_gh.py prepare --out _site) lalu deploy tiap push ke main.
      Setelah `dan.py release`, cukup `git push` → situs ter-update sendiri.

UPDATE RUTIN
   A: prepare ulang → git add -A && git commit && git push
   B: git push (Actions yang rebuild)

CEK BIAYA: seluruh alur di atas gratis. Upgrade (domain custom/pro) nanti saja,
setelah semua dipastikan OK. Detail + troubleshooting: DEPLOY-GITHUB.md
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="publish_gh.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("prepare")
    p.add_argument("--out", default="")
    g = sub.add_parser("guide")
    g.add_argument("--repo", default="", help="USERNAME/NAMA-REPO (untuk URL akurat)")
    a = ap.parse_args(argv)

    if a.cmd == "guide":
        print(guide_text(a.repo))
        return 0
    outdir = getattr(a, "out", "") or None
    r = prepare(outdir)
    print("✓ Folder siap push: %s (v%s, %d KB, %d artefak: %s)"
          % (r["out"], r["versi"], r["bytes"] // 1024, len(r["files"]), ", ".join(r["files"])))
    print("✓ Arsip unggah-web (tanpa git): %s" % r["zip"])
    if a.cmd != "prepare":
        print()
        print(guide_text(""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
