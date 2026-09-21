# FORM MONITORING — Tinjauan Berkala Proyek

> Diisi oleh **PMO / lead proyek** pada setiap tinjauan (mingguan/bulanan).
> Versi interaktif: tab **2 · Form Monitoring** di `forms.html`.
> Menjadi record `"form": "monitoring"` pada batch JSON.
> Sumber angka KPI sebaiknya dari `analysis.json` (sub-skill 01), bukan diketik ulang.

---

**Tanggal tinjauan** : `____-__-__`
**Proyek**           : `[ID]` — `[nama]`
**Periode dilaporkan** : `____-__-__` s.d. `____-__-__`
**Reviewer**         : `[nama]`

## 1. Status keseluruhan pekan ini  (pilih satu)
- [ ] **GREEN** — on-track; variance ≥ −5 pp; tidak ada blocker kritis
- [ ] **YELLOW** — waspada; −20 ≤ variance < −5 pp, atau terlambat ≤3 hari, atau blocker aktif
- [ ] **RED** — kritis; variance < −20 pp, atau terlambat >3 hari, atau CPI < 0,85

Alasan status (1 kalimat, sebut angka):

## 2. Progres & biaya
| Field | Nilai |
|---|---|
| % selesai aktual (berbobot) | `___` % |
| % selesai rencana | `___` % |
| Variance | `___` pp |
| Biaya aktual kumulatif | Rp `___` |
| Budget tersisa | Rp `___` |
| CPI (EV ÷ biaya aktual) | `___` |

## 3. KPI
| KPI | Target | Aktual pekan lalu | Aktual pekan ini | Tren | Status |
|---|---|---|---|---|---|
| | | | | ↑ / → / ↓ | 🟢🟡 |
| | | | | | |
| | | | | | |

## 4. Risiko (perbarui skor & mitigasi)
| # | Deskripsi | Prob (1-5) | Dampak (1-5) | Skor | Mitigasi | Owner | Tenggat |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
| | | | | | | | |

Risiko baru pekan ini:
Risiko yang tertutup/tidak relevan lagi:

## 5. Tugas yang perlu perhatian (max 3)
| Tugas | Owner | Masalah | Keputusan pekan ini |
|---|---|---|---|
| | | | |

## 6. Ringkasan untuk stakeholder (maks 3 kalimat)
1.
2.
3.

## 7. Keputusan & tindak lanjut
| Keputusan | Owner | Tenggat |
|---|---|---|
| | | |

---
### Pemetaan ke JSON
```json
{ "form": "monitoring", "project": "PRJ-01", "date": "2026-09-16", "rag": "yellow",
  "budget_actual": 96000000,
  "kpi": [ { "name": "ROAS", "target": 3.0, "actual": 2.4 } ],
  "risks": [ { "desc": "KOL utama batal", "prob": 2, "impact": 4,
               "mitigation": "3 KOL cadangan", "owner": "Sari" } ],
  "summary": "Media buying jalan; landing page jadi bottleneck." }
```
