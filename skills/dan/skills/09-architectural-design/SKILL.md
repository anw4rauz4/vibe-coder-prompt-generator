---
name: dan-architectural-design
description: >-
  Agent arsitektur BANGUNAN (ala SketchUp/arsitek): menghasilkan denah 2D per lantai
  (shelf-packing ruang + dinding + dimensi + arah utara + skala), massa 3D isometrik
  berwarna per fungsi ruang, tampak depan (elevasi) dengan bukaan, serta dokumen:
  program ruang, kepatuhan KDB/KLB terhadap lahan, RAB estimasi per m2, jadwal material
  per fungsi, daftar gambar set 2D & 3D, tahapan konstruksi + durasi, dan prompt render
  interior/eksterior siap pakai untuk image generator. Mendukung rumah tinggal, ruko,
  kantor kecil, kafe; gaya modern tropis, minimalis, industrial, skandinavia, klasik.
  Gunakan saat pengguna meminta denah rumah, layout ruangan, desain interior/eksterior,
  model 3D/massing, tampak bangunan, estimasi biaya bangun (RAB), tahapan konstruksi,
  atau prompt render arsitektur.
---

# 09 · Architectural Design (2D / 3D / Konstruksi)

## Prinsip
1. **Angka dulu, gambar kemudian.** Program ruang (nama, fungsi, lebar, dalam) adalah
   sumber kebenaran; denah/3D/RAB semuanya turunan.
2. **Kepatuhan lahan wajib dicek**: KDB & KLB terhadap batas; bila melanggar,
   tampilkan ⛔ dan tawarkan opsi pengurangan.
3. **Jujur soal tingkat detail**: keluaran ini **tahap konsep/skematik**, bukan gambar
   kerja berskala sertifikasi. Selalu cantumkan disclaimer ±25% untuk RAB.
4. **Setiap ruang punya fungsi** (living/private/service/wet/circulation) karena warna
   3D, material, dan bukaan ditentukan dari situ.

---

## A. Perintah

```bash
cd skills/dan/scripts
python3 arch_design.py ../templates/building.example.json
python3 arch_design.py building.json --out-dir ../../../deliverables --scale 26 --theme light
```

Keluaran (semua SVG murni, bisa di-preview & dicetak):
```
arch_report.md        program ruang, KDB/KLB, RAB, material, daftar gambar, tahapan, prompt
arch_report.json      model terhitung (siap diolah lanjut)
arch_denah_L1.svg …   denah 2D per lantai (dimensi + utara + skala bar)
arch_massing_3d.svg   massa isometrik 3D, warna per fungsi ruang
arch_tampak_depan.svg elevasi depan dengan bukaan per ruang
```

---

## B. Model input (`building.json`)

```jsonc
{
  "meta": { "name": "...", "style": "modern tropis", "currency": "Rp" },
  "site": {
    "width": 12, "length": 20,        // ukuran lahan (m)
    "build_width": 10,                // lebar area boleh dibangun (setelah setback)
    "kdb_max": 0.6, "klb_max": 1.6,   // batas koefisien
    "floors_allowed": 2
  },
  "floors": [{
    "name": "Lantai 1", "height": 3.4,
    "rooms": [ { "name": "Ruang Keluarga", "w": 4.2, "d": 4.5, "function": "living" } ]
  }],
  "cost": { "structure_per_m2": 3500000, "finish_per_m2": 2600000,
            "mep_per_m2": 1300000, "other_pct": 10 },
  "notes": { "struktur": "...", "dinding": "...", "atap": "..." }
}
```

Fungsi ruang & pengaruhnya:
| function | Warna 3D | Material bawaan | Bukaan di tampak |
|---|---|---|---|
| `living` | seri 0 | granit/vinyl, cat emulsi | jendela besar |
| `private` | seri 1 | vinyl/parket | jendela sedang |
| `service` | seri 4 | keramik anti-slip | pintu/garasi di Lt.1 |
| `wet` | seri 3 | keramik full height, slope 1% | kecil/tinggi |
| `circulation` | seri 5 | granit/keramik | terbuka |

---

## C. Metrik & aturan yang dihitung

| Metrik | Rumus | Catatan |
|---|---|---|
| Luas ruang | w × d | per ruang |
| Luas program | Σ luas ruang | kebutuhan bersih |
| Luas terbangun | bounding box layout per lantai | termasuk dinding & sirkulasi |
| Sirkulasi | (terbangun − program) ÷ terbangun | sehat 20–35%; >40% = boros |
| KDB | luas terbangun Lt.1 ÷ luas lahan | bandingkan `kdb_max` |
| KLB | Σ luas terbangun ÷ luas lahan | bandingkan `klb_max` |
| RAB | terbangun × (struktur+finish+MEP) + other% | kelas konsep ±25% |
| Durasi | Σ tahapan + 1 minggu tiap 100 m² > 100 m² | heuristik |

**Aturan layout:** shelf-packing — ruang diurutkan depth menurun, diisi baris
kiri→kanan dalam `build_width`, baris baru bila penuh. Dinding antar ruang 0,15 m.
Ini skematik untuk studi massa & luas, **bukan** denah kerja (pintu, tangga, dan
orientasi matahari perlu digambar manual/di CAD).

---

## D. Interior & eksterior

- **Interior**: pilih ruang `living`/`private` terbesar per lantai sebagai hero shot.
  Pakai prompt dari `arch_report.json["prompts"]["interior"]`, lalu perkaya dengan
  template di `references/prompt-library-image-video.md` (§2.1–2.5).
- **Eksterior**: 2 angle wajib — fasad depan (two-point, street level) dan angle taman
  (golden hour). Pastikan jumlah lantai & gaya konsisten dengan prompt.
- **Konsistensi antar render**: kunci satu kalimat deskripsi massa (jumlah lantai,
  material fasad, bentuk atap) dan ulang identik di semua prompt.
- Setelah gambar jadi, verifikasi rasio dengan `fit_asset.py` (mis. 16:9 untuk
  presentasi, 4:5 untuk feed).

## E. Konstruksi & biaya

- Tahapan bawaan 10 langkah (persiapan → pondasi → struktur → dinding → atap → MEP kasar
  → kusen → finishing → MEP akhir → serah terima) dengan durasi minggu; total ditampilkan
  dan menyesuaikan luas.
- RAB memakai harga satuan per m² yang bisa ditimpa lewat `cost`. **Selalu** tampilkan
  disclaimer ±25% dan anjurkan verifikasi harga lokal + gambar kerja sebelum tender.
- Untuk penawaran ke klien: sajikan 3 opsi (standar / menengah / premium) dengan
  mengalikan harga satuan 0,85 / 1,0 / 1,25.

## F. Daftar gambar (set yang disarankan)
Lihat `arch_report.md` §5 — kode A-001…A-601 (2D), S-101 struktur, M/E-101 MEP,
3D-01…3D-03 (massing & render). Gunakan sebagai checklist kelengkapan dokumen.

## G. Keterbatasan yang WAJIB disebut
1. Denah = shelf-packing skematik: belum memuat pintu, tangga, shaft, orientasi matahari.
2. Tidak menghitung struktur secara engineering (beban, momen, penulangan).
3. RAB kelas konsep; bukan quantity take-off.
4. Kepatuhan hanya KDB/KLB; GSB, sempadan, Koefisien Dasar Hijau, dan aturan setempat
   perlu dicek ke dinas/IMB.

## H. Integrasi
- Render gambar → **04** (image/video creator) dengan prompt dari laporan.
- Presentasi klien → **03** (infografik: tabel program ruang + RAB sebagai waterfall).
- Jadwal & monitoring pembangunan → **07** (project monitoring; tahapan = tasks).
- Penawaran/komunikasi ke klien yang ragu → **06**.
