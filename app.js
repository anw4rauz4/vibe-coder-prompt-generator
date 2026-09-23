// ============================================
// VIBE CODER PROMPT GENERATOR
// ============================================

const STORAGE_KEY = 'vibe-coder-state-v1';
const HISTORY_KEY = 'vibe-coder-history-v1';
const CUSTOM_KEY = 'vibe-coder-custom-v1';
const HISTORY_LIMIT = 20;

const MAX_IMAGES = 10;
const DEFAULT_DETAIL_PLACEHOLDER = 'Contoh: Buatkan aplikasi e-commerce dengan React dan Tailwind...';
const ACCENT_VARS = ['--p-accent', '--p-accent-2', '--p-accent-soft', '--p-accent-soft-2'];

// escapeHtml tersedia global dari core.js (jangan dideklarasikan ulang di sini)

class VibeCoderApp {
  constructor() {
    this.state = {
      projects: [],
      categories: [],
      skills: [],
      agents: [],
      adapters: [],
      selectedProject: null,
      selectedCategory: '',
      selectedSkills: [],
      selectedAgents: [],
      selectedPlatform: 'chatgpt',
      selectedLang: 'id',
      platformLangs: {},
      projectDetail: '',
      images: [],
      imageNotes: '',
      skillSearch: '',
      agentSearch: '',
      autoSelect: true,
      theme: 'dark',
      customSkills: [],
      customAgents: [],
      history: []
    };

    this.init();
  }

  async init() {
    try {
      // Restore theme tersimpan sebelum apply
      try {
        const savedTheme = localStorage.getItem('vibe-coder-theme');
        if (savedTheme === 'light' || savedTheme === 'dark') this.state.theme = savedTheme;
      } catch (e) { /* storage unavailable (private mode) */ }
      this.applyTheme();
      this.loadCustomData();
      this.loadHistory();
      this.loadImages();
      this.loadPlatformLangs();
      await this.loadData();
      this.restoreState();
      this.render();
      this.restoreLangControl();
    } catch (err) {
      // Jangan biarkan app mati diam-diam: tampilkan pesan agar user tahu
      try { this.showErrorBanner(err); } catch (e2) { console.error(err); }
    }
    // attachEvents WAJIB tetap jalan meski langkah lain gagal —
    // kalau tidak, seluruh tombol & list jadi mati (tidak bisa diklik)
    try {
      this.attachEvents();
    } catch (err) {
      console.error('attachEvents gagal:', err);
      try { this.showErrorBanner(err); } catch (e2) {}
    }
  }

  showErrorBanner(err) {
    let banner = document.getElementById('boot-error-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'boot-error-banner';
      banner.setAttribute('role', 'alert');
      banner.style.cssText = 'margin:1rem;padding:0.9rem 1.1rem;border-radius:10px;background:#7f1d1d;color:#fecaca;font-size:0.85rem;line-height:1.5;z-index:2000;';
      const anchor = document.querySelector('.content') || document.querySelector('.main') || document.body;
      anchor.insertBefore(banner, anchor.firstChild);
    }
    banner.innerHTML = '<strong>⚠️ Ada bagian app yang gagal dimuat.</strong><br>Halaman tetap bisa dipakai sebagian, tapi disarankan muat ulang (pull-to-refresh).<br><code style="opacity:.8">' +
      String(err && err.message || err).replace(/[<>&]/g, '') + '</code>';
  }

  restoreLangControl() {
    const select = document.getElementById('lang-select');
    if (select) select.value = this.state.selectedLang === 'en' ? 'en' : 'id';
    this.updateLangMemoryNote();
  }

  // ============================================
  // DATA LOADING
  // ============================================

  async loadData() {
    // 1) Coba fetch JSON (butuh HTTP server)
    try {
      const results = await Promise.all([
        fetch('data/projects.json').then(this.toJson),
        fetch('data/categories.json').then(this.toJson),
        fetch('data/skills.json').then(this.toJson),
        fetch('data/agents.json').then(this.toJson),
        fetch('data/adapters.json').then(this.toJson)
      ]);
      this.setLoadedData(results);
      return;
    } catch (e) { /* fallback di bawah */ }

    // 2) Fallback: data tertanam di data.js (bisa jalan via file://)
    if (window.EMBEDDED_DATA && Array.isArray(window.EMBEDDED_DATA.projects)) {
      this.setLoadedData([
        window.EMBEDDED_DATA.projects,
        window.EMBEDDED_DATA.categories,
        window.EMBEDDED_DATA.skills,
        window.EMBEDDED_DATA.agents,
        window.EMBEDDED_DATA.adapters
      ]);
      this.toast('📂 Data dimuat dari data.js (built-in)', 'info');
      return;
    }

    // 3) Terakhir: data inline minimal
    console.error('Data loading gagal total, pakai fallback minimal');
    this.toast('⚠️ Gagal memuat data — pakai data minimal', 'warning');
    this.loadFallbackData();
  }

  toJson(r) {
    if (!r.ok) throw new Error(`HTTP ${r.status} untuk ${r.url}`);
    return r.json();
  }

  setLoadedData([projects, categories, skills, agents, adapters]) {
    this.state.projects = projects;
    this.state.categories = categories;
    this.state.skills = skills;
    this.state.agents = agents;
    this.state.adapters = adapters;
    this.mergeCustom();
  }

  loadFallbackData() {
    this.state.projects = [
      { id: 'web-app', name: '🌐 Web App', desc: 'Buat aplikasi web', category: 'web_app' },
      { id: 'mobile-app', name: '📱 Mobile App', desc: 'Buat aplikasi mobile', category: 'web_app' },
      { id: 'dashboard', name: '📊 Dashboard', desc: 'Buat dashboard analytics', category: 'data_viz' },
      { id: 'video-cinematic', name: '🎬 Video Sinematik', desc: 'Buat video sinematik', category: 'cinematic' },
      { id: 'ai-saas', name: '🤖 AI SaaS', desc: 'Buat AI SaaS', category: 'ai_modern' },
      { id: 'clone-app', name: '🧬 Clone App', desc: 'Clone dari link/screenshot', category: 'cloning' },
      { id: 'presentation', name: '📽️ Presentasi', desc: 'Buat presentasi', category: 'education' },
      { id: 'teaching-material', name: '📚 Bahan Ajar', desc: 'Buat bahan ajar', category: 'education' },
      { id: 'sales-strategy', name: '💼 Sales Strategy', desc: 'Buat strategi sales', category: 'business' },
      { id: 'hr-management', name: '👥 HR Management', desc: 'Kelola SDM', category: 'business' },
      { id: 'image-analysis', name: '🔍 Image Analysis', desc: 'Analisis gambar', category: 'image_processing' }
    ];

    this.state.categories = [
      { id: 'web_app', name: '🌐 Web & App' },
      { id: 'data_viz', name: '📊 Data Viz' },
      { id: 'media_gen', name: '🎬 Media Gen' },
      { id: '3d_2d', name: '🏗️ 3D & 2D' },
      { id: 'engineering', name: '⚙️ Engineering' },
      { id: 'design', name: '🎨 Design' },
      { id: 'ai_modern', name: '🤖 AI Modern' },
      { id: 'business', name: '💼 Business' },
      { id: 'education', name: '📚 Education' },
      { id: 'image_processing', name: '🖼️ Image Processing' },
      { id: 'cloning', name: '🧬 Cloning' },
      { id: 'cinematic', name: '🎥 Cinematic' }
    ];

    this.state.skills = [];
    this.state.agents = [];
    this.state.adapters = [{ id: 'chatgpt', name: 'ChatGPT', features: [] }];
    this.mergeCustom();
  }

  // ============================================
  // IMAGES (multi upload + notes)
  // ============================================

  async addImageFiles(fileList) {
    const files = Array.from(fileList || []).filter(f => f.type.startsWith('image/'));
    if (files.length === 0) {
      this.toast('⚠️ Tidak ada file gambar yang valid.', 'warning');
      return;
    }

    const room = MAX_IMAGES - this.state.images.length;
    if (room <= 0) {
      this.toast(`⚠️ Maksimal ${MAX_IMAGES} gambar.`, 'warning');
      return;
    }
    if (files.length > room) {
      this.toast(`⚠️ Hanya ${room} gambar ditambahkan (maks ${MAX_IMAGES}).`, 'warning');
    }

    for (const file of files.slice(0, room)) {
      try {
        const dataUrl = await this.compressImage(file);
        this.state.images.push({
          id: `img-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
          name: file.name || 'screenshot.png',
          type: file.type || 'image/png',
          size: file.size || 0,
          dataUrl,
          note: ''
        });
      } catch (e) {
        this.toast(`❌ Gagal memproses ${file.name}.`, 'error');
      }
    }

    this.renderImages();
    this.saveImages();
    this.generatePrompt(true);
  }

  compressImage(file) {
    return new Promise((resolve, reject) => {
      // PNG/GIF kecil: simpan apa adanya (biar animasi/ketajaman aman)
      if (file.size <= 300 * 1024 && (file.type === 'image/png' || file.type === 'image/gif')) {
        const r = new FileReader();
        r.onload = () => resolve(r.result);
        r.onerror = reject;
        r.readAsDataURL(file);
        return;
      }

      // Kompres via canvas → JPEG (hindari masalah encoding berbagai browser)
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => {
        try {
          const MAX_DIM = 1568;
          const scale = Math.min(1, MAX_DIM / Math.max(img.width, img.height));
          const canvas = document.createElement('canvas');
          canvas.width = Math.max(1, Math.round(img.width * scale));
          canvas.height = Math.max(1, Math.round(img.height * scale));
          canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
          const out = canvas.toDataURL('image/jpeg', 0.82);
          URL.revokeObjectURL(url);
          resolve(out);
          this._warnIfTransparentPng(file);
        } catch (e) {
          URL.revokeObjectURL(url);
          reject(e);
        }
      };
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('decode gagal')); };
      img.src = url;
    });
  }

  _warnIfTransparentPng(file) {
    if (file.type === 'image/png') {
      if (!this._pngWarned) {
        this._pngWarned = true;
        this.toast('💡 PNG dikompres ke JPEG — area transparan jadi putih.', 'info');
      }
      return;
    }
  }

  removeImage(id) {
    this.state.images = this.state.images.filter(i => i.id !== id);
    this.renderImages();
    this.saveImages();
    this.generatePrompt(true);
  }

  updateImageNote(id, note) {
    const img = this.state.images.find(i => i.id === id);
    if (!img) return;
    img.note = note;
    this.saveImages();
    clearTimeout(this._noteTimer);
    this._noteTimer = setTimeout(() => this.generatePrompt(true), 300);

  }

  renderImages() {
    const list = document.getElementById('image-preview-list');
    const count = document.getElementById('image-count');
    if (!list || !count) return;

    count.textContent = `${this.state.images.length} gambar`;

    list.innerHTML = this.state.images.map((img, idx) => `
      <div class="image-preview-item" data-id="${escapeHtml(img.id)}">
        <img src="${escapeHtml(img.dataUrl)}" alt="${escapeHtml(img.name)}">
        <span class="image-meta">${idx + 1}. ${escapeHtml(img.name)}</span>
        <button class="image-remove" title="Hapus gambar" type="button">✕</button>
      </div>
    `).join('');
  }

  saveImages() {
    try {
      localStorage.setItem('vibe-coder-images-v1', JSON.stringify({
        notes: this.state.imageNotes,
        images: this.state.images
      }));
    } catch (e) {
      // Kemungkinan kuota localStorage penuh → buang gambar, simpan catatan saja
      try {
        localStorage.setItem('vibe-coder-images-v1', JSON.stringify({
          notes: this.state.imageNotes,
          images: []
        }));
      } catch (e2) { /* storage unavailable */ }
      if (this.state.images.length > 0) {
        this.toast('⚠️ Kuota browser penuh — gambar tidak ikut tersimpan permanen.', 'warning');
      }
  }
  }

  loadImages() {
    try {
      const raw = localStorage.getItem('vibe-coder-images-v1');
      if (!raw) return;
      const saved = JSON.parse(raw);
      this.state.imageNotes = typeof saved.notes === 'string' ? saved.notes : '';
      this.state.images = Array.isArray(saved.images)
        ? saved.images.filter(i => i && i.id && typeof i.dataUrl === 'string').slice(0, MAX_IMAGES)
        : [];
    } catch (e) { /* corrupted */ }
  }

  // ============================================
  // CUSTOM SKILLS & AGENTS
  // ============================================

  mergeCustom() {
    const skillIds = new Set(this.state.skills.map(s => s.id));
    this.state.customSkills.forEach(c => { if (!skillIds.has(c.id)) this.state.skills.push(c); });
    const agentIds = new Set(this.state.agents.map(a => a.id));
    this.state.customAgents.forEach(c => { if (!agentIds.has(c.id)) this.state.agents.push(c); });
  }

  loadCustomData() {
    try {
      const raw = localStorage.getItem(CUSTOM_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw);
      this.state.customSkills = Array.isArray(saved.skills)
        ? saved.skills.filter(c => c && c.id && c.name) : [];
      this.state.customAgents = Array.isArray(saved.agents)
        ? saved.agents.filter(c => c && c.id && c.name) : [];
    } catch (e) { /* corrupted */ }
  }

  saveCustomData() {
    try {
      localStorage.setItem(CUSTOM_KEY, JSON.stringify({
        skills: this.state.customSkills,
        agents: this.state.customAgents
      }));
    } catch (e) { /* storage unavailable */ }
  }

  openCustomDialog(type) {
    this._customType = type;
    document.getElementById('custom-type-label').textContent =
      type === 'skills' ? 'Skill' : 'Sub-Agent';
    document.getElementById('custom-name').value = '';
    document.getElementById('custom-desc').value = '';
    document.getElementById('custom-dialog').classList.add('open');
    document.getElementById('custom-name').focus();
  }

  closeCustomDialog() {
    document.getElementById('custom-dialog').classList.remove('open');
    this._customType = null;
  }

  submitCustom() {
    const type = this._customType;
    if (!type) return;

    const name = document.getElementById('custom-name').value.trim();
    const desc = document.getElementById('custom-desc').value.trim();
    if (!name) { this.toast('⚠️ Nama wajib diisi!', 'warning'); return; }

    const category = this.state.selectedCategory || 'custom';
    const list = type === 'skills' ? this.state.customSkills : this.state.customAgents;
    const id = `custom-${type}-${Date.now().toString(36)}`;

    list.push({ id, name: `${name} ✨`, category, description: desc || 'Custom (dibuat user)' });
    this.saveCustomData();
    this.mergeCustom();
    this.renderSkills();
    this.renderAgents();
    this.renderCounts();
    this.closeCustomDialog();
    this.toast(`✅ Custom ${type === 'skills' ? 'skill' : 'agent'} ditambahkan!`, 'success');
  }

  deleteCustom(type, id) {
    if (type === 'skills') {
      this.state.customSkills = this.state.customSkills.filter(c => c.id !== id);
      this.state.skills = this.state.skills.filter(s => s.id !== id);
      this.state.selectedSkills = this.state.selectedSkills.filter(s => s !== id);
    } else {
      this.state.customAgents = this.state.customAgents.filter(c => c.id !== id);
      this.state.agents = this.state.agents.filter(a => a.id !== id);
      this.state.selectedAgents = this.state.selectedAgents.filter(a => a !== id);
    }
    this.saveCustomData();
    this.renderSkills();
    this.renderAgents();
    this.renderCounts();
    this.saveState();
    this.generatePrompt(true);
    this.toast('🗑️ Item custom dihapus', 'info');
  }

  isCustom(type, id) {
    const list = type === 'skills' ? this.state.customSkills : this.state.customAgents;
    return list.some(c => c.id === id);
  }

  // ============================================
  // PERSISTENCE
  // ============================================

  saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        projectId: this.state.selectedProject?.id || null,
        category: this.state.selectedCategory,
        skills: this.state.selectedSkills,
        agents: this.state.selectedAgents,
        platform: this.state.selectedPlatform,
        lang: this.state.selectedLang,
        detail: this.state.projectDetail,
        autoSelect: this.state.autoSelect
      }));
    } catch (e) { /* storage unavailable */ }
  }

  restoreState() {
    // 1. Dari URL hash (share mode) — prioritas tertinggi
    if (this.loadFromUrl()) return;

    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const saved = JSON.parse(raw);

      this.state.selectedProject = saved.projectId
        ? this.state.projects.find(p => p.id === saved.projectId) || null : null;
      this.state.selectedCategory = saved.category || '';
      this.state.selectedSkills = Array.isArray(saved.skills) ? saved.skills : [];
      this.state.selectedAgents = Array.isArray(saved.agents) ? saved.agents : [];
      this.state.selectedPlatform = saved.platform || 'chatgpt';
      this.state.selectedLang = saved.lang || this.getPlatformLang(this.state.selectedPlatform);
      this.state.projectDetail = saved.detail || '';
      if (typeof saved.autoSelect === 'boolean') this.state.autoSelect = saved.autoSelect;
    } catch (e) { /* corrupted state */ }
  }

  loadFromUrl() {
    try {
      const hash = window.location.hash.slice(1);
      if (!hash) return false;
      const decoded = VibeCore.decodeConfig(hash);
      if (!decoded) return false;

      this.state.selectedProject = decoded.projectId
        ? this.state.projects.find(p => p.id === decoded.projectId) || null : null;
      this.state.selectedCategory = decoded.category || '';
      this.state.selectedSkills = Array.isArray(decoded.skills) ? decoded.skills : [];
      this.state.selectedAgents = Array.isArray(decoded.agents) ? decoded.agents : [];
      this.state.selectedPlatform = decoded.platform || 'chatgpt';
      this.state.selectedLang = decoded.lang === 'en' ? 'en'
        : decoded.lang === 'id' ? 'id'
        : this.getPlatformLang(this.state.selectedPlatform);
      this.state.projectDetail = decoded.detail || '';
      this.state.autoSelect = false;
      return true;
    } catch (e) {
      return false;
    }
  }

  // ============================================
  // RENDER
  // ============================================

  render() {
    this.renderProjects();
    this.renderCategories();
    this.renderSkills();
    this.renderAgents();
    this.renderPlatformOptions();
    this.renderStats();
    this.restoreFormControls();
  }

  restoreFormControls() {
    document.getElementById('category-select').value = this.state.selectedCategory || '';
    document.getElementById('platform-select').value = this.state.selectedPlatform;
    document.getElementById('project-detail').value = this.state.projectDetail;
    document.getElementById('auto-select-toggle').checked = this.state.autoSelect;
    document.getElementById('image-notes').value = this.state.imageNotes;
    const langSel = document.getElementById('lang-select');
    if (langSel) langSel.value = this.state.selectedLang === 'en' ? 'en' : 'id';
    this.renderImages();

    // Highlight project aktif
    if (this.state.selectedProject) {
      const item = document.querySelector(`.project-item[data-id="${this.state.selectedProject.id}"]`);
      if (item) item.classList.add('active');
    }

    // Sinkronkan UI adaptif dengan project yang dipulihkan
    this.applyProjectUi(this.state.selectedProject);
  }

  renderProjects() {
    const container = document.getElementById('project-list');
    container.innerHTML = this.state.projects.map(p => `
      <div class="project-item" data-id="${escapeHtml(p.id)}" role="button" tabindex="0">
        <div class="project-name">${escapeHtml(p.name)}</div>
        <div class="project-desc">${escapeHtml(p.desc)}</div>
      </div>
    `).join('');
  }

  renderCategories() {
    const select = document.getElementById('category-select');
    select.innerHTML = '<option value="">-- Pilih Kategori --</option>' +
      this.state.categories.map(c =>
        `<option value="${escapeHtml(c.id)}">${escapeHtml(c.name)}</option>`
      ).join('');
  }

  renderSkills() {
    const container = document.getElementById('skill-list');
    const q = (this.state.skillSearch || '').toLowerCase();

    let filtered = this.state.selectedCategory
      ? this.state.skills.filter(s => s.category === this.state.selectedCategory)
      : this.state.skills;

    if (q) {
      filtered = filtered.filter(s =>
        s.name.toLowerCase().includes(q) ||
        (s.description || '').toLowerCase().includes(q)
      );
    }

    if (filtered.length === 0) {
      container.innerHTML = '<div class="empty-note">Tidak ada skill yang cocok.</div>';
      return;
    }

    container.innerHTML = filtered.map(s => `
      <label class="skill-item">
        <input type="checkbox" value="${escapeHtml(s.id)}"
          ${this.state.selectedSkills.includes(s.id) ? 'checked' : ''}>
        <span class="item-name" title="${escapeHtml(s.description || '')}">${escapeHtml(s.name)}</span>
        ${this.isCustom('skills', s.id) ? `<button class="item-remove" data-type="skills" data-id="${escapeHtml(s.id)}" title="Hapus custom" type="button">✕</button>` : ''}
      </label>
    `).join('');
  }

  renderAgents() {
    const container = document.getElementById('agent-list');
    const q = (this.state.agentSearch || '').toLowerCase();

    let filtered = this.state.selectedCategory
      ? this.state.agents.filter(a => a.category === this.state.selectedCategory)
      : this.state.agents;

    if (q) {
      filtered = filtered.filter(a =>
        a.name.toLowerCase().includes(q) ||
        (a.description || '').toLowerCase().includes(q)
      );
    }

    if (filtered.length === 0) {
      container.innerHTML = '<div class="empty-note">Tidak ada agent yang cocok.</div>';
      return;
    }

    container.innerHTML = filtered.map(a => `
      <label class="agent-item">
        <input type="checkbox" value="${escapeHtml(a.id)}"
          ${this.state.selectedAgents.includes(a.id) ? 'checked' : ''}>
        <span class="item-name" title="${escapeHtml(a.description || '')}">${escapeHtml(a.name)}</span>
        ${this.isCustom('agents', a.id) ? `<button class="item-remove" data-type="agents" data-id="${escapeHtml(a.id)}" title="Hapus custom" type="button">✕</button>` : ''}
      </label>
    `).join('');
  }

  renderPlatformOptions() {
    const select = document.getElementById('platform-select');
    if (this.state.adapters.length === 0) return;

    select.innerHTML = this.state.adapters.map(a => {
      const features = (a.features || []).slice(0, 3).join(', ');
      const label = features ? `${a.name} (${features})` : a.name;
      return `<option value="${escapeHtml(a.id)}">${escapeHtml(label)}</option>`;
    }).join('');
    select.value = this.state.selectedPlatform;
  }

  renderStats() {
    const { skills, agents, adapters } = this.state;
    const stats = document.querySelector('.stats');
    if (stats) {
      stats.innerHTML = `
        <span class="stat">${skills.length} Skills</span>
        <span class="stat">${agents.length} Sub-Agents</span>
        <span class="stat">${adapters.length} Platforms</span>`;
    }
    const footer = document.querySelector('.footer p');
    if (footer) {
      footer.textContent = `RAUZA Prompt Generator — ${skills.length} Skills, ${agents.length} Sub-Agents, ${adapters.length} Platforms`;
    }
  }

  renderCounts() {
    document.getElementById('skill-count').textContent = `${this.state.selectedSkills.length} dipilih`;
    document.getElementById('agent-count').textContent = `${this.state.selectedAgents.length} dipilih`;
  }

  // ============================================
  // EVENTS
  // ============================================

  attachEvents() {
    const $ = (id) => {
      const el = document.getElementById(id);
      if (!el) console.warn('Elemen tidak ditemukan (abaikan bila cache lama): #' + id);
      return el || { addEventListener() {} };
    };

    // --- Project selection (click + keyboard) ---
    $('project-list').addEventListener('click', (e) => {
      const item = e.target.closest('.project-item');
      if (item) this.selectProject(item.dataset.id);
    });
    $('project-list').addEventListener('keydown', (e) => {
      if (e.key !== 'Enter' && e.key !== ' ') return;
      const item = e.target.closest('.project-item');
      if (item) { e.preventDefault(); this.selectProject(item.dataset.id); }
    });

    // --- Category ---
    $('category-select').addEventListener('change', (e) => {
      this.state.selectedCategory = e.target.value;
      this.renderSkills();
      this.renderAgents();
      this.saveState();
    });

    // --- Search filters (debounced) ---
    let skillTimer, agentTimer;
    $('skill-search').addEventListener('input', (e) => {
      clearTimeout(skillTimer);
      skillTimer = setTimeout(() => {
        this.state.skillSearch = e.target.value.trim();
        this.renderSkills();
      }, 150);
    });
    $('agent-search').addEventListener('input', (e) => {
      clearTimeout(agentTimer);
      agentTimer = setTimeout(() => {
        this.state.agentSearch = e.target.value.trim();
        this.renderAgents();
      }, 150);
    });

    // --- Skill selection (toggle + select all / clear) ---
    $('skill-list').addEventListener('change', (e) => {
      if (e.target.type !== 'checkbox') return;
      this.toggleItem('selectedSkills', e.target.value, e.target.checked);
    });
    $('skill-select-all').addEventListener('click', () => this.selectAll('skills'));
    $('skill-clear').addEventListener('click', () => this.clearAll('skills'));

    // --- Agent selection ---
    $('agent-list').addEventListener('change', (e) => {
      if (e.target.type !== 'checkbox') return;
      this.toggleItem('selectedAgents', e.target.value, e.target.checked);
    });
    $('agent-select-all').addEventListener('click', () => this.selectAll('agents'));
    $('agent-clear').addEventListener('click', () => this.clearAll('agents'));

    // --- Detail & platform ---
    $('project-detail').addEventListener('input', (e) => {
      this.state.projectDetail = e.target.value;
      this.saveState();
      this.generatePrompt(true);
    });
    $('platform-select').addEventListener('change', (e) => {
      this.state.selectedPlatform = e.target.value;
      // Ingat bahasa per platform — pulihkan pilihan bahasa untuk platform ini
      this.state.selectedLang = this.getPlatformLang(this.state.selectedPlatform);
      $('lang-select').value = this.state.selectedLang;
      this.updateLangMemoryNote();
      this.saveState();
      this.generatePrompt(true);
    });
    $('lang-select').addEventListener('change', (e) => {
      this.state.selectedLang = e.target.value === 'en' ? 'en' : 'id';
      this.state.platformLangs[this.state.selectedPlatform] = this.state.selectedLang;
      this.savePlatformLangs();
      this.updateLangMemoryNote();
      this.saveState();
      this.applyProjectUi(this.state.selectedProject);
      this.generatePrompt(true);
    });

    // --- Images: upload, drag & drop, paste, notes ---
    $('image-input').addEventListener('change', (e) => {
      this.addImageFiles(e.target.files);
      e.target.value = '';
    });

    const dropzone = $('image-dropzone');
    dropzone.addEventListener('click', () => $('image-input').click());
    dropzone.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); $('image-input').click(); }
    });
    ['dragenter', 'dragover'].forEach(ev => dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }));
    ['dragleave', 'drop'].forEach(ev => dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }));
    dropzone.addEventListener('drop', (e) => {
      if (e.dataTransfer && e.dataTransfer.files) this.addImageFiles(e.dataTransfer.files);
    });

    document.addEventListener('paste', (e) => {
      const items = e.clipboardData && e.clipboardData.files;
      if (!items || items.length === 0) return;
      const imgs = Array.from(items).filter(f => f.type.startsWith('image/'));
      if (imgs.length > 0) {
        e.preventDefault();
        this.addImageFiles(imgs);
      }
    });

    $('image-notes').addEventListener('input', (e) => {
      this.state.imageNotes = e.target.value;
      this.saveImages();
      this.generatePrompt(true);
    });

    $('image-preview-list').addEventListener('click', (delegated) => {
      const btn = delegated.target.closest('.image-remove');
      if (!btn) return;
      delegated.preventDefault();
      this.removeImage(btn.closest('.image-preview-item').dataset.id);
    });

    // --- Auto-select toggle ---
    $('auto-select-toggle').addEventListener('change', (e) => {
      this.state.autoSelect = e.target.checked;
      this.saveState();
      if (this.state.autoSelect && this.state.selectedProject) {
        this.applyProjectPreset(this.state.selectedProject);
      }
    });

    // --- Actions ---
    $('generate-btn').addEventListener('click', () => {
      const prompt = this.generatePrompt();
      if (prompt) this.saveToHistory();
    });
    $('clear-btn').addEventListener('click', () => this.clearAll('form'));
    $('copy-btn').addEventListener('click', () => this.copyPrompt());
    $('download-btn').addEventListener('click', () => this.downloadPrompt());
    $('export-json-btn').addEventListener('click', () => this.exportJSON());
    $('share-btn').addEventListener('click', () => this.sharePrompt());
    $('import-json-btn').addEventListener('click', () => $('import-file').click());
    $('import-file').addEventListener('change', (e) => this.importJSON(e));
    $('theme-toggle').addEventListener('click', () => this.toggleTheme());

    // --- Custom skills & agents ---
    $('add-skill-btn').addEventListener('click', () => this.openCustomDialog('skills'));
    $('add-agent-btn').addEventListener('click', () => this.openCustomDialog('agents'));
    $('custom-submit').addEventListener('click', () => this.submitCustom());
    $('custom-cancel').addEventListener('click', () => this.closeCustomDialog());
    $('custom-dialog').addEventListener('click', (e) => {
      if (e.target.id === 'custom-dialog') this.closeCustomDialog();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.closeCustomDialog();
    });

    // --- History ---
    $('history-toggle-btn').addEventListener('click', () => {
      const panel = document.getElementById('history-panel');
      const btn = document.getElementById('history-toggle-btn');
      const open = panel.classList.toggle('open');
      btn.classList.toggle('active', open);
      if (open) this.renderHistory();
    });
    $('history-clear-btn').addEventListener('click', () => this.clearHistory());
    $('history-list').addEventListener('click', (e) => {
      const del = e.target.closest('.history-delete');
      if (del) { this.deleteHistory(del.dataset.id); return; }
      const load = e.target.closest('.history-load');
      if (load) this.loadFromHistory(load.dataset.id);
    });

    // --- Hapus item custom (tombol ✕) ---
    $('skill-list').addEventListener('click', (e) => {
      const btn = e.target.closest('.item-remove');
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      this.deleteCustom(btn.dataset.type, btn.dataset.id);
    });
    $('agent-list').addEventListener('click', (e) => {
      const btn = e.target.closest('.item-remove');
      if (!btn) return;
      e.preventDefault();
      e.stopPropagation();
      this.deleteCustom(btn.dataset.type, btn.dataset.id);
    });

    // --- Keyboard shortcut: Ctrl+Enter generate ---
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        this.generatePrompt();
      }
    });
  }

  // ============================================
  // LOGIC
  // ============================================

  selectProject(projectId) {
    const project = this.state.projects.find(p => p.id === projectId);
    if (!project) return;

    this.state.selectedProject = project;
    this.state.selectedCategory = project.category || '';

    document.querySelectorAll('.project-item').forEach(i =>
      i.classList.toggle('active', i.dataset.id === projectId));
    document.getElementById('category-select').value = this.state.selectedCategory;

    this.renderSkills();
    this.renderAgents();
    this.applyProjectUi(project);

    if (this.state.autoSelect) {
      this.applyProjectPreset(project);
    }

    this.saveState();
    this.generatePrompt(true);
  }

  // ============================================
  // ADAPTIVE UI — tampilan menyesuaikan project yang dipilih
  // ============================================

  hexToRgba(hex, alpha) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(String(hex || ''));
    if (!m) return '';
    const [r, g, b] = [parseInt(m[1], 16), parseInt(m[2], 16), parseInt(m[3], 16)];
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  applyProjectUi(project) {
    const ui = VibeCore.resolveProjectUi(project, this.state.selectedLang);
    const root = document.documentElement;

    // 1) Aksen warna via CSS variables (fallback ke tema bila project tanpa aksen)
    if (ui && ui.accent) {
      root.style.setProperty('--p-accent', ui.accent);
      root.style.setProperty('--p-accent-2', ui.accent2 || ui.accent);
      root.style.setProperty('--p-accent-soft', this.hexToRgba(ui.accent, 0.14));
      root.style.setProperty('--p-accent-soft-2', this.hexToRgba(ui.accent2 || ui.accent, 0.10));
    } else {
      ACCENT_VARS.forEach((v) => root.style.removeProperty(v));
    }

    // 2) Kelas body: layout & ikon konten menyesuaikan jenis project
    document.body.classList.toggle('mode-visual', !!(ui && ui.accent));

    // 3) Hero card dinamis
    const hero = document.getElementById('project-hero');
    if (hero) {
      if (!project) {
        hero.hidden = true;
        hero.innerHTML = '';
      } else {
        hero.hidden = false;
        const wf = ui && ui.workflow
          ? `<div class="hero-workflow"><strong>🔁 Alur kerja:</strong><ol>${ui.workflow.map(w => `<li>${escapeHtml(w.replace(/^\d+\.\s*/, ''))}</li>`).join('')}</ol></div>`
          : '';
        const tips = ui && ui.tips
          ? `<div class="hero-tips">💡 <em>${escapeHtml(ui.tips)}</em></div>`
          : '';
        hero.innerHTML = `
          <div class="hero-main">
            <span class="hero-icon">${escapeHtml(ui.icon)}</span>
            <div class="hero-text">
              <div class="hero-title">${escapeHtml(project.name)}${ui.vibe ? `<span class="hero-vibe">${escapeHtml(ui.vibe)}</span>` : ''}</div>
              <div class="hero-desc">${escapeHtml(project.desc)}</div>
            </div>
          </div>
          ${tips}
          ${wf}`;
      }
    }

    // 4) Placeholder textarea detail menyesuaikan konteks project
    const detailEl = document.getElementById('project-detail');
    if (detailEl) {
      detailEl.placeholder = (ui && ui.detailPlaceholder) || DEFAULT_DETAIL_PLACEHOLDER;
    }

    this.renderPersonaBadge(project);
  }

  renderPersonaBadge(project, skills) {
    const badge = document.getElementById('persona-badge');
    if (!badge) return;
    const sk = skills || this.state.selectedSkills
      .map(id => this.state.skills.find(s => s.id === id)).filter(Boolean);
    const persona = project
      ? VibeCore.resolvePersona(project, this.state.categories, sk, this.state.selectedLang)
      : null;
    if (!persona) { badge.hidden = true; badge.innerHTML = ''; return; }
    badge.hidden = false;
    badge.innerHTML =
      `<span>${escapeHtml(persona.icon)} Mode ${escapeHtml(persona.label)}</span>` +
      `<span class="persona-label">— struktur output menyesuaikan profesi ini</span>`;
  }

  applyProjectPreset(project) {
    const skills = (project.skills || []).filter(id =>
      this.state.skills.some(s => s.id === id));
    const agents = (project.agents || []).filter(id =>
      this.state.agents.some(a => a.id === id));

    this.state.selectedSkills = [...new Set([...this.state.selectedSkills, ...skills])];
    this.state.selectedAgents = [...new Set([...this.state.selectedAgents, ...agents])];

    this.renderSkills();
    this.renderAgents();
  }

  toggleItem(key, id, checked) {
    const list = this.state[key];
    if (checked && !list.includes(id)) list.push(id);
    if (!checked) this.state[key] = list.filter(v => v !== id);
    this.renderCounts();
    this.saveState();
    this.generatePrompt(true);
  }

  selectAll(type) {
    const q = (this.state[`${type}Search`] || '').toLowerCase();
    const source = type === 'skills' ? this.state.skills : this.state.agents;
    const key = type === 'skills' ? 'selectedSkills' : 'selectedAgents';

    const visible = source.filter(s => {
      const inCat = !this.state.selectedCategory || s.category === this.state.selectedCategory;
      const matchQ = !q || s.name.toLowerCase().includes(q);
      return inCat && matchQ;
    });

    this.state[key] = [...new Set([...this.state[key], ...visible.map(s => s.id)])];
    this.renderSkills();
    this.renderAgents();
    this.renderCounts();
    this.saveState();
    this.generatePrompt(true);
    this.toast(`✅ ${visible.length} ${type} ditambahkan`, 'success');
  }

  clearAll(type) {
    if (type === 'form') {
      this.state.selectedProject = null;
      this.state.selectedCategory = '';
      this.state.selectedSkills = [];
      this.state.selectedAgents = [];
      this.state.projectDetail = '';
      this.state.skillSearch = '';
      this.state.agentSearch = '';
      this.state.images = [];
      this.state.imageNotes = '';

      document.querySelectorAll('.project-item').forEach(i => i.classList.remove('active'));
      document.getElementById('category-select').value = '';
      document.getElementById('project-detail').value = '';
      document.getElementById('skill-search').value = '';
      document.getElementById('agent-search').value = '';
      document.getElementById('image-notes').value = '';
      document.getElementById('output-preview').textContent =
        'Pilih project dan klik "Generate Prompt" untuk melihat hasilnya...';
      const badge = document.getElementById('persona-badge');
      if (badge) { badge.hidden = true; badge.innerHTML = ''; }
      this.applyProjectUi(null);
      window.location.hash = '';
    } else {
      const key = type === 'skills' ? 'selectedSkills' : 'selectedAgents';
      this.state[key] = [];
    }

    this.renderSkills();
    this.renderAgents();
    this.renderCounts();
    this.renderImages();
    this.saveImages();
    this.saveState();
    this.generatePrompt(true);
  }

  // ============================================
  // PROMPT GENERATION
  // ============================================

  // ============================================
  // BAHASA OUTPUT — diingat per platform AI
  // ============================================

  PLATFORM_LANGS_KEY = 'rauza-platform-langs-v1';

  loadPlatformLangs() {
    try {
      const raw = localStorage.getItem(this.PLATFORM_LANGS_KEY);
      this.state.platformLangs = raw ? (JSON.parse(raw) || {}) : {};
    } catch (e) {
      this.state.platformLangs = {};
    }
  }

  savePlatformLangs() {
    try {
      localStorage.setItem(this.PLATFORM_LANGS_KEY, JSON.stringify(this.state.platformLangs));
    } catch (e) { /* storage unavailable */ }
  }

  getPlatformLang(platformId) {
    return this.state.platformLangs[platformId] || this.state.selectedLang || 'id';
  }

  updateLangMemoryNote() {
    const note = document.getElementById('lang-memory-note');
    if (!note) return;
    const saved = this.state.platformLangs[this.state.selectedPlatform];
    note.textContent = saved
      ? `(platform ini terakhir pakai ${saved === 'en' ? 'English' : 'Indonesia'})`
      : '(pilihan diingat otomatis per platform)';
  }

  generatePrompt(silent = false) {
    const { selectedProject, selectedSkills, selectedAgents, selectedPlatform, selectedLang, projectDetail, images, imageNotes } = this.state;

    if (!selectedProject) {
      if (!silent) this.toast('⚠️ Pilih project terlebih dahulu!', 'warning');
      return null;
    }

    const platform = this.state.adapters.find(a => a.id === selectedPlatform) || {};
    const skills = selectedSkills.map(id => this.state.skills.find(s => s.id === id)).filter(Boolean);
    const agents = selectedAgents.map(id => this.state.agents.find(a => a.id === id)).filter(Boolean);

    const prompt = VibeCore.buildPrompt({
      project: selectedProject,
      skills,
      agents,
      platform,
      detail: projectDetail,
      categories: this.state.categories,
      images,
      imageNotes,
      lang: selectedLang === 'en' ? 'en' : 'id'
    });
    document.getElementById('output-preview').textContent = prompt;
    this.renderPersonaBadge(selectedProject, skills);
    return prompt;
  }

  // ============================================
  // EXPORT / IMPORT / SHARE
  // ============================================

  getConfig() {
    return {
      project: this.state.selectedProject?.id || null,
      category: this.state.selectedCategory || null,
      skills: this.state.selectedSkills,
      agents: this.state.selectedAgents,
      platform: this.state.selectedPlatform,
      lang: this.state.selectedLang === 'en' ? 'en' : 'id',
      detail: this.state.projectDetail,
      imageNotes: this.state.imageNotes || '',
      images: this.state.images.map(i => ({
        id: i.id, name: i.name, type: i.type, size: i.size,
        width: i.width, height: i.height, note: i.note, dataUrl: i.dataUrl
      })),
      timestamp: new Date().toISOString()
    };
  }

  applyConfig(config) {
    this.state.selectedProject = config.project
      ? this.state.projects.find(p => p.id === config.project) || null : null;
    this.state.selectedCategory = config.category || '';
    this.state.selectedSkills = Array.isArray(config.skills) ? config.skills : [];
    this.state.selectedAgents = Array.isArray(config.agents) ? config.agents : [];
    this.state.selectedPlatform = config.platform || 'chatgpt';
    this.state.selectedLang = config.lang === 'en' ? 'en'
      : config.lang === 'id' ? 'id'
      : this.getPlatformLang(this.state.selectedPlatform);
    this.state.projectDetail = config.detail || '';
    this.state.imageNotes = typeof config.imageNotes === 'string' ? config.imageNotes : '';
    this.state.images = Array.isArray(config.images)
      ? config.images.filter(i => i && typeof i.dataUrl === 'string').slice(0, MAX_IMAGES)
      : [];

    document.querySelectorAll('.project-item').forEach(i =>
      i.classList.toggle('active', i.dataset.id === config.project));
    document.getElementById('category-select').value = this.state.selectedCategory;
    document.getElementById('project-detail').value = this.state.projectDetail;
    const langSelect = document.getElementById('lang-select');
    if (langSelect) langSelect.value = this.state.selectedLang === 'en' ? 'en' : 'id';
    this.updateLangMemoryNote();
    document.getElementById('image-notes').value = this.state.imageNotes;

    this.renderSkills();
    this.renderAgents();
    this.renderCounts();
    this.renderImages();
    this.applyProjectUi(this.state.selectedProject);
    this.saveImages();
    this.generatePrompt(true);
    this.saveState();
  }

  copyPrompt() {
    const text = this.generatePrompt(true);
    if (!text) { this.toast('⚠️ Belum ada prompt. Pilih project dulu!', 'warning'); return; }

    navigator.clipboard.writeText(text)
      .then(() => {
        this.saveToHistory();
        this.toast('✅ Prompt berhasil di-copy!', 'success');
      })
      .catch(() => this.toast('❌ Gagal copy. Coba manual.', 'error'));
  }

  downloadPrompt() {
    const text = this.generatePrompt(true);
    if (!text) { this.toast('⚠️ Belum ada prompt. Pilih project dulu!', 'warning'); return; }

    this.download(new Blob([text], { type: 'text/plain' }),
      `rauza-prompt-${this.timestamp()}.txt`);
    this.saveToHistory();
    this.toast('✅ Prompt ter-download!', 'success');
  }

  exportJSON() {
    if (!this.state.selectedProject) {
      this.toast('⚠️ Pilih project terlebih dahulu!', 'warning');
      return;
    }
    const blob = new Blob([JSON.stringify(this.getConfig(), null, 2)], { type: 'application/json' });
    this.download(blob, `rauza-config-${this.timestamp()}.json`);
    this.toast('✅ Config ter-export!', 'success');
  }

  importJSON(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const config = JSON.parse(reader.result);
        this.applyConfig(config);
        this.toast('✅ Config berhasil di-import!', 'success');
      } catch {
        this.toast('❌ File JSON tidak valid.', 'error');
      }
    };
    reader.readAsText(file);
    e.target.value = ''; // reset agar file sama bisa di-import lagi
  }

  sharePrompt() {
    const config = this.getLightConfig();
    const encoded = VibeCore.encodeConfig(config);
    if (!encoded) { this.toast('❌ Gagal encode config.', 'error'); return; }
    const url = `${window.location.origin}${window.location.pathname}#${encoded}`;

    this.saveToHistory();

    // Coba Web Share API dulu (mobile-friendly)
    if (navigator.share) {
      navigator.share({ title: 'RAUZA Prompt', url })
        .catch(() => {}); // user cancel
      return;
    }

    navigator.clipboard.writeText(url)
      .then(() => {
        window.history.replaceState(null, '', `#${encoded}`);
        this.toast('🔗 Link share di-copy ke clipboard!', 'success');
      })
      .catch(() => this.toast('❌ Gagal copy link.', 'error'));
  }

  download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  timestamp() {
    const d = new Date();
    return `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}-${String(d.getHours()).padStart(2, '0')}${String(d.getMinutes()).padStart(2, '0')}${String(d.getSeconds()).padStart(2, '0')}`;
  }

  // ============================================
  // HISTORY
  // ============================================

  loadHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      this.state.history = raw ? (JSON.parse(raw) || []) : [];
    } catch (e) {
      this.state.history = [];
    }
  }

  // Config ringan untuk riwayat/share: tanpa base64 gambar (hemat kuota localStorage & panjang URL)
  getLightConfig() {
    const config = this.getConfig();
    return { ...config, images: [] };
  }

  saveToHistory() {
    const prompt = document.getElementById('output-preview').textContent;
    if (!prompt || !this.state.selectedProject) return;

    const config = this.getLightConfig();
    const last = this.state.history[0];
    const imgCount = this.state.images.length;
    if (last && last.config.project === config.project &&
        JSON.stringify(last.config.skills) === JSON.stringify(config.skills) &&
        JSON.stringify(last.config.agents) === JSON.stringify(config.agents) &&
        last.config.detail === config.detail &&
        last.config.platform === config.platform &&
        (last.config.imageCount || 0) === imgCount) {
      return;
    }

    this.state.history.unshift({
      id: Date.now().toString(36),
      at: new Date().toISOString(),
      preview: prompt.slice(0, 120),
      config: { ...config, imageCount: imgCount }
    });
    this.state.history = this.state.history.slice(0, HISTORY_LIMIT);
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(this.state.history)); } catch (e) {}
    this.renderHistory();
  }

  renderHistory() {
    const list = document.getElementById('history-list');
    if (!list) return;

    if (this.state.history.length === 0) {
      list.innerHTML = '<div class="empty-note">Belum ada riwayat. Klik Generate / Copy untuk menyimpan.</div>';
      return;
    }

    list.innerHTML = this.state.history.map(h => `
      <div class="history-item">
        <button class="history-load" data-id="${escapeHtml(h.id)}" title="Muat config ini">
          <span class="history-preview">${escapeHtml((h.config.detail || '').slice(0, 60) || h.preview)}</span>
          <span class="history-meta">${new Date(h.at).toLocaleString('id-ID')} · ${(h.config.skills || []).length} skill · ${(h.config.agents || []).length} agent${h.config.imageCount ? ` · 🖼️ ${h.config.imageCount}` : ''}</span>
        </button>
        <button class="history-delete" data-id="${escapeHtml(h.id)}" title="Hapus dari riwayat" type="button">✕</button>
      </div>
    `).join('');
  }

  loadFromHistory(id) {
    const entry = this.state.history.find(h => h.id === id);
    if (!entry) return;
    this.applyConfig(entry.config);
    this.toast('✅ Config dimuat dari riwayat!', 'success');
  }

  deleteHistory(id) {
    this.state.history = this.state.history.filter(h => h.id !== id);
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(this.state.history)); } catch (e) {}
    this.renderHistory();
  }

  clearHistory() {
    if (this.state.history.length === 0) return;
    this.state.history = [];
    try { localStorage.removeItem(HISTORY_KEY); } catch (e) {}
    this.renderHistory();
    this.toast('🗑️ Riwayat dikosongkan', 'info');
  }

  // ============================================
  // THEME
  // ============================================

  applyTheme() {
    document.documentElement.dataset.theme = this.state.theme;
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = this.state.theme === 'dark' ? '☀️ Light' : '🌙 Dark';
  }

  toggleTheme() {
    this.state.theme = this.state.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('vibe-coder-theme', this.state.theme); } catch (e) {}
    this.applyTheme();
  }

  // ============================================
  // TOAST
  // ============================================

  toast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    container.appendChild(el);

    setTimeout(() => el.classList.add('show'), 10);
    setTimeout(() => {
      el.classList.remove('show');
      setTimeout(() => el.remove(), 300);
    }, 3000);
  }
}

// ============================================
// INITIALIZE APP
// ============================================
function bootApp() {
  if (window.vibeCoder) return;
  window.vibeCoder = new VibeCoderApp();
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootApp);
} else {
  // Script termuat setelah DOM siap (cache/urutan load) — jangan tunggu event
  bootApp();
}
