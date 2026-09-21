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

const VibeCore = { escapeHtml, encodeConfig, decodeConfig, buildPrompt, buildImageSection, buildDanPlaybook, PLATFORM_TEMPLATES };

// UMD-style: Node (tests) & browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = VibeCore;
} else if (typeof window !== 'undefined') {
  window.VibeCore = VibeCore;
}
