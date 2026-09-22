# 🧠 Vibe Coder Prompt Generator

Generator prompt AI berbasis web — tanpa framework, tanpa install, langsung jalan di browser.

Pilih project → pilih skills & sub-agents → tulis detail → lampirkan gambar referensi → dapatkan **prompt siap pakai** yang sudah dioptimalkan sesuai platform AI tujuan Anda (ChatGPT, Claude, Gemini, dan lainnya).

> 🆕 **Terintegrasi paket skill DAN** — metodologi marketing multi-keahlian (analisa data, strategi, infografik, storyboard, PMO, arsitektur software & bangunan). Pilih skill "DAN ..." dan prompt otomatis memuat **DAN Playbook**: prinsip kerja berbasis data + target deliverable per skill. Paket lengkap (pustaka referensi, engine CLI Python zero-dependency, template dokumen) ada di folder [`skills/dan/`](skills/dan/).
>
> 🎭 **Persona Profesi** — tampilan & struktur prompt otomatis menyesuaikan profesi. Pilih project coaching → prompt jadi **sesi GROW + rencana aksi**. Pilih project konstruksi → prompt menuntut **denah 2D, takeoff material, RAB, jadwal**. Ada 10 persona: Coach, Engineer Konstruksi, Arsitek, Software Engineer, Data Analyst, Strategist Marketing, Creative Producer, UI/UX Designer, Edukator, Business Ops — masing-masing dengan alur kerja, blueprint deliverable, dan quality checklist-nya sendiri.

---

## ✨ Fitur

| Fitur | Keterangan |
|---|---|
| 📁 **Preset Project** | 32 template project siap pakai: Web App, Mobile App, Dashboard, Video Sinematik, AI SaaS, UI/UX, Sales Strategy, Bahan Ajar, dll. |
| 🛠️ **114 Skills** | Multi-pilih skill, cari dengan pencarian, filter per kategori — termasuk 9 skill DAN |
| 🤖 **115 Sub-Agents** | Pilih agent pendamping untuk memecah tugas kompleks — termasuk 9 agent DAN |
| 🧠 **DAN Playbook** | Skill "DAN ..." mengaktifkan metodologi: data dulu, tiap temuan = aksi terukur, deliverable jelas per skill |
| 🎭 **Persona Profesi** | 10 blueprint profesi (coach, engineer konstruksi, arsitek, dst) — struktur prompt berbeda sesuai kebutuhan tiap profesi |
| 🌐 **10 Platform AI** | Template prompt berbeda untuk ChatGPT, Claude, Gemini, Grok, Perplexity, Llama, Mistral, DeepSeek, Qwen, dan generic |
| 🎯 **Auto-Preset** | Skill & agent rekomendasi otomatis terpilih saat project diklik |
| ✨ **Custom Skills/Agents** | Tambah skill atau agent buatan sendiri (tersimpan di browser) |
| 📋 **Copy / Download** | Salin prompt ke clipboard atau unduh sebagai file `.txt` |
| 🖼️ **Upload Multi-Image** | Lampirkan hingga 10 gambar referensi (klik, drag & drop, atau Ctrl+V) + catatan per kebutuhan — AI paham visual yang Anda maksud |
| 📦 **Export / Import JSON** | Simpan konfigurasi ke file (termasuk gambar), buka lagi kapan saja |
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
5. **Lampirkan Gambar Referensi** (opsional) — klik/drag & drop/Ctrl+V, beri catatan misal *"Gambar 1 adalah layout yang saya mau"*
6. **Pilih Platform AI** tujuan, klik **🚀 Generate Prompt**, lalu **📋 Copy**

Tempel hasilnya ke ChatGPT / Claude / Gemini Anda. Prompt sudah berisi struktur instruksi yang disesuaikan dengan kemampuan platform tersebut.

> 💡 **Tips gambar:** gambar otomatis dipadatkan agar ringan. Data gambar tersimpan lokal di browser Anda dan ikut saat Export JSON — tapi tidak ikut di link share & riwayat agar tetap ringan.

---

## 📁 Struktur Proyek

```
├── index.html          # Halaman utama (UI)
├── style.css           # Styling + tema dark/light
├── app.js              # Logika UI, state, event, localStorage
├── core.js             # Logika murni: template per-platform, playbook DAN, encode/decode
├── data.js             # Data tertanam (auto-generated, agar jalan via file://)
├── data/
│   ├── projects.json   # Preset project (incl. 3 preset DAN)
│   ├── categories.json # Kategori project
│   ├── skills.json     # Daftar skills (incl. 9 skill DAN)
│   ├── agents.json     # Daftar sub-agents (incl. 9 agent DAN)
│   └── adapters.json   # Platform AI + template-nya
├── skills/dan/         # 🆕 Paket skill DAN: SKILL.md, AGENT.md, SYSTEM_PROMPT,
│   │                   #    9 pustaka referensi, 40+ engine Python zero-dependency,
│   │                   #    11+ template dokumen, data contoh
│   └── ...             # Lihat skills/dan/SKILL.md untuk indeks lengkap
└── tests/
    ├── build-data.js   # Generator data.js dari data/*.json
    └── core.test.js    # Unit test logika inti + integrasi DAN
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
