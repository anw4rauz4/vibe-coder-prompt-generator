# FORM PROGRESS — Update Mingguan Tugas

> Diisi oleh **setiap pemilik tugas**, maksimal 5 menit, tiap Senin sebelum tinjauan.
> Versi interaktif: tab **1 · Form Progress** di `forms.html`.
> Hasil form ini menjadi record `"form": "progress"` pada batch JSON →
> `python3 project_monitor.py apply projects.json batch.json`.

---

**Tanggal update** : `____-__-__`
**Proyek**         : `[ID proyek]` — `[nama proyek]`
**Tugas**          : `[ID tugas]` — `[nama tugas]`
**Owner**          : `[nama]`

## 1. Progres
| Field | Isi |
|---|---|
| Progres aktual (%) | `___` %  _(0–100, berbasis bukti)_ |
| Progres rencana hari ini (%) | dihitung otomatis / `___` % |
| Selisih (aktual − rencana) | `___` pp |
| Effort aktual kumulatif (orang-hari) | `___` |

**Bukti kemajuan pekan ini** (tautan/file/aset yang benar-benar selesai):
1.
2.

## 2. Blocker _(wajib diisi bila progres tidak bergerak)_
| # | Blocker | Menghambat berapa hari? | Siapa yang bisa membuka? | Sudah dihubungi? |
|---|---|---|---|---|
| 1 | | | | ya / belum |
| 2 | | | | ya / belum |

## 3. Status
Pilih satu: `on-track` · `blocked` · `stalled` · `done`
Alasan singkat bila bukan on-track:

## 4. Rencana 7 hari ke depan
| Potongan kerja | Target selesai | Butuh bantuan? |
|---|---|---|
| | | |
| | | |

## 5. Catatan untuk lead _(opsional, 1–2 kalimat)_


---
### Pemetaan ke JSON (bila menyalin manual)
```json
{ "form": "progress", "project": "PRJ-01", "task": "T5", "date": "2026-09-16",
  "progress": 40, "effort_actual": 6, "status": "blocked",
  "blockers": ["menunggu aset foto final"], "notes": "…", "owner": "Dewi" }
```
