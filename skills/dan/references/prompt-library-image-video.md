# Prompt Library — Image & Video

Pustaka template prompt untuk sub-skill **04**. Isi `{placeholder}` dengan brief pengguna.
Semua prompt memakai struktur berlapis agar hasilnya konsisten dan bisa diulang.

---

## 1. Rumus universal prompt image (6 lapis)

```
[SUBJEK] + [KOMPOSISI/LENSA] + [LINGKUNGAN] + [CAHAYA] + [WARNA & MOOD] + [TEKNIS & LARANGAN]
```

| Lapis | Contoh isian |
|---|---|
| Subjek | "botol serum kaca amber 30 ml, label matte, tutup pipet hitam" |
| Komposisi | "hero shot, 85mm f/2.8, eye-level, rule of thirds, negative space kiri" |
| Lingkungan | "meja marmer putih, daun monstera blur di latar, pagi hari" |
| Cahaya | "softbox 45° dari kiri, fill card kanan, rim light hangat, soft shadow" |
| Warna/mood | "palet hangat krem-sage, muted, editorial clean, tenang" |
| Teknis | "9:16, 1080x1920, photorealistic, 8K" |
| Larangan | "no text, no watermark, no logo, no extra fingers, no plastic skin" |

**Negative prompt standar (salin apa adanya):**
```
text, captions, subtitles, watermark, signature, logo distortion, extra fingers,
deformed hands, malformed product shape, blurry, lowres, oversaturated,
plastic skin, cartoonish, cropped subject, jpeg artifacts
```

---

## 2. Template per kebutuhan marketing

### 2.1 Product hero (feed, banner, thumbnail)
```
{produk} berdiri tegak di {permukaan}, {proporsi} sebagai latar belakang blur,
hero shot, lensa 85mm f/2.8, sudut eye-level sedikit dari bawah agar terlihat premium,
pencahayaan tiga titik (key softbox 45°, fill lembut, rim hangat di tepi),
palet {warna brand}, ruang negatif di {posisi} untuk headline,
fotorealistik, detail material tajam, 8K, rasio {rasio},
tanpa teks, tanpa watermark
```

### 2.2 Lifestyle / UGC (paling tinggi performanya di TikTok-Reels)
```
kandid {talent} sedang {aksi} menggunakan {produk} di {lokasi nyata},
cahaya alami dari jendela, handheld sedikit goyang, grain halus,
tone hangat sedikit desaturasi, terasa seperti konten UGC asli bukan iklan studio,
medium close-up, 35mm, rasio 9:16, tanpa teks
```

### 2.3 Before – After
```
split frame vertikal dua sisi dengan garis pembatas tipis putih,
kiri: {kondisi awal}, tone dingin, desaturasi 20%, cahaya datar,
kanan: {kondisi akhir}, tone hangat, saturasi naik, cahaya terarah,
pencahayaan dan sudut kamera identik agar perbandingan adil,
{subjek} sama persis di kedua sisi, rasio {rasio}, tanpa teks
```

### 2.4 Flatlay / top-down (katalog, carousel)
```
top-down flatlay {produk utama} dikelilingi {prop pendukung} di atas {tekstur latar},
tata letak grid rapi dengan jarak konsisten, cahaya merata tanpa bayangan keras,
ruang kosong {posisi} untuk teks, warna {palet}, rasio 4:5, tanpa teks
```

### 2.5 Tekstur / macro (bahan, makanan, kosmetik)
```
extreme macro {tekstur/isi produk}, depth of field sangat dangkal,
tetesan dan partikel terlihat jelas, pencahayaan sisi untuk menonjolkan dimensi,
latar {warna} polos, fotorealistik, tajam pada titik fokus, rasio 1:1
```

### 2.6 Mockup kemasan
```
mockup kemasan {jenis kemasan} untuk {produk}, {material & finishing},
dimensi proporsional {P×L×T} mm, ditempel label dengan tata letak {gaya},
diletakkan di {latar}, studio lighting, sudut {3/4 atau frontal},
render fotorealistik, rasio {rasio}, teks label harus {isi teks bila perlu}
```

### 2.7 Latar untuk infografik (sub-skill 03)
```
latar abstrak minimalis {warna dasar} dengan gradasi halus dari {warna A} ke {warna B},
bentuk geometris lembut di tepi, ruang besar di tengah untuk grafik dan teks,
tanpa objek mengganggu, clean corporate, rasio {rasio}
```

### 2.8 Ilustrasi / ikon set
```
set {n} ikon garis untuk {topik}, stroke {1.5–2}px seragam, grid 24×24,
ujung rounded, gaya minimalis konsisten, warna {aksen} di atas latar {netral},
vektor rapi, tanpa bayangan, tanpa gradasi
```

### 2.9 Talented/team (employer branding)
```
foto dokumenter tim {jumlah orang} sedang {aktivitas kerja nyata} di {lokasi kantor},
ekspresi natural tidak berpose ke kamera, cahaya alami campuran lampu kantor,
35mm, kedalaman dangkal, tone hangat, terasa jujur bukan stok foto
```

---

## 3. Konsistensi karakter/produk antar gambar

Masalah paling umum: produk berubah bentuk/warna antar shot. Cara mengatasinya:

1. **Kunci deskripsi produk** dalam satu kalimat tetap, salin identik ke semua prompt:
   `"botol kaca amber 30ml, label matte putih-krem, tutup pipet hitam doff, tinggi 105mm"`.
2. **Sebutkan referensi visual** bila tool mendukung (`--cref`, image input, IP-Adapter).
3. **Satu pengaturan cahaya** untuk satu rangkaian shot (mis. "softbox 45° kiri").
4. **Sebutkan larangan perubahan**: `"jangan ubah bentuk kemasan, warna label, atau proporsi logo"`.
5. **Generate satu hero image dulu**, lalu pakai sebagai referensi untuk shot lain.
6. Bila tetap meleset → **komposit**: produk difoto/di-render terpisah lalu ditempel di editing.

---

## 4. Rumus prompt video

```
[DURASI & RASIO] + [SUBJEK & SATU AKSI] + [GERAKAN KAMERA] + [LENSA/FOKUS]
+ [CAHAYA] + [TRANSISI KELUAR] + [KONSISTENSI] + [LARANGAN]
```

**Template:**
```
Shot {durasi}s, {rasio}. {tipe shot}, kamera: {gerakan + kecepatan}.
Aksi tunggal: {kata kerja spesifik}. Lensa {mm}, {rack focus / depth}.
Pencahayaan: {sumber & arah}. Transisi keluar: {tipe transisi}.
Pertahankan identitas & warna {produk}; jangan ubah bentuk kemasan.
Tanpa teks dalam frame (teks ditambahkan saat editing).
```

**Gerakan kamera & kapan memakainya**

| Gerakan | Efek psikologis | Pakai untuk |
|---|---|---|
| static tripod | stabil, dapat dipercaya | testimoni, demo |
| handheld subtle | nyata, UGC | lifestyle, story |
| slow push-in | membangun fokus/emosi | hook, momen penting |
| pull-out reveal | kejutan, konteks | before-after, lokasi |
| orbit 180° | premium, memamerkan bentuk | product hero 3D |
| tracking follow | energi, pergerakan | aktivitas, perjalanan |
| whip pan | cepat, transisi | pergantian poin |
| rack focus | mengalihkan perhatian | detail → produk |
| dolly zoom | gelisah, tak nyaman | problem/agitate |
| crane up | megah, penutup | ending, landscape |

**Aturan shot:** 1 shot = 1 aksi = 2–4 detik. Video 30 detik idealnya 8–13 shot.
Untuk AI video generator, buat per potongan pendek lalu gabung di editor.

---

## 5. Prompt audio/VO (bila memakai text-to-speech)

```
Bahasa: Indonesia. Nada: {friendly/profesional/inspiratif}. Tempo: {145 kata/menit}.
Karakter suara: {dewasa muda, hangat, jelas}. Penekanan pada kata: {daftar}.
Jeda 0,3 detik di setiap tanda baca; 0,6 detik sebelum CTA.
Teks: "{naskah dari storyboard.py}"
```

> `storyboard.py` sudah menghitung jumlah kata per shot (`vo_words`) dengan asumsi
> 145 kata/menit — pakai angka itu agar VO tidak melebihi durasi shot.

---

## 6. Bank hook visual (3 detik pertama)

| Pola | Eksekusi |
|---|---|
| Pattern interrupt | objek tak terduga masuk frame / warna kontras ekstrem |
| Reverse reveal | tunjukkan hasil akhir dulu, lalu mundur |
| Hands-only | hanya tangan + produk, tanpa wajah (murah & konsisten) |
| Text slap | teks besar menutup layar lalu tergeser |
| Split screen | dua kondisi berdampingan sekaligus |
| Slow-mo detail | macro tekstur 120fps |
| Direct address | talent menatap lensa + kalimat menohok |
| Countdown | "3 kesalahan…" muncul satu per satu |

---

## 7. Etika & kepatuhan
- Tandai konten berbayar: `#ad`, `#sponsored`, atau label kemitraan platform.
- Jangan membuat wajah orang nyata tanpa izin; jangan meniru suara selebritas.
- Before-after harus nyata dan dalam kondisi pemotretan yang sama.
- Hindari klaim medis/finansial; tambahkan disclaimer bila hasil tidak tipikal.
- Jangan memakai musik berhak cipta untuk iklan berbayar — pakai library berlisensi.
- Simpan jejak prompt & seed agar hasil bisa direproduksi.
