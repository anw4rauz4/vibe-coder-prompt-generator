#!/usr/bin/env python3
"""
_test_all.py — Smoke test seluruh pipeline DAN.
Jalankan sebelum menyerahkan hasil:  python3 _test_all.py

Memeriksa:
  1. parser angka (dan_analytics.self_test)
  2. semua tipe chart di svg_charts menghasilkan XML valid
  3. mode SPEC merender semua chart dari data-spec.example.json tanpa error
  4. mode AUTO menghasilkan infografik dari analysis.json
  5. storyboard deterministik & total durasi sesuai brief
  6. graph analyst cocok dengan networkx (bila terpasang)
  7. tidak ada elemen keluar kanvas pada semua artefak
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

import svg_charts as sc            # noqa: E402
import dan_analytics as da         # noqa: E402
import make_infographic as mi      # noqa: E402
import graph_analyst as ga         # noqa: E402
import storyboard as sb            # noqa: E402

PASS, FAIL = [], []


def chk(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (f" — {detail}" if detail else ""))


def _tpl(name: str) -> str:
    """Lokasi template: filesystem dulu, lalu dari dalam .pyz (zipimport)."""
    cands = [os.path.join(ROOT, "skills", "dan", "templates", name),
             os.path.join(HERE, "templates", name)]
    for c in cands:
        if os.path.exists(c):
            return c
    import zipfile
    import tempfile as _tf2
    for sp in sys.path:
        if str(sp).endswith(".pyz") and zipfile.is_zipfile(sp):
            z = zipfile.ZipFile(sp)
            entry = "templates/" + name
            if entry in z.namelist():
                tmp = os.path.join(_tf2.gettempdir(), "dan_pyz_" + name)
                with open(tmp, "wb") as f:
                    f.write(z.read(entry))
                return tmp
    raise FileNotFoundError(name)


def valid_svg(s: str) -> bool:
    try:
        ET.fromstring(s)
        return True
    except Exception:
        return False


def main() -> int:
    print("\n[1] Parser angka")
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = da.self_test()
    chk("dan_analytics.self_test()", rc == 0, buf.getvalue().strip().splitlines()[-1])

    print("\n[2] Semua tipe chart -> XML valid")
    samples = {
        "bar": lambda: sc.bar([("A", 12), ("B", 30), ("C", 7)], title="t"),
        "hbar": lambda: sc.hbar([("A", 12), ("B", 30)], title="t"),
        "stacked_bar": lambda: sc.stacked_bar(["Q1", "Q2"], {"a": [1, 2], "b": [3, 4]}, title="t"),
        "line": lambda: sc.line([("A", 1), ("B", 5), ("C", 3)], title="t"),
        "line+gap": lambda: sc.line(compare={"x": [1, 2, None], "y": [None, 2, 4]},
                                    x_labels=["a", "b", "c"], title="t"),
        "area": lambda: sc.area([1, 4, 2, 8], title="t"),
        "donut": lambda: sc.donut([("A", 5), ("B", 3)], center_value="8", center_label="x"),
        "pie": lambda: sc.pie([("A", 5), ("B", 3)]),
        "funnel": lambda: sc.funnel([("A", 100), ("B", 40), ("C", 10)]),
        "radar": lambda: sc.radar({"k": [3, 5, 4]}, ["a", "b", "c"]),
        "scatter": lambda: sc.scatter([(1, 2), (3, 4), (5, 3)]),
        "heatmap": lambda: sc.heatmap(["r1", "r2"], ["c1", "c2"], [[1, 2], [3, 4]]),
        "waterfall": lambda: sc.waterfall([("A", 10), ("B", -3), ("C", 13)]),
        "gauge": lambda: sc.gauge(65, 100, "label"),
        "network": lambda: sc.network([{"id": "a"}, {"id": "b"}], [("a", "b", 2)]),
        "sparkline": lambda: sc.sparkline([1, 3, 2, 5]),
        "kosong": lambda: sc.bar([]),
        "tema-dan": lambda: sc.bar([("A", 1)], th="dan"),
        "tema-light": lambda: sc.bar([("A", 1)], th="light"),
        "tema-neon": lambda: sc.bar([("A", 1)], th="neon"),
        "tema-mono": lambda: sc.bar([("A", 1)], th="mono"),
        "tema-custom": lambda: sc.bar([("A", 1)], th={"accent": "#FF0000"}),
        "loc-en": lambda: sc.bar([("A", 12345)], loc="en"),
    }
    for name, fn in samples.items():
        try:
            chk(f"chart {name}", valid_svg(fn()))
        except Exception as e:
            chk(f"chart {name}", False, repr(e))

    print("\n[3] Mode SPEC (data-spec.example.json)")
    spec_path = _tpl("data-spec.example.json")
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    n_ok = n_fail = 0
    for s in spec.get("sections", []):
        if s.get("type") != "chart":
            continue
        out = mi.render_chart(s, "dan", "id")
        if out.startswith("<svg") and valid_svg(out):
            n_ok += 1
        else:
            n_fail += 1
            print("        ->", s.get("chart"), ":", re.sub(r"<[^>]+>", "", out)[:100])
    chk("semua chart spec ter-render", n_fail == 0, f"{n_ok}/{n_ok + n_fail}")
    B = mi.build_spec(spec)
    html = mi.to_html(B, "dan", "a3")
    chk("HTML spec self-contained", "<script" not in html and "cdn" not in html.lower())

    print("\n[4] Mode AUTO (analysis.json)")
    an = os.path.join(ROOT, "deliverables", "analysis.json")
    if os.path.exists(an):
        with open(an, encoding="utf-8") as f:
            A = json.load(f)
        B2 = mi.build_auto(A, "dan", "id")
        h2 = mi.to_html(B2, "dan", "a3")
        nsvg = len(re.findall(r"<svg.*?</svg>", h2, re.S))
        chk("infografik AUTO punya chart", nsvg >= 8, f"{nsvg} svg")
        chk("semua svg AUTO valid", all(valid_svg(x) for x in re.findall(r"<svg.*?</svg>", h2, re.S)))
        chk("health score terisi", 0 <= A.get("health_score", -1) <= 100, str(A.get("health_score")))
        chk("insight punya aksi", all(i.get("action") for i in A["insights"]))
        tot = sum(x["value"] for x in A["funnel"]) if A.get("funnel") else 0
        chk("funnel menurun", tot > 0 and A["funnel"][0]["value"] >= A["funnel"][-1]["value"])
    else:
        print("  skip  analysis.json tidak ada (lingkungan minimal/pyz)")

    print("\n[5] Storyboard")
    brief = {"product": "Tes Produk", "audience": "audiens uji", "platform": "tiktok",
             "duration": 30, "structure": "pas", "goal": "konversi", "tone": "friendly",
             "problem": "masalah uji", "result": "hasil uji", "cta": "klik sekarang"}
    B3 = sb.build(brief)
    tot = round(sum(s["duration"] for s in B3["shots"]), 2)
    chk("total durasi = brief", abs(tot - 30.0) < 0.35, f"{tot}s")
    chk("shot punya prompt image", all(s["image_prompt"] for s in B3["shots"]))
    chk("shot punya prompt video", all(s["video_prompt"] for s in B3["shots"]))
    chk("VO kalimat utuh", all(s["vo"].endswith((".", "!", "?")) for s in B3["shots"]))
    chk("waktu shot tidak tumpang tindih",
        all(B3["shots"][i]["end"] <= B3["shots"][i + 1]["start"] + 1e-9
            for i in range(len(B3["shots"]) - 1)))
    srt = sb.make_srt(B3["shots"])
    chk("SRT terbentuk", "-->" in srt and srt.strip().startswith("1"))
    chk("5 varian hook", len(B3["hooks"]) == 5)
    det1 = json.dumps(sb.build(brief), ensure_ascii=False, sort_keys=True, default=str)
    det2 = json.dumps(sb.build(brief), ensure_ascii=False, sort_keys=True, default=str)
    d1 = re.sub(r'"generated_at":\s*"[^"]+"', "", det1)
    d2 = re.sub(r'"generated_at":\s*"[^"]+"', "", det2)
    chk("deterministik", d1 == d2)

    print("\n[6] Graph analyst")
    g = ga.demo_graph()
    R = ga.analyze(g)
    chk("analisa graph sukses", R["meta"]["nodes"] == 12 and R["meta"]["edges"] == 16)
    chk("pagerank berjumlah 1", abs(sum(n["pagerank"] for n in R["nodes"]) - 1.0) < 0.02,
        f"{sum(n['pagerank'] for n in R['nodes']):.3f}")
    chk("komunitas terisi", len(R["communities"]) >= 1)
    chk("svg graph valid", valid_svg(ga.to_svg(R, g)))
    try:
        import networkx as nx
        G = nx.Graph()
        for a, b, w in g.edges:
            G.add_edge(a, b, weight=w)
        ref = {"b": nx.betweenness_centrality(G), "c": nx.closeness_centrality(G),
               "e": nx.eigenvector_centrality(G, weight="weight", max_iter=3000),
               "p": nx.pagerank(G)}
        mine = {"b": g.betweenness(), "c": g.closeness(), "e": g.eigenvector(), "p": g.pagerank()}
        dev = max(abs(mine[k][n] - ref[k][n]) for k in ref for n in G.nodes)
        chk("cocok dengan networkx", dev < 0.02, f"deviasi maks {dev:.4f}")
    except ImportError:
        print("  skip  networkx tidak terpasang (fallback pure-python tetap dipakai)")

    print("\n[7] Layout artefak")
    dlv = os.path.join(ROOT, "deliverables")
    checked = overflow = unparsed = 0
    for fnm in sorted(os.listdir(dlv)) if os.path.isdir(dlv) else []:
        if not fnm.endswith((".html", ".svg")):
            continue
        path = os.path.join(dlv, fnm)
        roots = []
        if fnm.endswith(".svg"):
            # file SVG bisa berisi <svg> bersarang (poster) -> parse utuh
            try:
                roots = [ET.parse(path).getroot()]
            except ET.ParseError as e:
                unparsed += 1
                print(f"        -> {fnm}: XML tidak valid ({e})")
        else:
            txt = open(path, encoding="utf-8").read()
            for s in re.findall(r"<svg.*?</svg>", txt, re.S):
                try:
                    roots.append(ET.fromstring(s))
                except ET.ParseError as e:
                    unparsed += 1
                    print(f"        -> {fnm}: fragmen SVG tidak valid ({e})")
        for root in roots:
            # setiap <svg> (root maupun bersarang) = satu kanvas; cek text anak langsungnya
            for canvas in root.iter():
                if canvas.tag.split("}")[-1] != "svg":
                    continue
                W = float(canvas.get("width") or 0)
                H = float(canvas.get("height") or 0)
                if not W or not H:
                    continue
                checked += 1
                for sub in canvas:
                    if sub.tag.split("}")[-1] != "text":
                        continue
                    x, y = float(sub.get("x", 0)), float(sub.get("y", 0))
                    if not (-2 <= x <= W + 2 and -2 <= y <= H + 2):
                        overflow += 1
                        print(f"        -> {fnm}: teks keluar kanvas ({x:.0f},{y:.0f}) "
                              f"vs {W:.0f}x{H:.0f} = {sub.text!r}")
    chk("artefak bisa diparse", unparsed == 0, f"{unparsed} bermasalah")
    chk("tidak ada teks keluar kanvas", overflow == 0, f"{checked} svg diperiksa")

    print("\n[8] fit_asset (rasio platform)")
    try:
        import fit_asset as fa
        from PIL import Image
        import tempfile
        src = Image.new("RGB", (2048, 2048), (200, 180, 160))
        tmp = os.path.join(tempfile.gettempdir(), "dan_fit_src.png")
        src.save(tmp)
        for ratio, want in (("9:16", (1080, 1920)), ("4:5", (1080, 1350)),
                            ("16:9", (1920, 1080)), ("1:1", (1080, 1080))):
            rw, rh = fa.parse_ratio(ratio)
            got = fa.fit(src, rw, rh, mode="crop", size=fa.PRESETS[ratio])
            chk(f"fit {ratio}", got.size == want, f"{got.size[0]}x{got.size[1]}")
        got_pad = fa.fit(src, *fa.parse_ratio("4:5"), mode="pad",
                         size=fa.PRESETS["4:5"])
        chk("fit pad 4:5", got_pad.size == fa.PRESETS["4:5"])
        # rasio hasil harus persis sama dengan target
        for ratio in ("9:16", "4:5", "16:9"):
            rw, rh = fa.parse_ratio(ratio)
            g = fa.fit(src, rw, rh, mode="crop", size=fa.PRESETS[ratio])
            chk(f"rasio tepat {ratio}", abs(g.size[0] / g.size[1] - rw / rh) < 0.002)
        os.remove(tmp)
    except ImportError:
        print("  skip  Pillow tidak terpasang (fit_asset opsional)")

    print("\n[9] Project monitoring / tracking / progress / forms")
    import project_monitor as pm
    import make_forms as mf
    tpl = _tpl("projects.example.json")
    with open(tpl, encoding="utf-8") as f:
        doc = json.load(f)
    A = pm.compute(doc)
    port = A["portfolio"]
    chk("compute portofolio", port["projects"] == 3 and port["tasks"] == 19,
        f"{port['projects']} proyek/{port['tasks']} tugas")
    chk("deteksi stalled", port["stalled"] >= 1, f"{port['stalled']}")
    chk("deteksi terlambat", port["overdue"] >= 1, f"{port['overdue']}")
    chk("deteksi kritis", port["bad"] >= 1, f"{port['bad']}")
    chk("RAG konsisten", port["on_track"] + port["warn"] + port["bad"] == port["tasks"])
    chk("forecast & slip terisi", all(p.get("forecast_end") for p in A["projects"]))
    chk("earned value terisi",
        all((p["cpi"] is not None) for p in A["projects"] if p["budget_actual"]))
    chk("coach per owner", len(A["coach"]) == len({t["owner"] for p in A["projects"]
                                                   for t in p["tasks"]}),
        f"{len(A['coach'])} owner")
    chk("coach berbasis data", all(c["step_15min"] and c["message"] for c in A["coach"]))
    # apply update
    upd = [{"form": "progress", "project": "PRJ-01", "task": "T5",
            "date": "2026-09-16", "progress": 62, "blockers": []}]
    res = pm.apply_updates(doc, upd)
    t5 = [t for p in res["doc"]["projects"] if p["id"] == "PRJ-01"
          for t in p["tasks"] if t["id"] == "T5"][0]
    chk("apply progress", t5["progress"] == 62 and res["applied"] == 1)
    chk("apply menambah history", any(h.get("form") == "progress" and h.get("progress") == 62
                                      for h in res["doc"]["history"]))
    upd2 = [{"form": "controlling", "project": "PRJ-01", "issue": "x",
             "corrective_action": "y", "owner": "Dewi", "due": "2026-09-20"}]
    res2 = pm.apply_updates(res["doc"], upd2)
    chk("apply controlling masuk actions",
        any(a.get("issue") == "x" for p in res2["doc"]["projects"]
            if p["id"] == "PRJ-01" for a in p.get("actions", [])))
    # dashboard spec -> html
    spec = pm.build_dashboard_spec(A)
    html = mi.to_html(mi.build_spec(spec), "dan", "a3")
    nsvg = len(re.findall(r"<svg.*?</svg>", html, re.S))
    chk("dashboard punya chart", nsvg >= 5, f"{nsvg} svg")
    chk("dashboard svg valid", all(valid_svg(x) for x in re.findall(r"<svg.*?</svg>", html, re.S)))
    chk("dashboard sebut gantt", 'Timeline &amp; Tracking Tugas' in html or "Tracking Tugas" in html)
    # forms.html
    import tempfile
    fout = os.path.join(tempfile.gettempdir(), "dan_forms.html")
    mf.main(["--projects", tpl, "--out", fout])
    fh = open(fout, encoding="utf-8").read()
    chk("forms self-contained", "http://" not in fh and "https://" not in fh)
    chk("forms 3 tab", all(x in fh for x in ("p-progress", "p-monitoring", "p-controlling")))
    chk("forms contoh tertanam", "__SAMPLE_JSON__" not in fh and '"projects"' in fh)
    chk("forms js ada", fh.count("<script>") == 1 and "addProgress" in fh)
    os.remove(fout)

    print("\n[10] Software architecture & architectural design")
    import arch_advisor as aa
    import arch_design as ad
    import tempfile as _tf
    # scaffold: semua bahasa × pola tersedia menghasilkan file & kode valid
    combos = [("python", "api"), ("python", "cli"), ("node", "worker"),
              ("typescript", "api"), ("go", "cli"), ("php", "api")]
    tmpd = _tf.mkdtemp(prefix="dan_scaffold_")
    for lang, pat in combos:
        r = aa.scaffold(lang, pat, "t_" + lang, os.path.join(tmpd, f"{lang}_{pat}"))
        chk(f"scaffold {lang}/{pat}", "files" in r and len(r["files"]) >= 5,
            f"{len(r.get('files', []))} file")
    pyf = os.path.join(tmpd, "python_api", "t_python", "main.py")
    if not os.path.exists(pyf):
        pyf = [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.join(tmpd, "python_api"))
               for f in fn if f == "main.py"][0]
    import ast as _ast
    _ast.parse(open(pyf, encoding="utf-8").read())
    chk("scaffold python valid syntax", True)
    nj = os.path.join(tmpd, "node_worker", "package.json")
    json.load(open(nj, encoding="utf-8"))
    chk("scaffold node package.json valid", True)
    # review: deteksi rahasia & todo & skor dalam rentang
    coddir = os.path.join(tmpd, "cod")
    os.makedirs(coddir, exist_ok=True)
    # secret palsu dirakit saat runtime agar repo tidak menyimpan literal yang
    # terlihat seperti rahasia bagi scanner; file temp tetap memuatnya untuk diuji.
    fake = "API_" + "KEY = " + '"sk-' + "abc123" + "secret999" + '"'
    open(os.path.join(coddir, "a.py"), "w").write(
        ("import os\n" + fake + "\n# TODO: fix\nprint(\"x\")\n") * 3)
    rv = aa.review(coddir)
    chk("review deteksi rahasia", rv["secrets"] >= 1, f"{rv['secrets']}")
    chk("review deteksi todo", rv["todos"] >= 1)
    chk("review skor turun karena rahasia", rv["score"] <= 60, f"{rv['score']}")
    chk("review punya kelebihan & kekurangan",
        isinstance(rv["kelebihan"], list) and isinstance(rv["kekurangan"], list))
    # compare: winner selalu salah satu opsi & skor konsisten
    c = aa.compare("pattern", "monolith", "microservices",
                   {"team": 4, "scale": "medium", "deadline": "ketat", "budget": "rendah"})
    chk("compare menghasilkan winner valid", c["winner"] in ("monolith", "microservices"))
    chk("compare skor = jumlah kriteria", c["a"]["total"] == sum(c["a"]["scores"].values()))
    ce = aa.compare("db", "tidakada", "postgresql", {})
    chk("compare opsi tak dikenal -> error ramah", "error" in ce)
    # arch design
    btpl = _tpl("building.example.json")
    bdoc = json.load(open(btpl, encoding="utf-8"))
    A = ad.compute(bdoc, 26)
    chk("arch compute lantai & ruang", len(A["floors"]) == 2 and A["totals"]["rooms"] == 12)
    chk("arch tanpa overlap ruang", all(
        not (a["x"] < b["x"] + b["w"] and b["x"] < a["x"] + a["w"]
             and a["y"] < b["y"] + b["d"] and b["y"] < a["y"] + a["d"])
        for fl in A["floors"] for i, a in enumerate(fl["rooms"]) for b in fl["rooms"][i + 1:]))
    chk("arch bbox konsisten", all(
        abs(max(r["x"] + r["w"] for r in fl["rooms"]) - fl["width"]) < 0.01
        for fl in A["floors"]))
    chk("arch KDB/KLB terhitung", 0 < A["compliance"]["kdb"] <= 100
        and A["compliance"]["kdb_ok"] is not None)
    chk("arch RAB total = jumlah komponen",
        abs(sum(r["amount"] for r in A["rab"]) - A["rab_total"]) < 1)
    chk("arch prompt render ada", A["prompts"]["interior"] and A["prompts"]["exterior"])
    for nm, svg in (("denah", ad.floorplan_svg(A["floors"][0], "dan", 26)),
                    ("massing", ad.isometric_svg(A, "dan", 26)),
                    ("tampak", ad.elevation_svg(A, "dan", 26))):
        chk(f"arch svg {nm} valid", valid_svg(svg))
    shutil.rmtree(tmpd, ignore_errors=True)

    print("\n[11] Property-based tests (invariant acak ber-seed)")
    import props_test as pt
    count, fails = pt.run_all(n=40, seed=42)
    chk("property tests tanpa pelanggaran", not fails,
        f"{count} pemeriksaan" + (f"; gagal: {fails[:2]}" if fails else ""))
    chk("nice_ticks selalu mencakup rentang", all(
        (lambda t, lo, hi: t[0] <= lo and t[-1] >= hi)(
            __import__("svg_charts").nice_ticks(lo, lo + span), lo, lo + span)
        for lo, span in ((-737.9, 1884.2), (0, 1146.3), (54.9, 4831.4), (-5, 7))))

    print("\n[12] PMO guard & slide deck")
    import pmo_guard as pg
    import make_slides as ms
    raw = json.load(open(tpl, encoding="utf-8"))
    v1 = pg.evaluate(raw, pm.compute(raw))
    chk("guard mendeteksi tugas kritis tanpa tindakan",
        any(x["code"] == "G1" and "PRJ-02" in x["message"] for x in v1),
        f"{len(v1)} pelanggaran")
    fixed = json.loads(json.dumps(raw))
    for p in fixed["projects"]:
        if p["id"] == "PRJ-02":
            p.setdefault("actions", []).append(
                {"issue": "migrasi", "action": "pecah tugas", "owner": "Budi",
                 "due": "2026-09-20", "status": "open"})
    fixed["history"].append({"form": "progress", "project": "PRJ-02", "task": "T3",
                             "date": fixed["meta"]["today"], "progress": 75})
    v2 = pg.evaluate(fixed, pm.compute(fixed))
    chk("guard bersih setelah tindakan+update", not any(x["severity"] == "high" for x in v2),
        f"{len(v2)} sisa")
    arch_doc = json.load(open(_tpl("building.example.json"), encoding="utf-8"))
    import arch_design as ad2
    mkt_doc = None
    _an = os.path.join(ROOT, "deliverables", "analysis.json")
    if os.path.exists(_an):
        mkt_doc = json.load(open(_an, encoding="utf-8"))
    deck = ms.build(mkt_doc, pm.compute(raw), [ad2.compute(arch_doc, 26)], "T", "dan")
    nslide = deck.count("class='slide")
    chk("deck punya >=6 slide", nslide >= 6, f"{nslide}")
    chk("deck memuat svg chart", deck.count("<svg") >= 4, f"{deck.count('<svg')}")
    ext = [u for u in re.findall(r"https?://[^\"' >]+", deck) if "w3.org" not in u]
    chk("deck self-contained", not ext, str(ext[:2]))

    print("\n[13] Claim audit & unified CLI")
    import claim_audit as ca
    import dan as dancli
    an = os.path.join(ROOT, "deliverables", "analysis.json")
    am = os.path.join(ROOT, "deliverables", "analysis.md")
    if os.path.exists(am) and os.path.exists(an):
        res = ca.audit(am, [an], 0.051)
        chk("laporan hasil engine terverifikasi tinggi", res["coverage_pct"] >= 99,
            f"{res['coverage_pct']}%")
    fake = os.path.join(_tf.gettempdir(), "dan_fake.md")
    open(fake, "w").write("ROAS kami 7,77x dan revenue Rp99.999.888.777 tahun ini.\n")
    res2 = ca.audit(fake, [an], 0.051)
    chk("angka karangan ditandai", res2["verified"] == 0 and len(res2["unverified"]) == 2,
        f"verified={res2['verified']}")
    os.remove(fake)
    import io as _io
    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = dancli.main(["list"])
    chk("dan.py list", rc == 0 and "SUB-SKILL" in buf.getvalue())
    outp = os.path.join(_tf.gettempdir(), "dan_new_test.json")
    rc = dancli.main(["new", "building.blank.json", "--out", outp,
                      "--set", "meta.name=Uji", "--set", "site.width=8"])
    d = json.load(open(outp, encoding="utf-8"))
    chk("dan.py new + --set", rc == 0 and d["meta"]["name"] == "Uji"
        and d["site"]["width"] == 8)
    if os.path.exists(outp):
        os.remove(outp)

    print("\n[14] i18n & katalog kasus")
    import i18n as i18nmod
    chk("i18n label EN", i18nmod.t("sec_numbers", "en") == "1. This week in numbers")
    chk("i18n fallback ke ID", i18nmod.t("sec_numbers", "xx") == "1. Angka minggu ini")
    import weekly_run as wr2
    P2 = pm.compute(json.load(open(tpl, encoding="utf-8")))
    decs2 = wr2.pick_decisions(P2, None)
    md_en = wr2.build_summary(P2, P2["coach"], decs2, [], {"marketing": None}, lang="en")
    md_id = wr2.build_summary(P2, P2["coach"], decs2, [], {"marketing": None}, lang="id")
    chk("ringkasan EN berlabel EN", "This week in numbers" in md_en
        and "Angka minggu ini" not in md_en)
    chk("ringkasan ID tetap ID", "Angka minggu ini" in md_id)
    import run_cases as rc
    if os.path.isdir(rc.CASES):
        okk, logk = rc.run_case("kafe-fb", os.path.join(_tf.gettempdir(), "dan_cases_test"))
        chk("kasus kafe-fb lulus via runner", okk,
            "; ".join(x for x in logk if "FAIL" in x)[:120])
    else:
        print("  skip  katalog cases tidak tersedia (lingkungan minimal/pyz)")

    print("\n[15] Antrean terjemahan, export fallback, & paket .pyz")
    import i18n_queue as iq
    import export_png as ep
    srcmd = os.path.join(_tf.gettempdir(), "dan_i18n_src.md")
    open(srcmd, "w", encoding="utf-8").write(
        "# Judul\n\nAngka minggu ini bagus sekali karena tim disiplin mengisi form.\n"
        "| tabel | tidak | dihitung |\n|---|---|---|\n\n- Pesan coach: mulai dari potongan terkecil.\n")
    q = iq.extract(srcmd)
    chk("extract menangkap narasi, melewatkan tabel", q["count"] == 2, f"{q['count']}")
    tr = {"items": [{"id": it["id"], "line": it["line"],
                     "text": it["text"].replace("disiplin", "disciplined")}
                    for it in q["items"]]}
    trpath = os.path.join(_tf.gettempdir(), "dan_i18n_tr.json")
    json.dump(tr, open(trpath, "w", encoding="utf-8"))
    outmd = os.path.join(_tf.gettempdir(), "dan_i18n_out.md")
    iq.apply_translations(srcmd, tr, outmd)
    body = open(outmd, encoding="utf-8").read()
    chk("apply mengganti narasi", "disciplined" in body and "disiplin" not in body)
    for f in (srcmd, trpath, outmd):
        if os.path.exists(f):
            os.remove(f)
    svgp = os.path.join(_tf.gettempdir(), "dan_exp.svg")
    open(svgp, "w").write('<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
                          '<rect width="10" height="10"/></svg>')
    rcx = ep.main([svgp, "--out-dir", os.path.join(_tf.gettempdir(), "dan_exp_out")])
    have_renderer = rcx == 0
    chk("export_png: graceful bila tanpa renderer", have_renderer or rcx == 2,
        f"exit={rcx} ({'renderer ada' if have_renderer else 'fallback'})")
    os.remove(svgp)
    import make_pyz as mp
    pyz = os.path.join(_tf.gettempdir(), "dan_test.pyz")
    mp.build(pyz)
    r = subprocess.run([sys.executable, pyz, "list"], capture_output=True, text=True)
    chk("pyz terbangun & `list` jalan", r.returncode == 0 and "SUB-SKILL" in r.stdout)
    if os.path.exists(pyz):
        os.remove(pyz)

    print("\n[16] Sub-skill AI 10-21 (engine baru)")
    import prompt_lab as pl
    import workflow as wfl
    import rag as ragmod
    import stack_advisor as sa
    import assistant_builder as ab
    import llm_obs as lo
    import weekly_diff as wd
    good = ("Bertindaklah sebagai analis marketing senior. Berdasarkan file campaign.csv "
            "periode Q3, buatlah tabel ROAS per channel dalam format markdown, maksimal "
            "200 kata, jangan mengarang data, pastikan setiap angka punya satuan.")
    bad = "buatkan laporan"
    chk("prompt_lab lint membedakan", pl.lint(good)["score"] > pl.lint(bad)["score"],
        f"{pl.lint(good)['score']} vs {pl.lint(bad)['score']}")
    chk("prompt_lab improve menambah kerangka", "FORMAT KELUARAN" in pl.improve(bad))
    chk("prompt_lab variants", len(pl.variants(bad, 3)) == 3)
    wf = {"name": "t", "steps": [
        {"id": "a", "engine": "make_sample_data",
         "args": ["--days", "7", "--out", os.path.join(_tf.gettempdir(), "wf_t.csv")]},
        {"id": "b", "engine": "make_infographic",
         "args": [os.path.join(_tf.gettempdir(), "wf_missing.json"),
                  "--out", os.path.join(_tf.gettempdir(), "wf_t.html")],
         "on_fail": "skip"}]}
    wdir = os.path.join(_tf.gettempdir(), "wf_t_out")
    summ = wfl.run(wf, wdir)
    chk("workflow ok+skip", summ["counts"]["ok"] == 1 and summ["counts"]["skipped"] == 1,
        str(summ["counts"]))
    d = os.path.join(_tf.gettempdir(), "rag_t")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "a.md"), "w").write(
        "# Judul\n\nAmbang waspada variance adalah minus lima poin persen pada proyek.\n" * 3)
    idx = ragmod.build_index([d])
    res = ragmod.query(idx, "ambang waspada variance proyek", 2)
    chk("rag retrieval bersitasi", len(res) >= 1 and res[0]["file"].endswith("a.md"),
        f"{len(res)} hasil")
    rec = sa.recommend("chatbot rag dokumen", "rendah", 2, "menengah")
    chk("stack_advisor dalam budget", rec["monthly_usd"] <= 25 and rec["stack"],
        f"${rec['monthly_usd']}")
    spec = {"name": "T", "role": "r", "tools": ["rag"], "evals": []}
    files = ab.build(spec)
    chk("assistant_builder 4 berkas", len(files) == 4 and "eval_set.json" in files)
    tp = os.path.join(_tf.gettempdir(), "obs_t.jsonl")
    if os.path.exists(tp):
        os.remove(tp)
    lo.log(tp, {"prompt_id": "p", "cost": 0.01, "latency": 100, "pass": "true"})
    lo.log(tp, {"prompt_id": "p", "cost": 0.01, "latency": 200, "pass": "false"})
    R = lo.report(tp, 80)
    chk("llm_obs pass-rate", R["rows"][0]["pass_pct"] == 50.0, str(R["rows"][0]["pass_pct"]))
    os.remove(tp)
    rep1 = pm.compute(json.load(open(tpl, encoding="utf-8")))
    sn1, sn2 = wd.snapshot(rep1), wd.snapshot(rep1)
    D = wd.diff(sn1, sn2)
    chk("weekly_diff struktur", len(D["rows"]) == len(rep1["projects"]))

    print("\n[17] Demo tour, RAG eval, & digest")
    import demo_tour as dt
    import rag_eval as re_
    import make_digest as mdg
    buf = _io.StringIO()
    with redirect_stdout(buf):
        rc = dt.main(["--only", "10,13"])
    outp = buf.getvalue()
    chk("demo tour jalan", rc == 0 and "[10]" in outp and "[13]" in outp)
    qs = json.load(open(os.path.join(ROOT, "skills", "dan", "templates",
                                     "rag_eval_set.json"), encoding="utf-8"))
    R = re_.evaluate(qs, 5, [os.path.join(ROOT, "skills", "dan")])
    chk("rag eval recall@5 wajar", R["recall@5"] >= 80, f"{R['recall@5']}%")
    chk("rag eval pisahkan lexical vs synonym",
        any(r["kind"] == "synonym" for r in R["rows"]))
    dpath = os.path.join(_tf.gettempdir(), "dan_digest.md")
    rc = mdg.main(["--out", dpath])
    body = open(dpath, encoding="utf-8").read()
    chk("digest 5 baris + checklist", rc == 0 and "5 baris untuk tim" in body
        and "Checklist tindakan" in body and "eng." not in body)
    os.remove(dpath)

    print("\n[18] Plug-and-play: adapter & server MCP")
    import make_adapters as mad
    meta = mad.subskill_meta()
    chk("frontmatter sub-skill terbaca", len(meta) >= 21 and all(m["desc"] for m in meta),
        f"{len(meta)} sub-skill")
    made = mad.build_all(meta, mad.persona())
    n, probs = mad.validate()
    chk("adapter ekspor & valid", n >= 20 and not probs, f"{n} berkas; {probs[:2]}")
    chk("cursor mdc ada", any(f.endswith(".mdc") for f in made["cursor"]))
    chk("chatgpt instructions <= 8000",
        os.path.getsize(os.path.join(mad.OUT, "chatgpt", "custom_gpt_instructions.txt")) < 8000)
    chk("AGENTS.md ada", os.path.exists(os.path.join(mad.OUT, "agents", "AGENTS.md")))
    # MCP handshake via subprocess
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "dan_lint_prompt", "arguments": {"text": "buatkan laporan"}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "dan_list_engines", "arguments": {}}},
    ]
    rp = subprocess.run([sys.executable, os.path.join(HERE, "mcp_server.py")],
                        input="\n".join(json.dumps(r) for r in reqs),
                        capture_output=True, text=True, timeout=120)
    msgs = [json.loads(x) for x in rp.stdout.splitlines() if x.strip()]
    byid = {m.get("id"): m for m in msgs}
    chk("mcp initialize", byid.get(1, {}).get("result", {}).get("serverInfo", {})
        .get("name") == "dan-skill-server")
    chk("mcp tools/list >=10", len(byid.get(2, {}).get("result", {}).get("tools", [])) >= 10)
    t3 = byid.get(3, {}).get("result", {}).get("content", [{}])[0].get("text", "")
    chk("mcp tools/call lint", "skor" in t3)
    t4 = byid.get(4, {}).get("result", {}).get("content", [{}])[0].get("text", "")
    chk("mcp tools/call list_engines", "dan_analytics" in t4)

    print("\n[19] MCP smoke: semua tool dipanggil nyata")
    import mcp_smoke as ms
    rows = ms.run()
    bad = [r for r in rows if not r["ok"]]
    chk("semua tool MCP lulus", not bad,
        "; ".join(r["tool"] for r in bad) or f"{len(rows)} baris OK")

    print("\n[20] Notifikasi, burn-up multi-periode, & simulator budget")
    import notify as nf
    import burnup as bu
    import budget_sim as bsim
    doc0 = json.load(open(tpl, encoding="utf-8"))
    pay = nf.build_payload(doc0, None)
    for chn in ("slack", "telegram", "email", "stdout"):
        msg = nf.render(pay, chn)
        chk(f"notify render {chn}", len(msg) > 100 and ("TERKENDALI" in msg
            or "PERLU" in msg), f"{len(msg)} karakter")
    logp = os.path.join(_tf.gettempdir(), "dan_burn.jsonl")
    open(logp, "w").close()
    import weekly_diff as wd2
    repA = pm.compute(doc0)
    for i, f in enumerate((0.6, 1.0)):
        r2 = json.loads(json.dumps(repA))
        for pp in r2["projects"]:
            pp["progress"] = round(pp["progress"] * f, 1)
        sn = wd2.snapshot(r2)
        sn["ts"] = f"2026-09-0{i+1}T09:00:00"
        open(logp, "a").write(json.dumps(sn) + "\n")
    B = bu.build(bu.load(logp))
    chk("burnup 2 snapshot", B["n"] == 2 and len(B["act"]) == 2)
    chk("burnup deteksi pergerakan", any(m["d"] != 0 for m in B["moves"]))
    os.remove(logp)
    an = os.path.join(ROOT, "deliverables", "analysis.json")
    if os.path.exists(an):
        Ad = json.load(open(an, encoding="utf-8"))
        chs = Ad.get("by_channel") or []
        scs = bsim.scenarios(chs, 20)
        r0 = bsim.simulate(chs, scs[0], 0.2, 0.85, 300, 42)
        chk("budget sim baseline masuk akal",
            abs(r0["rev_p50"] - Ad["kpi"]["revenue"]) / Ad["kpi"]["revenue"] < 0.15,
            f"{r0['rev_p50'] / 1e9:.1f}B vs {Ad['kpi']['revenue'] / 1e9:.1f}B")
        if len(scs) > 1:
            r1 = bsim.simulate(chs, scs[1], 0.2, 0.85, 300, 42)
            chk("budget sim interval terurut", r1["rev_p10"] <= r1["rev_p50"] <= r1["rev_p90"])

    print("\n[21] Ritme satu-perintah, pemeriksa narasi, & lapisan anotasi")
    import weekly as wk
    import narrative_check as nc
    import annotate as an
    wdir = os.path.join(_tf.gettempdir(), "dan_weekly_t")
    rc = wk.main(["--projects", tpl, "--updates",
                  os.path.join(ROOT, "data", "weekly_batch.example.json"),
                  "--out-dir", wdir, "--skip", "digest,burnup"])
    logj = json.load(open(os.path.join(wdir, "run_log.json"), encoding="utf-8"))
    chk("weekly satu perintah ok", rc == 0 and not logj["failed"],
        str(logj["failed"]))
    chk("weekly menghasilkan artefak inti",
        all(os.path.exists(os.path.join(wdir, x)) for x in
            ("weekly_summary.md", "notif_stdout.txt", "run_log.json", "history.jsonl")))
    bad_txt = ("Pendapatan pasti naik karena kampanye kami. Budi gagal. "
               "Proyeksi mencapai Rp5 miliar. Kami termurah.")
    R = nc.check(bad_txt)
    chk("narrative menangkap 5 pola", len(R["findings"]) >= 5, f"{len(R['findings'])}")
    R2 = nc.check("Progres 41% vs rencana 39%; estimasi ±2 pp bila asumsi bertahan.")
    chk("narratif bersih lolos", not R2["findings"], str(R2["findings"][:1]))
    srcp = os.path.join(_tf.gettempdir(), "dan_ann_src.html")
    open(srcp, "w").write("<html><body><div class='card'>x</div></body></html>")
    outp2 = os.path.join(_tf.gettempdir(), "dan_ann_out.html")
    rc = an.inject(srcp, outp2)
    body = open(outp2, encoding="utf-8").read()
    chk("annotate menyuntik lapisan", rc == 0 and "annBar" in body and "annPanel" in body)
    for f in (srcp, outp2):
        os.remove(f)

    print("\n[22] Laporan klien, doctor --full, & VS Code artifacts")
    import client_report as cr
    an2 = os.path.join(ROOT, "deliverables", "analysis.json")
    if os.path.exists(an2):
        md = cr.build(json.load(open(an2, encoding="utf-8")), "Uji", "periode uji")
        chk("client report bahasa manusia", "Ringkasan satu napas" in md
            and "Istilah singkat" in md and "ROAS" in md)
        chk("client report menyebut rupiah", "Rp" in md)
    import dan as danmod
    os.environ["DAN_IN_QA"] = "1"
    try:
        rc = danmod.main(["doctor", "--full"])
    finally:
        os.environ.pop("DAN_IN_QA", None)
    qr = os.path.join(ROOT, "deliverables", "qa_report.md")
    chk("doctor --full sehat + qa_report", rc == 0 and os.path.exists(qr))
    vsc = os.path.join(ROOT, ".vscode")
    chk("vscode artifacts ada", all(os.path.exists(os.path.join(vsc, x)) for x in
        ("settings.json", "tasks.json", "launch.json", "mcp.json",
         "dan.code-snippets")) and os.path.exists(os.path.join(ROOT,
        "dan.code-workspace")))
    kursus = os.path.join(ROOT, "kursus")
    chk("kursus internal ada", os.path.exists(os.path.join(kursus, "README.md"))
        and os.path.exists(os.path.join(kursus, "kunci.md")))

    print("\n[23] Ekspor PDF, kesehatan paket, & laporan klien EN")
    import export_pdf as ep
    import pkg_health as ph
    buf = _io.StringIO()
    with redirect_stdout(buf):
        rcx = ep.export(os.path.join(_tf.gettempdir(), "dan_no.html"),
                        os.path.join(_tf.gettempdir(), "dan_no.pdf"))
    has_renderer = rcx == 0
    chk("export_pdf graceful tanpa renderer", has_renderer or rcx == 2,
        f"exit={rcx} ({'renderer ada' if has_renderer else 'fallback jujur'})")
    hist2 = [{"version": "vA", "tests_pass": 100, "tests_fail": 1, "refs_missing": 2,
              "bytes": 500000}, {"version": "vB", "tests_pass": 157, "tests_fail": 0,
                                 "refs_missing": 0, "bytes": 600000}]
    spec = ph.build_spec(hist2, ph.inventory())
    kinds = [x.get("chart") for x in spec["sections"] if x.get("type") == "chart"]
    chk("pkg_health tren >=2 rilis", kinds.count("line") >= 2, str(kinds))
    spec1 = ph.build_spec(hist2[:1], ph.inventory())
    chk("pkg_health 1 rilis jujur (tanpa tren karangan)",
        not any(x.get("type") == "chart" and x.get("chart") == "line"
                for x in spec1["sections"]))
    import client_report as cr2
    an3 = os.path.join(ROOT, "deliverables", "analysis.json")
    if os.path.exists(an3):
        en = cr2.build(json.load(open(an3, encoding="utf-8")), "X", "P", "en")
        chk("client report EN", "One-breath summary" in en and "What happened" in en)

    print("\n[24] Release ber-gate, deck cetak, & contoh sektor")
    import release as rel
    import print_deck as pd_
    rc = rel.main(["--version", "0.0.0-test", "--dry-run"])
    chk("release dry-run", rc == 0)
    dlx = os.path.join(ROOT, "deliverables")
    mkt_d = json.load(open(an3, encoding="utf-8")) if os.path.exists(an3) else None
    arch_d = ad2.compute(json.load(open(_tpl("building.example.json"),
                                        encoding="utf-8")), 20)
    html = pd_.build(mkt_d, pm.compute(json.load(open(tpl, encoding="utf-8"))),
                     [arch_d], "light")
    npages = html.count('<section class=\'pslide\'>')
    chk("print deck 5 halaman", npages == 5, f"{npages}")
    chk("print deck CSS cetak landscape", "A4 landscape" in html)
    ex = os.path.join(ROOT, "examples")
    nsec = 0
    for sec in ("fnb", "fashion", "b2b"):
        cp = os.path.join(ex, sec, "campaign.csv")
        bp = os.path.join(ex, sec, "brief.md")
        if os.path.exists(cp) and os.path.exists(bp):
            A = da.analyze(cp)
            nsec += 1 if A["kpi"]["revenue"] > 0 else 0
    chk("3 contoh sektor teranalisa", nsec == 3, f"{nsec}")

    print("\n[25] Wizard onboarding, watchdog, & showcase")
    import init_wizard as iw
    import weekly_watch as ww
    import showcase as shw
    wdir = os.path.join(_tf.gettempdir(), "dan_init_t")
    R = iw.run("fnb", os.path.join(ROOT, "examples", "fnb", "campaign.csv"),
               "infografik", "Uji", "P", "id", wdir)
    chk("wizard menghasilkan keluaran pertama", R["ok"] and
        any(f.endswith("infografik.html") for f in R["made"]), str(R.get("error", "")))
    rcw = ww.main(["--projects", tpl, "--channel", "stdout", "--out-dir", wdir])
    chk("watchdog ALARM pada portofolio mentah (kritis tanpa tindakan)", rcw == 1,
        f"exit={rcw}")
    docw = json.load(open(tpl, encoding="utf-8"))
    upsw = json.load(open(os.path.join(ROOT, "data", "weekly_batch.example.json"),
                          encoding="utf-8"))["updates"]
    upath = os.path.join(wdir, "proj_upd.json")
    json.dump(pm.apply_updates(docw, upsw)["doc"], open(upath, "w", encoding="utf-8"))
    rcw2 = ww.main(["--projects", upath, "--channel", "stdout", "--out-dir", wdir])
    chk("watchdog SEHAT setelah update", rcw2 == 0, f"exit={rcw2}")
    outf = os.path.join(_tf.gettempdir(), "dan_showcase.html")
    rcs = shw.main(["--out", outf])
    body = open(outf, encoding="utf-8").read()
    chk("showcase mengindeks artefak", rcs == 0 and body.count("class='c'") >= 10,
        f"{body.count(chr(39) + 'c' + chr(39))} kartu")
    for f in (outf,):
        if os.path.exists(f):
            os.remove(f)

    print("\n[26] Notify kirim-aman, bundle offline, & tren narasi")
    import notify as nf2
    import make_bundle as mb
    import narrative_trend as nt
    rcs2 = nf2.send("telegram", "uji")
    chk("notify --send menolak tanpa env", rcs2 == 2, f"exit={rcs2}")
    bpath = os.path.join(_tf.gettempdir(), "dan_bundle_t.zip")
    rcb = mb.main(["--version", "test", "--out", bpath])
    import zipfile as zf
    names = zf.ZipFile(bpath).namelist() if os.path.exists(bpath) else []
    chk("bundle berisi pyz+install+examples", rcb == 0 and "dan.pyz" in names
        and "INSTALL-OFFLINE.md" in names and any(n.startswith("examples/")
                                                  for n in names), f"{len(names)} berkas")
    if os.path.exists(bpath):
        os.remove(bpath)
    dirl = os.path.join(ROOT, "deliverables")
    rows = nt.scan([os.path.join(dirl, "analysis.md")], [])
    chk("narrative trend mengukur laporan", rows and 0 <= rows[0]["narrative_score"] <= 100,
        str(rows[0]["narrative_score"]) if rows else "-")

    print("\n[27] Dashboard lintas-klien, SOP, & simulasi krisis")
    import multi_client as mc
    import make_sop as msop
    import crisis_sim as cs
    import make_sample_data as msd
    an4 = os.path.join(_tf.gettempdir(), "an_b.json")
    msd.main(["--days", "20", "--seed", "9", "--out",
              os.path.join(_tf.gettempdir(), "c_b.csv")])
    Ab = da.analyze(os.path.join(_tf.gettempdir(), "c_b.csv"))
    json.dump(Ab, open(an4, "w", encoding="utf-8"))
    Aa = json.load(open(an3, encoding="utf-8")) if os.path.exists(an3) else Ab
    htmlm = mc.build([("KlienA", Aa), ("KlienB", Ab)])
    chk("multi_client 2 tab + tabel", htmlm.count("class='view'") == 2
        and "Perbandingan antar-klien" in htmlm)
    sop = msop.build(["PMO", "Analyst"])
    chk("sop memuat cadence+RACI+eskalasi", "RACI" in sop and "eskalasi" in sop
        and "Harian" in sop)
    scen = cs.build(Aa, 4000)
    chk("crisis 4 skenario berangka", len(scen) == 4 and all("respons" in x for x in scen))
    bsc = [x for x in scen if x["id"] == "B"][0]
    chk("crisis B memperhitungkan saturasi",
        bsc["angka"]["pemulihan_estimasi"] < bsc["angka"]["revenue_terpapar"])

    print("\n[28] Multi-bahasa terpusat, audit keamanan, & paket kursus")
    import i18n as i18nmod2
    import sec_audit as secu
    import make_course as mkc
    chk("i18n punya 3 bahasa", sorted(i18nmod2.langs()) == ["en", "id", "zh"],
        str(i18nmod2.langs()))
    for lg in ("id", "en", "zh"):
        md2 = da.to_markdown(json.load(open(an3, encoding="utf-8")), lg) \
            if os.path.exists(an3) else da.to_markdown(A, lg)
        chk(f"laporan {lg} ber-heading terjemah", "## 1. " in md2
            and (lg != "zh" or "核心" in md2))
    fnds = secu.scan(HERE)
    nh = sum(1 for f in fnds if f["severity"] == "high")
    chk("repo bersih dari secret high", nh == 0, f"{nh} high")
    td = os.path.join(_tf.gettempdir(), "sec_t")
    os.makedirs(td, exist_ok=True)
    fake_key = "AK" + "IA" + "IOSFODNN7EXAMPLE" + " = 1\n"   # dirakit runtime
    open(os.path.join(td, "leak.py"), "w").write(fake_key)
    f2 = secu.scan(td)
    chk("sec_audit menangkap kunci AWS", any(x["severity"] == "high" and "AWS" in x["kind"]
                                             for x in f2))
    shutil.rmtree(td, ignore_errors=True)
    cd = os.path.join(_tf.gettempdir(), "course_t")
    R3 = mkc.build(cd)
    chk("course kit 7 slide + timestamp", len(R3["slides"]) == 7 and
        os.path.exists(os.path.join(cd, "course_audio_script.md")) and
        os.path.exists(os.path.join(cd, "course_deck.html")))
    script = open(os.path.join(cd, "course_audio_script.md"), encoding="utf-8").read()
    chk("naskah audio ber-timestamp", "[00:00" in script and "detik)" in script)
    shutil.rmtree(cd, ignore_errors=True)

    print("\n[29] Regresi pasca-pemangkasan: routing & cakupan isi")
    sk = open(os.path.join(ROOT, "skills", "dan", "SKILL.md"), encoding="utf-8").read()
    paths = re.findall(r"`(skills/\d{2}-[^`]+/SKILL\.md)`", sk)
    chk("indeks memuat 21 sub-skill", len(set(paths)) == 21, f"{len(set(paths))}")
    PKG = os.path.join(ROOT, "skills", "dan")
    miss = [q for q in set(paths)
            if not os.path.exists(os.path.join(PKG, q.replace("skills/", "skills/", 1)))]
    chk("semua target routing ada", not miss, str(miss[:2]))
    nofm = [q for q in set(paths)
            if "description:" not in open(os.path.join(PKG, q), encoding="utf-8").read()[:400]]
    chk("tiap target punya frontmatter", not nofm, str(nofm[:2]))
    rb = open(os.path.join(ROOT, "skills", "dan", "references",
                           "pipeline-runbook.md"), encoding="utf-8").read()
    need = ["make_infographic.py", "weekly.py", "release.py", "claim_audit",
            "narrative_check", "Deliverable minimum", "Disiplin konteks",
            "make_adapters.py"]
    hilang = [k for k in need if k not in rb]
    chk("isi lama tidak hilang (pindah, bukan terbuang)", not hilang, str(hilang[:3]))
    skp = os.path.join(PKG, "SKILL.md")
    chk("indeks ramping (<2k token)", os.path.getsize(skp) / 4 < 2000,
        f"{os.path.getsize(skp) / 4:.0f} token")

    print("\n[30] Pipeline xlsx: xlsx_lite + plan_analyst (business plan)")
    import zipfile as _zf
    import xlsx_lite as _xl
    import plan_analyst as _pa

    def _sheet_xml(rows):
        """rows: {row: {col: value}} -> XML worksheet (inline string / angka / formula cache)."""
        out = ['<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/'
               'spreadsheetml/2006/main"><sheetData>']
        for r in sorted(rows):
            out.append(f'<row r="{r}">')
            for c in sorted(rows[r]):
                ref = _xl.rc_to_ref(r, c)
                v = rows[r][c]
                if isinstance(v, str):
                    out.append(f'<c r="{ref}" t="inlineStr"><is><t>{v}</t></is></c>')
                elif isinstance(v, tuple):      # (formula, cached)
                    out.append(f'<c r="{ref}"><f>{v[0]}</f><v>{v[1]}</v></c>')
                else:
                    out.append(f'<c r="{ref}"><v>{v}</v></c>')
            out.append("</row>")
        out.append("</sheetData></worksheet>")
        return "".join(out)

    def _mkxlsx(path, sheets):
        """sheets: [(nama, {row: {col: val}})] -> file .xlsx valid tanpa dependensi."""
        ct = ['<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/'
              '2006/content-types"><Default Extension="rels" ContentType="application/vnd.'
              'openxmlformats-package.relationships+xml"/><Default Extension="xml" '
              'ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType='
              '"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>']
        for i in range(len(sheets)):
            ct.append(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/'
                      'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        ct.append("</Types>")
        sh = "".join(f'<sheet name="{n}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
                     for i, (n, _) in enumerate(sheets))
        wb = ('<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/'
              'spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/'
              f'officeDocument/2006/relationships"><sheets>{sh}</sheets></workbook>')
        rel = "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/'
                      'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet'
                      f'{i + 1}.xml"/>' for i in range(len(sheets)))
        rels = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/'
                f'package/2006/relationships">{rel}</Relationships>')
        root = ('<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/'
                'package/2006/relationships"><Relationship Id="rId1" Type="http://'
                'schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="xl/workbook.xml"/></Relationships>')
        with _zf.ZipFile(path, "w") as z:
            z.writestr("[Content_Types].xml", "".join(ct))
            z.writestr("_rels/.rels", root)
            z.writestr("xl/workbook.xml", wb)
            z.writestr("xl/_rels/workbook.xml.rels", rels)
            for i, (_, rows) in enumerate(sheets):
                z.writestr(f"xl/worksheets/sheet{i + 1}.xml", _sheet_xml(rows))

    td = os.path.join(_tf.gettempdir(), "xlsx_t")
    os.makedirs(td, exist_ok=True)
    f1 = os.path.join(td, "mini.xlsx")
    _mkxlsx(f1, [("S1", {1: {1: "teks", 2: 42, 3: ("SUM(A1:B1)", 43)}}),
                 ("S2", {5: {2: 3.5}})])
    wbx = _xl.load(f1)
    chk("xlsx_lite baca sheet + tipe", wbx["sheets"] == ["S1", "S2"]
        and _xl.cell(wbx, "S1", "A1") == "teks" and _xl.cell(wbx, "S1", "B1") == 42
        and abs(_xl.cell(wbx, "S2", "B5") - 3.5) < 1e-9)
    chk("xlsx_lite simpan formula cache",
        wbx["formula"]["S1"].get((1, 3)) == "SUM(A1:B1)" and _xl.cell(wbx, "S1", "C1") == 43)
    chk("ref bolak-balik A1<->(r,c)", _xl.rc_to_ref(*_xl.ref_to_rc("AZ104")) == "AZ104"
        and _xl.ref_to_rc("BA3") == (3, 53))

    # workbook sintetis berpola business plan (4 divisi, 3 bulan data, stok)
    DIV = {"KALBE": 24, "KENVEU": 42, "OOH": 60, "DK": 78}
    A26 = {"KALBE": [40, 90, 140], "KENVEU": [30, 60, 90], "OOH": [15, 25, 40], "DK": [5, 15, 20]}
    A25 = {"KALBE": [45, 105, 125], "KENVEU": [25, 55, 70], "OOH": [12, 30, 35], "DK": [8, 20, 20]}
    TGT = {"KALBE": [60, 90, 150], "KENVEU": [30, 60, 90], "OOH": [20, 20, 40], "DK": [10, 10, 20]}
    om = {5: {2: "ALL DIVISI", 3: "Bulan", 4: 2024, 5: 2025, 6: 2026, 7: "Target"}}
    for i in range(3):
        om[6 + i] = {2: "SANCHO", 3: _pa.BULAN[i], 4: 10 + i, 5: sum(A25[k][i] for k in A25),
                     6: sum(A26[k][i] for k in A26), 7: sum(TGT[k][i] for k in TGT)}
    for k, r0 in DIV.items():
        om[r0 - 1] = {2: "DIVISI", 3: "Bulan", 4: 2024, 5: 2025, 6: 2026, 7: "Target"}
        for i in range(3):
            om[r0 + i] = {2: k, 3: _pa.BULAN[i], 4: 5 + i, 5: A25[k][i], 6: A26[k][i],
                          7: TGT[k][i],
                          # M=EA2025 N=EA2026 · T=IPT2025 U=IPT2026 · Y=CB2025 Z=CB2026
                          13: 120 + 10 * i, 14: 100 + 10 * i,
                          20: 3.0, 21: 4.0, 25: 150, 26: 160}
    st = {3: {2: "Divisi", 3: "Kalbe", 4: "Kenveu", 5: "OOH-FFI", 6: "Dua Kelinci"},
          4: {2: "Avg L3M", 3: 7e9, 4: 3e9, 5: 2e9, 6: 1.4e9},
          5: {2: "Stock On Hand", 3: 5.7e9, 4: 6.9e9, 5: 0.6e9, 6: 1.37e9},
          6: {2: "Scd", 3: 24.3, 4: 60.1, 5: 9.2, 6: 29.3},
          7: {2: "Target SCD", 3: 30, 4: 45, 5: 30, 6: 30}}
    f2 = os.path.join(td, "plan.xlsx")
    _mkxlsx(f2, [("Omset All", om), ("Stock", st)])
    an = _pa.bangun(f2, "PT Uji Coba")
    r = an["ringkasan"]
    chk("plan_analyst: YTD & target & gap", abs(r["ytd2026"] - 570) < 1e-6
        and abs(r["target"] - 600) < 1e-6 and abs(r["gap"] + 30) < 1e-6, f"{r['ytd2026']}/{r['target']}")
    chk("plan_analyst: pencapaian & YoY", abs(r["pencapaian"] - 0.95) < 1e-9
        and abs(r["yoy"] - (570 / 550 - 1)) < 1e-9)
    d = {x["kode"]: x for x in an["divisi"]}
    chk("plan_analyst: RAG per divisi", d["KALBE"]["status"] == "kuning"
        and d["KENVEU"]["status"] == "hijau" and d["KALBE"]["yoy"] < 0)
    chk("plan_analyst: gap divisi penentu", min(an["divisi"], key=lambda z: z["gap"])["kode"] == "KALBE")
    chk("plan_analyst: metrik EA/CB/IPT kebaca", abs(d["KALBE"]["ea26"] - 110) < 1e-6
        and abs(d["KALBE"]["ea25"] - 130) < 1e-6 and abs(d["KALBE"]["cb26"] - 160) < 1e-6
        and abs(d["KALBE"]["ipt26"] - 4.0) < 1e-9
        and abs(d["KALBE"]["efektivitas_call26"] - 110 / 160) < 1e-9)
    chk("plan_analyst: stok kritis & overstock",
        {s["divisi"]: s["status"] for s in an["stok"]}["OOH-FFI"] == "kritis"
        and {s["divisi"]: s["status"] for s in an["stok"]}["Kenveu"] == "overstock")
    chk("plan_analyst: insight = dict ber-severity",
        an["insights"] and all(isinstance(i, dict) and i.get("severity") in
                               ("bad", "warn", "good", "info") and i.get("title")
                               for i in an["insights"]))
    chk("plan_analyst: rekomendasi punya dampak+PIC+KPI",
        an["recommendations"] and all(x["dampak"] and x["pemilik"] and x["kpi"] and x["prioritas"]
                                      for x in an["recommendations"]))
    chk("plan_analyst: prioritas unik & urut",
        [x["prioritas"] for x in an["recommendations"]]
        == list(range(1, len(an["recommendations"]) + 1)))
    chk("plan_analyst: proyeksi 3 skenario konsisten",
        len(an["proyeksi"]["skenario"]) == 3
        and all(abs(s["setahun"] - (r["ytd2026"] + s["sep_des"])) < 1e-6
                for s in an["proyeksi"]["skenario"]))
    chk("plan_analyst: DQ-02 target kosong terdeteksi",
        any(x["kode"] == "DQ-02" for x in an["temuan_data"]))
    sp = _pa.buat_spec(an)
    chk("spec infografik: sections valid",
        len(sp["sections"]) >= 5 and all(s["type"] in ("kpi", "chart", "html", "insights",
                                                       "recommendations") for s in sp["sections"]))
    pj = _pa.buat_projects(an, today="2026-09-16")
    chk("projects.json: rekomendasi + divisi jadi proyek",
        len(pj["projects"]) == len(an["recommendations"]) + len(an["divisi"])
        and all(p["tasks"] and p["kpi"] and p["risks"] for p in pj["projects"]))
    chk("projects.json: risiko pakai skala numerik",
        all(isinstance(rr["prob"], (int, float)) and isinstance(rr["impact"], (int, float))
            for p in pj["projects"] for rr in p["risks"]))
    outd = os.path.join(td, "out")
    rc = _pa.main(["--file", f2, "--outdir", outd, "--nama", "PT Uji Coba"])
    perlu = ["analysis.json", "analysis.md", "data_quality.md", "spec_infografik.json",
             "projects.json", "omset_divisi.csv", "kanal.csv", "tim_achievement.csv"]
    ada = [f for f in perlu if not os.path.exists(os.path.join(outd, f))]
    chk("plan_analyst CLI: semua keluaran tertulis", rc == 0 and not ada, str(ada))
    md = open(os.path.join(outd, "analysis.md"), encoding="utf-8").read()
    chk("analysis.md: ada tabel divisi + rekomendasi + batasan",
        "| Divisi |" in md and "## 9. Rekomendasi" in md and "## 10. Batasan" in md)
    chk("angka di md bersatuan & periode jelas",
        "| Kalbe | Rp" in md and "90,0%" in md and "Jan" in md and "Rp0,00 M" in md)
    # sheet hilang tidak boleh bikin crash
    f3 = os.path.join(td, "min2.xlsx")
    _mkxlsx(f3, [("Omset All", om)])
    an2 = _pa.bangun(f3, "PT Minimal")
    chk("tahan sheet tidak lengkap", abs(an2["ringkasan"]["ytd2026"] - 570) < 1e-6
        and an2["stok"] == [] and an2["tim"] == {})
    shutil.rmtree(td, ignore_errors=True)

    print("\n[31] Web hub: make_web + serve")
    import tempfile
    import http.server
    import make_web as _mw
    import serve as _srv
    wdir = tempfile.mkdtemp(prefix="danweb")
    r = _mw.bangun(wdir)
    chk("make_web: index.html tertulis & cukup besar",
        os.path.exists(r["path"]) and r["bytes"] > 20000, str(r["bytes"]))
    wh = open(r["path"], encoding="utf-8").read()
    chk("situs: judul + 7 tab + data tersemat",
        "<title>DAN" in wh and all('id="tab-%s"' % t in wh for t in
        ("beranda", "skills", "tools", "mesin", "pasang", "unduh", "rilis"))
        and "const D = {" in wh)
    chk("situs: self-contained (tanpa URL eksternal di src/href)",
        not re.search(r'(?:src|href)\s*=\s*"https?://', wh))
    baris = next(x for x in wh.splitlines() if x.startswith("const D = "))
    blob = json.loads(baris[len("const D = "):].rstrip(";"))
    chk("data sinkron paket: 21 skill, >50 engine, QA>0",
        len(blob["skills"]) == 21 and len(blob["engines"]) > 50
        and blob["stat"]["tests"] > 0 and blob["stat"]["fail"] == 0)
    chk("data: adapters >= 12 + unduhan rilis ada",
        len(blob["adapters"]) >= 12 and any(u["file"].endswith(".zip") for u in blob["unduhan"]))
    chk("situs: 8 tools interaktif terdefinisi",
        all(x in wh for x in ("k-out", "f-out", "b-out", "a-out", "n-out", "p-out",
                              "s-out", "m-out")))
    chk("serve: ROOT = workspace root & handler tersedia",
        _srv.ROOT == os.path.dirname(os.path.dirname(_mw.PAKET))
        and issubclass(_srv.Handler, http.server.SimpleHTTPRequestHandler))
    shutil.rmtree(wdir, ignore_errors=True)

    print("\n[32] memory: session_log lintas-sesi")
    import memory as _mem
    import dan as _dancli
    mdir = tempfile.mkdtemp(prefix="danmem")
    sp = os.path.join(mdir, "session_log.jsonl")
    _mem.add(sp, "Klien Kalbe: fokus perbaiki outlet EA", "keputusan")
    _mem.add(sp, "Klien suka laporan ringkas hemat token", "preferensi")
    _mem.add(sp, "Minta target Sep-Des ke klien", "tugas")
    recs = _mem.load(sp)
    chk("memory: add 3 → 3 rekam, id unik, tag benar",
        len(recs) == 3 and len({r["id"] for r in recs}) == 3
        and {r["tag"] for r in recs} == {"keputusan", "preferensi", "tugas"})
    hits = _mem.search(sp, "kalbe")
    chk("memory: search 'kalbe' → keputusan Kalbe teratas",
        bool(hits) and "Kalbe" in hits[0]["text"])
    with open(sp, "a", encoding="utf-8") as f:
        f.write("{baris korup\n")
    chk("memory: tahan baris korup (tetap 3)", len(_mem.load(sp)) == 3)
    md = _mem.context_md(sp, k=12)
    chk("memory: context_md memuat semua entri + heading",
        md.startswith("## Memori DAN") and "Kalbe" in md and "ringkas" in md)
    st = _mem.stats(sp)
    chk("memory: stats total & per-tag", st["total"] == 3 and st["tags"].get("tugas") == 1)
    chk("memory: tag tak dikenal → 'lainnya'",
        _mem.add(sp, "catatan bebas", "ngawur")["tag"] == "lainnya")
    chk("dan.py: engine 'memory' terdaftar + subcmd tersedia",
        any(e[0] == "memory" for e in _dancli.ENGINES)
        and _dancli.main(["memory", "stats", "--store", sp]) == 0)
    chk("memory: default store = <repo>/data/session_log.jsonl",
        _mem.ROOT == _dancli.ROOT
        and _mem.default_store().endswith(os.path.join("data", "session_log.jsonl")))
    shutil.rmtree(mdir, ignore_errors=True)

    print("\n[33] deploy: publish_gh → GitHub Pages (gratis)")
    import publish_gh as _pg
    gdir = tempfile.mkdtemp(prefix="dangh")
    sout = os.path.join(gdir, "site")
    r = _pg.prepare(sout)
    idx = open(os.path.join(sout, "index.html"), encoding="utf-8").read()
    chk("prepare: index.html + .nojekyll + 404.html + README",
        os.path.exists(r["index"]) and r["bytes"] > 20000
        and os.path.exists(os.path.join(sout, ".nojekyll"))
        and os.path.exists(os.path.join(sout, "404.html"))
        and os.path.exists(os.path.join(sout, "README.md")))
    chk("tautan unduh dipatch ke files/ (bukan ../)",
        'href="../' not in idx and 'href="files/' in idx)
    berkas = os.listdir(os.path.join(sout, "files"))
    chk("files/: artefak rilis (zip + pyz) tersalin",
        any(f.endswith(".zip") for f in berkas) and "dan.pyz" in berkas, str(berkas))
    chk("site.zip utk unggah-web tanpa git", os.path.exists(r["zip"]))
    g = _pg.guide_text("USER/dan-hub")
    chk("guide: opsi A+B, URL github.io, penegasan gratis",
        "A) MANUAL" in g and "B) OTOMATIS" in g and "user.github.io/dan-hub" in g
        and "Rp0" in g and "DEPLOY-GITHUB.md" in g)
    wf = os.path.join(_dancli.ROOT, ".github", "workflows", "deploy-pages.yml")
    wtxt = open(wf, encoding="utf-8").read()
    chk("workflow deploy-pages.yml: build publish_gh + deploy-pages",
        "publish_gh.py prepare --out _site" in wtxt
        and "actions/deploy-pages" in wtxt and "pages: write" in wtxt)
    dmd = open(os.path.join(_dancli.ROOT, "DEPLOY-GITHUB.md"), encoding="utf-8").read()
    chk("DEPLOY-GITHUB.md: opsi A+B + tabel gratis + troubleshooting",
        "Opsi A" in dmd and "Opsi B" in dmd and "GitHub Actions" in dmd
        and "Troubleshooting" in dmd and "Rp0" in dmd)
    chk("dan.py: engine publish_gh + `deploy guide` rc=0",
        any(e[0] == "publish_gh" for e in _dancli.ENGINES)
        and _dancli.main(["deploy", "guide", "--repo", "u/r"]) == 0)
    shutil.rmtree(gdir, ignore_errors=True)
    if os.path.exists(gdir + ".zip"):
        os.remove(gdir + ".zip")

    print(f"\n{'=' * 58}\nHASIL: {len(PASS)} lulus, {len(FAIL)} gagal")
    if FAIL:
        print("Gagal: " + ", ".join(FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
