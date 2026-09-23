// Toggle buka/tutup panel skill/agent — hemat ruang vertikal di HP.
// Default TERTUTUP. Terbuka otomatis saat user memilih project (agar terlihat
// hasil auto-select), atau saat user membuka manual lewat tombol chevron.
(function () {
  const PANELS = [
    { list: 'skill-list', toggle: 'skill-panel-toggle', key: 'rauza-panel-skills' },
    { list: 'agent-list', toggle: 'agent-panel-toggle', key: 'rauza-panel-agents' },
  ];

  function setOpen(panel, open) {
    const list = document.getElementById(panel.list);
    const btn = document.getElementById(panel.toggle);
    if (!list || !btn) return;
    list.classList.toggle('collapsed', !open);
    btn.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.textContent = open ? '▲' : '▼';
    try { localStorage.setItem(panel.key, open ? 'open' : 'closed'); } catch (e) {}
  }

  window.RauzaPanels = {
    // Dipanggil app saat project dipilih: buka keduanya agar user melihat hasil auto-pilih
    openOnProjectSelect() {
      PANELS.forEach((p) => setOpen(p, true));
    },
    init() {
      PANELS.forEach((panel) => {
        const list = document.getElementById(panel.list);
        const btn = document.getElementById(panel.toggle);
        if (!list || !btn) return;
        let saved = null;
        try { saved = localStorage.getItem(panel.key); } catch (e) {}
        setOpen(panel, saved === 'open'); // default: tertutup
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          // collapsed=true artinya sedang tertutup → klik harus MEMBUKANYA
          setOpen(panel, list.classList.contains('collapsed'));
        });
      });
      // Buka otomatis saat project dipilih (delegasi, aman terhadap re-render list)
      const projectList = document.getElementById('project-list');
      if (projectList) {
        projectList.addEventListener('click', (e) => {
          if (e.target.closest('.project-item')) {
            setTimeout(() => this.openOnProjectSelect(), 0);
          }
        });
      }
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.RauzaPanels.init());
  } else {
    window.RauzaPanels.init();
  }
})();
