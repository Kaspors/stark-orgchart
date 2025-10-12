(function () {
  const containerSel = '#chart';
  const alertSel = '#alert';
  const infoSel = '#info';

  const setInfo = t => { const el = document.querySelector(infoSel); if (el) el.textContent = t; };
  const showAlert = html => { const el = document.querySelector(alertSel); if (!el) return; el.innerHTML = html; el.style.display = 'block'; };
  const clearAlert = () => { const el = document.querySelector(alertSel); if (!el) return; el.style.display = 'none'; el.innerHTML = ''; };

  function ensureDeps() {
    if (typeof d3 === 'undefined') throw new Error('d3 not loaded');
    if (typeof d3.flextree !== 'function') throw new Error('d3-flextree not loaded (d3.flextree missing)');
    if (typeof d3.OrgChart === 'undefined') throw new Error('d3-org-chart not loaded');
  }

  // --- Data helpers ---
  async function loadFromApi() {
    const res = await fetch('/api/tree', { headers: { accept: 'application/json' } });
    if (!res.ok) throw new Error(`GET /api/tree → HTTP ${res.status}`);
    const json = await res.json();
    if (!Array.isArray(json)) throw new Error('GET /api/tree → expected array');
    return json;
  }

  function cleanParentId(x) {
    if (x === null || x === undefined) return null;
    const s = String(x).trim().toLowerCase();
    if (s === '' || s === 'null' || s === 'undefined') return null;
    return String(x);
  }

  function normalizeData(records) {
    // Make shallow copy & normalize ids
    const data = records.map((r, i) => ({
      ...r,
      id: String(r.id ?? r.ID ?? r.Id ?? `n${i}`),
      parentId: cleanParentId(r.parentId ?? r.ParentId ?? r.managerId ?? r.ManagerId ?? r.Manager),
      name: r.name ?? r.Name ?? r.fullName ?? String(r.id ?? r.ID ?? r.Id ?? `n${i}`),
      title: r.title ?? r.Title ?? r.role ?? r.Role ?? r.Function ?? ''
    }));

    // Count roots
    const roots = data.filter(n => n.parentId === null);
    if (roots.length <= 1) return { data, rootsCount: roots.length, syntheticRootAdded: false };

    // Add a synthetic root
    const ROOT_ID = '__root__';
    const synthetic = { id: ROOT_ID, parentId: null, name: 'All Functions', title: '' };
    // Attach all current roots under synthetic
    const attached = data.map(n => (n.parentId === null ? { ...n, parentId: ROOT_ID } : n));
    return { data: [synthetic, ...attached], rootsCount: roots.length, syntheticRootAdded: true };
  }

  function demoData() {
    return [
      { id: '1', parentId: null, name: 'Morten S.', title: 'Head of Architecture' },
      { id: '2', parentId: '1', name: 'Ernesto',   title: 'Engineer' },
      { id: '3', parentId: '1', name: 'Mateusz',   title: 'Engineer' },
    ];
  }

  async function renderChart(data) {
    const chart = new d3.OrgChart()
      .container(containerSel)
      .data(data)
      .nodeId(d => d.id)
      .parentNodeId(d => d.parentId ?? null)
      // This build uses nodeWidth/nodeHeight (not nodeSize)
      .nodeWidth(() => 260)
      .nodeHeight(() => 90)
      .childrenMargin(() => 36)
      .compactMarginBetween(() => 22)
      .compactMarginPair(() => 44)
      .initialZoom(0.8)
      .nodeContent(d => `
        <div class="node-card">
          <p class="node-name">${(d.data.name ?? d.data.Name ?? d.data.fullName ?? d.data.id) || '—'}</p>
          <p class="node-title">${(d.data.title ?? d.data.role ?? d.data.Role ?? d.data.Function ?? '')}</p>
        </div>
      `);

    await chart.render();

    document.getElementById('btn-zoom-in')?.addEventListener('click', () => chart.zoomIn());
    document.getElementById('btn-zoom-out')?.addEventListener('click', () => chart.zoomOut());
    document.getElementById('btn-fit')?.addEventListener('click', () => chart.fit());

    let t;
    window.addEventListener('resize', () => {
      clearTimeout(t);
      t = setTimeout(() => chart.fit(), 150);
    });

    setInfo(`${data.length} nodes`);
    console.info('[orgchart] nodes:', data.length, 'sample:', data.slice(0, 5));
  }

  async function main() {
    setInfo('loading…'); clearAlert();

    try { ensureDeps(); }
    catch (e) { console.error(e); showAlert(`<strong>Library load error.</strong> ${e.message}`); setInfo('error'); return; }

    // Load real data (fallback to demo)
    let raw = [];
    try { raw = await loadFromApi(); }
    catch (e) { console.warn('Using demo data. Reason:', e); showAlert(`<strong>Using demo data.</strong> Could not load <code>/api/tree</code>: ${e.message}`); raw = demoData(); }

    if (!Array.isArray(raw) || raw.length === 0) { showAlert('<strong>No data.</strong> The dataset is empty.'); setInfo('empty'); return; }

    // Normalize + synthetic root if needed
    const { data, rootsCount, syntheticRootAdded } = normalizeData(raw);
    if (syntheticRootAdded) {
      showAlert(`<strong>Multiple roots detected (${rootsCount}).</strong> Added a synthetic root “All Functions” for layout.`);
    }

    // Validate shape after normalization
    const badShape = data.some(d => typeof d.id === 'undefined' || !('parentId' in d));
    if (badShape) { console.warn('Bad data sample:', data.slice(0, 5)); showAlert('<strong>Unexpected data shape.</strong> Need { id, parentId, name, title }.'); setInfo('bad-data'); return; }

    try { await renderChart(data); }
    catch (e) { console.error('Render error:', e); showAlert(`<strong>Render error.</strong> ${e.message || e}`); setInfo('error'); }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', main); else main();
})();
