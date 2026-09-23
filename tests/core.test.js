// ============================================
// UNIT TESTS — RAUZA Core (no framework)
// Run: node tests/core.test.js
// ============================================

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const { escapeHtml, encodeConfig, decodeConfig, buildPrompt, PLATFORM_TEMPLATES } = require('../core.js');

const ROOT = path.join(__dirname, '..');
let passed = 0, failed = 0;
const failures = [];

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  ✅ ${name}`);
  } catch (e) {
    failed++;
    failures.push({ name, error: e.message });
    console.log(`  ❌ ${name}\n     ${e.message}`);
  }
}

// ---------- DATA FILES ----------
console.log('\n📦 Data files');
const dataFiles = ['projects', 'categories', 'skills', 'agents', 'adapters'];
const data = {};

dataFiles.forEach(name => {
  test(`${name}.json valid`, () => {
    data[name] = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', `${name}.json`), 'utf8'));
    assert.ok(Array.isArray(data[name]), 'must be array');
    assert.ok(data[name].length > 0, 'must not be empty');
  });
});

test('referensi lintas-file valid', () => {
  const catIds = new Set(data.categories.map(c => c.id));
  const skillIds = new Set(data.skills.map(s => s.id));
  const agentIds = new Set(data.agents.map(a => a.id));

  data.projects.forEach(p => {
    assert.ok(catIds.has(p.category), `project ${p.id}: kategori ${p.category} tidak ada`);
    (p.skills || []).forEach(s => assert.ok(skillIds.has(s), `project ${p.id}: skill ${s} tidak ada`));
    (p.agents || []).forEach(a => assert.ok(agentIds.has(a), `project ${p.id}: agent ${a} tidak ada`));
  });
  data.skills.forEach(s => assert.ok(catIds.has(s.category), `skill ${s.id}: kategori tidak ada`));
  data.agents.forEach(a => assert.ok(catIds.has(a.category), `agent ${a.id}: kategori tidak ada`));
});

test('setiap kategori punya minimal 1 skill & agent', () => {
  const cats = new Set(data.categories.map(c => c.id));
  const skillCats = new Set(data.skills.map(s => s.category));
  const agentCats = new Set(data.agents.map(a => a.category));
  cats.forEach(c => {
    assert.ok(skillCats.has(c), `kategori ${c} tidak punya skill`);
    assert.ok(agentCats.has(c), `kategori ${c} tidak punya agent`);
  });
});

test('ID unik di setiap file', () => {
  dataFiles.forEach(name => {
    const ids = data[name].map(x => x.id);
    assert.strictEqual(new Set(ids).size, ids.length, `${name}: duplikat ID`);
  });
});

// ---------- ESCAPE HTML ----------
console.log('\n🔒 escapeHtml');
test('escape karakter berbahaya', () => {
  assert.strictEqual(escapeHtml('<script>alert(1)</script>'), '&lt;script&gt;alert(1)&lt;/script&gt;');
  assert.strictEqual(escapeHtml('a"b\'c&d'), 'a&quot;b&#39;c&amp;d');
});

test('null/undefined jadi string kosong', () => {
  assert.strictEqual(escapeHtml(null), '');
  assert.strictEqual(escapeHtml(undefined), '');
});

test('emoji & unicode aman', () => {
  assert.strictEqual(escapeHtml('🌐 Web App'), '🌐 Web App');
});

// ---------- ENCODE / DECODE CONFIG ----------
console.log('\n🔗 encodeConfig / decodeConfig');
test('roundtrip config dengan unicode', () => {
  const config = { project: 'web-app', skills: ['a', 'b'], detail: 'Halo é✓ 世界' };
  assert.deepStrictEqual(decodeConfig(encodeConfig(config)), config);
});

test('decode string invalid → null', () => {
  assert.strictEqual(decodeConfig('bukan-base64!!!'), null);
  assert.strictEqual(decodeConfig(''), null);
});

test('encode input invalid → string kosong', () => {
  assert.strictEqual(encodeConfig(undefined), '');
});

// ---------- BUILD PROMPT ----------
console.log('\n📝 buildPrompt');
const baseProject = data.projects.find(p => p.id === 'web-app');

test('generate prompt lengkap untuk project valid', () => {
  const prompt = buildPrompt({
    project: baseProject,
    skills: data.skills.filter(s => (baseProject.skills || []).includes(s.id)),
    agents: data.agents.filter(a => (baseProject.agents || []).includes(a.id)),
    platform: data.adapters.find(a => a.id === 'claude'),
    detail: 'E-commerce dengan Next.js',
    categories: data.categories
  });

  assert.ok(prompt.includes('RAUZA PROMPT'), 'missing title');
  assert.ok(prompt.includes('PROJECT OVERVIEW'), 'missing overview');
  assert.ok(prompt.includes('Web App'), 'missing project name');
  assert.ok(prompt.includes('E-commerce dengan Next.js'), 'missing detail');
  assert.ok(prompt.includes('SKILLS'), 'missing skills section');
  assert.ok(prompt.includes('SUB-AGENTS'), 'missing agents section');
  assert.ok(prompt.includes('EXECUTION INSTRUCTIONS'), 'missing execution');
  assert.ok(prompt.includes('OUTPUT FORMAT'), 'missing output format');
  assert.ok(prompt.includes('TOKEN OPTIMIZATION'), 'missing token optimization');
});

test('template per-platform berbeda (claude vs generic)', () => {
  const args = { project: baseProject, skills: [], agents: [], detail: '', categories: [] };
  const claude = buildPrompt({ ...args, platform: { id: 'claude', name: 'Claude' } });
  const generic = buildPrompt({ ...args, platform: { id: 'unknown-x', name: 'X' } });

  assert.ok(claude.includes('Artifacts'), 'claude template harus sebut Artifacts');
  assert.ok(!generic.includes('Artifacts'), 'generic tidak boleh sebut Artifacts');
  assert.ok(PLATFORM_TEMPLATES.claude.execution.length >= 5);
  assert.ok(PLATFORM_TEMPLATES.generic.execution.length >= 5);
});

test('setiap platform di adapters.json punya template', () => {
  data.adapters.forEach(a => {
    assert.ok(PLATFORM_TEMPLATES[a.id], `template untuk ${a.id} tidak ada`);
  });
});

test('lempar error jika project kosong', () => {
  assert.throws(() => buildPrompt({}), TypeError);
  assert.throws(() => buildPrompt({ project: {} }), TypeError);
});

test('prompt dengan skills/agents kosong tetap valid', () => {
  const prompt = buildPrompt({
    project: baseProject, skills: [], agents: [],
    platform: {}, detail: '', categories: []
  });
  assert.ok(!prompt.includes('## 🛠️ SKILLS'));
  assert.ok(!prompt.includes('## 🤖 SUB-AGENTS'));
  assert.ok(prompt.includes('**Platform:** Generic'));
});

// ---------- IMAGE SUPPORT ----------
console.log('\n🖼️ Image support');
const baseImage = {
  id: 'img-1', name: 'mockup.png', type: 'image/png',
  size: 2048, width: 1920, height: 1080, note: 'Layout yang diinginkan',
  dataUrl: 'data:image/png;base64,AAAA'
};

test('tanpa gambar: tidak ada section REFERENCE IMAGES', () => {
  const prompt = buildPrompt({ project: baseProject, skills: [], agents: [], platform: {}, detail: '', categories: [] });
  assert.ok(!prompt.includes('REFERENCE IMAGES'));
});

test('dengan gambar: section REFERENCE IMAGES muncul + nomor urut + catatan', () => {
  const prompt = buildPrompt({
    project: baseProject, skills: [], agents: [], platform: {},
    detail: '', categories: [],
    images: [baseImage, { ...baseImage, id: 'img-2', name: 'warna.png', note: '' }],
    imageNotes: 'Gambar 1 wajib, Gambar 2 hanya referensi warna'
  });
  assert.ok(prompt.includes('## 🖼️ REFERENCE IMAGES (2)'));
  assert.ok(prompt.includes('1. **mockup.png**'));
  assert.ok(prompt.includes('2. **warna.png**'));
  assert.ok(prompt.includes('(1920×1080'));
  assert.ok(prompt.includes('Layout yang diinginkan'));
  assert.ok(prompt.includes('Gambar 1 wajib, Gambar 2 hanya referensi warna'));
  assert.ok(prompt.includes('Instruksi analisis gambar'));
});

test('prompt TIDAK pernah memuat data base64 gambar', () => {
  const prompt = buildPrompt({
    project: baseProject, skills: [], agents: [], platform: {},
    detail: '', categories: [], images: [baseImage]
  });
  assert.ok(!prompt.includes('data:image'), 'base64 tidak boleh bocor ke prompt text');
});

test('buildImageSection: null jika kosong, terformat jika ada', () => {
  const { buildImageSection } = require('../core.js');
  assert.strictEqual(buildImageSection([], ''), null);
  assert.strictEqual(buildImageSection(null, 'abc'), null);
  const lines = buildImageSection([baseImage], '');
  assert.ok(Array.isArray(lines) && lines.length > 3);
});

test('app.js punya integrasi gambar (state, persistence, dropzone)', () => {
  const appSrc = fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8');
  assert.ok(appSrc.includes('addImageFiles'));
  assert.ok(appSrc.includes("'vibe-coder-images-v1'"));
  assert.ok(appSrc.includes('image-dropzone'));
  assert.ok(appSrc.includes('getLightConfig'), 'riwayat/share harus pakai config ringan');
});

test('index.html punya UI upload gambar', () => {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  for (const id of ['image-input', 'image-dropzone', 'image-notes', 'image-preview-list', 'image-count']) {
    assert.ok(html.includes(`id="${id}"`), `element ${id} tidak ada`);
  }
  assert.ok(html.includes('multiple'), 'input harus multiple');
});

// ---------- RAUZA PLAYBOOK INTEGRATION ----------
console.log('\n🧠 RAUZA Playbook');
const danSkill = { id: 'marketing-data-analyst', name: 'RAUZA Marketing Data Analyst', description: 'KPI, funnel' };
const danAgent = { id: 'dan-data-analyst', name: 'RAUZA Data Analyst', description: 'KPI' };

test('skill RAUZA → prompt memuat RAUZA PLAYBOOK + prinsip + deliverable', () => {
  const prompt = buildPrompt({
    project: baseProject, skills: [danSkill], agents: [danAgent],
    platform: {}, detail: '', categories: []
  });
  assert.ok(prompt.includes('## 🧠 RAUZA PLAYBOOK'));
  assert.ok(prompt.includes('Data dulu, opini belakangan'));
  assert.ok(prompt.includes('**RAUZA Marketing Data Analyst** → JSON hasil analisa'));
  assert.ok(prompt.includes('skills/dan/'));
});

test('tanpa skill RAUZA → tidak ada blok playbook', () => {
  const prompt = buildPrompt({ project: baseProject, skills: [], agents: [], platform: {}, detail: '', categories: [] });
  assert.ok(!prompt.includes('RAUZA PLAYBOOK'));
});

test('paket skills/dan/ lengkap & konsisten', () => {
  const danRoot = path.join(ROOT, 'skills', 'dan');
  assert.ok(fs.existsSync(path.join(danRoot, 'SKILL.md')), 'SKILL.md tidak ada');
  assert.ok(fs.existsSync(path.join(danRoot, 'AGENT.md')), 'AGENT.md tidak ada');
  assert.ok(fs.existsSync(path.join(danRoot, 'SYSTEM_PROMPT.txt')), 'SYSTEM_PROMPT.txt tidak ada');
  assert.ok(fs.existsSync(path.join(danRoot, 'references', 'metric-library.md')), 'references hilang');
  assert.ok(fs.existsSync(path.join(danRoot, 'scripts', 'dan_analytics.py')), 'engine hilang');
  assert.ok(fs.existsSync(path.join(danRoot, 'templates', 'campaign-plan.md')), 'templates hilang');
  assert.ok(fs.existsSync(path.join(danRoot, 'examples-data', 'sample_campaign.csv')), 'contoh data hilang');
});

test('skill/agent RAUZA di data JSON match paket (9 inti + 12 AI Skills 2027)', () => {
  const danSkillsInData = data.skills.filter(s => s.name.startsWith('RAUZA '));
  const danAgentsInData = data.agents.filter(a => a.name.startsWith('RAUZA '));
  assert.ok(danSkillsInData.length >= 9, 'minimal 9 skill RAUZA inti');
  assert.ok(danAgentsInData.length >= 9, 'minimal 9 agent RAUZA inti');
  assert.strictEqual(danSkillsInData.length, 10, '10 skill RAUZA (9 inti + Visual Director)');
  assert.strictEqual(danAgentsInData.length, 21, '21 agent RAUZA (9 inti + 12 AI Skills 2027)');
  const engineSkillIds = Object.keys(require('../core.js').buildDanPlaybook ? {} : {});
  danSkillsInData.forEach(s => {
    assert.ok(/^(marketing-data-analyst|marketing-strategist|data-to-infographic|image-video-creator|design-engineer-2d-3d|motivator-coach|project-monitoring-controlling|software-architecture|architectural-design)$|^(marketing-data-analyst|marketing-strategist|data-to-infographic|image-video-creator|design-engineer-2d-3d|motivator-coach|project-monitoring-controlling|software-architecture|architectural-design|persona-visual-director)$/.test(s.id), `id tak dikenal: ${s.id}`);
  });
});

// ---------- PERSONA PROFESI ----------
console.log('\n🎭 Persona Profesi');
const { resolvePersona } = require('../core.js');
const cats = [{ id: 'business', name: 'Business' }, { id: 'engineering', name: 'Engineering' }];

function buildFor(project, skills) {
  return buildPrompt({ project, skills, agents: [], platform: {}, detail: '', categories: cats });
}

test('project coaching → persona COACH (GROW, sesi, rencana aksi)', () => {
  const prompt = buildFor(
    { name: '🎯 Sales Coaching', desc: 'Coach tim sales', category: 'business', persona: 'coach' },
    [{ id: 'sales-coaching', name: 'Sales Coaching', description: 'GROW' }]
  );
  assert.ok(prompt.includes('PERSONA: PERFORMANCE COACH'));
  assert.ok(prompt.includes('GROW'));
  assert.ok(prompt.includes('BLUEPRINT SESI COACHING'));
  assert.ok(prompt.includes('pertanyaan reflektif'));
  assert.ok(prompt.includes('Quality Checklist'.toUpperCase().slice(0, 8)));
  const p = resolvePersona({ category: 'business', persona: 'coach' }, cats, []);
  assert.strictEqual(p.id, 'coach');
});

test('project konstruksi → persona ENGINEER (RAB, denah 2D, material takeoff)', () => {
  const prompt = buildFor(
    { name: '📐 CAD Drawing', desc: 'Gambar teknik', category: 'engineering' },
    [{ id: 'cad-engineering', name: 'CAD', description: 'AutoCAD' }]
  );
  assert.ok(prompt.includes('PERSONA: ENGINEER KONSTRUKSI'));
  assert.ok(prompt.includes('RAB'));
  assert.ok(prompt.includes('Denah 2D'));
  assert.ok(prompt.includes('Material (Takeoff)'));
  assert.ok(prompt.includes('Jadwal konstruksi'));
  assert.ok(prompt.includes('KDB/KLB'));
});

test('skill architectural-design mengangkat persona ARSITEK meski kategori design', () => {
  const prompt = buildFor(
    { name: '🏠 Indoor Design', desc: 'Interior', category: 'design' },
    [{ id: 'architectural-design', name: 'RAUZA Architectural Design', description: 'Denah' }]
  );
  assert.ok(prompt.includes('PERSONA: ARSITEK'));
  assert.ok(prompt.includes('BLUEPRINT DESAIN ARSITEKTUR'));
});

test('kategori web_app → default SOFTWARE ENGINEER; kategori kosong → tanpa persona', () => {
  const web = buildFor({ name: '🌐 Web App', desc: 'Web', category: 'web_app' }, []);
  assert.ok(web.includes('PERSONA: SOFTWARE ENGINEER'));
  const noCat = buildFor({ name: 'X', desc: 'x' }, []);
  assert.ok(!noCat.includes('## 🎯 PERSONA'));
});

test('10 persona terdaftar & semua project preset punya persona valid', () => {
  const { PERSONA_TEMPLATES } = require('../core.js');
  assert.strictEqual(Object.keys(PERSONA_TEMPLATES).length, 10);
  data.projects.forEach(p => {
    if (p.persona) {
      assert.ok(PERSONA_TEMPLATES[p.persona], `project ${p.id}: persona ${p.persona} tidak dikenal`);
    }
  });
});

// ---------- FITUR BARU: PLATFORM GENERATOR, PIPELINE, ADAPTIVE UI ----------
console.log('\n🚀 Platform Generator & Visual Pipeline');
test('setiap platform generator punya template & prompt framework muncul', () => {
  data.adapters.forEach(a => {
    assert.ok(PLATFORM_TEMPLATES[a.id], `template untuk ${a.id} tidak ada`);
  });
  const prompt = buildPrompt({
    project: baseProject,
    skills: [],
    agents: [],
    platform: data.adapters.find(a => a.id === 'banana'),
    detail: 'foto produk serum',
    categories: data.categories
  });
  assert.ok(prompt.includes('PROMPT FRAMEWORK'), 'framework block hilang');
  assert.ok(prompt.includes('[PROMPT UTAMA]'), 'struktur framework hilang');
});

test('struktur detail 9 elemen muncul saat detail diisi', () => {
  const prompt = buildPrompt({
    project: baseProject, skills: [], agents: [], platform: {},
    detail: 'E-commerce UMKM', categories: data.categories
  });
  assert.ok(prompt.includes('STRUKTUR DETAIL'), 'blok struktur detail hilang');
  assert.ok(prompt.includes('[Kriteria Sukses]'), 'elemen kriteria sukses hilang');
  assert.ok(prompt.includes('asumsi:'), 'petunjuk asumsi hilang');
});

test('visual pipeline aktif untuk project screenshot-to-visual', () => {
  const proj = data.projects.find(p => p.id === 'screenshot-to-visual');
  const prompt = buildPrompt({
    project: proj,
    skills: data.skills.filter(s => (proj.skills || []).includes(s.id)),
    agents: [], platform: {}, detail: 'demo', categories: data.categories
  });
  assert.ok(prompt.includes('VISUAL PIPELINE'), 'pipeline hilang');
  assert.ok(prompt.includes('Pipeline A'), 'pipeline video hilang');
  assert.ok(prompt.includes('Pipeline B'), 'pipeline 3D hilang');
  assert.ok(prompt.includes('Pipeline C'), 'pipeline wireframe hilang');
});

test('visual pipeline aktif otomatis saat ada gambar terlampir', () => {
  const prompt = buildPrompt({
    project: baseProject, skills: [], agents: [], platform: {},
    detail: '', categories: data.categories,
    images: [{ name: 'shot.png', dataUrl: 'data:image/png;base64,xxx' }]
  });
  assert.ok(prompt.includes('VISUAL PIPELINE'));
});

test('resolveProjectUi: aksen, placeholder & workflow per project', () => {
  const { resolveProjectUi } = require('../core.js');
  const banana = resolveProjectUi(data.projects.find(p => p.id === 'banana-product-photo'));
  assert.ok(banana.accent, 'aksen banana hilang');
  assert.ok(banana.detailPlaceholder.includes('Serum'), 'placeholder banana salah');
  assert.ok(Array.isArray(banana.workflow) && banana.workflow.length >= 3, 'workflow banana hilang');
  const plain = resolveProjectUi({ id: 'web-app', name: '🌐 Web App', desc: 'web' });
  assert.strictEqual(plain.accent, null, 'project tanpa aksen harus null');
});

test('app.js punya adaptive UI (hero, aksen, placeholder)', () => {
  const appSrc = fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8');
  assert.ok(appSrc.includes('applyProjectUi'), 'applyProjectUi hilang');
  assert.ok(appSrc.includes('resolveProjectUi'), 'resolveProjectUi hilang');
  assert.ok(appSrc.includes('--p-accent'), 'set CSS var aksen hilang');
});

test('index.html punya hero card adaptif', () => {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  assert.ok(html.includes('project-hero'), 'hero card hilang');
});

// ---------- OUTPUT KONTEKSTUAL & ANTI-HALU ----------
console.log('\n🎯 Output Kontekstual & Anti-Halu');
test('fokus & audit menyesuaikan jenis project (media vs document)', () => {
  const vid = data.projects.find(p => p.id === 'google-flow-video');
  const mkt = data.projects.find(p => p.id === 'sales-strategy');
  const pv = buildFor(vid, data.skills.filter(s => (vid.skills || []).includes(s.id)));
  const pm = buildFor(mkt, data.skills.filter(s => (mkt.skills || []).includes(s.id)));
  assert.ok(pv.includes('Jenis pekerjaan: MEDIA'), 'flavor media hilang');
  assert.ok(pm.includes('Jenis pekerjaan: DOCUMENT'), 'flavor document hilang');
  assert.ok(pv.includes('bisa dibayangkan orang lain secara identik'), 'audit visual hilang');
  assert.ok(pm.includes('superlatif tanpa pembanding'), 'audit anti-halu dokumen hilang');
  assert.ok(!pm.includes('VISUAL PIPELINE'), 'pipeline video bocor ke prompt marketing');
  assert.ok(!pv.includes('Tanya maksimal 3 pertanyaan'), 'aturan coaching bocor ke prompt video');
});

test('blok audit & anti-halusinasi selalu ada + kerangka fokus', () => {
  const p = buildFor(baseProject, []);
  assert.ok(p.includes('AUDIT & ANTI-HALUSINASI'), 'audit hilang');
  assert.ok(p.includes('Kerjakan HANYA yang diminta'), 'fokus hilang');
  assert.ok(p.includes('Dilarang keluar'), 'larangan hilang');
  assert.ok(p.includes('Definisi selesai'), 'metrik selesai hilang');
});

test('branding RAUZA menggantikan yang lama', () => {
  const p = buildFor(baseProject, []);
  assert.ok(p.includes('RAUZA PROMPT'));
  assert.ok(!p.includes('VIBE CODER'));
});

// ---------- BAHASA OUTPUT (ID/EN) ----------
console.log('\n🌐 Bahasa Output');
test('lang=id → direktif Indonesia; lang=en → direktif English', () => {
  const pid = buildFor(baseProject, []);
  const pen = buildPrompt({ project: baseProject, skills: [], agents: [], platform: {}, detail: '', categories: data.categories, lang: 'en' });
  assert.ok(pid.includes('BAHASA KELUARAN: INDONESIA'));
  assert.ok(pen.includes('OUTPUT LANGUAGE: ENGLISH'));
});

test('lang=en menerjemahkan audit, fokus, framework & pipeline', () => {
  const proj = data.projects.find(p => p.id === 'screenshot-to-visual');
  const pen = buildPrompt({
    project: proj, skills: data.skills.filter(s => (proj.skills || []).includes(s.id)),
    agents: [], platform: {}, detail: 'x', categories: data.categories,
    images: [{ name: 'a.png', dataUrl: 'data:image/png;base64,x' }], lang: 'en'
  });
  assert.ok(pen.includes('AUDIT & ANTI-HALLUCINATION'), 'audit EN hilang');
  assert.ok(pen.includes('CONTEXT & FOCUS'), 'fokus EN hilang');
  assert.ok(pen.includes('[MAIN PROMPT]'), 'framework EN hilang');
  assert.ok(pen.includes('FROM SCREENSHOT TO READY-TO-USE OUTPUT'), 'pipeline EN hilang');
  assert.ok(pen.includes('Work type: MEDIA'), 'flavor EN hilang');
});

test('lang=default id saat tidak dikirim; app.js kirim lang ke core', () => {
  const p = buildFor(baseProject, []);
  assert.ok(p.includes('BAHASA KELUARAN: INDONESIA'));
  const appSrc = fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8');
  assert.ok(appSrc.includes("lang: selectedLang"), 'buildPrompt tidak menerima lang');
  assert.ok(appSrc.includes('getPlatformLang'), 'memori bahasa per platform hilang');
});

test('index.html punya dropdown bahasa', () => {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  assert.ok(html.includes('lang-select'), 'dropdown bahasa hilang');
});

test('10 persona EN lengkap & dipakai saat lang=en', () => {
  const { PERSONA_TEMPLATES_EN, PERSONA_TEMPLATES } = require('../core.js');
  assert.strictEqual(Object.keys(PERSONA_TEMPLATES_EN).length, 10, 'persona EN tidak 10');
  assert.deepStrictEqual(Object.keys(PERSONA_TEMPLATES_EN).sort(), Object.keys(PERSONA_TEMPLATES).sort(), 'kunci persona EN != ID');
  Object.values(PERSONA_TEMPLATES_EN).forEach(t => {
    assert.ok(t.label && t.role && t.mission && t.tone, 'field persona EN kurang');
    assert.ok(t.workflow.length >= 5, 'workflow persona EN < 5');
    assert.ok(t.blueprint.items.length >= 5, 'blueprint persona EN < 5');
    assert.ok(t.qualityChecks.length >= 4, 'qualityChecks persona EN < 4');
  });
  const coach = data.projects.find(p => p.id === 'sales-coaching');
  const pen = buildPrompt({ project: coach, skills: [], agents: [], platform: {}, detail: '', categories: data.categories, lang: 'en' });
  assert.ok(pen.includes('COACHING SESSION BLUEPRINT'), 'blueprint EN hilang');
  assert.ok(pen.includes('find their own answers'), 'mission EN hilang');
  assert.ok(!pen.includes('BLUEPRINT SESI COACHING'), 'blueprint ID bocor ke EN');
});

// ---------- APP.JS INTEGRITY ----------
console.log('\n🧩 app.js integrity');
test('app.js syntax valid', () => {
  const { execSync } = require('child_process');
  execSync('node --check app.js', { cwd: ROOT, stdio: 'pipe' });
});

test('app.js tidak punya buildPrompt internal lagi (pakai core)', () => {
  const appSrc = fs.readFileSync(path.join(ROOT, 'app.js'), 'utf8');
  assert.ok(appSrc.includes('VibeCore.buildPrompt'), 'harus panggil VibeCore.buildPrompt');
  assert.ok(!appSrc.includes('buildPrompt({ project, skills, agents, platform, detail })'),
    'masih ada buildPrompt internal');
});

test('index.html load core.js sebelum app.js', () => {
  const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
  const coreIdx = html.indexOf('src="core.js"');
  const appIdx = html.indexOf('src="app.js"');
  assert.ok(coreIdx !== -1, 'core.js tidak di-load');
  assert.ok(appIdx !== -1, 'app.js tidak di-load');
  assert.ok(coreIdx < appIdx, 'core.js harus sebelum app.js');
});

// ---------- SUMMARY ----------
console.log(`\n${'='.repeat(50)}`);
console.log(`Hasil: ${passed} passed, ${failed} failed`);
console.log('='.repeat(50));

if (failed > 0) {
  process.exit(1);
}
