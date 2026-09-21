#!/usr/bin/env python3
"""Cross-check metrik graph pure-python DAN vs networkx (ground truth)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import networkx as nx
import graph_analyst as ga

g = ga.demo_graph()
G = nx.Graph()
for a, b, w in g.edges:
    G.add_edge(a, b, weight=w)

mine = {
    "betweenness": g.betweenness(),
    "closeness": g.closeness(),
    "eigenvector": g.eigenvector(),
    "pagerank": g.pagerank(),
}
ref = {
    "betweenness": nx.betweenness_centrality(G, normalized=True),
    "closeness": nx.closeness_centrality(G),
    "eigenvector": nx.eigenvector_centrality(G, weight="weight", max_iter=2000),
    "pagerank": nx.pagerank(G, alpha=0.85),
}
worst = 0.0
for k in mine:
    print(f"\n--- {k}")
    for n in sorted(G.nodes, key=lambda x: -ref[k][x])[:5]:
        a, b = mine[k][n], ref[k][n]
        d = abs(a - b)
        worst = max(worst, d)
        flag = "ok " if d < 0.02 else ("~  " if d < 0.08 else "DIF")
        print(f"  {flag} {n:20} dan={a:.4f}  nx={b:.4f}  Δ={d:.4f}")

deg_ok = all(g.degree()[n] == G.degree[n] for n in G.nodes)
comp_ok = len(g.components()) == nx.number_connected_components(G)
dens_ok = abs((2 * len(g.edges)) / (len(g.V) * (len(g.V) - 1)) - nx.density(G)) < 1e-9
print(f"\ndegree match={deg_ok}  components match={comp_ok}  density match={dens_ok}")
print(f"deviasi terbesar metrik centrality: {worst:.4f}")
print("HASIL:", "LULUS" if (worst < 0.02 and deg_ok and comp_ok and dens_ok) else "PERLU DICEK")
