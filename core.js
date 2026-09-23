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
  banana: {
    execution: [
      '1. **Parse Intent:** Identifikasi subjek produk, gaya, dan hasil yang diinginkan.',
      '2. **Instruct Edit:** Nyatakan APA yang diubah dan APA YANG DIKUNCI (bentuk, label, logo produk).',
      '3. **Multi-Reference:** Manfaatkan hingga beberapa gambar referensi (subjek, gaya, latar).',
      '4. **Generate:** Hasilkan gambar + penjelasan singkat perubahan yang dilakukan.',
      '5. **Validate:** Periksa konsistensi teks pada kemasan & logo — regenerasi bila rusak.'
    ],
    output: [
      '- **Gambar:** per varian dengan rasio eksplisit (1:1, 9:16, 16:9)',
      '- **Revisi:** prompt ulang singkat untuk tiap perbaikan',
      '- **Iterasi:** 2-3 saran variasi lanjutan'
    ]
  },
  'google-flow': {
    execution: [
      '1. **Storyboard:** Pecah durasi target menjadi scene 5-8 detik (batas per prompt).',
      '2. **Ingredients:** Gunakan gambar produk/karakter sebagai referensi konsistensi.',
      '3. **Prompt per Scene:** Subjek, aksi, gerakan kamera, dialog (native audio), SFX, ambience.',
      '4. **Scenebuilder:** Rangkai dengan jump-to & extend sampai durasi tercapai.',
      '5. **Validate:** Cek kontinuitas visual & audio antar scene.'
    ],
    output: [
      '- **Tabel Scene:** detik → visual → dialog/VO → SFX',
      '- **Prompt per Scene:** siap-tempel, satu blok kode per scene',
      '- **Spesifikasi:** rasio aset (16:9 / 9:16) & total durasi'
    ]
  },
  gamma: {
    execution: [
      '1. **Outline:** Pecah konten menjadi slide (judul + maksimal 3 poin).',
      '2. **Layout:** Sarankan layout & kebutuhan visual per slide.',
      '3. **Theme:** Kunci palet warna & tipografi agar konsisten.',
      '4. **Generate:** Output outline siap di-paste ke Gamma / struktur PPTX.',
      '5. **Validate:** Tiap slide satu pesan utama, visual mendukung.'
    ],
    output: [
      '- **Outline:** per slide dalam markdown bernomor',
      '- **Visual:** saran chart/gambar per slide',
      '- **Ekspor:** instruksi PPTX/PDF'
    ]
  },
  'ai-web-builder': {
    execution: [
      '1. **MVP Dulu:** Daftar halaman/fitur inti; non-goal dilarang dikerjakan.',
      '2. **Stack Eksplisit:** Framework, styling, database, auth disebut jelas.',
      '3. **Komposisi Berurutan:** Satu instruksi per layar agar AI tidak melompat.',
      '4. **Iterate:** Permintaan perbaikan kecil & spesifik, bukan rewrite besar.',
      '5. **Validate:** Responsif + empty/error state tersedia.'
    ],
    output: [
      '- **Prompt Awal:** siap-tempel ke Lovable/Bolt/v0/Replit',
      '- **Prompt Iterasi:** antrian perbaikan lanjutan',
      '- **Integrasi:** catatan env/DB/deploy'
    ]
  },
  'ai-ux-tool': {
    execution: [
      '1. **Scan Screenshot:** Ekstrak komponen & hierarki informasi.',
      '2. **Wireframe:** Struktur ulang per layar (zona, komponen, alur).',
      '3. **Theme:** Palet & tipografi baru yang konsisten.',
      '4. **Handoff:** Design tokens + spesifikasi komponen.',
      '5. **Validate:** Kontras & aksesibilitas (WCAG AA).'
    ],
    output: [
      '- **Wireframe:** tekstual per layar',
      '- **Tokens:** CSS variables siap pakai',
      '- **Interaksi:** catatan animasi & state'
    ]
  },
  'image-gen-generic': {
    execution: [
      '1. **Parse:** Subjek → gaya → komposisi → lighting → kualitas.',
      '2. **Susun Prompt:** Padat dan deskriptif, istilah fotografi/desain nyata.',
      '3. **Parameter:** Sertakan --ar/--v (Midjourney) atau negative prompt (SD).',
      '4. **Variasi:** Berikan 2-3 varian prompt.',
      '5. **Validate:** Cek anatomi, teks pada gambar, dan konsistensi produk.'
    ],
    output: [
      '- **Prompt Utama:** + 2 varian',
      '- **Parameter:** rasio, versi model, negative prompt',
      '- **Tips:** perbaikan untuk iterasi berikutnya'
    ]
  },
  'video-gen-generic': {
    execution: [
      '1. **Scene:** Satu prompt = satu shot 5-10 detik.',
      '2. **Motion:** Deskripsikan gerakan kamera & subjek secara eksplisit.',
      '3. **Image-to-Video:** Gunakan gambar produk sebagai frame awal.',
      '4. **Validate:** Hindari morphing produk; cek konsistensi antar shot.'
    ],
    output: [
      '- **Prompt per Shot:** + camera motion',
      '- **Spesifikasi:** durasi & rasio per shot',
      '- **Rangkaian:** urutan shot untuk video penuh'
    ]
  },
  '3d-gen': {
    execution: [
      '1. **Input:** Foto/screenshot multi-sudut bila tersedia.',
      '2. **Rekonstruksi:** Deskripsikan bentuk, material, detail yang harus dipertahankan.',
      '3. **Texture:** PBR material, warna, roughness.',
      '4. **Export:** glb/usdz + turntable render 360°.'
    ],
    output: [
      '- **Prompt:** image-to-3d / text-to-3d',
      '- **Settings:** polygon, texture resolution',
      '- **QC:** checklist mesh (topologi, uv, material)'
    ]
  },
  'cursor-agent': {
    execution: [
      '1. **Konteks Repo:** Sebut struktur folder & file yang disentuh.',
      '2. **Tugas Spesifik:** Per file, hindari permintaan luas.',
      '3. **Rules:** Ikuti .cursor/rules / AGENTS.md bila ada.',
      '4. **Validate:** Jalankan test/typecheck setelah edit.'
    ],
    output: [
      '- **Diff:** per file',
      '- **Command:** terminal yang perlu dijalankan',
      '- **Verifikasi:** langkah QA'
    ]
  },
  'voice-gen': {
    execution: [
      '1. **Naskah:** Siapkan teks dengan penanda jeda & intonasi.',
      '2. **Voice:** Pilih karakter suara & kunci konsistensinya.',
      '3. **Avatar:** Penampilan, pakaian, latar (bila video avatar).',
      '4. **Validate:** Pelafalan angka & istilah teknis.'
    ],
    output: [
      '- **Naskah:** siap baca untuk TTS',
      '- **Setting:** voice id, stability, speed',
      '- **Brief Avatar:** lengkap per scene'
    ]
  },
  suno: {
    execution: [
      '1. **Konsep:** Tentukan tema, pesan, dan pendengar target lagu.',
      '2. **Lirik:** Tulis berstruktur dengan tag [Verse]/[Chorus]/[Bridge]/[Outro]; sebut nama/brand bila perlu.',
      '3. **Style of Music:** Satu baris padat: genre + subgenre, mood, tempo (BPM), jenis vokal, instrumen kunci.',
      '4. **Mode:** Custom Mode (lirik + style) atau Simple (deskripsi saja); [Instrumental] bila tanpa vokal.',
      '5. **Validate:** Suku kata per baris masuk akal dinyanyikan; hindari kata sulit diuapkan.'
    ],
    output: [
      '- **Kotak 1 — Lyrics:** lirik berstruktur lengkap dengan tag',
      '- **Kotak 2 — Style of Music:** maksimal ±200 karakter',
      '- **Varian:** 2 alternatif gaya + saran extend/remix'
    ]
  },
  hailuo: {
    execution: [
      '1. **Klip 6-10 detik:** Satu prompt = satu klip; aksi tunggal yang jelas.',
      '2. **Formula:** Subjek + aksi + gerakan kamera + lighting + suasana; hindari multi-aksi berantakan.',
      '3. **T2V vs S2V:** Text-to-video untuk scene bebas; image-to-video (S2V) bila produk/wajah harus konsisten — gambar = frame awal.',
      '4. **Kamera:** Sebut eksplisit (orbit, dolly-in, pan, handheld, slow motion).',
      '5. **Validate:** Konsistensi produk antar klip; rencana penyambungan di editor.'
    ],
    output: [
      '- **Prompt per klip:** siap-tempel, satu blok kode per klip',
      '- **Rencana klip:** tabel urutan klip → durasi → transisi',
      '- **Spesifikasi:** rasio (16:9/9:16), durasi total, referensi gambar bila S2V'
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

const IMAGE_INSTRUCTIONS_EN = [
  '- Treat every image as a binding visual requirement.',
  '- Extract layout, color palette, components, and information hierarchy from the images.',
  '- If text and images conflict, state the conflict and ask for clarification before proceeding.',
  '- Refer to images by number (e.g., "as in Image 2") in your answer.'
];

const formatBytes = (bytes) => {
  if (!Number.isFinite(bytes) || bytes <= 0) return '';
  const units = ['B', 'KB', 'MB'];
  let i = 0, v = bytes;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${Number.isInteger(v) ? v : v.toFixed(1)} ${units[i]}`;
};

const RAUZA_PRINCIPLES = [
  '1. Data dulu, opini belakangan — setiap klaim punya angka atau ditandai `asumsi:`.',
  '2. Setiap temuan punya "so what": satu aksi konkret + pemilik + tenggat.',
  '3. Jujur soal ketidakpastian: sebut sampel, rentang waktu, dan keterbatasan.',
  '4. Hemat kata, kaya substansi: tabel/daftar, bukan paragraf panjang.',
  '5. Selesaikan sampai deliverable, bukan sekadar saran.',
  '6. Tutup dengan 2-3 langkah berikutnya.'
];

const RAUZA_DELIVERABLE_HINTS = {
  'marketing-data-analyst': 'JSON hasil analisa + Markdown ringkasan (KPI, anomali, forecast)',
  'marketing-strategist': 'Campaign plan: tujuan, audiens, channel mix, budget, A/B test',
  'data-to-infographic': 'Infografik/chart SVG self-contained (tanpa CDN)',
  'image-video-creator': 'Storyboard shot-list bertiming + prompt image/video + SRT',
  'design-engineer-2d-3d': 'Brief desain + spec teknis + sketsa/mockup 3D',
  'motivator-coach': 'Rencana coaching GROW berbasis data performa',
  'project-monitoring-controlling': 'Status proyek: variance, SPI, RAG, stalled, earned value',
  'software-architecture': 'Scaffold/review/trade-off + rekomendasi ber-konteks',
  'architectural-design': 'Denah 2D, massa 3D, tampak, KDB/KLB, RAB, tahapan konstruksi',
  'persona-visual-director': 'Brand visual guide: palet, mood, gaya konsisten lintas aset (foto/video/3D/banner)'
};

const RAUZA_PRINCIPLES_EN = [
  '1. Data first, opinion later — every claim has a number or is marked `assumption:`.',
  '2. Every finding has a "so what": one concrete action + owner + deadline.',
  '3. Be honest about uncertainty: state sample, timeframe, and limitations.',
  '4. Few words, rich substance: tables/lists over long paragraphs.',
  '5. Finish at the deliverable, not just advice.',
  '6. Close with 2-3 next steps.'
];

const RAUZA_DELIVERABLE_HINTS_EN = {
  'marketing-data-analyst': 'Analysis JSON + Markdown summary (KPI, anomalies, forecast)',
  'marketing-strategist': 'Campaign plan: goal, audience, channel mix, budget, A/B test',
  'data-to-infographic': 'Self-contained SVG infographic/charts (no CDN)',
  'image-video-creator': 'Timed shot-list storyboard + image/video prompts + SRT',
  'design-engineer-2d-3d': 'Design brief + technical spec + 3D sketch/mockup',
  'motivator-coach': 'Data-driven GROW coaching plan',
  'project-monitoring-controlling': 'Project status: variance, SPI, RAG, stalled, earned value',
  'software-architecture': 'Scaffold/review/trade-off + context-aware recommendation',
  'architectural-design': '2D floor plans, 3D massing, elevations, KDB/KLB, RAB, construction phases',
  'persona-visual-director': 'Brand visual guide: palette, mood, consistent style across assets (photo/video/3D/banner)'
};

function buildRauzaPlaybook(skills = [], lang = 'id') {
  const en = lang === 'en';
  const hints = en ? RAUZA_DELIVERABLE_HINTS_EN : RAUZA_DELIVERABLE_HINTS;
  const rauzaSkills = skills.filter(s => hints[s.id]);
  if (rauzaSkills.length === 0) return null;

  const lines = [];
  lines.push(en ? '## 🧠 RAUZA PLAYBOOK (MANDATORY METHODOLOGY)' : '## 🧠 RAUZA PLAYBOOK (METODOLOGI WAJIB)');
  lines.push(en
    ? 'RAUZA skills are active in this prompt. Follow the RAUZA methodology:'
    : 'Skill RAUZA aktif dalam prompt ini. Ikuti metodologi RAUZA:');
  lines.push('');
  (en ? RAUZA_PRINCIPLES_EN : RAUZA_PRINCIPLES).forEach(l => lines.push(l));
  lines.push('');
  lines.push(en ? '**Expected deliverable per RAUZA skill:**' : '**Deliverable yang diharapkan per skill RAUZA:**');
  rauzaSkills.forEach(s => lines.push(`- **${s.name}** → ${hints[s.id]}`));
  lines.push('');
  lines.push(en
    ? 'The full reference package (metric library, frameworks, runbooks, CLI engines) lives in the `skills/dan/` folder of this repository.'
    : 'Paket referensi lengkap (pustaka metrik, framework, runbook, engine CLI) tersedia di folder `skills/dan/` pada repositori ini.');
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

function buildImageSection(images = [], notes = '', lang = 'id') {
  if (!Array.isArray(images) || images.length === 0) return null;
  const en = lang === 'en';

  const lines = [];
  lines.push(en ? `## 🖼️ REFERENCE IMAGES (${images.length})` : `## 🖼️ REFERENCE IMAGES (${images.length})`);
  lines.push(en
    ? `The user attached ${images.length} image(s) as visual reference (attached together with this prompt):`
    : `User melampirkan ${images.length} gambar sebagai referensi visual (dilampirkan bersama prompt ini):`);
  lines.push('');

  images.forEach((img, i) => {
    const dims = (img.width && img.height)
      ? ` (${img.width}×${img.height}${img.size ? `, ${formatBytes(img.size)}` : ''})`
      : (img.size ? ` (${formatBytes(img.size)})` : '');
    const note = img.note ? ` — ${img.note}` : '';
    lines.push(`${i + 1}. **${img.name || (en ? `Image ${i + 1}` : `Gambar ${i + 1}`)}**${dims}${note}`);
  });

  if (notes && String(notes).trim()) {
    lines.push('');
    lines.push(en
      ? `**Additional notes from the user:** ${String(notes).trim()}`
      : `**Catatan tambahan dari user:** ${String(notes).trim()}`);
  }

  lines.push('');
  lines.push(en ? '**Image analysis instructions:**' : '**Instruksi analisis gambar:**');
  (en ? IMAGE_INSTRUCTIONS_EN : IMAGE_INSTRUCTIONS).forEach(l => lines.push(l));
  return lines;
}

// ============================================
// AKSEN UI PER PROJECT — tampilan menyesuaikan project yang dipilih
// ============================================
const PROJECT_ACCENTS = {
  'banana-product-photo': { accent: '#f5c518', accent2: '#ff8a3d', icon: '🍌', vibe: 'Kreatif Studio',
    workflow: ['1. Analisis gambar: bentuk produk, label, bahan, latar.', '2. Susun prompt instruct-edit: apa yang diganti, apa yang DIKUNCI (bentuk & label produk).', '3. Sarankan variasi: rasio 1:1 / 9:16 / 16:9, latar, dan sudut kamera.', '4. QA hasil: konsistensi logo & teks pada kemasan.'] },
  'google-flow-video': { accent: '#ff5d6c', accent2: '#ff8a3d', icon: '🎥', vibe: 'Flow Scenebuilder',
    workflow: ['1. Pecah durasi target menjadi scene ±8 detik (batas per prompt Veo).', '2. Siapkan ingredients: gambar produk/karakter sebagai referensi konsistensi.', '3. Tulis prompt per scene: subjek, aksi, kamera, dialog, SFX, ambience.', '4. Rangkai di Flow: jump-to, extend, dan sinkronkan audio antar scene.'] },
  'gamma-presentation': { accent: '#7c5cff', accent2: '#00d4ff', icon: '📽️', vibe: 'Deck Instant',
    workflow: ['1. Tentukan audiens, tujuan deck, dan jumlah slide.', '2. Susun outline per slide: judul + maksimal 3 poin + kebutuhan visual.', '3. Tambahkan petunjuk layout & palet agar tema konsisten.', '4. Ekspor: paste outline ke Gamma, atau minta PPTX dari ChatGPT/Claude.'] },
  'ai-web-builder': { accent: '#00d4ff', accent2: '#2ecc8f', icon: '⚡', vibe: 'Ship Cepat',
    workflow: ['1. Definisikan MVP: halaman/fitur inti dulu, non-goal dilarang dikerjakan.', '2. Sebutkan tech stack & integrasi secara eksplisit.', '3. Komposisikan halaman berurutan — satu instruksi per layar agar AI tidak melompat.', '4. Iterasi: permintaan perbaikan kecil dan spesifik, bukan rewrite besar.'] },
  'screenshot-to-visual': { accent: '#2ecc8f', accent2: '#00d4ff', icon: '📸', vibe: 'One-Shot Visual',
    workflow: ['1. Baca screenshot: identifikasi produk/UI, gaya, dan tujuan output.', '2. Pilih pipeline: video, 3D, atau wireframe (bisa lebih dari satu).', '3. Susun prompt per pipeline sesuai standar generator tujuan.', '4. Beri catatan QA: konsistensi produk, durasi, dan rasio aset.'] },
  'product-visual-suite': { accent: '#e8b4ff', accent2: '#7c5cff', icon: '🧴', vibe: 'Brand Kit Visual',
    workflow: ['1. Kunci brand: palet, mood, dan gaya visual dipakai di SEMUA aset.', '2. Foto hero: latar, properti, lighting, rasio per marketplace.', '3. Video: storyboard 15 detik + VO + musik + teks layar.', '4. 3D & banner: turntable render + banner per platform (Meta/TikTok/MP).'] },
  'ai-ux-redesign': { accent: '#f59e0b', accent2: '#7c5cff', icon: '🎨', vibe: 'UX Doctor',
    workflow: ['1. Audit screenshot: hierarki, kontras, spacing, alur pengguna.', '2. Daftar masalah UX diurutkan dari dampak terbesar.', '3. Wireframe ulang: struktur per layar + alur baru.', '4. Design tokens: warna, tipografi, spacing — siap handoff Figma.'] },
  'suno-song': { accent: '#e85d9e', accent2: '#7c5cff', icon: '🎵', vibe: 'Music Studio',
    workflow: ['1. Konsep: tema, pesan, pendengar target.', '2. Lirik berstruktur: [Verse]/[Chorus]/[Bridge] + hook yang nempel.', '3. Style of Music: genre, mood, BPM, vokal, instrumen dalam satu baris.', '4. Generate di Suno → extend/remix varian terbaik.'] },
  'hailuo-short': { accent: '#14b8c4', accent2: '#00d4ff', icon: '🌊', vibe: 'Cinematic Clips',
    workflow: ['1. Pecah konsep jadi klip 6-10 detik, satu aksi per klip.', '2. Formula prompt: subjek + aksi + kamera + lighting + suasana.', '3. S2V: pakai gambar produk sebagai frame awal untuk konsistensi.', '4. Rangkai klip di editor + grading agar satu gaya.'] }
};

const FALLBACK_PLACEHOLDER = 'Contoh: Buatkan produk digital untuk UMKM — jelaskan target pengguna, fitur utama, gaya visual, dan platform tujuan...';

function resolveProjectUi(project) {
  if (!project) return null;
  const extra = PROJECT_ACCENTS[project.id] || {};
  return {
    accent: extra.accent || null,
    accent2: extra.accent2 || null,
    icon: extra.icon || (project.name || '').split(' ')[0] || '🚀',
    vibe: extra.vibe || null,
    workflow: extra.workflow || null,
    tips: project.tips || null,
    detailPlaceholder: (project.placeholders && project.placeholders.detail) || FALLBACK_PLACEHOLDER
  };
}

// ============================================
// PROMPT DETAIL — struktur 9 elemen universal (diterima semua AI generator)
// ============================================
const DETAIL_ELEMENTS = {
  id: [
    '- [Subjek] Apa objek/produk/aplikasi yang dikerjakan?',
    '- [Tujuan] Untuk apa hasilnya dipakai (ads, pitch, dev, edukasi)?',
    '- [Audiens] Siapa yang melihat/memakai hasilnya?',
    '- [Gaya & Mood] Referensi visual, palet, suasana, tone.',
    '- [Spesifikasi Teknis] Rasio/dimensi, durasi, format file, platform.',
    '- [Kendala] Larangan, batasan brand, hal yang TIDAK boleh berubah.',
    '- [Format Keluaran] Struktur jawaban yang diharapkan.',
    '- [Kriteria Sukses] Bagaimana hasil disebut "berhasil".'
  ],
  en: [
    '- [Subject] What object/product/app is being worked on?',
    '- [Purpose] What will the output be used for (ads, pitch, dev, education)?',
    '- [Audience] Who will see/use the result?',
    '- [Style & Mood] Visual references, palette, atmosphere, tone.',
    '- [Technical Specs] Aspect ratio/dimensions, duration, file format, platform.',
    '- [Constraints] Prohibitions, brand limits, things that must NOT change.',
    '- [Output Format] Expected structure of the answer.',
    '- [Success Criteria] How the result is judged "done".'
  ]
};

function buildDetailRequirements(detail, lang = 'id') {
  const en = lang === 'en';
  const text = String(detail || '').trim();
  if (!text) return null;
  const lines = [];
  lines.push(en
    ? '### 🧩 DETAIL STRUCTURE (understand each element before working)'
    : '### 🧩 STRUKTUR DETAIL (pahami tiap elemen sebelum bekerja)');
  lines.push(text);
  lines.push('');
  lines.push(en
    ? '**Extraction framework — answer implicitly in your output when the user does not state it (mark `assumption:`):**'
    : '**Framework ekstraksi — jawab implisit di output Anda bila user tidak menyebutkannya (tandai `asumsi:`):**');
  DETAIL_ELEMENTS[lang === 'en' ? 'en' : 'id'].forEach(l => lines.push(l));
  return lines;
}

// ============================================
// VISUAL PIPELINE — screenshot/foto produk → video / 3D / wireframe
// Aktif otomatis bila project punya skill pipeline atau ada gambar terlampir
// ============================================
const PIPELINE_SKILL_HINTS = ['screenshot-to-video', 'screenshot-to-3d', 'screenshot-to-wireframe', 'product-visual-suite'];

function buildVisualPipeline(images, skills, lang = 'id') {
  const en = lang === 'en';
  const skillIds = new Set((skills || []).map(s => s.id));
  const wantsPipeline = PIPELINE_SKILL_HINTS.some(id => skillIds.has(id));
  if (!wantsPipeline && (!images || images.length === 0)) return null;

  const video = wantsPipeline || skillIds.has('screenshot-to-video') || skillIds.has('product-visual-suite');
  const three = wantsPipeline || skillIds.has('screenshot-to-3d') || skillIds.has('product-visual-suite');
  const wire = wantsPipeline || skillIds.has('screenshot-to-wireframe');

  const lines = [];
  lines.push(en
    ? '## 🎬 VISUAL PIPELINE — FROM SCREENSHOT TO READY-TO-USE OUTPUT'
    : '## 🎬 VISUAL PIPELINE — DARI SCREENSHOT MENJADI OUTPUT SIAP PAKAI');
  lines.push(en
    ? 'The user only needs to attach a screenshot/photo. Compose READY-TO-PASTE prompts for each relevant pipeline below (the user just copies them into the target generator):'
    : 'User cukup melampirkan screenshot/foto. Susun PROMPT SIAP-PAKAI untuk tiap pipeline yang relevan di bawah (user tinggal copy ke generator tujuan):');
  lines.push('');
  if (video) {
    lines.push('### ▶️ Pipeline A — Video (Google Flow / Veo 3, Runway, Kling, Pika)');
    lines.push(en
      ? '- Break into 5-8 second scenes; per scene write: subject, action, camera movement, lighting, dialogue/VO, SFX, ambience.'
      : '- Pecah jadi scene 5–8 detik; per scene tulis: subjek, aksi, gerakan kamera, lighting, dialog/VO, SFX, ambience.');
    lines.push(en
      ? '- The product screenshot/photo = `ingredients` (consistency reference) — the product MUST NOT change shape.'
      : '- Screenshot/foto produk = `ingredients` (referensi konsistensi) — produk TIDAK BOLEH berubah bentuk.');
    lines.push(en
      ? '- State the aspect ratio (16:9 / 9:16 / 1:1) and total target duration.'
      : '- Sebut rasio (16:9 / 9:16 / 1:1) dan total durasi target.');
  }
  if (three) {
    lines.push('### 🏗️ Pipeline B — 3D (Meshy / Tripo / Luma / Spline)');
    lines.push(en
      ? '- Reconstruction prompt: main shape, material, details that must be preserved.'
      : '- Prompt rekonstruksi: bentuk utama, material, detail yang harus dipertahankan.');
    lines.push(en
      ? '- Render instructions: 360° turntable, studio lighting, PBR materials, glb/usdz output + 1:1 video ratio.'
      : '- Instruksi render: turntable 360°, lighting studio, PBR material, output glb/usdz + rasio video 1:1.');
  }
  if (wire) {
    lines.push('### 📐 Pipeline C — Wireframe / Redesign (Uizard, Figma AI, hand-off dev)');
    lines.push(en
      ? '- Analyze the screenshot: information hierarchy, detected components, UX problems.'
      : '- Analisis screenshot: hierarki informasi, komponen terdeteksi, masalah UX.');
    lines.push(en
      ? '- Produce a textual wireframe per screen (zones, components, flow) + design tokens (CSS vars).'
      : '- Hasilkan wireframe tekstual per layar (zona, komponen, alur) + design tokens (CSS vars).');
  }
  lines.push('');
  lines.push(en
    ? '**Pipeline rule:** do not mix two pipelines in one prompt; write each prompt in a separate code block for easy copying.'
    : '**Aturan pipeline:** jangan campur instruksi dua pipeline dalam satu prompt; tulis tiap prompt dalam blok kode terpisah agar mudah disalin.');
  return lines;
}

// ============================================
// PLATFORM PROMPT FRAMEWORK — struktur standar yang diterima AI generator apa pun
// ============================================
function buildPlatformFramework(platform, lang = 'id') {
  const en = lang === 'en';
  const lines = [];
  lines.push(en
    ? '## 🧱 PROMPT FRAMEWORK (MANDATORY — standard output structure)'
    : '## 🧱 PROMPT FRAMEWORK (WAJIB — struktur keluaran standar)');
  lines.push(en
    ? 'Structure your answer with this frame so the result works in any generator:'
    : 'Susun jawaban Anda dengan kerangka ini sehingga hasilnya bisa langsung dipakai di generator mana pun:');
  lines.push('');
  lines.push('```');
  lines.push(en
    ? '[SUBJECT]     - one sentence: what is being made'
    : '[SUBJEK]      — satu kalimat: apa yang dibuat');
  lines.push(en
    ? '[STYLE]       - palette, mood, visual references, lighting'
    : '[GAYA]        — palet, mood, referensi visual, lighting');
  lines.push(en
    ? '[TECHNICAL]   - ratio, duration, format, target platform'
    : '[TEKNIS]      — rasio, durasi, format, platform target');
  lines.push(en
    ? '[CONSTRAINTS] - prohibitions & things locked (e.g., product shape)'
    : '[KENDALA]     — larangan & hal yang dikunci (mis. bentuk produk)');
  lines.push(en
    ? '[MAIN PROMPT] - ready-to-paste prompt per scene/screen/asset'
    : '[PROMPT UTAMA]— prompt siap-tempel per scene/layar/aset');
  lines.push(en
    ? '[NEGATIVE]    - things to avoid (for generators that support it)'
    : '[NEGATIVE]    — hal yang dihindari (untuk generator yang mendukung)');
  lines.push(en
    ? '[QA CHECK]    - quick checklist before use'
    : '[QA CHECK]    — daftar cek cepat sebelum dipakai');
  lines.push('```');
  lines.push('');
  lines.push(en
    ? `- Target platform: **${platform.name || 'Generic'}** — adapt the syntax (e.g., --ar/--v parameters for Midjourney, natural language for Veo 3, JSON schema for coding agents).`
    : `- Platform tujuan: **${platform.name || 'Generic'}** — sesuaikan sintaksnya (mis. parameter --ar/--v untuk Midjourney, natural language untuk Veo 3, JSON schema untuk agent coding).`);
  lines.push(en
    ? '- If the platform has an input limit (e.g., max prompt length), produce a concise version + a full version.'
    : '- Jika satu platform punya batas input (mis. prompt maksimum), buat versi ringkas + versi lengkap.');
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

// ============================================
// KONTEKS PROJECT — output prompt menyesuaikan jenis project, to the point
// ============================================
const FLAVOR_AUDIT = {
  code: ['Kode berjalan tanpa error saat dieksekusi.', 'Tidak ada fungsi/variabel yang direferensikan tapi tidak ada. Jika asumsi teknis dipakai, tandai `asumsi:`.', 'Semua state ditangani: loading, error, empty.', 'Sebutkan cara menjalankan/test hasil.'],
  media: ['Deskripsi visual bisa dibayangkan orang lain secara identik (subyek, latar, lighting, kamera eksplisit).', 'Sifat produk/karakter yang dikunci tidak berubah — sebutkan eksplisit apa yang dikunci.', 'Durasi/rasio/format sesuai spesifikasi yang diminta.', 'Tidak menambahkan brand/teks/wajah yang tidak diminta.'],
  design: ['Setiap keputusan desain punya alasan yang mengacu ke user goal, bukan selera pribadi.', 'Kontras & aksesibilitas (WCAG AA) terpenuhi.', 'Design token konsisten — tidak ada nilai di luar sistem.', 'Semua state komponen ada: default, hover, active, disabled, error, empty.'],
  data: ['Setiap angka bisa ditelusuri ke sumber/tabel yang disebut; angka tanpa sumber ditandai `asumsi:`.', 'Proyeksi/forecast selalu dengan rentang (±) dan asumsi eksplisit — tidak ada angka tunggal palsu-akurat.', 'Korelasi bukan sebab-akibat; jangan klaim sebab tanpa bukti.', 'Anomali selalu disertai hipotesis penyebab yang bisa diuji.'],
  document: ['Setiap klaim faktual punya sumber; tanpa sumber ditandai `asumsi:` atau dihapus.', 'Tidak ada superlatif tanpa pembanding ("terbaik", "nomor satu").', 'Struktur mengikuti kerangka deliverable — tidak ada bagian kosong/placeholder.', 'Bahasa sesuai audiens; istilah teknis didefinisikan.'],
  coaching: ['Rekomendasi merujuk data/angka performa, bukan opini atau kata motivasi kosong.', 'Target & aksi selalu terukur: angka + tenggat + pemilik.', 'Pertanyaan reflektif dipisahkan dari rekomendasi.', 'Tidak ada janji hasil yang tidak bisa dipertanggungjawabkan.']
};

const FLAVOR_CONTEXT_RULES = {
  code: ['Cukup kode + catatan esensial; penjelasan panjang dilarang.', 'Jangan mengerjakan fitur di luar permintaan (no scope creep).', 'Jika requirement ambigu, pilih asumsi paling masuk akal, tandai `asumsi:`, lalu lanjut — jangan berhenti bertanya.'],
  media: ['Tulis HANYA aset yang diminta; jangan menawarkan variasi tambahan di luar permintaan.', 'Satu aset = satu prompt; jangan mencampur instruksi aset berbeda.', 'Tanpa narrasi pemasaran berlebihan — deskripsi visual netral dan presisi.'],
  design: ['Fokus pada masalah desain yang disebut; jangan mendesain ulang bagian yang tidak dikeluhkan.', 'Sertakan token/spesifikasi, bukan hanya gambaran.', 'Jangan menambah fitur/layar baru di luar permintaan.'],
  data: ['Tampilkan angka dalam tabel; narasi maksimal 2-3 kalimat per temuan.', 'Jangan mengulang angka yang sama dalam bentuk berbeda.', 'Jika data tidak tersedia, tulis `data tidak tersedia` — dilarang mengarang angka.'],
  document: ['Poin-poin, bukan paragraf panjang; satu ide per poin.', 'Jangan mengulang konteks di setiap bagian.', 'Kalimat pasif/berlebihan diganti kalimat aktif singkat.'],
  coaching: ['Tanya maksimal 3 pertanyaan kunci; sisanya rekomendasi terukur.', 'Dilarang memberi kata penyemangat tanpa data di baliknya.', 'Tutup dengan aksi terukur, bukan semangat.']
};

const FLAVOR_BANNED = {
  code: 'pseudocode untuk kode final, kode yang tidak bisa dikompilasi, placeholder TODO pada kode yang diserahkan',
  media: 'istilah kabur ("cantik", "keren", "bagus") tanpa deskripsi konkret, penambahan elemen yang tidak diminta',
  design: 'klaim estetika tanpa alasan fungsional, token liar di luar sistem',
  data: 'angka karangan, proyeksi tanpa rentang, sebab-akibat tanpa bukti, "mengalami tren" tanpa angka',
  document: 'superlatif tanpa pembanding, klaim tanpa sumber, kalimat pengisi ("sebagaimana kita ketahui")',
  coaching: 'kata motivasi kosong, target tanpa angka, saran generik tanpa konteks'
};

const FLAVOR_META_BRIEF = {
  code: 'mulai langsung dari arsitektur/kode; tanpa pembuka pengantar',
  media: 'mulai dari tabel aset/scene; tanpa teori produksi',
  design: 'mulai dari daftar masalah → keputusan; tanpa kuliah teori desain',
  data: 'mulai dari ringkasan angka; tanpa metodologi panjang',
  document: 'mulai dari jawaban/ringkasan; tanpa pembuka basa-basi',
  coaching: 'mulai dari fakta performa; tanpa pembuka motivasi'
};

const FLAVOR_METRICS = {
  code: 'Kode berjalan / test lulus; nol referensi rusak.',
  media: 'Setiap aset punya subjek+aksi+teknis lengkap dan bisa langsung diproduksi.',
  design: 'Tiap layar punya satu aksi utama; semua state komponen terdefinisi.',
  data: 'Setiap insight bisa ditindaklanjuti: aksi + pemilik + tenggat.',
  document: 'Pembaca bisa bertindak tanpa bertanya ulang.',
  coaching: 'Ada 1-3 aksi terukur dengan pemilik & tenggat yang jelas.'
};

const FLAVOR_WIRE = {
  code: 'tulis ulang pernyataan bahasa/framework, jalankan logika di kepala, cek import/export',
  media: 'baca ulang prompt per aset; pastikan tak ada elemen yang saling kontradiksi',
  design: 'cek konsistensi token & alasan tiap keputusan',
  data: 'hitung ulang setiap angka; cocokkan dengan sumber yang disebut',
  document: 'baca ulang klaim faktual; pastikan sumber ada',
  coaching: 'cek setiap rekomendasi punya angka & tenggat'
};

function detectProjectFlavor(project, skills = []) {
  const sid = new Set((skills || []).map(s => s.id));
  if (sid.has('software-architecture') || sid.has('ai-app-saas-building')) return 'code';
  if (sid.has('motivator-coach') || sid.has('sales-coaching')) return 'coaching';
  if (sid.has('data-to-infographic') || sid.has('marketing-data-analyst')) return 'data';

  const byProject = {
    'video-cinematic': 'media', 'video-ads': 'media', 'short-form': 'media', 'ai-video': 'media',
    'image-analysis': 'media', 'image-to-video': 'media', 'image-to-banner': 'media',
    'banana-product-photo': 'media', 'google-flow-video': 'media', 'screenshot-to-visual': 'media',
    'product-visual-suite': 'media', 'suno-song': 'media', 'hailuo-short': 'media',
    'gamma-presentation': 'document',
    'ai-web-builder': 'code', 'software-engineering': 'code',
    'dashboard': 'data', 'sales-monitoring': 'data', 'dan-marketing-analysis': 'data',
    'sales-coaching': 'coaching', 'hr-management': 'coaching', 'talent-mapping': 'coaching',
    'indoor-design': 'design', 'outdoor-design': 'design', 'ai-ux-redesign': 'design', 'ui-ux-design': 'design'
  };
  if (project && byProject[project.id]) return byProject[project.id];

  const byCategory = {
    web_app: 'code', ai_modern: 'code', cloning: 'code', engineering: 'code', '3d_2d': 'code',
    media_gen: 'media', cinematic: 'media', image_processing: 'media',
    design: 'design', data_viz: 'data', business: 'document', education: 'document'
  };
  if (project && byCategory[project.category]) return byCategory[project.category];
  return 'document';
}

const FLAVOR_AUDIT_EN = {
  code: ['Code runs without errors when executed.', 'No function/variable referenced but missing. Mark technical assumptions with `assumption:`.', 'All states handled: loading, error, empty.', 'State how to run/test the result.'],
  media: ['Visual descriptions must be imaginable identically by others (subject, setting, lighting, camera explicit).', 'Locked product/character traits do not change — state explicitly what is locked.', 'Duration/ratio/format match the requested spec.', 'No brands/text/faces added that were not requested.'],
  design: ['Every design decision has a reason tied to the user goal, not personal taste.', 'Contrast & accessibility (WCAG AA) are met.', 'Design tokens consistent — no values outside the system.', 'All component states exist: default, hover, active, disabled, error, empty.'],
  data: ['Every number traces back to a stated source/table; unsourced numbers are marked `assumption:`.', 'Projections/forecasts always carry a range (±) and explicit assumptions — no fake-precise single numbers.', 'Correlation is not causation; no causal claims without evidence.', 'Anomalies always come with a testable hypothesis.'],
  document: ['Every factual claim has a source; without one it is marked `assumption:` or removed.', 'No superlatives without comparison ("best", "number one").', 'Structure follows the deliverable frame — no empty/placeholder sections.', 'Language fits the audience; technical terms are defined.'],
  coaching: ['Recommendations reference performance data, not opinions or empty pep talk.', 'Targets & actions are measurable: number + deadline + owner.', 'Reflective questions are separated from recommendations.', 'No promised outcomes that cannot be accounted for.']
};

const FLAVOR_CONTEXT_RULES_EN = {
  code: ['Code + essential notes only; long explanations are forbidden.', 'Do not build features beyond the request (no scope creep).', 'If requirements are ambiguous, pick the most reasonable assumption, mark `assumption:`, and continue — do not stop to ask.'],
  media: ['Write ONLY the requested assets; do not offer extra variations beyond the request.', 'One asset = one prompt; never mix different asset instructions.', 'No marketing fluff — visual descriptions stay neutral and precise.'],
  design: ['Focus on the design problems stated; do not redesign parts nobody complained about.', 'Include tokens/specs, not just visuals.', 'Do not add new features/screens beyond the request.'],
  data: ['Show numbers in tables; narrative max 2-3 sentences per finding.', 'Do not repeat the same number in different forms.', 'If data is unavailable, write `data unavailable` — fabricating numbers is forbidden.'],
  document: ['Bullets, not long paragraphs; one idea per bullet.', 'Do not repeat context in every section.', 'Replace passive/verbose sentences with short active ones.'],
  coaching: ['Ask at most 3 key questions; the rest is measurable recommendation.', 'Giving pep talk without data behind it is forbidden.', 'Close with measurable actions, not motivation.']
};

const FLAVOR_BANNED_EN = {
  code: 'pseudocode for final code, non-compilable code, TODO placeholders in delivered code',
  media: 'vague terms ("beautiful", "nice", "cool") without concrete description, adding elements nobody asked for',
  design: 'aesthetic claims without functional reasons, wild tokens outside the system',
  data: 'made-up numbers, projections without ranges, causation without evidence, "trending" without numbers',
  document: 'superlatives without comparison, claims without sources, filler sentences ("as we all know")',
  coaching: 'empty motivational words, targets without numbers, generic advice without context'
};

const FLAVOR_META_BRIEF_EN = {
  code: 'start directly with architecture/code; no introductory preface',
  media: 'start with the asset/scene table; no production theory',
  design: 'start with problem list → decisions; no design-theory lecture',
  data: 'start with the numbers summary; no long methodology',
  document: 'start with the answer/summary; no opening pleasantries',
  coaching: 'start with performance facts; no motivational opening'
};

const FLAVOR_METRICS_EN = {
  code: 'Code runs / tests pass; zero broken references.',
  media: 'Every asset has subject+action+technical details and can be produced immediately.',
  design: 'Every screen has one primary action; all component states defined.',
  data: 'Every insight is actionable: action + owner + deadline.',
  document: 'The reader can act without asking again.',
  coaching: '1-3 measurable actions with clear owner & deadline.'
};

const FLAVOR_WIRE_EN = {
  code: 're-state language/framework claims, run the logic mentally, check imports/exports',
  media: 're-read each asset prompt; ensure no contradictory elements',
  design: 'check token consistency & the reason behind each decision',
  data: 'recalculate every number; match against the sources cited',
  document: 're-read factual claims; ensure sources exist',
  coaching: 'check every recommendation has a number & deadline'
};

function buildContextRules(flavor, project, skills = [], agents = [], lang = 'id') {
  const en = lang === 'en';
  const rules = en ? FLAVOR_CONTEXT_RULES_EN : FLAVOR_CONTEXT_RULES;
  const banned = en ? FLAVOR_BANNED_EN : FLAVOR_BANNED;
  const lines = [];
  lines.push(en
    ? '## 🎧 CONTEXT & FOCUS (MANDATORY — no rambling, no hallucination)'
    : '## 🎧 KONTEKS & FOKUS (WAJIB — anti bertele-tele & anti halu)');
  lines.push(en
    ? `**Work type: ${flavor.toUpperCase()}**. Do ONLY what is requested in the details below.`
    : `**Jenis pekerjaan: ${flavor.toUpperCase()}**. Kerjakan HANYA yang diminta pada detail di bawah.`);
  lines.push('');
  lines.push(en ? '**Focus limits:**' : '**Batasan fokus:**');
  rules[flavor].forEach(r => lines.push(`- ${r}`));
  lines.push('');
  lines.push(en
    ? '**Out of scope — ignore unless explicitly requested:**'
    : '**Di luar cakupan — abaikan kecuali diminta eksplisit:**');
  const skList = skills.length ? skills.map(s => s.name).join(', ') : (en ? '(no skills)' : '(tidak ada skill)');
  const agList = agents.length ? agents.map(a => a.name).join(', ') : (en ? '(no agents)' : '(tidak ada agent)');
  lines.push(en
    ? `- Registered skills: ${skList}`
    : `- Skill terdaftar: ${skList}`);
  lines.push(en
    ? `- Registered agents: ${agList}`
    : `- Agent terdaftar: ${agList}`);
  lines.push('');
  lines.push((en ? '**Never output:** ' : '**Dilarang keluar:** ') + banned[flavor] + '.');
  return lines;
}

function buildAuditBlock(flavor, lang = 'id') {
  const en = lang === 'en';
  const audit = en ? FLAVOR_AUDIT_EN : FLAVOR_AUDIT;
  const metrics = en ? FLAVOR_METRICS_EN : FLAVOR_METRICS;
  const wire = en ? FLAVOR_WIRE_EN : FLAVOR_WIRE;
  const brief = en ? FLAVOR_META_BRIEF_EN : FLAVOR_META_BRIEF;
  const lines = [];
  lines.push(en
    ? '## 🔍 AUDIT & ANTI-HALLUCINATION (pass all before answering)'
    : '## 🔍 AUDIT & ANTI-HALUSINASI (lulus semua sebelum menjawab)');
  lines.push(en ? '**Fact verification:**' : '**Verifikasi fakta:**');
  audit[flavor].forEach(c => lines.push(`- [ ] ${c}`));
  lines.push('');
  lines.push(en
    ? `- [ ] **Self-check before final:** ${wire[flavor]}.`
    : `- [ ] **Wire / self-check sebelum final:** ${wire[flavor]}.`);
  lines.push(en
    ? `- [ ] **Definition of done:** ${metrics[flavor]}`
    : `- [ ] **Definisi selesai:** ${metrics[flavor]}`);
  lines.push('');
  lines.push((en ? '**Answer format:** ' : '**Format jawaban:** ') + brief[flavor] + '.');
  return lines;
}

const LANG_DIRECTIVE_EN = [
  '## 🌐 OUTPUT LANGUAGE: ENGLISH',
  '- Write ALL your deliverables and explanations in **English**.',
  '- Some specification blocks below are written in Indonesian — treat them as the spec, execute them fully, but deliver the result in English.',
  '- Keep product names, brand terms, and quoted user text as-is.'
];

const LANG_DIRECTIVE_ID = [
  '## 🌐 BAHASA KELUARAN: INDONESIA',
  '- Tulis SELURUH deliverable dan penjelasan dalam **Bahasa Indonesia**.',
  '- Istilah teknis dalam bahasa asing boleh dipertahankan bila memang baku (mis. framework, nama tools).'
];

function buildPrompt({ project, skills = [], agents = [], platform = {}, detail = '', categories = [], images = [], imageNotes = '', lang = 'id' } = {}) {
  if (!project || !project.name) {
    throw new TypeError('buildPrompt: project dengan .name wajib ada');
  }

  const tpl = PLATFORM_TEMPLATES[platform.id] || PLATFORM_TEMPLATES.generic;
  const flavor = detectProjectFlavor(project, skills);
  const lines = [];
  const sep = '='.repeat(60);

  lines.push(sep);
  lines.push(`🎯 RAUZA PROMPT — ${(cleanName(project.name).toUpperCase() || 'PROJECT')}`);
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

  // --- DIREKTIF BAHASA KELUARAN ---
  lines.push(...(lang === 'en' ? LANG_DIRECTIVE_EN : LANG_DIRECTIVE_ID));
  lines.push('');

  // --- KONTEKS: fokus & larangan spesifik jenis project ---
  lines.push(...buildContextRules(flavor, project, skills, agents, lang));
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
  }  if (detail) {
    const detailLines = buildDetailRequirements(detail, lang);
  if (detailLines) {
      lines.push('## 📝 PROJECT DETAIL');
      lines.push(...detailLines);
      lines.push('');
    }
  }

  if (images && images.length > 0) {
    const imageLines = buildImageSection(images, imageNotes, lang);
    if (imageLines) {
      lines.push(...imageLines);
      lines.push('');
    }
  }

  const visualPipeline = buildVisualPipeline(images, skills, lang);
  if (visualPipeline) {
    lines.push(...visualPipeline);
    lines.push('');
  }

  const rauzaPlaybook = buildRauzaPlaybook(skills, lang);
  if (rauzaPlaybook) {
    lines.push(...rauzaPlaybook);
    lines.push('');
  }

  // --- BLUEPRINT OUTPUT: daftar deliverable khas profesi ---
  if (persona && persona.blueprint) {
    lines.push(`## 📦 ${persona.blueprint.heading}`);
    lines.push('Hasil akhir WAJIB memuat semua bagian berikut (tanpa bagian tambahan di luar daftar ini):');
    lines.push('');
    persona.blueprint.items.forEach(item => lines.push(`- [ ] ${item}`));
    lines.push('');
    lines.push('### ✅ QUALITY CHECKLIST (cek sebelum menyerahkan)');
    (persona.qualityChecks || []).forEach(c => lines.push(`- [ ] ${c}`));
    lines.push('');
  }

  lines.push(...buildPlatformFramework(platform, lang));
  lines.push('');

  lines.push(lang === 'en' ? '## 🚀 EXECUTION INSTRUCTIONS' : '## 🚀 EXECUTION INSTRUCTIONS');
  tpl.execution.forEach(l => lines.push(l));
  lines.push('');

  lines.push(lang === 'en' ? '## 📤 OUTPUT FORMAT' : '## 📤 OUTPUT FORMAT');
  tpl.output.forEach(l => lines.push(l));
  lines.push('');

  lines.push('## ⚡ TOKEN OPTIMIZATION');
  TOKEN_LINES.forEach(l => lines.push(l));
  lines.push('');

  lines.push(...buildAuditBlock(flavor, lang));
  lines.push('');

  lines.push(sep);
  lines.push('RAUZA — One Prompt, Infinite Possibilities');
  lines.push(sep);

  return lines.join('\n');
}

const VibeCore = { escapeHtml, encodeConfig, decodeConfig, buildPrompt, buildImageSection, buildRauzaPlaybook, resolvePersona, resolveProjectUi, buildDetailRequirements, buildVisualPipeline, buildPlatformFramework, detectProjectFlavor, buildContextRules, buildAuditBlock, PROJECT_ACCENTS, PERSONA_TEMPLATES, PLATFORM_TEMPLATES };

// UMD-style: Node (tests) & browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = VibeCore;
} else if (typeof window !== 'undefined') {
  window.VibeCore = VibeCore;
}
