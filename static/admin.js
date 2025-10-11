let adminKeyInput, fileInput, addBtn, uploadBtn, tableBody, managerSelect, roleSelect;
let people = [];

function getAdminKey(){ return localStorage.getItem("ADMIN_KEY") || ""; }
function setAdminKey(v){ localStorage.setItem("ADMIN_KEY", v || ""); }

async function fetchPeople(){
  try {
    const res = await fetch('/api/people');
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length >= 0) {
        people = data;
        return render();
      }
    }
  } catch (e) {
    console.warn('GET /api/people failed, will fall back to /api/tree', e);
  }

  try {
    const res2 = await fetch('/api/tree');
    if (!res2.ok) throw new Error(`HTTP ${res2.status}`);
    const nodes = await res2.json();
    people = nodes
      .filter(n => n.type === 'person')
      .map(n => ({
        id: n.id.replace(/^person:/,''),
        name: n.name || '',
        title: n.title || '',
        department: n.department || '',
        sub_department: n.sub_department || '',
        team: n.team || '',
        role: n.role || '',
        manager_id: null
      }));
    return render();
  } catch (e) {
    alert(`Failed to load people (both /api/people and /api/tree).\n${e}`);
  }
}

function render(){
  managerSelect.innerHTML = '<option value="">Manager (optional)</option>' +
    people.map(p => `<option value="${p.id}">${escapeHtml(p.name)}</option>`).join('');

  tableBody.innerHTML = people.map(p => {
    const mgr = people.find(x => x.id === p.manager_id);
    return `<tr>
      <td><a href="/edit.html?id=${encodeURIComponent(p.id)}" class="btn-link" style="padding:4px 8px">${escapeHtml(p.name)}</a></td>
      <td>${escapeHtml(p.title || "")}</td>
      <td>${escapeHtml(p.department || "")}</td>
      <td>${escapeHtml(p.sub_department || "")}</td>
      <td>${escapeHtml(p.team || "")}</td>
      <td>${escapeHtml(p.role || "")}</td>
      <td>${escapeHtml(mgr ? mgr.name : "")}</td>
      <td><button data-id="${p.id}" class="del">Delete</button></td>
    </tr>`;
  }).join('');

  document.querySelectorAll('.del').forEach(btn=>{
    btn.onclick = async () => {
      const id = btn.getAttribute('data-id');
      const ok = await api(`/api/people/${id}`, { method:'DELETE' });
      if(ok) fetchPeople();
    };
  });
}

function escapeHtml(s){
  return String(s ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
}

async function api(url, opt={}){
  const key = adminKeyInput.value.trim();
  setAdminKey(key);
  opt.headers = Object.assign({}, opt.headers||{}, { 'x-admin-key': key, 'Content-Type':'application/json' });
  const res = await fetch(url, opt);
  if(!res.ok){
    const text = await res.text().catch(()=>'(no body)');
    alert(`Error: ${res.status}\n${text}`);
    return null;
  }
  try { return await res.json(); } catch { return true; }
}

async function addPerson(){
  const payload = {
    name: document.getElementById('name').value.trim(),
    title: document.getElementById('title').value.trim() || null,
    department: document.getElementById('department').value.trim() || null,
    sub_department: document.getElementById('sub_department').value.trim() || null,
    team: document.getElementById('team').value.trim() || null,
    role: roleSelect.value || null,
    manager_id: managerSelect.value || null
  };
  if(!payload.name){ alert('Name required'); return; }
  const ok = await api('/api/people', { method:'POST', body: JSON.stringify(payload) });
  if(ok) fetchPeople();
}

async function uploadExcel(){
  const key = adminKeyInput.value.trim();
  setAdminKey(key);
  if(!fileInput.files.length){ alert('Choose an Excel file'); return; }
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  const res = await fetch('/api/upload-excel', { method:'POST', body: fd, headers: { 'x-admin-key': key } });
  if(!res.ok){
    const text = await res.text().catch(()=>'(no body)');
    alert(`Upload/import failed\nHTTP ${res.status}\n${text}`);
    return;
  }
  await res.json();
  fetchPeople();
}

window.addEventListener('DOMContentLoaded', ()=>{
  adminKeyInput = document.getElementById('adminKey');
  fileInput = document.getElementById('file');
  addBtn = document.getElementById('add');
  uploadBtn = document.getElementById('upload');
  tableBody = document.querySelector('#table tbody');
  managerSelect = document.getElementById('manager');
  roleSelect = document.getElementById('role');

  adminKeyInput.value = getAdminKey();

  addBtn.onclick = addPerson;
  uploadBtn.onclick = uploadExcel;

  fetchPeople();
});
