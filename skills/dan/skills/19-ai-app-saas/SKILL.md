---
name: dan-ai-app-saas-building
description: >-
  Membangun produk AI/SaaS dari ide sampai launch: validasi masalah, spec MVP
  (fitur inti vs tunda), arsitektur sederhana (API LLM terbungkus, cache, queue),
  model harga (per-seat/per-usage/credit), landing & waitlist, checklist launch,
  dan metrik aktivasi/retensi. Menggunakan template strategi DAN agar spec tidak
  mengawang. Gunakan saat pengguna meminta "buatkan aplikasi AI", "MVP SaaS",
  "harga produk AI", "launch checklist", atau memvalidasi ide produk.
---

# 19 · AI App / SaaS Building

## Prinsip
1. **Jual hasil, bukan model**: pengguna membayar outcomes (laporan jadi, balasan
   terkirim), bukan "akses GPT".
2. MVP = satu alur nilai yang selesai ujung-ke-ujung; fitur lain = daftar tunda.
3. Biaya inferensi adalah COGS: ukur cost-per-outcome sejak hari pertama (sub-skill 20).

## Alur
```
masalah (siapa, seberapa sakit, bukti) -> MVP spec -> arsitektur minimalis
 -> harga (unit economics) -> landing+waitlist -> launch kecil -> ukur & iterasi
```

## Spec MVP (isi dari templates/strategy-brief.md bagian terkait)
```
Masalah & bukti      : 1 kalimat + 3 data/wawancara
Pengguna pertama     : segmen sempit yang bisa dijangkau minggu ini
Alur nilai inti      : input → proses AI → keluaran (≤3 langkah)
Fitur TUNDA          : daftar eksplisit (auth sosial, kolaborasi, mobile app…)
Kriteria lulus MVP   : 10 pengguna pertama menyelesaikan alur tanpa bantuan
```

## Arsitektur minimalis yang cukup
- Satu backend + satu queue untuk tugas panjang; cache hasil per input-hash.
- Bungkus semua pemanggilan LLM di satu modul (ganti model = 1 file).
- Simpan trace biaya/latensi per request (llm_obs.py) sejak awal.
- Auth & billing pakai penyedia (jangan bangun sendiri di MVP).

## Model harga AI (pilih satu untuk mulai)
| Model | Cocok bila | Risiko |
|---|---|---|
| Credit/usage | biaya per request bervariasi besar | pengguna bingung kuota |
| Per-seat | nilai kolaborasi tim | adopsi lambat di tim kecil |
| Flat + fair-use | prediksi biaya mudah | heavy user memakan margin |
Aturan: harga ≥ 4× biaya inferensi per outcome pada p95 penggunaan.

## Launch checklist
- [ ] 10 pengguna awal menyelesaikan alur nilai (tanpa dibantu)
- [ ] halaman harga menjelaskan unit (credit/seat) + contoh perhitungan
- [ ] kegagalan AI punya jalan manual/fallback yang jelas
- [ ] privacy page: data apa disimpan, berapa lama, cara hapus
- [ ] dashboard metrik: aktivasi D1/D7, cost-per-outcome, churn minggu 4

## Integrasi
- Strategi & positioning: sub-skill 02. Landing copy & kreatif: 04/10.
- Observability biaya: 20. Stack tool: 17.
