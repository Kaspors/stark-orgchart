const params = new URLSearchParams(location.search);
const id = params.get('id');

function getAdminKey(){ return localStorage.getItem("ADMIN_KEY") || ""; }

let formEl;

async function loadPerson(){
  const res = await fetch('/api/people');
  if(!res.ok){ alert('Failed to load people'); return; }
  const all = await res.json();
  const me = all.find(p => p.id === id);
  if(!me){ alert('Person not found'); location.href='/admin'; return; }

  const managers = all.filter(p => p.id !== id);

  formEl.innerHTML = `
    <label>Name <input id="name" value="${esc(me.name)}"/></label>
    <label>Title <input id="title" value="${esc(me.title||'')}"/></label>
    <label>Department <input id="department" value="${esc(me.department||'')}"/></label>
    <label>Sub-department <input id="sub_department" value="${esc(me.sub_department||'')}"/></label>
    <label>Team <input id="team" value="${esc(me.team||'')}"/></label>
    <label>Role
      <select id="role">
        ${opt('', '(none)', !me.role)}
        ${opt('Head','Head', me.role==='Head')}
        ${opt('Director','Director', me.role==='Director')}
        ${opt('Senior Manager','Senior Manager', me.role==='Senior Manager')}
        ${opt('Manager','Manager', me.role==='Manager')}
        ${opt('Specialist','Specialist', me.role==='Specialist')}
      </select>
    </label>
    <label>Manager
      <select id="manager_id">
        ${opt('', '(none)', !me.manager_id)}
        ${managers.map(m => `<option value="${m.id}" ${m.id===me.manager_id?'selected':''}>${esc(m.name)}</option>`).join('')}
      </select>
    </label>
  `;

  document.getElementById('save').onclick = () => save(me.id);
  document.getElementById('cancel').onclick = () => history.back();
}

function esc(s){ return String(s ?? '').replace(/"/g,'&quot;'); }
function opt(v,t,sel){ return `<option value="${v}" ${sel?'selected':''}>${t}</option>`; }

async function save(pid){
  const payload = {
    name: document.getElementById('name').value.trim(),
    title: document.getElementById('title').value.trim() || null,
    department: document.getElementById('department').value.trim() || null,
    sub_department: document.getElementById('sub_department').value.trim() || null,
    team: document.getElementById('team').value.trim() || null,
    role: document.getElementById('role').value || null,
    manager_id: document.getElementById('manager_id').value || null
  };
  const res = await fetch(`/api/people/${pid}`, {
    method: 'PATCH',
    headers: { 'Content-Type':'application/json', 'x-admin-key': getAdminKey() },
    body: JSON.stringify(payload)
  });
  if(!res.ok){
    const txt = await res.text();
    alert(`Save failed: ${res.status}\n${txt}`);
    return;
  }
  location.href = '/admin';
}

window.addEventListener('DOMContentLoaded', ()=>{
  formEl = document.getElementById('form');
  loadPerson();
});
