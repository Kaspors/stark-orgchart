(function () {
  const qs = new URLSearchParams(location.search);
  const personId = qs.get('id');           // null => creating new
  const LS_KEY = 'org_admin_key';

  const $ = id => document.getElementById(id);
  const toast = () => $('toast');

  function showToast(msg, ok = true) {
    const t = toast(); if (!t) return;
    t.textContent = msg;
    t.style.background = ok ? 'rgba(0,0,0,.82)' : '#b00020';
    t.style.display = 'block';
    setTimeout(() => (t.style.display = 'none'), 2200);
  }

  // ---- Admin key helpers ----
  function getAdminKey() {
    return (localStorage.getItem(LS_KEY) || $('adminKey')?.value || '').trim();
  }
  function saveAdminKeyToLS() {
    const v = $('adminKey')?.value?.trim() || '';
    localStorage.setItem(LS_KEY, v);
  }
  function reflectAdminKeyHint() {
    const k = getAdminKey();
    const hint = $('hint'); if (!hint) return;
    hint.textContent = k ? 'Admin key is set locally (will be sent on save).'
                         : 'Enter your admin key and press “Save key”. It will be used when saving.';
  }

  // ---- API helpers (always include admin key) ----
  function addAdminKeyToUrl(url) {
    const key = getAdminKey();
    if (!key) return url;
    const u = new URL(url, location.origin);
    u.searchParams.set('adminKey', key);
    return u.toString();
  }
  function withAdminKeyOpts(method, bodyObj) {
    const key = getAdminKey();
    const headers = { 'content-type': 'application/json' };
    if (key) headers['X-Admin-Key'] = key;
    const body = JSON.stringify({ ...(bodyObj || {}), adminKey: key });
    return { method, headers, body };
  }

  // ---- Data load ----
  async function loadPeople() {
    const res = await fetch('/api/people');
    if (!res.ok) throw new Error(`GET /api/people → ${res.status}`);
    const list = await res.json();
    if (!Array.isArray(list)) throw new Error('Expected array from /api/people');
    return list;
  }

  function fillManagerOptions(list, selectedId) {
    const sel = $('manager'); if (!sel) return;
    sel.innerHTML = '<option value="">(none)</option>';
    list.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name || p.fullName || p.title || p.id;
      sel.appendChild(opt);
    });
    sel.value = selectedId || '';
  }

  function fillForm(p) {
    $('name')  && ($('name').value = p.name ?? '');
    $('title') && ($('title').value = p.title ?? '');
    $('department') && ($('department').value = p.department ?? '');
    $('subdepartment') && ($('subdepartment').value = p.subdepartment ?? '');
    $('team') && ($('team').value = p.team ?? '');
    $('role') && ($('role').value = p.role ?? '');
    $('manager') && ($('manager').value = p.managerId ?? p.parentId ?? '');
  }

  function readForm() {
    return {
      id: personId || undefined,
      name: $('name')?.value?.trim() || '',
      title: $('title')?.value?.trim() || '',
      department: $('department')?.value?.trim() || '',
      subdepartment: $('subdepartment')?.value?.trim() || '',
      team: $('team')?.value?.trim() || '',
      role: $('role')?.value?.trim() || '',
      managerId: $('manager')?.value || null,
    };
  }

  // ---- Save flow ----
  async function savePerson(payload) {
    const tryEndpoints = [
      { url: `/api/people/${encodeURIComponent(payload.id || '')}`, method: payload.id ? 'PUT' : 'POST' },
      { url: `/api/people`, method: payload.id ? 'PUT' : 'POST' },
      { url: `/api/person/${encodeURIComponent(payload.id || '')}`, method: payload.id ? 'PUT' : 'POST' },
    ];
    let lastErr;
    for (const ep of tryEndpoints) {
      try {
        const u = addAdminKeyToUrl(ep.url);
        const res = await fetch(u, withAdminKeyOpts(ep.method, payload));
        if (res.ok) return await res.json().catch(() => ({}));
        if (res.status === 401 || res.status === 403) {
          const msg = await res.text();
          throw new Error(msg || `Unauthorized (${res.status})`);
        }
        lastErr = new Error(`${ep.method} ${ep.url} → ${res.status}`);
      } catch (e) { lastErr = e; }
    }
    throw lastErr || new Error('All save attempts failed');
  }

  // ---- Init (runs after DOM is ready) ----
  async function init() {
    // Wire admin key UI
    if ($('adminKey')) {
      // preload from localStorage
      $('adminKey').value = localStorage.getItem(LS_KEY) || '';
      reflectAdminKeyHint();

      $('btnSaveKey')?.addEventListener('click', () => {
        saveAdminKeyToLS();
        reflectAdminKeyHint();
        showToast('Admin key saved');
      });
      $('btnShowKey')?.addEventListener('click', () => {
        const i = $('adminKey'); if (!i) return;
        i.type = i.type === 'password' ? 'text' : 'password';
      });
    }

    // Load people and fill form/manager list
    let people = [];
    try {
      people = await loadPeople();
    } catch (e) {
      console.warn(e);
      $('hint') && ( $('hint').textContent = 'Could not load people list. You can still edit fields and try to save.' );
    }

    const current = personId ? people.find(p => String(p.id) === String(personId)) : null;
    fillManagerOptions(people.filter(p => !personId || String(p.id) !== String(personId)),
                       current?.managerId || current?.parentId || '');
    if (current) fillForm(current);

    // Save/Cancel handlers
    $('btnSave')?.addEventListener('click', async () => {
      try {
        const payload = readForm();
        if (!payload.name) { showToast('Name is required', false); return; }
        const saved = await savePerson(payload);
        showToast('Saved');
        if (!personId && saved && saved.id) {
          const u = new URL(location.href); u.searchParams.set('id', saved.id); history.replaceState({}, '', u);
        }
      } catch (e) {
        console.error(e);
        showToast(`Save failed: ${e.message}`, false);
      }
    });

    $('btnCancel')?.addEventListener('click', () => { location.href = '/admin'; });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
