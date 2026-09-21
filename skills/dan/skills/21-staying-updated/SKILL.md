---
name: dan-staying-updated
description: >-
  Menjaga pengetahuan & paket tetap segar tanpa kecanduan berita: daftar sumber
  terpercaya per topik, ritme digest mingguan (30 menit), template digest, aturan
  "adopsi vs tunggu" untuk teknologi baru (proof-of-value kecil sebelum komitmen),
  dan checklist refresh paket (CHANGELOG, versi, regression). Gunakan saat pengguna
  bertanya "apa yang baru di AI minggu ini", "haruskah saya pindah tool/model",
  "buatkan ringkasan berita untuk tim", atau menjadwalkan pembaruan pengetahuan.
---

# 21 · Staying Updated

## Prinsip
1. **Jadwal, bukan scroll**: satu sesi digest 30 menit/minggu mengalahkan 3 jam/hari mencicil.
2. Berita ≠ keputusan: adopsi teknologi baru lewat **proof-of-value kecil** (≤1 hari,
   1 metrik) sebelum mengganti stack produksi.
3. Setiap adopsi/ditolak dicatat (CHANGELOG/ADR) agar tim tahu alasan & waktunya.

## Sumber terpercaya per topik (mulai dari sini)
| Topik | Sumber |
|---|---|
| Riset/LLM | arXiv cs.CL/cs.LG (abstract), blog lab resmi, repo rilis |
| Engineering | blog engineering vendor, changelog produk yang Anda pakai |
| Biaya/harga | halaman pricing vendor + pengumuman perubahan |
| Keamanan | advisories vendor, CVE feed untuk dependensi Anda |
| Industri lokal | asosiasi/regulator terkait (mis. aturan PDP) |

## Template digest mingguan (30 menit)
```
1. (10 mnt) Scan judul sumber terpilih; tandai ≤5 butir relevan tujuan kuartal.
2. (10 mnt) Baca mendalam 2 butir; catat: apa berubah, dampak ke kita, bukti.
3. (5 mnt)  Keputusan: adopsi / tunggu / abaikan + alasan satu kalimat.
4. (5 mnt)  Tulis digest 5 baris untuk tim + tautan; arsipkan ke notes/.
```

## Aturan "adopsi vs tunggu"
- **Adopsi sekarang** bila: memperbaiki bottleneck terukur kita, migrasi ≤1 hari,
  ada exit strategy.
- **Proof-of-value** bila: menjanjikan tapi dampak belum terukur di konteks kita.
- **Tunggu** bila: belum stabil (breaking changes sering), atau biaya migrasi >
  manfaat 6 bulan.

## Refresh paket DAN (bulanan)
- [ ] jalankan `_test_all.py` + `run_cases.py run all` (regression)
- [ ] perbarui CHANGELOG & naikkan versi semver bila ada perubahan perilaku
- [ ] bangun ulang `dan.pyz` + `dan-skill-<v>.zip` (manifest merekam QA)
- [ ] tinjau 1 sub-skill terhadap praktik terbaru; perbarui referensi bila usang

## Integrasi
- Digest bisa dibacakan sebagai audio briefing: sub-skill 16.
- Keputusan adopsi tool: sub-skill 17; dampak arsitektur: 08.
