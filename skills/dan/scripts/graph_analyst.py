#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
graph_analyst.py — Analisa Graph/Network untuk marketing (sub-skill DAN #01/#03).

Menghitung metrik jaringan + menggambar visualisasinya (SVG, zero-dependency).
Memakai networkx bila tersedia, jika tidak maka fallback pure-python.

Metrik: degree, weighted degree, betweenness (Brandes), closeness, eigenvector
(power iteration), PageRank, HITS (hub/authority), komunitas (label propagation),
density, komponen terhubung, diameter/rata-rata jarak.

Input (pilih salah satu):
  --edges file.csv        kolom: source,target[,weight]  (header opsional)
  --graph file.json       {"nodes":[{"id","label","group","value"}], "edges":[[a,b,w]]}
  --demo                  pakai contoh jaringan influencer bawaan

Output:
  --out   graph.json      metrik lengkap
  --svg   graph.svg       visualisasi jaringan
  --report graph.md       ringkasan + rekomendasi

CONTOH:
  python3 graph_analyst.py --demo --svg ../../../deliverables/graph.svg \
      --report ../../../deliverables/graph.md
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import sys
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import svg_charts as sc  # noqa: E402

try:
    import networkx as nx  # type: ignore
    HAVE_NX = True
except Exception:                                     # pragma: no cover
    nx = None
    HAVE_NX = False


# --------------------------------------------------------------------- graph core

class Graph:
    """Graph tak-berarah, berbobot, pure-python."""

    def __init__(self) -> None:
        self.adj: Dict[Any, Dict[Any, float]] = defaultdict(dict)
        self.nodes: Dict[Any, Dict[str, Any]] = {}

    def add_node(self, n: Any, **attrs: Any) -> None:
        self.nodes.setdefault(n, {})
        self.nodes[n].update(attrs)
        _ = self.adj[n]

    def add_edge(self, a: Any, b: Any, w: float = 1.0) -> None:
        self.add_node(a)
        self.add_node(b)
        self.adj[a][b] = self.adj[a].get(b, 0.0) + w
        self.adj[b][a] = self.adj[b].get(a, 0.0) + w

    @property
    def V(self) -> List[Any]:
        return list(self.nodes.keys())

    @property
    def edges(self) -> List[Tuple[Any, Any, float]]:
        seen, out = set(), []
        for a in self.adj:
            for b, w in self.adj[a].items():
                k = tuple(sorted((str(a), str(b))))
                if k not in seen:
                    seen.add(k)
                    out.append((a, b, w))
        return out

    def degree(self) -> Dict[Any, int]:
        return {n: len(self.adj[n]) for n in self.V}

    def strength(self) -> Dict[Any, float]:
        return {n: sum(self.adj[n].values()) for n in self.V}

    def components(self) -> List[List[Any]]:
        seen, comps = set(), []
        for s in self.V:
            if s in seen:
                continue
            q, comp = deque([s]), []
            seen.add(s)
            while q:
                u = q.popleft()
                comp.append(u)
                for v in self.adj[u]:
                    if v not in seen:
                        seen.add(v)
                        q.append(v)
            comps.append(sorted(comp, key=lambda x: str(x)))
        return sorted(comps, key=len, reverse=True)

    def bfs_dist(self, src: Any) -> Dict[Any, int]:
        dist = {src: 0}
        q = deque([src])
        while q:
            u = q.popleft()
            for v in self.adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return dist

    def betweenness(self) -> Dict[Any, float]:
        """Brandes' algorithm (unweighted, normalized)."""
        cb: Dict[Any, float] = {v: 0.0 for v in self.V}
        for s in self.V:
            S: List[Any] = []
            P: Dict[Any, List[Any]] = {v: [] for v in self.V}
            sigma: Dict[Any, float] = {v: 0.0 for v in self.V}
            d: Dict[Any, int] = {v: -1 for v in self.V}
            sigma[s], d[s] = 1.0, 0
            q = deque([s])
            while q:
                v = q.popleft()
                S.append(v)
                for w in self.adj[v]:
                    if d[w] < 0:
                        d[w] = d[v] + 1
                        q.append(w)
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)
            delta = {v: 0.0 for v in self.V}
            while S:
                w = S.pop()
                for v in P[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != s:
                    cb[w] += delta[w]
        n = len(self.V)
        norm = 1.0 / ((n - 1) * (n - 2)) if n > 2 else 1.0
        return {v: cb[v] * norm for v in cb}          # tak-berarah -> /2 sudah termasuk norm

    def closeness(self) -> Dict[Any, float]:
        out = {}
        n = len(self.V)
        for v in self.V:
            d = self.bfs_dist(v)
            tot = sum(d.values())
            out[v] = ((len(d) - 1) / tot) if tot else 0.0
        return out

    def eigenvector(self, iters: int = 120, tol: float = 1e-9) -> Dict[Any, float]:
        x = {v: 1.0 / max(1, len(self.V)) for v in self.V}
        for _ in range(iters):
            new = {v: sum(x.get(u, 0.0) * w for u, w in self.adj[v].items()) for v in self.V}
            norm = math.sqrt(sum(x * x for x in new.values())) or 1.0
            new = {v: new[v] / norm for v in new}
            if max(abs(new[v] - x[v]) for v in self.V) < tol:
                x = new
                break
            x = new
        return x

    def pagerank(self, d: float = 0.85, iters: int = 100, tol: float = 1e-9) -> Dict[Any, float]:
        n = len(self.V) or 1
        pr = {v: 1.0 / n for v in self.V}
        for _ in range(iters):
            new = {}
            leak = 0.0
            for v in self.V:
                tot = sum(self.adj[v].values())
                if tot == 0:
                    leak += pr[v]
            for v in self.V:
                s = sum(pr[u] * (w / (sum(self.adj[u].values()) or 1))
                        for u, w in self.adj[v].items())
                new[v] = (1 - d) / n + d * (s + leak / n)
            if max(abs(new[v] - pr[v]) for v in self.V) < tol:
                pr = new
                break
            pr = new
        tot = sum(pr.values()) or 1
        return {v: pr[v] / tot for v in pr}

    def hits(self, iters: int = 80) -> Tuple[Dict[Any, float], Dict[Any, float]]:
        h = {v: 1.0 for v in self.V}
        a = {v: 1.0 for v in self.V}
        for _ in range(iters):
            a = {v: sum(h[u] for u in self.adj[v]) for v in self.V}
            na = math.sqrt(sum(x * x for x in a.values())) or 1
            a = {v: a[v] / na for v in a}
            h = {v: sum(a[u] for u in self.adj[v]) for v in self.V}
            nh = math.sqrt(sum(x * x for x in h.values())) or 1
            h = {v: h[v] / nh for v in h}
        return h, a

    def label_propagation(self, seed: int = 7) -> Dict[Any, int]:
        rnd = random.Random(seed)
        lab = {v: i for i, v in enumerate(self.V)}
        for _ in range(60):
            changed = False
            order = self.V[:]
            rnd.shuffle(order)
            for v in order:
                if not self.adj[v]:
                    continue
                cnt: Dict[int, float] = defaultdict(float)
                for u, w in self.adj[v].items():
                    cnt[lab[u]] += w
                best = max(cnt.items(), key=lambda x: (x[1], -x[0]))[0]
                if best != lab[v]:
                    lab[v] = best
                    changed = True
            if not changed:
                break
        uniq = sorted(set(lab.values()))
        remap = {o: i for i, o in enumerate(uniq)}
        return {v: remap[l] for v, l in lab.items()}


# --------------------------------------------------------------------- io

def load_edges_csv(path: str) -> Graph:
    g = Graph()
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        rows = [r for r in rd if r and any(c.strip() for c in r)]
    if not rows:
        return g
    start = 0
    head = [c.strip().lower() for c in rows[0]]
    if any(h in ("source", "src", "from", "a", "node1", "dari") for h in head):
        start = 1
    for r in rows[start:]:
        if len(r) < 2:
            continue
        a, b = r[0].strip(), r[1].strip()
        w = 1.0
        if len(r) > 2:
            try:
                w = float(str(r[2]).replace(",", "."))
            except ValueError:
                w = 1.0
        if a and b and a != b:
            g.add_edge(a, b, w)
    return g


def load_graph_json(path: str) -> Graph:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    g = Graph()
    for n in d.get("nodes", []):
        if isinstance(n, dict):
            g.add_node(n.get("id"), **{k: v for k, v in n.items() if k != "id"})
        else:
            g.add_node(n)
    for e in d.get("edges", d.get("links", [])):
        if isinstance(e, dict):
            g.add_edge(e.get("source"), e.get("target"), float(e.get("weight", 1)))
        else:
            g.add_edge(e[0], e[1], float(e[2]) if len(e) > 2 else 1.0)
    return g


def demo_graph() -> Graph:
    """Contoh: jaringan brand–KOL–komunitas untuk kampanye F&B."""
    g = Graph()
    meta = {
        "BrandKami": ("brand", 10), "KOL-Kuliner-A": ("kol-mega", 9),
        "KOL-Lifestyle-B": ("kol-mega", 8), "KOL-Review-C": ("kol-mid", 6),
        "KOL-Mikro-D": ("kol-micro", 4), "KOL-Mikro-E": ("kol-micro", 3),
        "KomunitasFoodie": ("komunitas", 7), "Reseller-Jabar": ("reseller", 5),
        "Media-Lokal": ("media", 4), "Marketplace": ("channel", 6),
        "KOL-Parenting-F": ("kol-mid", 5), "KomunitasIbu": ("komunitas", 4),
    }
    for n, (grp, val) in meta.items():
        g.add_node(n, label=n, group=grp, value=val)
    E = [("BrandKami", "KOL-Kuliner-A", 5), ("BrandKami", "KOL-Lifestyle-B", 4),
         ("BrandKami", "Marketplace", 6), ("BrandKami", "Media-Lokal", 2),
         ("BrandKami", "KomunitasFoodie", 3), ("KOL-Kuliner-A", "KOL-Review-C", 4),
         ("KOL-Kuliner-A", "KomunitasFoodie", 3), ("KOL-Lifestyle-B", "KOL-Mikro-D", 2),
         ("KOL-Lifestyle-B", "KOL-Mikro-E", 2), ("KOL-Review-C", "Reseller-Jabar", 3),
         ("KomunitasFoodie", "Reseller-Jabar", 2), ("BrandKami", "KOL-Parenting-F", 3),
         ("KOL-Parenting-F", "KomunitasIbu", 4), ("KomunitasIbu", "Marketplace", 2),
         ("KOL-Mikro-D", "KomunitasFoodie", 1), ("Media-Lokal", "Marketplace", 1)]
    for a, b, w in E:
        g.add_edge(a, b, w)
    return g


# --------------------------------------------------------------------- analyse

def analyze(g: Graph, seed: int = 7) -> Dict[str, Any]:
    V = g.V
    if not V:
        return {"error": "graph kosong"}
    deg = g.degree()
    strg = g.strength()
    bet = g.betweenness()
    clo = g.closeness()
    eig = g.eigenvector()
    pr = g.pagerank()
    hubs, auth = g.hits()
    comm = g.label_propagation(seed)
    comps = g.components()
    n = len(V)
    m = len(g.edges)
    density = (2 * m) / (n * (n - 1)) if n > 1 else 0.0
    if n <= 250 and len(comps[0]) == n:
        dists = [sum(d.values()) for d in (g.bfs_dist(v) for v in V)]
        avg_path = sum(dists) / (n * (n - 1)) if n > 1 else 0.0
        diameter = max((max(g.bfs_dist(v).values()) for v in V), default=0)
    else:
        avg_path, diameter = None, None
    wtot = sum(w for _, _, w in g.edges)

    def rank(d: Dict[Any, float], top: int = 8) -> List[Dict[str, Any]]:
        return [{"node": str(k), "value": round(float(v), 4)}
                for k, v in sorted(d.items(), key=lambda x: -x[1])[:top]]

    size = {c: sum(1 for v in comm if comm[v] == c) for c in set(comm.values())}
    communities = []
    for c in sorted(size, key=lambda x: -size[x]):
        members = [str(v) for v in V if comm[v] == c]
        top = max(members, key=lambda x: pr.get(x, 0))
        communities.append({"id": int(c), "size": size[c], "members": members,
                            "leader": top,
                            "label": str(g.nodes.get(top, {}).get("group", top))})

    per_node = []
    mx_deg = max(deg.values()) or 1
    for v in V:
        per_node.append({
            "id": str(v), "label": str(g.nodes.get(v, {}).get("label", v)),
            "group": str(g.nodes.get(v, {}).get("group", "")),
            "value": float(g.nodes.get(v, {}).get("value", 0) or 0),
            "degree": deg[v], "strength": round(strg[v], 2),
            "betweenness": round(bet[v], 4), "closeness": round(clo[v], 4),
            "eigenvector": round(eig[v], 4), "pagerank": round(pr[v], 4),
            "hub": round(hubs[v], 4), "authority": round(auth[v], 4),
            "community": int(comm[v]),
            "role": _role(deg[v] / mx_deg, bet[v], auth[v], hubs[v]),
        })
    per_node.sort(key=lambda d: -d["pagerank"])

    return {
        "meta": {"nodes": n, "edges": m, "total_weight": round(wtot, 2),
                 "density": round(density, 4), "components": len(comps),
                 "largest_component": len(comps[0]),
                 "avg_path_length": round(avg_path, 3) if avg_path else None,
                 "diameter": diameter, "engine": "networkx+pure" if HAVE_NX else "pure-python"},
        "centrality": {"degree": rank({k: float(v) for k, v in deg.items()}),
                       "betweenness": rank(bet), "closeness": rank(clo),
                       "eigenvector": rank(eig), "pagerank": rank(pr),
                       "authority": rank(auth), "hub": rank(hubs)},
        "communities": communities,
        "nodes": per_node,
        "insights": _graph_insights(per_node, communities, density, comps, n, m),
    }


def _role(ndeg: float, bet: float, auth: float, hub: float) -> str:
    if ndeg >= 0.75 and bet >= 0.15:
        return "Super-connector"
    if bet >= 0.20:
        return "Broker / Bridge"
    if auth >= 0.45:
        return "Authority (sumber pengaruh)"
    if hub >= 0.45:
        return "Hub (penghubung banyak authority)"
    if ndeg >= 0.45:
        return "Influencer lokal"
    if ndeg <= 0.12:
        return "Peripheral (isolat/ujung)"
    return "Anggota jaringan"


def _graph_insights(nodes, communities, density, comps, n, m) -> List[Dict[str, str]]:
    ins = []
    if nodes:
        top = nodes[0]
        ins.append({"title": f"Node paling berpengaruh: {top['label']}",
                    "detail": f"PageRank {top['pagerank']:.3f}, degree {top['degree']}, "
                              f"betweenness {top['betweenness']:.3f}. Peran: {top['role']}.",
                    "action": f"Jadikan '{top['label']}' sebagai anchor kampanye dan negosiasi "
                              f"eksklusivitas lebih awal — jaringan bergantung padanya."})
        br = [x for x in nodes if x["role"].startswith(("Broker", "Super"))]
        if br:
            b = br[0]
            ins.append({"title": f"Titik rawan (single point of failure): {b['label']}",
                        "detail": f"Betweenness {b['betweenness']:.3f} — banyak jalur komunikasi "
                                  f"melewatinya. Jika node ini non-aktif, jaringan terpecah.",
                        "severity": "warn",
                        "action": "Bangun jalur cadangan: hubungkan 2-3 node periferal langsung "
                                  "ke brand agar tidak bergantung pada satu perantara."})
    periph = [x for x in nodes if x["role"].startswith("Peripheral")]
    if periph:
        ins.append({"title": f"{len(periph)} node periferal ({len(periph) / max(1, n) * 100:.0f}% jaringan)",
                    "detail": "Node dengan koneksi minim: " +
                              ", ".join(p["label"] for p in periph[:6]) +
                              ("…" if len(periph) > 6 else ""),
                    "severity": "info",
                    "action": "Aktifkan lewat program komunitas/UGC; node periferal yang "
                              "diaktifkan sering jadi micro-influencer paling efisien (CPM rendah)."})
    if len(comps) > 1:
        ins.append({"title": f"Jaringan terpecah jadi {len(comps)} komponen",
                    "detail": f"Komponen terbesar {len(comps[0])} node; "
                              f"{n - len(comps[0])} node terisolasi dari komponen utama.",
                    "severity": "bad",
                    "action": "Buat konten kolaboratif lintas-cluster untuk menjembatani "
                              "komponen yang terpisah."})
    else:
        ins.append({"title": "Jaringan terhubung penuh",
                    "detail": f"Density {density:.3f} dengan {m} relasi antar {n} node. "
                              f"{'Rapat — informasi menyebar cepat.' if density > 0.2 else 'Renggang — butuh amplifier.'}",
                    "severity": "good" if density > 0.2 else "info",
                    "action": "Pertahankan density > 0,2 dengan kolaborasi antar-KOL (bukan hanya brand→KOL)."})
    if len(communities) > 1:
        c = communities[0]
        ins.append({"title": f"{len(communities)} komunitas terdeteksi; terbesar = '{c['label']}' ({c['size']} node)",
                    "detail": "Leader tiap komunitas: " +
                              ", ".join(f"{x['label']} ({x['size']})" for x in communities[:4]),
                    "action": "Sesuaikan pesan per komunitas; jangan pakai satu creative untuk semua cluster."})
    return ins


# --------------------------------------------------------------------- report / viz

def to_markdown(R: Dict[str, Any], title: str = "Analisa Graph") -> str:
    mt = R["meta"]
    L = [f"# {title}", "",
         f"**{mt['nodes']} node · {mt['edges']} relasi · density {mt['density']:.4f} · "
         f"{mt['components']} komponen**  ",
         f"_Engine: {mt['engine']} · avg path {mt['avg_path_length']} · diameter {mt['diameter']}_", "",
         "## Node Terpenting (PageRank)", "",
         "| # | Node | Grup | Peran | Degree | Betweenness | PageRank | Komunitas |",
         "|---|---|---|---|---|---|---|---|"]
    for i, nd in enumerate(R["nodes"][:12], 1):
        L.append(f"| {i} | {nd['label']} | {nd['group'] or '-'} | {nd['role']} | {nd['degree']} | "
                 f"{nd['betweenness']:.3f} | {nd['pagerank']:.3f} | {nd['community']} |")
    L += ["", "## Komunitas / Cluster", ""]
    for c in R["communities"]:
        L.append(f"- **Cluster {c['id']} — {c['label']}** ({c['size']} node, leader: {c['leader']}): "
                 + ", ".join(c["members"][:10]) + ("…" if len(c["members"]) > 10 else ""))
    L += ["", "## Insight & Rekomendasi", ""]
    for i, x in enumerate(R["insights"], 1):
        icon = {"good": "✅", "warn": "⚠️", "bad": "⛔"}.get(x.get("severity", "info"), "ℹ️")
        L.append(f"{i}. {icon} **{x['title']}** — {x['detail']}")
        if x.get("action"):
            L.append(f"   → _Aksi: {x['action']}_")
    L += ["", "## Cara Pakai untuk Marketing", "",
          "- **Pemilihan KOL**: urutkan PageRank × relevansi grup, bukan sekadar follower.",
          "- **Deteksi echo chamber**: komunitas dengan density internal tinggi tapi bridge sedikit "
          "= pesan tidak akan menyebar keluar cluster.",
          "- **Mitigasi risiko**: node ber-betweenness tinggi adalah single point of failure.",
          "- **Efisiensi budget**: node periferal yang terhubung ke authority = CPV termurah.",
          "", "---", "_DAN · Graph Analyst. Betweenness dinormalisasi; PageRank d=0,85._"]
    return "\n".join(L)


def to_svg(R: Dict[str, Any], g: Graph, title: str = "Jaringan Marketing",
           width: int = 900, height: int = 620, th: str = "dan") -> str:
    grp_index = {}
    for nd in R["nodes"]:
        if nd["group"] and nd["group"] not in grp_index:
            grp_index[nd["group"]] = len(grp_index)
    nodes = []
    for nd in R["nodes"]:
        nodes.append({"id": nd["id"], "label": nd["label"],
                      "group": grp_index.get(nd["group"], nd["community"]),
                      "value": nd["pagerank"] * 100})
    edges = [(a, b, w) for a, b, w in g.edges]
    sub = (f"{R['meta']['nodes']} node · {R['meta']['edges']} relasi · "
           f"density {R['meta']['density']:.3f} · ukuran node = PageRank")
    return sc.network(nodes, edges, title=title, subtitle=sub, width=width, height=height,
                      th=th, size_by="value", weighted=True)


def to_spec_json(R: Dict[str, Any], g: Graph) -> Dict[str, Any]:
    """Siap disuntikkan ke data-spec.json sebagai section chart 'network'."""
    grp_index = {}
    for nd in R["nodes"]:
        if nd["group"] and nd["group"] not in grp_index:
            grp_index[nd["group"]] = len(grp_index)
    return {
        "type": "chart", "chart": "network", "span": 12,
        "title": "Jaringan Marketing", "width": 1100, "height": 620,
        "data": {"nodes": [{"id": nd["id"], "label": nd["label"],
                            "group": grp_index.get(nd["group"], nd["community"]),
                            "value": round(nd["pagerank"] * 100, 2)} for nd in R["nodes"]],
                 "edges": [[a, b, w] for a, b, w in g.edges]},
        "note": "Ukuran node proporsional terhadap PageRank.",
    }


# --------------------------------------------------------------------- main

def main(argv: Optional[Sequence[str]] = None) -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.environ.get("DAN_ROOT") or os.path.abspath(os.path.join(here, "..", "..", ".."))
    dl = os.path.join(root, "deliverables")
    ap = argparse.ArgumentParser(description="DAN · Graph Analyst")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--edges", help="CSV source,target[,weight]")
    src.add_argument("--graph", help="JSON {nodes, edges}")
    src.add_argument("--demo", action="store_true", help="pakai contoh bawaan")
    ap.add_argument("--title", default="Jaringan Marketing")
    ap.add_argument("--out", default=os.path.join(dl, "graph.json"))
    ap.add_argument("--svg", default=os.path.join(dl, "graph.svg"))
    ap.add_argument("--report", default=os.path.join(dl, "graph.md"))
    ap.add_argument("--theme", default="dan", choices=list(sc.THEMES))
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--height", type=int, default=620)
    a = ap.parse_args(argv)

    if a.demo:
        g = demo_graph()
    elif a.graph:
        g = load_graph_json(a.graph)
    else:
        g = load_edges_csv(a.edges)
    if not g.V:
        sys.exit("[DAN] graph kosong — periksa format input.")

    R = analyze(g)
    for p in (a.out, a.svg, a.report):
        os.makedirs(os.path.dirname(os.path.abspath(p)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    with open(a.svg, "w", encoding="utf-8") as f:
        f.write(to_svg(R, g, a.title, a.width, a.height, a.theme))
    with open(a.report, "w", encoding="utf-8") as f:
        f.write(to_markdown(R, a.title))
    mt = R["meta"]
    print(f"[DAN] graph: {mt['nodes']} node / {mt['edges']} relasi / density {mt['density']:.3f} "
          f"/ {len(R['communities'])} komunitas ({mt['engine']})")
    print(f"[DAN] top: " + ", ".join(f"{x['node']}({x['value']:.3f})"
                                     for x in R["centrality"]["pagerank"][:3]))
    print(f"[DAN] -> {a.out}\n[DAN] -> {a.svg}\n[DAN] -> {a.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
