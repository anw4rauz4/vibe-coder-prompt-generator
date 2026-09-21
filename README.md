# 🧠 Vibe Coder Prompt Generator

Generator prompt AI berbasis web — tanpa framework, tanpa install, langsung jalan di browser.

Pilih project → pilih skills & sub-agents → tulis detail → dapatkan **prompt siap pakai** yang sudah dioptimalkan sesuai platform AI tujuan Anda (ChatGPT, Claude, Gemini, dan lainnya).

---

## ✨ Fitur

| Fitur | Keterangan |
|---|---|
| 📁 **Preset Project** | 32 template project siap pakai: Web App, Mobile App, Dashboard, Video Sinematik, AI SaaS, UI/UX, Sales Strategy, Bahan Ajar, dll. |
| 🛠️ **105 Skills** | Multi-pilih skill, cari dengan pencarian, filter per kategori |
| 🤖 **106 Sub-Agents** | Pilih agent pendamping untuk memecah tugas kompleks |
| 🌐 **10 Platform AI** | Template prompt berbeda untuk ChatGPT, Claude, Gemini, Grok, Perplexity, Llama, Mistral, DeepSeek, Qwen, dan generic |
| 🎯 **Auto-Preset** | Skill & agent rekomendasi otomatis terpilih saat project diklik |
| ✨ **Custom Skills/Agents** | Tambah skill atau agent buatan sendiri (tersimpan di browser) |
| 📋 **Copy / Download** | Salin prompt ke clipboard atau unduh sebagai file `.txt` |
| 📦 **Export / Import JSON** | Simpan konfigurasi ke file, buka lagi kapan saja |
| 🔗 **Share Link** | Bagikan konfigurasi via URL — penerima langsung melihat setup yang sama |
| 🕘 **Riwayat** | 20 prompt terakhir tersimpan otomatis, bisa dimuat ulang |
| 🌗 **Dark / Light Mode** | Tema gelap & terang, preferensi diingat |
| 💾 **Auto-Save** | Semua pilihan tersimpan otomatis di `localStorage` |

---

## 🚀 Cara Menjalankan

### Cara 1: Langsung buka (paling gampang)
Buka file `index.html` di browser (double-click). Selesai — data sudah tertanam di dalam `data.js`, jadi tetap jalan tanpa server.

### Cara 2: Via lokal server (direkomendasikan)
```bash
npm start
```
Lalu buka `http://localhost:8080`. Mode ini memuat data langsung dari folder `data/*.json`.

> Aplikasi ini 100% client-side. Tidak butuh backend, tidak ada data yang dikirim ke mana pun.

---

## 🖼️ Cara Pakai (5 Langkah)

1. **Pilih Project** di sidebar kiri — misal `🌐 Web App` atau `🎬 Video Sinematik`
2. **Pilih Kategori** (opsional) untuk memfilter daftar skill & agent
3. **Centang Skills & Sub-Agents** yang diinginkan — atau biarkan auto-preset yang memilihkan
4. **Tulis Detail Project** — misal: *"Buatkan aplikasi e-commerce dengan React dan Tailwind"*
5. **Pilih Platform AI** tujuan, klik **🚀 Generate Prompt**, lalu **📋 Copy**

Tempel hasilnya ke ChatGPT / Claude / Gemini Anda. Prompt sudah berisi struktur instruksi yang disesuaikan dengan kemampuan platform tersebut.

---

## 📁 Struktur Proyek

```
├── index.html          # Halaman utama (UI)
├── style.css           # Styling + tema dark/light
├── app.js              # Logika UI, state, event, localStorage
├── core.js             # Logika murni: template prompt per-platform, encode/decode
├── data.js             # Data tertanam (auto-generated, agar jalan via file://)
├── data/
│   ├── projects.json   # Preset project
│   ├── categories.json # Kategori project
│   ├── skills.json     # Daftar skills
│   ├── agents.json     # Daftar sub-agents
│   └── adapters.json   # Platform AI + template-nya
└── tests/
    ├── build-data.js   # Generator data.js dari data/*.json
    └── core.test.js    # Unit test logika inti
```

---

## 🧪 Test

```bash
npm test
```

Memperbarui data tertanam setelah mengubah `data/*.json`:

```bash
npm run build:data
```

---

## 🛠️ Teknologi

- **Vanilla JavaScript** (ES6+, tanpa framework, tanpa build tool)
- **HTML5 + CSS3** (responsive, mobile-friendly)
- **localStorage** untuk penyimpanan
- **Web Share API** & **Clipboard API** untuk berbagi

---

## 🤝 Kontribusi

Pull request terbuka! Untuk menambah skill/agent baru:
1. Edit `data/skills.json` atau `data/agents.json`
2. Jalankan `npm run build:data` untuk regenerate `data.js`
3. Jalankan `npm test` untuk memastikan semua valid

---

## 📄 Lisensi

MIT — bebas digunakan, dimodifikasi, dan dibagikan.
