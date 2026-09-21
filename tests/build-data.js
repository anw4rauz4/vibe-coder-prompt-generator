// ============================================
// BUILD DATA — tanam JSON ke data.js
// agar app jalan juga dibuka via file://
// Jalankan: npm run build:data
// ============================================

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const NAMES = ['projects', 'categories', 'skills', 'agents', 'adapters'];

const out = {};
NAMES.forEach(n => {
  const file = path.join(ROOT, 'data', `${n}.json`);
  out[n] = JSON.parse(fs.readFileSync(file, 'utf8'));
});

const banner = `// ============================================
// AUTO-GENERATED dari data/*.json
// Jangan edit manual — jalankan: npm run build:data
// Ada agar app tetap jalan dibuka via file://
// ============================================
window.EMBEDDED_DATA = ${JSON.stringify(out, null, 2)};
`;

fs.writeFileSync(path.join(ROOT, 'data.js'), banner, 'utf8');
const total = NAMES.reduce((s, n) => s + out[n].length, 0);
console.log(`✅ data.js dibuat (${total} entri dari ${NAMES.length} file)`);
