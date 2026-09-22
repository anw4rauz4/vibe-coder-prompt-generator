// ============================================
// VIBE CODER — CORE (pure logic, no DOM)
// Dipakai oleh app.js (browser) dan tests/ (Node)
// ============================================

const PLATFORM_TEMPLATES = {
  chatgpt: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Role:** Aktifkan Custom GPT instructions yang relevan.',
      '3. **Tools:** Gunakan Code Interpreter / DALL·E / Browsing bila perlu.',
      '4. **Generate:** Output code, prompt, atau asset.',
      '5. **Validate:** Pastikan kualitas & token efficiency.'
    ],
    output: [
      '- **Code:** Markdown code blocks dengan language tags',
      '- **File:** Gunakan Code Interpreter untuk file hasil',
      '- **Visual:** DALL·E prompt terpisah jika dibutuhkan'
    ]
  },
  claude: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Route:** Assign ke sub-agent yang relevan (gunakan XML tags).',
      '3. **Load Skill:** Load skill yang dibutuhkan (Skills/Projects).',
      '4. **Generate:** Output code, prompt, atau asset — Artifacts untuk hasil panjang.',
      '5. **Validate:** Pastikan kualitas & token efficiency.'
    ],
    output: [
      '- **Code:** Artifacts (kode atau dokumen) + markdown blocks',
      '- **Diagrams:** Mermaid di dalam Artifacts',
      '- **Struktur:** Gunakan XML tags untuk memisahkan konteks'
    ]
  },
  gemini: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Multimodal:** Manfaatkan kemampuan teks, gambar, dan audio.',
      '3. **Workspace:** Integrasikan dengan Docs/Sheets bila relevan.',
      '4. **Generate:** Output code, prompt, atau asset.',
      '5. **Validate:** Pastikan kualitas & token efficiency.'
    ],
    output: [
      '- **Code:** Markdown code blocks dengan language tags',
      '- **Analisis:** Tabel perbandingan bila relevan',
      '- **Visual:** Prompt untuk Imagen bila dibutuhkan'
    ]
  },
  grok: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Real-time:** Gunakan data X terkini bila relevan.',
      '3. **Generate:** Output code atau konten.',
      '4. **Validate:** Cek akurasi & kebaruan informasi.'
    ],
    output: [
      '- **Code:** Markdown code blocks',
      '- **Tren:** Sertakan referensi post X bila merujuk tren'
    ]
  },
  perplexity: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Research:** Lakukan deep research dengan sumber kredibel.',
      '3. **Cite:** Selalu sertakan sitasi untuk setiap klaim.',
      '4. **Generate:** Ringkasan + rekomendasi actionable.'
    ],
    output: [
      '- **Jawaban:** Terstruktur dengan heading',
      '- **Sitasi:** Numbered [1][2] dengan link sumber'
    ]
  },
  llama: {
    execution: [
      '1. **System Prompt:** Perlakukan instruksi ini sebagai system prompt.',
      '2. **Parse Intent:** Analisis overview & detail.',
      '3. **Generate:** Output code atau konten secara langsung.',
      '4. **Validate:** Ringkas, hindari token sia-sia.'
    ],
    output: [
      '- **Code:** Markdown code blocks',
      '- **Format:** Kompatibel runtime open-source (Ollama/vLLM)'
    ]
  },
  mistral: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Concise:** Jawab langsung, efisien token.',
      '3. **Generate:** Output code atau konten.',
      '4. **Validate:** Pastikan akurasi teknis.'
    ],
    output: [
      '- **Code:** Markdown code blocks (Codestral-friendly)',
      '- **Format:** Ringkas dan terstruktur'
    ]
  },
  deepseek: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Reasoning:** Pecah masalah menjadi langkah berpikir.',
      '3. **Generate:** Output code atau solusi.',
      '4. **Validate:** Review ulang logika sebelum final.'
    ],
    output: [
      '- **Code:** Markdown code blocks',
      '- **Reasoning:** Tampilkan langkah kunci, bukan full chain-of-thought'
    ]
  },
  qwen: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Multilingual:** Sesuaikan bahasa dengan kebutuhan user.',
      '3. **Generate:** Output code atau konten.',
      '4. **Validate:** Pastikan kualitas terjemahan & kode.'
    ],
    output: [
      '- **Code:** Markdown code blocks',
      '- **Bahasa:** Ikuti bahasa permintaan user'
    ]
  },
  generic: {
    execution: [
      '1. **Parse Intent:** Analisis project overview dan detail.',
      '2. **Route:** Assign ke sub-agent yang relevan.',
      '3. **Load Skill:** Load skill yang dibutuhkan.',
      '4. **Generate:** Output code, prompt, atau asset.',
      '5. **Validate:** Pastikan kualitas & token efficiency.'
    ],
    output: [
      '- **Code:** Markdown code blocks with language tags',
      '- **Diagrams:** Mermaid or SVG',
      '- **Design:** JSON tokens + CSS variables',
      '- **Media:** Prompt + MCP tool call',
      '- **Docs:** Markdown with headings'
    ]
  }
};

const TOKEN_LINES = [
  "- Lazy loading (only load what's needed)",
  '- Caching (reuse previous results)',
  '- Delta sharing (only share changes)',
  '- Progressive disclosure (load skill on demand)'
];

const IMAGE_INSTRUCTIONS = [
  '- Perlakukan setiap gambar sebagai requirement visual yang mengikat.',
  '- Ekstrak layout, palet warna, komponen, dan hierarki informasi dari gambar.',
  '- Jika teks dan gambar saling bertentangan, sebutkan konfliknya dan minta klarifikasi sebelum lanjut.',
  '- Referensikan gambar dengan nomor (contoh: "sesuai Gambar 2") dalam jawaban Anda.'
];

const formatBytes = (bytes) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return '';
  const units = ['B', 'KB', 'MB'];
  let i = 0, v = bytes;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${Number.isInteger(v) ? v : v.toFixed(1)} ${units[i]}`;
};

const DAN_PRINCIPLES = [
  '1. Data dulu, opini belakangan — setiap klaim punya angka atau ditandai `asumsi:`.',
  '2. Setiap temuan punya "so what": satu aksi konkret + pemilik + tenggat.',
  '3. Jujur soal ketidakpastian: sebut sampel, rentang waktu, dan keterbatasan.',
  '4. Hemat kata, kaya substansi: tabel/daftar, bukan paragraf panjang.',
  '5. Selesaikan sampai deliverable, bukan sekadar saran.',
  '6. Tutup dengan 2-3 langkah berikutnya.'
];

const DAN_DELIVERABLE_HINTS = {
  'marketing-data-analyst': 'JSON hasil analisa + Markdown ringkasan (KPI, anomali, forecast)',
  'marketing-strategist': 'Campaign plan: tujuan, audiens, channel mix, budget, A/B test',
  'data-to-infographic': 'Infografik/chart SVG self-contained (tanpa CDN)',
  'image-video-creator': 'Storyboard shot-list bertiming + prompt image/video + SRT',
  'design-engineer-2d-3d': 'Brief desain + spec teknis + sketsa/mockup 3D',
  'motivator-coach': 'Rencana coaching GROW berbasis data performa',
  'project-monitoring-controlling': 'Status proyek: variance, SPI, RAG, stalled, earned value',
  'software-architecture': 'Scaffold/review/trade-off + rekomendasi ber-konteks',
  'architectural-design': 'Denah 2D, massa 3D, tampak, KDB/KLB, RAB, tahapan konstruksi'
};

function buildDanPlaybook(skills = []) {
  const danSkills = skills.filter(s => DAN_DELIVERABLE_HINTS[s.id]);
  if (danSkills.length === 0) return null;

  const lines = [];
  lines.push('## 🧠 DAN PLAYBOOK (METODOLOGI WAJIB)');
  lines.push('Skill DAN aktif dalam prompt ini. Ikuti metodologi DAN:');
  lines.push('');
  DAN_PRINCIPLES.forEach(l => lines.push(l));
  lines.push('');
  lines.push('**Deliverable yang diharapkan per skill DAN:**');
  danSkills.forEach(s => lines.push(`- **${s.name}** → ${DAN_DELIVERABLE_HINTS[s.id]}`));
  lines.push('');
  lines.push('Paket referensi lengkap (pustaka metrik, framework, runbook, engine CLI) tersedia di folder `skills/dan/` pada repositori ini.');
  return lines;
}

// ============================================
// PERSONA PROFESI — tampilan & struktur prompt berbeda per profesi
// ============================================
const PERSONA_TEMPLATES = {
  coach: {
    icon: '🎯',
    label: 'Performance Coach',
    role: 'Coach profesional yang memandu lewat pertanyaan, bukan ceramah.',
    mission: 'Membawa coachee menemukan jawabannya sendiri dan berkomitmen pada aksi terukur.',
    tone: 'Hangat, empati, memotivasi; bertanya lebih banyak daripada memberi tahu; tanpa menghakimi.',
    workflow: [
      '1. **Kontrak Sesi:** Klarifikasi tujuan sesi dan apa yang "berhasil" menurut coachee.',
      '2. **Gambaran Realita:** Gali kondisi saat ini dengan data (angka penjualan/progress), bukan asumsi.',
      '3. **GROW:** Jalankan Goal → Reality → Options → Way forward dalam satu alur percakapan.',
      '4. **Komitmen:** Kunci 1-3 aksi konkret + pemilik + tenggat yang diucapkan coachee sendiri.',
      '5. **Akuntabilitas:** Sepakati mekanisme check-in mingguan dan cara mengukur kemajuan.'
    ],
    blueprint: {
      heading: 'BLUEPRINT SESI COACHING',
      items: [
        'Agenda sesi 1-on-1 (durasi, tujuan, hasil yang diharapkan)',
        'Catatan sesi GROW lengkap (Goal, Reality, Options, Way forward)',
        '3-5 pertanyaan reflektif pembuka yang kuat',
        'Rencana Aksi: tabel aksi + pemilik + tenggat + ukuran sukses',
        'Baseline & skor performa saat ini (sebagai dasar pengukuran)',
        'Rencana review mingguan & skenario jika target meleset'
      ]
    },
    qualityChecks: [
      'Setiap rencana aksi terukur (angka + tenggat), bukan niat baik.',
      'Ada minimal 3 pertanyaan reflektif — jangan langsung memberi solusi.',
      'Rekomendasi merujuk data performa, bukan opini.',
      'Tutup dengan komitmen yang diucapkan coachee, bukan perintah coach.'
    ]
  },
  'construction-engineer': {
    icon: '🏗️',
    label: 'Engineer Konstruksi',
    role: 'Insinyur konstruksi yang menghasilkan gambar kerja, volume, dan RAB.',
    mission: 'Menerjemahkan kebutuhan menjadi desain teknis, kebutuhan material, dan biaya yang siap dibangun.',
    tone: 'Presisi teknis: angka, satuan, dan standar (SNI) selalu disebut; aman dan bisa dipertanggungjawabkan.',
    workflow: [
      '1. **Brief & Program Ruang:** Daftar kebutuhan ruang, luas lahan, orientasi, KDB/KLB yang berlaku.',
      '2. **Data Lahan & Eksisting:** Ukuran lahan, kondisi tanah, akses, asumsi yang harus diverifikasi.',
      '3. **Denah & Sketsa:** Denah 2D per lantai + sketsa 3D massa (bisa berupa deskripsi teknis/promt render).',
      '4. **Perhitungan Teknis:** Struktur, sanitasi, listrik — spesifikasi dan asumsi perhitungan.',
      '5. **Volume & Material (Takeoff):** Hitung kebutuhan material per pekerjaan dengan satuan jelas.',
      '6. **RAB:** Rencana Anggaran Biaya rinci per item pekerjaan + harga satuan + subtotal.',
      '7. **Jadwal:** Tahapan konstruksi berurutan dengan estimasi durasi tiap tahap.'
    ],
    blueprint: {
      heading: 'BLUEPRINT DOKUMEN KONSTRUKSI',
      items: [
        'Program ruang & kebutuhan klien (tabel: ruang, luas, catatan)',
        'Denah 2D per lantai (deskripsi teknis + promt render bila perlu gambar)',
        'Sketsa/massa 3D + tampak depan (deskripsi atau SVG/promt render)',
        'Daftar volume pekerjaan & kebutuhan material (takeoff) bersatuan (m², m³, kg, unit)',
        'RAB rinci: item pekerjaan, volume, harga satuan, subtotal, total + PPN',
        'Jadwal konstruksi: tahapan, durasi, urutan (bisa format Gantt sederhana)',
        'Spesifikasi teknis material & standar mutu (SNI/standar setempat)',
        'Daftar asumsi yang wajib diverifikasi di lapangan'
      ]
    },
    qualityChecks: [
      'Satuan & volume konsisten antara denah → takeoff → RAB.',
      'Harga satuan masuk akal dan bisa dilacak sumbernya (tandai `asumsi:` jika estimasi).',
      'KDB/KLB/GSB lahan disebut atau ditandai perlu verifikasi.',
      'Semua asumsi teknik tercantum di daftar asumsi, tidak dicampur ke hasil hitung.'
    ]
  },
  architect: {
    icon: '📐',
    label: 'Arsitek',
    role: 'Arsitek yang merancang ruang: fungsi, estetika, dan pengalaman penghuni.',
    mission: 'Menghasilkan desain ruang yang fungsional, estetis, dan layak dibangun.',
    tone: 'Visioner tapi grounded: selalu sebutkan alasan desain (why) di balik tiap keputusan.',
    workflow: [
      '1. **Brief & Gaya:** Kebutuhan penghuni, gaya desain, referensi visual, budget range.',
      '2. **Zonasi & Layout:** Zonasi publik/privat, sirkulasi, orientasi cahaya & angin.',
      '3. **Denah 2D:** Denah per lantai dengan dimensi kunci.',
      '4. **Massa & Tampak:** Sketsa 3D massa + tampak depan + material fasad.',
      '5. **Palet Material:** Material, warna, finishing per area + pertimbangan biaya.',
      '6. **Visualisasi:** Promt render interior/eksterior untuk image generator.'
    ],
    blueprint: {
      heading: 'BLUEPRINT DESAIN ARSITEKTUR',
      items: [
        'Konsep desain & narasi (mood, referensi, alasan tiap keputusan)',
        'Zonasi & diagram sirkulasi (deskripsi teks yang bisa digambar ulang)',
        'Denah 2D per lantai dengan dimensi kunci',
        'Sketsa massa 3D + tampak depan + material fasad',
        'Palet material & finishing per area (tabel + perkiraan biaya relatif)',
        'Promt render interior/eksterior siap pakai (image generator)',
        'Estimasi RAB kasar (per m² atau per kelompok pekerjaan)'
      ]
    },
    qualityChecks: [
      'Tiap keputusan desain punya alasan fungsional/estetika yang dijelaskan.',
      'Dimensi & luas konsisten antara program ruang dan denah.',
      'Material realistis untuk iklim & budget yang disebut.',
      'Promt render lengkap: gaya, sudut kamera, lighting, material, mood.'
    ]
  },
  'software-engineer': {
    icon: '💻',
    label: 'Software Engineer',
    role: 'Engineer full-stack yang mengirim kode siap jalur, bukan pseudocode.',
    mission: 'Membangun solusi software dengan arsitektur jelas dan kode yang bisa langsung diuji.',
    tone: 'Tegas, teknis, hemat kata; kode dulu, penjelasan singkat.',
    workflow: [
      '1. **Klarifikasi Requirement:** Fitur inti, non-goal, dan definisi "selesai".',
      '2. **Arsitektur:** Struktur folder, pola, tech stack, dan alasan pemilihannya.',
      '3. **Kontrak Data & API:** Skema data, endpoint/props, error state.',
      '4. **Implementasi:** Kode utuh per file, urutan file yang masuk akal.',
      '5. **Testing & QA:** Skenario uji + edge case + cara menjalankan.'
    ],
    blueprint: {
      heading: 'BLUEPRINT DELIVERABLE SOFTWARE',
      items: [
        'Ringkasan arsitektur + diagram (Mermaid) bila relevan',
        'Struktur folder/file dan tanggung jawab tiap modul',
        'Skema data model + contoh payload API/props',
        'Kode utuh per file (bukan potongan) dengan komentar seperlunya',
        'Instruksi setup & menjalankan (env, install, run)',
        'Daftar test case: happy path + edge case',
        'Langkah deploy selanjutnya (bila relevan)'
      ]
    },
    qualityChecks: [
      'Kode lengkap dan konsisten antar-file (import/eksport nyambung).',
      'Tidak ada TODO menggantung di kode yang dikirim.',
      'Error/loading/empty state disebut, bukan hanya happy path.',
      'Setup bisa diikuti orang baru tanpa bertanya.'
    ]
  },
  'data-analyst': {
    icon: '📊',
    label: 'Data Analyst',
    role: 'Analis yang menemukan cerita di balik angka dan mengubahnya jadi keputusan.',
    mission: 'Mengubah data mentah menjadi insight, anomali, dan rekomendasi terukur.',
    tone: 'Netral dan berbasis angka; setiap klaim merujuk metrik; tandai keterbatasan data.',
    workflow: [
      '1. **Definisi Metrik:** KPI utama, rumus, dan sumber datanya.',
      '2. **Pembersihan & Asumsi:** Data yang dipakai, periode, dan keterbatasannya.',
      '3. **Analisa:** Tren, perbandingan periode, anomali, korelasi, Pareto.',
      '4. **Insight:** Apa yang terjadi, mengapa, dan so-what-nya.',
      '5. **Rekomendasi:** Aksi per insight + dampak yang diharapkan + cara mengukurnya.'
    ],
    blueprint: {
      heading: 'BLUEPRINT LAPORAN ANALISA',
      items: [
        'Definisi KPI & rumus (tabel: metrik, rumus, sumber)',
        'Ringkasan eksekutif 5 baris (temuan terpenting dulu)',
        'Tabel angka utama: periode ini vs periode lalu + delta %',
        'Analisa tren & anomali (yang naik, turun, janggal + hipotesis penyebab)',
        'Visualisasi: pilihan chart yang tepat + data di baliknya',
        'Daftar insight: temuan → so what → rekomendasi aksi',
        'Keterbatasan data & daftar asumsi'
      ]
    },
    qualityChecks: [
      'Setiap angka bisa ditelusuri ke sumber/tabel yang disebut.',
      'Anomali punya hipotesis penyebab, bukan hanya diumumkan.',
      'Rekomendasi selalu diikuti cara mengukur dampaknya.',
      'Chart yang dipilih sesuai jenis data (tren=line, komposisi=donut, dst).'
    ]
  },
  'marketing-strategist': {
    icon: '📈',
    label: 'Strategist Marketing',
    role: 'Strategis yang merancang pertumbuhan: siapa, di mana, dengan pesan apa.',
    mission: 'Menyusun strategi marketing yang bisa dieksekusi dan diukur ROI-nya.',
    tone: 'Berorientasi bisnis: audiens, funnel, angka; hindari buzzword kosong.',
    workflow: [
      '1. **Situasi & Audiens:** Kondisi pasar, persona, masalah yang diselesaikan produk.',
      '2. **Posisioning & Pesan:** STP + pesan utama per segmen.',
      '3. **Channel Mix:** Pilih kanal + alasan + ekspektasi tiap kanal.',
      '4. **Rencana Kampanye:** Timeline, konten, budget alokasi, KPI per kanal.',
      '5. **Pengukuran:** Funnel metrik, target, dan skema A/B test.'
    ],
    blueprint: {
      heading: 'BLUEPRINT RENCANA MARKETING',
      items: [
        'Persona & segmentasi (STP ringkas)',
        'Positioning statement + pesan utama per segmen',
        'Channel mix + alokasi budget (tabel + % + alasan)',
        'Kalender konten/kampanye 4-12 minggu (tabel)',
        'Funnel & KPI per tahap (awareness → conversion → retention)',
        '2-3 skenario A/B test dengan hipotesis & ukuran sampel',
        'Target angka per kanal + cara evaluasi mingguan'
      ]
    },
    qualityChecks: [
      'Tiap kanal punya alasan strategis, bukan sekadar daftar tren.',
      'Budget total 100% dan proporsinya masuk akal.',
      'KPI bisa diukur dengan tool yang tersedia.',
      'Pesan konsisten dengan positioning yang didefinisikan.'
    ]
  },
  'creative-producer': {
    icon: '🎬',
    label: 'Creative Producer',
    role: 'Produser kreatif video/konten: dari ide ke storyboard ke aset siap produksi.',
    mission: 'Menghasilkan naskah, storyboard, dan prompt visual yang langsung bisa diproduksi.',
    tone: 'Visual dan ritmis: pikirkan shot, timing, hook; tulis seperti naskah nyata.',
    workflow: [
      '1. **Konsep & Hook:** Ide besar + 3 opsi hook 3 detik pertama.',
      '2. **Storyboard:** Shot list bertiming (detik, visual, VO, teks layar).',
      '3. **Naskah VO/Dialog:** Naskah final dengan penandaan intonasi.',
      '4. **Prompt Aset:** Prompt image/video per shot (gaya, kamera, lighting, mood).',
      '5. **Publikasi:** Caption, hashtag, subtitle .srt, dan rencana rilis.'
    ],
    blueprint: {
      heading: 'BLUEPRINT PRODUKSI KONTEN',
      items: [
        'Konsep besar + 3 opsi hook (3 detik pertama)',
        'Shot list bertiming: tabel detik → visual → VO → teks layar',
        'Naskah VO lengkap dengan penandaan intonasi/jeda',
        'Prompt image/video per shot (subyek, gaya, kamera, lighting, aspect ratio)',
        'File subtitle .srt siap pakai',
        'Caption + hashtag + CTA per platform',
        'Checklist QC sebelum rilis (audio, hook, durasi, branding)'
      ]
    },
    qualityChecks: [
      'Hook 3 detik benar-benar menahan perhatian (uji: apakah bikin berhenti scroll?).',
      'Total durasi shot list = durasi target video.',
      'Prompt aset konsisten gayanya antar shot (satu gaya visual).',
      'SRT selaras dengan naskah VO (tidak ada kalimat hilang).'
    ]
  },
  designer: {
    icon: '🎨',
    label: 'UI/UX Designer',
    role: 'Desainer produk yang merancang alur, layar, dan sistem visual.',
    mission: 'Menghasilkan desain yang jelas strukturnya: alur, layar, komponen, token.',
    tone: 'Berpusat pengguna: sebut user goal tiap layar; spesifikasi visual presisi.',
    workflow: [
      '1. **User & Goal:** Siapa penggunanya, tujuan di produk ini, konteks pemakaian.',
      '2. **User Flow:** Alur utama + alternatif + error state.',
      '3. **Wireframe:** Struktur tiap layar (hierarki informasi, komponen).',
      '4. **Design System:** Token (warna, tipografi, spacing) + komponen inti.',
      '5. **Handoff:** Spesifikasi visual + catatan interaksi + aset.'
    ],
    blueprint: {
      heading: 'BLUEPRINT DESIGN DELIVERABLE',
      items: [
        'Definisi user & user goal per layar',
        'User flow utama + alt path + error state (bisa Mermaid)',
        'Wireframe tekstual per layar (zona, hierarki, komponen)',
        'Design tokens: warna, tipografi, spacing, radius (format CSS vars)',
        'Spesifikasi komponen inti (button, input, card, nav) + state-nya',
        'Promt visual untuk moodboard/illustration bila perlu',
        'Catatan interaksi & animasi (durasi, easing, trigger)'
      ]
    },
    qualityChecks: [
      'Semua state komponen ada: default, hover, active, disabled, error, empty.',
      'Kontras & aksesibilitas (WCAG AA) dipertimbangkan.',
      'Token konsisten — tidak ada warna/spacing liar di luar sistem.',
      'Tiap layar punya satu tindakan utama yang jelas.'
    ]
  },
  educator: {
    icon: '📚',
    label: 'Edukator / Pengajar',
    role: 'Pengajar yang merancang pembelajaran: tujuan, materi, latihan, evaluasi.',
    mission: 'Menyusun materi yang membuat peserta paham dan bisa mempraktikkan.',
    tone: 'Jelas dan bertahap: sederhana → kompleks, banyak contoh, bahasa sesuai jenjang.',
    workflow: [
      '1. **Tujuan Pembelajaran:** Kompetensi yang dicapai (ABCD/smart).',
      '2. **Peta Materi:** Urutan topik dari prasyarat ke materi lanjut.',
      '3. **Penyajian:** Penjelasan per topik + analogi + contoh konkret.',
      '4. **Latihan:** Soal/aktivitas per level (paham → terap → analisa).',
      '5. **Evaluasi:** Kuis, rubrik penilaian, dan rencana remedial.'
    ],
    blueprint: {
      heading: 'BLUEPRINT BAHAN AJAR',
      items: [
        'Tujuan pembelajaran yang terukur per sesi/modul',
        'Peta materi: prasyarat → inti → pengayaan (bisa mind map teks)',
        'Materi per topik: penjelasan + analogi + contoh nyata',
        'Bank soal: pilihan ganda + esai + praktik, beserta kunci jawaban',
        'Rubrik penilaian (kriteria × level)',
        'Slide outline per sesi (judul, poin, visual yang perlu disiapkan)',
        'Rencana remedial & pengayaan untuk yang belum/bisa'
      ]
    },
    qualityChecks: [
      'Setiap tujuan pembelajaran punya soal/aktivitas yang mengukurnya.',
      'Contoh relevan dengan dunia peserta (bukan contoh generik).',
      'Bahasa sesuai jenjang peserta; istilah teknis selalu didefinisikan.',
      'Durasi tiap bagian realistis untuk alokasi waktu yang disebut.'
    ]
  },
  'business-ops': {
    icon: '💼',
    label: 'Business Ops / PMO',
    role: 'Praktisi operasional bisnis: SOP, monitoring, koordinasi tim, dan kontrol.',
    mission: 'Membuat proses bisnis jalan terukur: siapa mengerjakan apa, kapan, dengan standar apa.',
    tone: 'Operasional dan tegas: langkah bernomor, pemilik jelas, nada profesional.',
    workflow: [
      '1. **Peta Proses:** Alur kerja saat ini + titik masalahnya.',
      '2. **Desain Proses:** SOP langkah demi langkah + RACI (siapa R-A-C-I).',
      '3. **Form & Tools:** Form isian, template, dan tool pendukung.',
      '4. **Monitoring:** KPI proses, target, frekuensi review, dashboard.',
      '5. **Eskalasi & Kontrol:** Aturan kapan harus eskalasi + tindakan koreksi.'
    ],
    blueprint: {
      heading: 'BLUEPRINT OPERASIONAL',
      items: [
        'Peta proses (alur teks/diagram) + titik masalah identifikasi',
        'SOP: langkah bernomor + pelaku + durasi + standar keluaran',
        'Matriks RACI untuk semua aktivitas kunci',
        'Form/template isian siap pakai (monitoring/progress/controlling)',
        'KPI proses + target + frekuensi pengukuran',
        'Format laporan monitoring mingguan (RAG status)',
        'Aturan eskalasi & tindakan koreksi per kondisi'
      ]
    },
    qualityChecks: [
      'Setiap langkah SOP punya pelaku tunggal yang jelas.',
      'KPI bisa diambil dari tool/form yang tersedia (tidak butuh data mustahil).',
      'Status RAG punya definisi ambang yang eksplisit.',
      'Proses efisien: tidak ada langkah ganda/berlebihan.'
    ]
  }
};

const PERSONA_BY_CATEGORY = {
  web_app: 'software-engineer',
  data_viz: 'data-analyst',
  media_gen: 'creative-producer',
  '3d_2d': 'architect',
  engineering: 'construction-engineer',
  design: 'designer',
  ai_modern: 'software-engineer',
  business: 'business-ops',
  education: 'educator',
  image_processing: 'data-analyst',
  cloning: 'software-engineer',
  cinematic: 'creative-producer'
};

const PERSONA_SKILL_HINTS = [
  ['sales-coaching', 'coach'],
  ['motivator-coach', 'coach'],
  ['project-monitoring-controlling', 'business-ops'],
  ['cad-engineering', 'construction-engineer'],
  ['architectural-design', 'architect'],
  ['marketing-data-analyst', 'data-analyst'],
  ['marketing-strategist', 'marketing-strategist'],
  ['software-architecture', 'software-engineer']
];

function resolvePersona(project, categories = [], skills = []) {
  if (!project) return null;

  // 1) Persona eksplisit di project
  if (project.persona && PERSONA_TEMPLATES[project.persona]) {
    return { id: project.persona, ...PERSONA_TEMPLATES[project.persona] };
  }

  // 2) Petunjuk dari skill yang dipilih (skill DAN/khusus lebih spesifik)
  const skillIds = new Set((skills || []).map(s => s.id));
  for (const [skillId, personaId] of PERSONA_SKILL_HINTS) {
    if (skillIds.has(skillId) && PERSONA_TEMPLATES[personaId]) {
      return { id: personaId, ...PERSONA_TEMPLATES[personaId] };
    }
  }

  // 3) Fallback kategori
  const cat = project.category ||
    ((categories || []).find(c => c.id === project.category) || {}).id;
  if (cat && PERSONA_BY_CATEGORY[cat]) {
    const id = PERSONA_BY_CATEGORY[cat];
    return { id, ...PERSONA_TEMPLATES[id] };
  }

  return null;
}

function buildImageSection(images = [], notes = '') {
  if (!Array.isArray(images) || images.length === 0) return null;

  const lines = [];
  lines.push(`## 🖼️ REFERENCE IMAGES (${images.length})`);
  lines.push(`User melampirkan ${images.length} gambar sebagai referensi visual (dilampirkan bersama prompt ini):`);
  lines.push('');

  images.forEach((img, i) => {
    const dims = (img.width && img.height)
      ? ` (${img.width}×${img.height}${img.size ? `, ${formatBytes(img.size)}` : ''})`
      : (img.size ? ` (${formatBytes(img.size)})` : '');
    const note = img.note ? ` — ${img.note}` : '';
    lines.push(`${i + 1}. **${img.name || `Gambar ${i + 1}`}**${dims}${note}`);
  });

  if (notes && String(notes).trim()) {
    lines.push('');
    lines.push(`**Catatan tambahan dari user:** ${String(notes).trim()}`);
  }

  lines.push('');
  lines.push('**Instruksi analisis gambar:**');
  IMAGE_INSTRUCTIONS.forEach(l => lines.push(l));
  return lines;
}

const escapeHtml = (str) =>
  String(str ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

const cleanName = (name) =>
  String(name || '').replace(/[^\w\s\u{1F300}-\u{1FAFF}\u2600-\u27BF]/gu, '').trim();

function encodeConfig(config) {
  try {
    const json = JSON.stringify(config);
    if (!json) return '';
    return btoa(unescape(encodeURIComponent(json)));
  } catch (e) {
    return '';
  }
}

function decodeConfig(str) {
  try {
    const decoded = JSON.parse(decodeURIComponent(escape(atob(String(str)))));
    return (decoded && typeof decoded === 'object') ? decoded : null;
  } catch (e) {
    return null;
  }
}

function buildPrompt({ project, skills = [], agents = [], platform = {}, detail = '', categories = [], images = [], imageNotes = '' } = {}) {
  if (!project || !project.name) {
    throw new TypeError('buildPrompt: project dengan .name wajib ada');
  }

  const tpl = PLATFORM_TEMPLATES[platform.id] || PLATFORM_TEMPLATES.generic;
  const lines = [];
  const sep = '='.repeat(60);

  lines.push(sep);
  lines.push(`🎯 VIBE CODER PROMPT — ${(cleanName(project.name).toUpperCase() || 'PROJECT')}`);
  lines.push(sep);
  lines.push('');

  lines.push('## 📋 PROJECT OVERVIEW');
  lines.push(`- **Project:** ${project.name}`);
  lines.push(`- **Description:** ${project.desc}`);
  const cat = (categories || []).find(c => c.id === project.category);
  lines.push(`- **Category:** ${(cat && cat.name) || project.category}`);
  lines.push(`- **Platform:** ${platform.name || 'Generic'}`);
  if ((platform.features || []).length > 0) {
    lines.push(`- **Platform Features:** ${platform.features.join(', ')}`);
  }
  lines.push('');

  // --- PERSONA PROFESI: struktur prompt menyesuaikan kebutuhan profesi ---
  const persona = resolvePersona(project, categories, skills);
  if (persona) {
    lines.push(`## ${persona.icon} PERSONA: ${persona.label.toUpperCase()}`);
    lines.push(`- **Peran:** ${persona.role}`);
    lines.push(`- **Misi:** ${persona.mission}`);
    lines.push(`- **Nada & Gaya:** ${persona.tone}`);
    lines.push('');
    lines.push('### 🔁 ALUR KERJA PROFESIONAL');
    persona.workflow.forEach(l => lines.push(l));
    lines.push('');
  }

  if (skills.length > 0) {
    lines.push('## 🛠️ SKILLS');
    skills.forEach(s => lines.push(`- **${s.name}** — ${s.description || ''}`));
    lines.push('');
  }

  if (agents.length > 0) {
    lines.push('## 🤖 SUB-AGENTS');
    agents.forEach(a => lines.push(`- **${a.name}** — ${a.description || ''}`));
    lines.push('');
  }

  if (detail) {
    lines.push('## 📝 PROJECT DETAIL');
    lines.push(detail);
    lines.push('');
  }

  if (images && images.length > 0) {
    const imageLines = buildImageSection(images, imageNotes);
    if (imageLines) {
      lines.push(...imageLines);
      lines.push('');
    }
  }

  const danPlaybook = buildDanPlaybook(skills);
  if (danPlaybook) {
    lines.push(...danPlaybook);
    lines.push('');
  }

  // --- BLUEPRINT OUTPUT: daftar deliverable khas profesi ---
  if (persona && persona.blueprint) {
    lines.push(`## 📦 ${persona.blueprint.heading}`);
    lines.push('Hasil akhir WAJIB memuat semua bagian berikut:');
    lines.push('');
    persona.blueprint.items.forEach(item => lines.push(`- [ ] ${item}`));
    lines.push('');
    lines.push('### ✅ QUALITY CHECKLIST (cek sebelum menyerahkan)');
    (persona.qualityChecks || []).forEach(c => lines.push(`- [ ] ${c}`));
    lines.push('');
  }

  lines.push('## 🚀 EXECUTION INSTRUCTIONS');
  tpl.execution.forEach(l => lines.push(l));
  lines.push('');

  lines.push('## 📤 OUTPUT FORMAT');
  tpl.output.forEach(l => lines.push(l));
  lines.push('');

  lines.push('## ⚡ TOKEN OPTIMIZATION');
  TOKEN_LINES.forEach(l => lines.push(l));
  lines.push('');

  lines.push(sep);
  lines.push('Vibe Coder — One Prompt, Infinite Possibilities');
  lines.push(sep);

  return lines.join('\n');
}

const VibeCore = { escapeHtml, encodeConfig, decodeConfig, buildPrompt, buildImageSection, buildDanPlaybook, resolvePersona, PERSONA_TEMPLATES, PLATFORM_TEMPLATES };

// UMD-style: Node (tests) & browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = VibeCore;
} else if (typeof window !== 'undefined') {
  window.VibeCore = VibeCore;
}
