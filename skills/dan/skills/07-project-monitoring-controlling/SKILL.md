---
name: dan-project-monitoring-controlling
description: >-
  Tools manajemen proyek untuk marketing: MONITORING (tinjauan berkala + RAG + KPI + risiko),
  TRACKING (status tiap tugas vs rencana, SPI, variance, hari terlambat, deteksi stalled),
  PROGRESS (% selesai berbobot, burn-up planned-vs-actual, forecast tanggal selesai),
  CONTROLLING (earned value CPI/EAC, matriks risiko, tindakan korektif/preventif),
  plus FORM interaktif (form progress, form monitoring, form controlling) dan Gantt chart.
  Terintegrasi dengan sub-skill motivator: pesan coaching dibangun dari data proyek.
  Gunakan saat pengguna menanyakan status proyek, progres kampanye, apakah on-track,
  tugas mana yang terlambat/stalled, laporan mingguan PMO, dashboard proyek, atau butuh
  form untuk update tim.
---

# 07 · Project Monitoring, Tracking, Progress & Controlling

## Prinsip
1. **Rencana adalah pembanding, bukan hiasan.** Setiap % aktual harus punya % rencana
   pada tanggal yang sama (interpolasi linear start→end bila tidak diisi manual).
2. **Variance dilaporkan dalam poin persentase (pp)**, bukan persen dari persen.
3. **Deteksi dini lebih berharga daripada laporan rapi**: stalled & terlambat harus
   muncul otomatis tanpa diminta.
4. **Controlling = keputusan**, bukan catatan: setiap variance melewati ambang wajib
   punya tindakan korektif ber-owner & ber-tenggat (form controlling).
5. **Motivasi mengikuti data**: pesan coach diambil dari fakta monitoring
   (lihat `coach`), bukan kata penyemangat generik.

---

## A. Perintah inti

```bash
cd skills/dan/scripts

# laporan lengkap: report.md + report.json + dashboard.html (Gantt, progress, burn-up,
# matriks risiko, beban owner, tabel tracking, insight, coach)
python3 project_monitor.py report ../templates/projects.example.json

# cek cepat di terminal
python3 project_monitor.py status ../templates/projects.example.json

# terapkan update dari form terisi (batch.json dari forms.html)
python3 project_monitor.py apply projects.json batch.json --out projects_updated.json

# pesan motivator per owner (berbasis data)
python3 project_monitor.py coach projects.json

# form interaktif (monitoring / controlling / progress) — self-contained
python3 make_forms.py --projects ../templates/projects.example.json \
    --out ../../../deliverables/forms.html
```

Alur mingguan yang disarankan:
```
Senin  → tim isi FORM PROGRESS (5 menit/orang)
Senin  → PMO jalankan: apply → report → bagikan dashboard
Jumat  → tinjau FORM MONITORING (RAG, KPI, risiko) + putuskan
Bila variance melewati ambang → isi FORM CONTROLLING hari itu juga
```

---

## B. Model data (`projects.json`)

```jsonc
{
  "meta": { "name": "...", "currency": "Rp", "today": "2026-09-16", "theme": "dan" },
  "projects": [{
    "id": "PRJ-01", "name": "...", "owner": "...",
    "start": "2026-09-01", "end": "2026-10-15",
    "budget_planned": 250000000, "budget_actual": 96000000,
    "goal": "...",
    "kpi": [{ "name": "ROAS", "target": 3.0, "actual": 2.4 }],
    "tasks": [{
      "id": "T5", "name": "Landing page & CRO", "owner": "Dewi",
      "start": "2026-09-10", "end": "2026-09-18",
      "progress": 40,            // aktual 0-100
      "weight": 18,              // bobot untuk % proyek
      "planned_progress": null,  // opsional; null = dihitung dari tanggal
      "status": "", "blockers": ["..."], "notes": ""
    }],
    "risks":  [{ "desc": "...", "prob": 3, "impact": 5, "mitigation": "...", "owner": "..." }],
    "actions":[{ "issue": "...", "root_cause": "...", "action": "...",
                 "owner": "...", "due": "2026-09-19", "status": "open" }]
  }],
  "history": [ { "form": "progress", "project": "PRJ-01", "task": "T5",
                 "date": "2026-09-15", "progress": 40 } ]   // diisi otomatis oleh `apply`
}
```

`history` adalah sumber deteksi **stalled** dan bahan kurva **burn-up aktual**.

---

## C. Metrik & ambang (wajib konsisten di semua keluaran)

| Metrik | Rumus | Ambang |
|---|---|---|
| Planned progress | interpolasi linear start→end pada tanggal laporan (atau isi manual) | — |
| Variance | aktual − rencana (pp) | ≥ −5 on-track · **−20 ≤ var < −5** waspada · **var < −20** kritis |
| SPI | aktual ÷ rencana | ≥1 baik · 0,9–1 perhatikan · <0,75 intervensi |
| Terlambat | hari sejak `end` bila progres <100 | ≤3 hari waspada · >3 hari kritis |
| Stalled | progres sama pada ≥2 update berjarak ≥3 hari, ATAU tanpa update >7 hari | flag |
| % proyek | Σ(bobot × progres) ÷ Σ bobot | — |
| EV | budget_planned × %selesai | — |
| CPI | EV ÷ budget_actual | ≥1 baik · 0,85–1 waspada · <0,85 kritis |
| EAC | budget_planned ÷ CPI | bandingkan vs budget |
| Forecast selesai | hari ini + (sisa % ÷ laju %/hari) | slip = forecast − rencana |
| Skor risiko | probabilitas × dampak (1–5) | ≥12 kritis · 6–11 waspada · <6 pantau |

> Batas ambang ditulis **tegas** (var < −5, bukan ≤) agar form, engine, dan laporan
> memberi hasil identik.

---

## D. Tiga form (versi interaktif & versi dokumen)

| Form | Kapan diisi | Versi interaktif | Versi dokumen |
|---|---|---|---|
| **Progress** | tiap anggota, mingguan (5 menit) | tab 1 di `forms.html` | `templates/form-progress.md` |
| **Monitoring** | PMO/lead, saat tinjauan berkala | tab 2 di `forms.html` | `templates/form-monitoring.md` |
| **Controlling** | segera saat variance melewati ambang | tab 3 di `forms.html` | `templates/form-controlling.md` |

Form interaktif menghasilkan **batch JSON** yang langsung bisa dipakai:
`project_monitor.py apply projects.json batch.json`.
Form dokumen dipakai bila tim lebih nyaman mengisi di chat/dokumen; PMO menyalinnya
ke batch JSON atau langsung ke `projects.json`.

**Aturan mutu pengisian:**
1. `% aktual` berbasis bukti (aset jadi, baris kode merged, kontrak signed) — bukan perasaan.
2. Blocker wajib disebut bila progres tidak bergerak; blocker tanpa owner = belum dikelola.
3. Form controlling wajib memisahkan **akar masalah** dari gejala.
4. Satu record = satu fakta; jangan gabung beberapa tugas dalam satu record progress.

---

Visual linimasa memakai chart `gantt` (warna RAG, % aktual, garis "hari ini",
milestone) dan `progress` (bullet bar dengan garis target) dari paket
`svg_charts` — keduanya SVG murni sehingga tajam dicetak & offline.

## E. Dashboard (keluaran `report`)

Urutan blok dan maksudnya:
1. **KPI portofolio** — proyek, % rata-rata, on-track/waspada/kritis, terlambat, stalled, budget.
2. **Gantt tracking** — semua tugas, warna RAG, % aktual, garis "hari ini".
3. **Progress vs rencana** — bullet bar per proyek (garis tegak = rencana hari ini).
4. **Burn-up planned vs actual** — akumulasi bobot; jarak antar garis = besar masalah.
5. **Matriks risiko** — probabilitas × dampak; sel kanan-atas wajib ber-mitigasi.
6. **Beban per owner** — deteksi kandidat burnout (beban tinggi + tugas kritis).
7. **Tabel tracking** — variance terburuk dulu, lengkap dengan blocker.
8. **Tindakan korektif** — dari form controlling, dengan status.
9. **Insight + coach** — aksi & pesan motivator berbasis data.

---

## E1b. Ritme satu perintah (cron-ready)
```bash
python3 weekly.py --projects projects.json --updates batch.json \
    --channel slack --out-dir out/
```
Menjalankan berurutan: weekly_run → snap → burnup → guard → notify → digest →
narrative → claim_audit, tercatat di `run_log.json`; exit≠0 bila guard gagal
(kecuali `--allow-guard-fail`) sehingga cron/CI bisa memberi sinyal.

## E2. Notifikasi & tren multi-periode
- `notify.py --channel slack|telegram|email` merangkai pesan dari summary + guard
  (tanpa mengirim; contoh curl disertakan agar secret tetap milik Anda).
- `burnup.py` membaca `history.jsonl` (isi lewat `weekly_diff.py snap` tiap minggu)
  dan menampilkan burn-up Aktual vs Rencana + proyek stagnan ≥2 snapshot.

## F. Ritme governance

| Ritme | Isi | Durasi | Keluaran |
|---|---|---|---|
| Harian (opsional) | angka kritis saja | 5 mnt | catatan blocker |
| Mingguan | apply → report → keputusan | 30 mnt | dashboard + 3 keputusan |
| Bulanan | review risiko, budget (CPI/EAC), scope | 60 mnt | perubahan baseline bila perlu |
| Per milestone | retro + update baseline | 45 mnt | lessons learned |

**Aturan escalation:**
- Tugas kritis >3 hari → owner + lead bahas dalam 1×24 jam.
- CPI <0,85 → freeze pengeluaran non-kritis sampai review budget.
- Slip forecast >7 hari → putuskan salah satu: tambah resource / kurangi scope / geser tanggal,
  dan komunikasikan ke stakeholder pada minggu yang sama.

---

## G. Integrasi dengan sub-skill lain
- **06 Motivator Expert** — `project_monitor.py coach` memakai pola dari
  `references/motivation-playbook.md` (acknowledge → fakta → angka → reframe → langkah 15 menit).
- **03 Infographic** — dashboard dibangun lewat `make_infographic.py` (mode SPEC);
  Gantt & progress bar dari paket `svg_charts`.
- **02 Strategist** — bila variance struktural (bukan eksekusi), naikkan ke review strategi.
- **01 Data Analyst** — KPI kampanye di form monitoring sebaiknya ditarik dari
  `analysis.json`, bukan diketik ulang.

## H. Jebakan umum monitoring
1. **% selesai subjektif** ("rasanya sudah 80%") → wajib bukti; gunakan definisi selesai per tugas.
2. **Rencana tidak pernah di-update** → variance jadi tidak berarti; revisi baseline saat scope berubah dan catat alasannya.
3. **Melaporkan rata-rata saja** → tugas kritis tenggelam; selalu tampilkan variance terburuk.
4. **Form jadi beban** → bila mengisi >10 menit/orang/minggu, sederhanakan field, bukan paksa disiplin.
5. **Controlling tanpa preventive** → masalah yang sama kembali bulan depan.
