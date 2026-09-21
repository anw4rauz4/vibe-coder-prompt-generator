# Software Architecture Guide — Trade-off & Keputusan

Rujukan untuk sub-skill **08**. Knowledge base mesin ada di `arch_advisor.py`;
dokumen ini menambah **kedalaman keputusan** yang tidak muat di kode.

---

## 1. Peta trade-off pola arsitektur

| Pola | Kecepatan rilis | Biaya ops | Skala tim | Kompleksitas | Kapan JANGAN dipakai |
|---|---|---|---|---|---|
| Monolith | cepat (1 pipeline) | rendah | ≤10 | rendah | tim besar otonom, scale per-bagian sangat berbeda |
| Modular monolith | cepat | rendah | 5–25 | sedang | butuh isolasi deploy per modul |
| Microservices | cepat per tim | tinggi | ≥20 (multi-tim) | tinggi | tim < 4, domain belum jelas |
| Serverless | sangat cepat | sangat rendah saat idle | kecil | sedang | proses panjang, latency sensitif, traffic konstan tinggi |
| Event-driven | sedang | sedang | sedang+ | sedang-tinggi | alur sederhana sinkron cukup |
| Layered | sedang | rendah | semua | rendah | domain kompleks butuh isolasi |
| Hexagonal | sedang (awal lambat) | rendah | sedang+ | sedang | CRUD sederhana, prototipe |
| CQRS | sedang | sedang-tinggi | sedang+ | tinggi | baca≈tulis, tidak butuh audit/replay |

**Aturan emas:** mulai dari yang paling sederhana yang memenuhi kebutuhan 12 bulan ke
depan, dan **desain batas modul sejak hari pertama** supaya bisa dipecah nanti tanpa
rewrite (monolith → modular → services).

## 2. Kapan microservices benar-benar diperlukan (checklist)
Butuh **≥3** dari ini; bila tidak, tetap monolith:
- [ ] ≥4 tim yang perlu rilis independen tiap minggu
- [ ] beban sangat tidak merata antar bagian (perlu scale terpisah)
- [ ] kebutuhan isolasi kegagalan/keamanan per bagian (mis. pembayaran)
- [ ] domain sudah stabil & terpetakan (bounded contexts jelas)
- [ ] ada platform team yang merawat CI/CD, observability, service discovery

## 3. Database — pertanyaan penentu
| Pertanyaan | Bila YA | Bila TIDAK |
|---|---|---|
| Butuh transaksi multi-baris ACID & join kompleks? | PostgreSQL/MySQL | pertimbangkan dokumen/KV |
| Skema berubah sangat cepat & nested? | MongoDB | relasional |
| Baca ≫ tulis dengan agregasi analitik? | ClickHouse/warehouse | OLTP DB |
| Butuh latensi sub-ms untuk cache/session? | Redis | — |
| Data = file/blob besar? | Object storage | — |
| Perlu full-text/facet search? | Elasticsearch (+DB utama) | LIKE/ILIKE cukup di awal |

**Pola aman:** satu OLTP (PostgreSQL) + Redis cache + object storage; tambah search/
warehouse hanya saat terasa sakit. Jangan polyglot persistence di hari pertama.

## 4. Bahasa — faktor selain "cepat/lambat"
| Faktor | Pertanyaan |
|---|---|
| Hiring | seberapa besar pool talent lokal & gaji pasar? |
| Ekosistem | apakah library inti domain sudah matang (AI→Python, web→TS/Go)? |
| Operasional | binary tunggal & memory footprint (Go/Rust unggul di container) |
| Kecepatan iterasi | dynamic typing cepat di awal, static typing murah saat besar |
| Longevity | seberapa lama kode harus hidup & dirawat siapa? |

## 5. Hosting — kurva keputusan
```
traffic kecil & tim kecil      → PaaS / static+CDN
mulai banyak service & tim ops → container + orchestrator
beban sporadis/event-driven    → serverless
compliance/kontrol penuh       → VM self-managed / on-prem
```
Biaya tersembunyi yang sering dilupakan: egress, logging/monitoring berbayar,
managed DB premium, dan waktu engineer untuk mengurus platform.

## 6. Template ADR (Architecture Decision Record) — 1 halaman
```markdown
# ADR-00X: <judul keputusan>
Status: proposed | accepted | deprecated | superseded oleh ADR-00Y
Tanggal: YYYY-MM-DD · Pengambil keputusan: <nama>

## Konteks
Masalah/kebutuhan apa; batasan apa (tim, budget, tenggat, compliance).

## Pilihan yang dipertimbangkan
1. <opsi A> — kelebihan / kekurangan
2. <opsi B> — kelebihan / kekurangan
3. <opsi C> — kelebihan / kekurangan

## Keputusan
Kami memilih <opsi> karena <alasan terukur>.

## Konsekuensi
- Positif: …
- Negatif / utang yang diterima: …
- Yang harus dipantau: <metrik + ambang>
```
Simpan semua ADR di repo (`docs/adr/`). Keputusan tanpa ADR = keputusan yang akan
diperdebatkan ulang selamanya.

## 7. Checklist review arsitektur (untuk sesi design review)
- [ ] Batas modul/service jelas & satu alasan untuk berubah
- [ ] Tidak ada circular dependency antar modul
- [ ] Data ownership: satu writer per data; pembaca lewat API/event
- [ ] Strategi kegagalan: timeout, retry+backoff, circuit breaker, fallback
- [ ] Observability: log terstruktur, metric, trace id lintas batas
- [ ] Keamanan: authn/authz di batas, rahasia di secret manager, input tervalidasi
- [ ] Kinerja: target p95 latency & throughput tercatat; ada load test plan
- [ ] Data: skema migrasi backward-compatible, backup & restore teruji
- [ ] Biaya: estimasi biaya infra per 1000 permintaan/transaksi
- [ ] Jalan keluar: apa rencana bila pilihan ini salah (exit strategy)

## 8. Anti-pattern yang sering muncul
| Anti-pattern | Tanda | Perbaikan |
|---|---|---|
| Distributed monolith | service saling panggil sinkron berantai, rilis harus bareng | konsolidasikan atau jadikan event-driven |
| God module | 1 file/modul >600 baris, banyak tanggung jawab | pecah berdasar tanggung jawab |
| Database shared antar service | 2 service tulis tabel sama | pisahkan ownership, sinkron lewat event |
| Premature microservices | 3 orang, 8 service | kembali ke modular monolith |
| Config hardcode | rahasia di kode/repo | env/secret manager + rotasi |
| No tests on core logic | logika bisnis tanpa test | test unit dulu sebelum fitur baru |
