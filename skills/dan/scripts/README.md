# scripts/ — Engine DAN

Semua engine inti **zero-dependency** (stdlib Python 3.8+). Dependensi opsional ada di
`requirements.txt`.

## Cara cepat
```bash
python3 _test_all.py        # 97 pemeriksaan; harus 0 gagal sebelum menyerahkan hasil
python3 _check_refs.py      # referensi silang dokumen = 0 hilang
```

## Engine
| File | Fungsi |
|---|---|
| `dan_analytics.py` | CSV/XLSX → KPI, tren, forecast, anomali, Pareto, korelasi → JSON/MD/CSV |
| `xlsx_lite.py` | baca .xlsx tanpa dependensi (nilai cache + formula) → stdout/CSV/JSON |
| `plan_analyst.py` | business plan xlsx → pencapaian vs target, YoY, gap divisi, EA/CB/IPT, SCD, tim, proyeksi, DQ, projects.json |
| `cost_router.py` | rekomendasi rute model (gratis/lokal/berbayar) saat kuota menipis |
| `svg_charts/` | Paket 18 tipe chart SVG murni (module-map di `svg_charts/__init__.py`) |
| `make_infographic.py` | JSON → infografik HTML self-contained (AUTO & SPEC) + poster SVG |
| `graph_analyst.py` | metrik jaringan (PageRank, betweenness, …) + visual + laporan |
| `storyboard.py` | brief → shot list bertiming, VO, prompt image/video, SRT |
| `fit_asset.py` | crop/pad gambar ke rasio platform (butuh Pillow) |
| `project_monitor.py` | monitoring/tracking/progress/controlling + coach |
| `make_forms.py` | form interaktif progress/monitoring/controlling → batch JSON |
| `arch_advisor.py` | scaffold multi-bahasa, review kelebihan/kekurangan, compare trade-off |
| `arch_design.py` | denah 2D, massa 3D isometrik, tampak, KDB/KLB, RAB, konstruksi |
| `exec_dashboard.py` | dashboard eksekutif gabungan (marketing+proyek+arsitektur) |
| `weekly_run.py` | otomasi ritme mingguan (apply→report→coach→dashboard→ringkasan) |
| `pmo_guard.py` | policy gate mingguan (exit code untuk CI/cron) |
| `make_slides.py` | slide deck HTML self-contained untuk rapat |
| `claim_audit.py` | validator provenance angka (anti angka karangan) |
| `dan.py` | unified CLI (list/run/new/audit/doctor) |
| `run_cases.py` | runner katalog kasus end-to-end |
| `i18n.py` | label struktural ID/EN |
| `i18n_queue.py` | antrean terjemahan narasi (extract/apply) |
| `export_png.py` | SVG/HTML → PNG (renderer opsional, fallback jujur) |
| `make_pyz.py` | bangun dan.pyz single-file |
| `make_package.py` | manifest sha256 + zip siap-import + INSTALL + CHANGELOG |
| `make_sample_data.py` | generator data demo |
| `prompt_lab.py` | lint/skor/varian prompt (sub-skill 10) |
| `workflow.py` | runner workflow JSON (sub-skill 11) |
| `rag.py` | RAG stdlib bersitasi (sub-skill 13) |
| `stack_advisor.py` | rekomendasi stack tool AI (sub-skill 17) |
| `assistant_builder.py` | builder asisten kustom (sub-skill 15) |
| `llm_obs.py` | observability LLM (sub-skill 20) |
| `weekly_diff.py` | riwayat append-only + diff mingguan |
| `demo_tour.py` | tur onboarding sub-skill 01-21 |
| `rag_eval.py` | eval retrieval RAG (recall/MRR/miss) |
| `make_digest.py` | digest rilis + naskah audio |
| `make_adapters.py` | ekspor adapter per runtime AI |
| `mcp_server.py` | server MCP stdio (10 tool) |
| `mcp_smoke.py` | uji integrasi nyata semua tool MCP |
| `notify.py` | notifikasi mingguan multi-channel |
| `burnup.py` | burn-up multi-periode |
| `budget_sim.py` | simulator budget what-if |
| `weekly.py` | ritme mingguan satu perintah |
| `narrative_check.py` | pemeriksa kualitas narasi |
| `annotate.py` | lapisan anotasi review |
| `client_report.py` | laporan klien non-teknis (ID/EN) |
| `export_pdf.py` | ekspor PDF headless (fallback jujur) |
| `pkg_health.py` | dashboard kesehatan paket |
| `release.py` | rilis ber-gate satu perintah |
| `print_deck.py` | deck cetak A4 landscape |
| `init_wizard.py` | wizard onboarding |
| `weekly_watch.py` | watchdog mingguan |
| `showcase.py` | galeri showcase |
| `narrative_trend.py` | tren kualitas narasi |
| `make_bundle.py` | bundle offline |
| `multi_client.py` | dashboard lintas-klien |
| `make_sop.py` | SOP/runbook tim |
| `crisis_sim.py` | simulasi krisis |
| `sec_audit.py` | audit keamanan ringan |
| `make_course.py` | paket pelatihan deck+audio |

## QA / test
| File | Fungsi |
|---|---|
| `_test_all.py` | smoke test terpadu (parser, chart, spec/auto, storyboard, graph, monitoring, forms, arch) |
| `_validate_svg.py <file>` | cek semua `<svg>` dalam file adalah XML valid |
| `_check_layout.py <file>` | cek tidak ada teks/elemen keluar kanvas |
| `_check_refs.py` | cek referensi file antar dokumen tidak mati |
| `_test_graph.py` | cross-check metrik graph vs networkx |
| `props_test.py` | property-based test: invariant acak ber-seed (parser, ticks, chart, layout, RAG, compare) |

## Konvensi kode
- Output artefak selalu ke `deliverables/` di root workspace (jangan `output/`, `build/`,
  `dist/` — nama itu diabaikan snapshot workspace).
- Semua teks pengguna di-escape (`sc.esc`) sebelum masuk SVG/HTML.
- Angka diformat lewat `sc.fmt_num(v, loc)` dengan `loc="id"` default.
- Jangan menambah dependensi wajib; bila perlu fitur berat, jadikan opsional + fallback.
- File bernama awal `_` = tool QA/internal, bukan engine publik.
