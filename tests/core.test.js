// ============================================
// UNIT TESTS — VibeCoder Core (no framework)
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

  assert.ok(prompt.includes('VIBE CODER PROMPT'), 'missing title');
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
