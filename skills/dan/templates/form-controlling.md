# FORM CONTROLLING — Tindakan Korektif & Preventif

> Diisi **segera** (maks 1×24 jam) saat variance melewati ambang, CPI < 0,85,
> atau tugas kritis >3 hari. Bukan laporan — ini dokumen keputusan.
> Versi interaktif: tab **3 · Form Controlling** di `forms.html`.
> Menjadi record `"form": "controlling"` pada batch JSON → masuk `actions` proyek.

---

**Tanggal**      : `____-__-__`
**Proyek**       : `[ID]` — `[nama]`
**Diisi oleh**   : `[nama]`
**No. tindakan** : `CA__`

## 1. Penyimpangan (fakta, bukan opini)
| Field | Isi |
|---|---|
| Metrik yang menyimpang | `progress` / `budget` / `scope` / `schedule` / `quality` |
| Nilai rencana | `___` |
| Nilai aktual | `___` |
| Besar penyimpangan | `___` |
| Sejak kapan terdeteksi | `____-__-__` |
| Sumber data | `dashboard / form progress / analysis.json / lainnya` |

Deskripsi masalah (1–2 kalimat, sebut tugas/objeknya):

## 2. Analisis akar masalah (gali minimal 3 lapis "kenapa")
| Lapis | Pertanyaan "kenapa?" | Jawaban |
|---|---|---|
| 1 | Kenapa penyimpangan terjadi? | |
| 2 | Kenapa penyebab lapis-1 ada? | |
| 3 | Kenapa penyebab lapis-2 dibiarkan? | |

**Akar masalah (yang bisa ditindak)** :

## 3. Tindakan
| Jenis | Uraian | Owner | Tenggat | Ukuran berhasil |
|---|---|---|---|---|
| **Korektif** (perbaiki yang sudah terjadi) | | | | |
| **Preventif** (cegah terulang) | | | | |

## 4. Dampak tindakan terhadap baseline
- [ ] Tidak mengubah baseline (cukup percepatan/realokasi internal)
- [ ] Mengubah jadwal → tanggal selesai baru: `____-__-__`
- [ ] Mengubah budget → tambahan: Rp `___` (disetujui oleh: `___`)
- [ ] Mengubah scope → yang dikurangi: `___`

## 5. Status & verifikasi
Status: `open` · `in-progress` · `done` · `cancelled`
Tanggal verifikasi efektivitas: `____-__-__`
Hasil verifikasi (isi saat verifikasi): efektif / sebagian / tidak → tindak lanjut:

---
### Pemetaan ke JSON
```json
{ "form": "controlling", "project": "PRJ-01", "date": "2026-09-16",
  "issue": "CVR landing 1,1% dari target 2,5%; progres 40% dari rencana 75%",
  "variance": { "metric": "progress", "planned": 75, "actual": 40 },
  "root_cause": "loading 6,2 dtk di 4G; form 7 field; aset foto terlambat dari produksi",
  "corrective_action": "kompres gambar + CDN, pangkas form jadi 3 field",
  "preventive": "checklist performa halaman masuk definisi selesai setiap rilis LP",
  "owner": "Dewi", "due": "2026-09-19", "status": "open" }
```
