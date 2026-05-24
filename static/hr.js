/* ── State ─────────────────────────────────────────────────────────────────── */
const state = {
  employees: [],
  departments: [],
  scrumTeams: [],
  currentScrumTeam: null,
  editingEmpId: null,
  editingDeptId: null,
  editingScrumId: null,
  addMemberToTeamId: null,
};

/* ── Helpers ───────────────────────────────────────────────────────────────── */
function adminKey() {
  return document.getElementById("admin-key-input").value.trim();
}

async function api(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const key = adminKey();
  if (key) headers["x-admin-key"] = key;
  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

function toast(msg, isError = false) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = "show" + (isError ? " error" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { el.className = ""; }, 3000);
}

function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

document.querySelectorAll("[data-close]").forEach(btn => {
  btn.addEventListener("click", () => closeModal(btn.dataset.close));
});
document.querySelectorAll(".modal-backdrop").forEach(bd => {
  bd.addEventListener("click", e => { if (e.target === bd) bd.classList.remove("open"); });
});

function formToObj(form) {
  const fd = new FormData(form);
  const obj = {};
  for (const [k, v] of fd.entries()) obj[k] = v === "" ? null : v;
  return obj;
}

function fillSelect(sel, items, valueKey, labelKey, current) {
  const first = sel.options[0];
  sel.innerHTML = "";
  sel.appendChild(first);
  items.forEach(item => {
    const opt = document.createElement("option");
    opt.value = item[valueKey];
    opt.textContent = item[labelKey];
    if (item[valueKey] === current) opt.selected = true;
    sel.appendChild(opt);
  });
}

/* ── Badges ────────────────────────────────────────────────────────────────── */
const SENIORITY_BADGE = { Junior: "badge-blue", Mid: "badge-purple", Senior: "badge-orange", Lead: "badge-orange", Principal: "badge-orange", Staff: "badge-gray", Intern: "badge-gray" };
const STATUS_BADGE = { Active: "badge-green", "On Leave": "badge-yellow", Terminated: "badge-red" };
const LEVEL_BADGE = { department: "badge-orange", sub_department: "badge-blue", team: "badge-purple" };

function badge(text, cls) {
  if (!text) return "";
  return `<span class="badge ${cls || "badge-gray"}">${text}</span>`;
}

/* ── Navigation ────────────────────────────────────────────────────────────── */
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`sec-${btn.dataset.section}`).classList.add("active");
    if (btn.dataset.section === "dashboard") loadDashboard();
    if (btn.dataset.section === "employees") loadEmployees();
    if (btn.dataset.section === "departments") loadDepartments();
    if (btn.dataset.section === "scrum") loadScrumTeams();
    if (btn.dataset.section === "reports") loadReports();
  });
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* DASHBOARD                                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */
async function loadDashboard() {
  try {
    const data = await api("GET", "/api/reports/summary");
    document.getElementById("stat-total").textContent = data.total_employees;
    document.getElementById("stat-active").textContent = data.active_employees;
    document.getElementById("stat-depts").textContent = data.total_departments;
    document.getElementById("stat-scrums").textContent = data.total_scrum_teams;

    const charts = document.getElementById("dash-charts");
    charts.innerHTML = "";
    charts.appendChild(buildBarCard("By Department", data.by_department));
    charts.appendChild(buildBarCard("By Seniority", data.by_seniority));
    charts.appendChild(buildBarCard("By Employment Type", data.by_employment_type));
    charts.appendChild(buildBarCard("By Status", data.by_status));
  } catch (e) {
    console.error(e);
  }
}

function buildBarCard(title, rows) {
  const total = rows.reduce((s, r) => s + r.count, 0);
  const card = document.createElement("div");
  card.className = "report-card";
  card.innerHTML = `<h3>${title}</h3>` + rows.map(r => {
    const pct = total ? Math.round((r.count / total) * 100) : 0;
    return `<div class="report-bar-row">
      <div class="report-bar-label" title="${r.group}">${r.group}</div>
      <div class="report-bar-track"><div class="report-bar-fill" style="width:${pct}%"></div></div>
      <div class="report-bar-count">${r.count}</div>
    </div>`;
  }).join("");
  return card;
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* EMPLOYEES                                                                   */
/* ═══════════════════════════════════════════════════════════════════════════ */
async function loadEmployees(filters = {}) {
  const params = new URLSearchParams();
  const search = document.getElementById("emp-search").value.trim();
  const dept = document.getElementById("emp-filter-dept").value;
  const seniority = document.getElementById("emp-filter-seniority").value;
  const status = document.getElementById("emp-filter-status").value;
  if (search) params.set("search", search);
  if (dept) params.set("department", dept);
  if (seniority) params.set("seniority", seniority);
  if (status) params.set("status", status);

  try {
    state.employees = await api("GET", `/api/employees?${params}`);
    document.getElementById("emp-count").textContent = `${state.employees.length} employee${state.employees.length !== 1 ? "s" : ""}`;
    renderEmployeeTable();
    populateDeptFilter();
  } catch (e) {
    toast("Failed to load employees: " + e.message, true);
  }
}

function renderEmployeeTable() {
  const tbody = document.getElementById("emp-tbody");
  if (!state.employees.length) {
    tbody.innerHTML = `<tr><td colspan="10"><div class="empty-state"><div class="icon">👥</div><p>No employees found</p></div></td></tr>`;
    return;
  }
  tbody.innerHTML = state.employees.map(e => {
    const teams = (e.scrum_teams || []).map(t =>
      `<span class="tag" title="${t.role_in_team || ""}">${t.scrum_team_name}</span>`
    ).join("");
    return `<tr>
      <td><strong>${e.name}</strong></td>
      <td>${e.employee_number || "<span style='color:#ccc'>—</span>"}</td>
      <td>${e.title || ""}</td>
      <td>${e.department || ""}</td>
      <td>${e.manager_name || ""}</td>
      <td>${badge(e.seniority, SENIORITY_BADGE[e.seniority])}</td>
      <td>${e.employment_type || ""}</td>
      <td>${badge(e.status || "Active", STATUS_BADGE[e.status || "Active"])}</td>
      <td><div class="tags">${teams}</div></td>
      <td><div class="row-actions">
        <button class="btn btn-sm btn-secondary btn-icon" onclick="editEmployee('${e.id}')" title="Edit">✏️</button>
        <button class="btn btn-sm btn-danger btn-icon" onclick="deleteEmployee('${e.id}','${e.name.replace(/'/g,"\\'")}'')" title="Delete">🗑</button>
      </div></td>
    </tr>`;
  }).join("");
}

function populateDeptFilter() {
  const depts = [...new Set(state.employees.map(e => e.department).filter(Boolean))].sort();
  const sel = document.getElementById("emp-filter-dept");
  const cur = sel.value;
  sel.innerHTML = `<option value="">All Departments</option>` +
    depts.map(d => `<option${d === cur ? " selected" : ""}>${d}</option>`).join("");

  // Also fill datalist for department input in modal
  const dl = document.getElementById("dept-list");
  if (dl) dl.innerHTML = depts.map(d => `<option value="${d}">`).join("");
}

["emp-search", "emp-filter-dept", "emp-filter-seniority", "emp-filter-status"].forEach(id => {
  document.getElementById(id).addEventListener("input", () => loadEmployees());
});

/* ── Add/Edit Employee ─────────────────────────────────────────────────────── */
document.getElementById("btn-add-employee").addEventListener("click", () => openEmployeeModal(null));

async function openEmployeeModal(emp) {
  state.editingEmpId = emp ? emp.id : null;
  document.getElementById("modal-emp-title").textContent = emp ? "Edit Employee" : "Add Employee";
  const form = document.getElementById("form-employee");
  form.reset();

  // Populate selects
  await loadDropdowns();
  fillSelect(
    form.querySelector("[name=manager_id]"), state.employees.filter(e => !emp || e.id !== emp.id),
    "id", "name", emp?.manager_id
  );
  fillSelect(
    form.querySelector("[name=org_unit_id]"), state.departments,
    "id", e => `${e.name} (${e.level})`, emp?.org_unit_id
  );

  if (emp) {
    const fields = ["name","employee_number","email","phone","title","department","sub_department","team",
      "role","seniority","employment_type","status","location","cost_center","start_date","end_date"];
    fields.forEach(f => {
      const el = form.querySelector(`[name=${f}]`);
      if (el && emp[f] != null) el.value = emp[f];
    });
    const mgSel = form.querySelector("[name=manager_id]");
    if (mgSel && emp.manager_id) mgSel.value = emp.manager_id;
    const ouSel = form.querySelector("[name=org_unit_id]");
    if (ouSel && emp.org_unit_id) ouSel.value = emp.org_unit_id;
  }
  openModal("modal-employee");
}

async function editEmployee(id) {
  try {
    const emp = await api("GET", `/api/employees/${id}`);
    openEmployeeModal(emp);
  } catch (e) { toast(e.message, true); }
}

document.getElementById("btn-save-employee").addEventListener("click", async () => {
  const form = document.getElementById("form-employee");
  if (!form.reportValidity()) return;
  const payload = formToObj(form);
  try {
    if (state.editingEmpId) {
      await api("PATCH", `/api/employees/${state.editingEmpId}`, payload);
      toast("Employee updated");
    } else {
      await api("POST", "/api/employees", payload);
      toast("Employee added");
    }
    closeModal("modal-employee");
    loadEmployees();
  } catch (e) { toast(e.message, true); }
});

async function deleteEmployee(id, name) {
  if (!confirm(`Delete ${name}? This cannot be undone.`)) return;
  try {
    await api("DELETE", `/api/employees/${id}`);
    toast("Employee deleted");
    loadEmployees();
  } catch (e) { toast(e.message, true); }
}

async function loadDropdowns() {
  if (!state.departments.length) {
    state.departments = await api("GET", "/api/departments").catch(() => []);
  }
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* DEPARTMENTS                                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */
async function loadDepartments() {
  try {
    state.departments = await api("GET", "/api/departments");
    renderDeptTable();
  } catch (e) { toast("Failed to load departments: " + e.message, true); }
}

function renderDeptTable() {
  const tbody = document.getElementById("dept-tbody");
  if (!state.departments.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty-state"><div class="icon">🏢</div><p>No org units defined</p></div></td></tr>`;
    return;
  }
  const unitMap = Object.fromEntries(state.departments.map(d => [d.id, d.name]));
  tbody.innerHTML = state.departments.map(d => `<tr>
    <td><strong>${d.name}</strong></td>
    <td>${badge(d.level, LEVEL_BADGE[d.level])}</td>
    <td>${d.parent_unit_id ? (unitMap[d.parent_unit_id] || d.parent_unit_id) : "<span style='color:#ccc'>—</span>"}</td>
    <td>${d.manager_name || "<span style='color:#ccc'>—</span>"}</td>
    <td>${d.member_count}</td>
    <td><div class="row-actions">
      <button class="btn btn-sm btn-secondary btn-icon" onclick="editDept('${d.id}')" title="Edit">✏️</button>
      <button class="btn btn-sm btn-danger btn-icon" onclick="deleteDept('${d.id}','${d.name.replace(/'/g,"\\'")}'')" title="Delete">🗑</button>
    </div></td>
  </tr>`).join("");
}

document.getElementById("btn-add-dept").addEventListener("click", () => openDeptModal(null));

async function openDeptModal(dept) {
  state.editingDeptId = dept ? dept.id : null;
  document.getElementById("modal-dept-title").textContent = dept ? "Edit Org Unit" : "Add Org Unit";
  const form = document.getElementById("form-dept");
  form.reset();

  await loadDropdowns();
  const employees = state.employees.length ? state.employees : await api("GET", "/api/employees").catch(() => []);

  fillSelect(form.querySelector("[name=parent_unit_id]"),
    state.departments.filter(d => !dept || d.id !== dept.id),
    "id", d => `${d.name} (${d.level})`, dept?.parent_unit_id);
  fillSelect(form.querySelector("[name=manager_id]"), employees, "id", "name", dept?.manager_id);

  if (dept) {
    ["name", "level"].forEach(f => {
      const el = form.querySelector(`[name=${f}]`);
      if (el) el.value = dept[f] || "";
    });
    if (dept.parent_unit_id) form.querySelector("[name=parent_unit_id]").value = dept.parent_unit_id;
    if (dept.manager_id) form.querySelector("[name=manager_id]").value = dept.manager_id;
  }
  openModal("modal-dept");
}

async function editDept(id) {
  const d = state.departments.find(x => x.id === id);
  if (d) openDeptModal(d);
}

document.getElementById("btn-save-dept").addEventListener("click", async () => {
  const form = document.getElementById("form-dept");
  if (!form.reportValidity()) return;
  const payload = formToObj(form);
  try {
    if (state.editingDeptId) {
      await api("PATCH", `/api/departments/${state.editingDeptId}`, payload);
      toast("Org unit updated");
    } else {
      await api("POST", "/api/departments", payload);
      toast("Org unit added");
    }
    closeModal("modal-dept");
    state.departments = [];
    loadDepartments();
  } catch (e) { toast(e.message, true); }
});

async function deleteDept(id, name) {
  if (!confirm(`Delete "${name}"? Members will be unassigned.`)) return;
  try {
    await api("DELETE", `/api/departments/${id}`);
    toast("Org unit deleted");
    state.departments = [];
    loadDepartments();
  } catch (e) { toast(e.message, true); }
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* SCRUM TEAMS                                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */
async function loadScrumTeams() {
  try {
    state.scrumTeams = await api("GET", "/api/scrum-teams");
    renderScrumGrid();
  } catch (e) { toast("Failed to load scrum teams: " + e.message, true); }
}

function renderScrumGrid() {
  const grid = document.getElementById("scrum-grid");
  if (!state.scrumTeams.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="icon">🏃</div><p>No scrum teams yet — create one!</p></div>`;
    return;
  }
  grid.innerHTML = state.scrumTeams.map(t => `
    <div class="scrum-card" onclick="viewScrumTeam('${t.id}')">
      <div class="scrum-card-header">
        <div class="scrum-card-name">${t.name}</div>
        <span class="badge badge-blue">${t.member_count} member${t.member_count !== 1 ? "s" : ""}</span>
      </div>
      <div class="scrum-card-desc">${t.description || "<em style='color:#ccc'>No description</em>"}</div>
      <div class="scrum-card-meta">
        <span>PO: <strong>${t.product_owner_name || "—"}</strong></span>
        <span>SM: <strong>${t.scrum_master_name || "—"}</strong></span>
      </div>
      <div class="scrum-card-actions" onclick="event.stopPropagation()">
        <button class="btn btn-sm btn-secondary" onclick="editScrum('${t.id}')">Edit</button>
        <button class="btn btn-sm btn-danger" onclick="deleteScrum('${t.id}','${t.name.replace(/'/g,"\\'")}')">Delete</button>
      </div>
    </div>
  `).join("");
}

async function viewScrumTeam(id) {
  try {
    const team = await api("GET", `/api/scrum-teams/${id}`);
    state.currentScrumTeam = team;
    renderScrumDetail(team);
    document.getElementById("scrum-list-view").style.display = "none";
    document.getElementById("scrum-detail-view").style.display = "";
    document.getElementById("btn-scrum-list-view").style.display = "";
    document.getElementById("btn-add-scrum").style.display = "none";
  } catch (e) { toast(e.message, true); }
}

function renderScrumDetail(team) {
  const roleCounts = {};
  (team.members || []).forEach(m => {
    const r = m.role_in_team || "Other";
    roleCounts[r] = (roleCounts[r] || 0) + 1;
  });

  const roleChips = Object.entries(roleCounts)
    .map(([r, c]) => `<span class="badge badge-blue">${r}: ${c}</span>`)
    .join(" ");

  const seniorityCounts = {};
  (team.members || []).forEach(m => {
    const s = m.seniority || "Unspecified";
    seniorityCounts[s] = (seniorityCounts[s] || 0) + 1;
  });

  const memberRows = (team.members || []).map(m => `
    <tr>
      <td><strong>${m.person_name}</strong></td>
      <td>${m.employee_number || ""}</td>
      <td>${m.title || ""}</td>
      <td>${badge(m.seniority, SENIORITY_BADGE[m.seniority])}</td>
      <td>${badge(m.role_in_team, "badge-blue")}</td>
      <td><div class="row-actions">
        <button class="btn btn-sm btn-danger btn-icon" onclick="removeMember('${team.id}','${m.person_id}','${m.person_name.replace(/'/g,"\\'")}')">🗑</button>
      </div></td>
    </tr>
  `).join("");

  document.getElementById("scrum-detail-view").innerHTML = `
    <div class="team-detail-header">
      <h2>${team.name}</h2>
      <p>${team.description || ""}</p>
    </div>
    <div style="display:flex;gap:24px;margin-bottom:18px;flex-wrap:wrap">
      <div><span style="font-size:12px;color:#6b7280">Product Owner</span><br><strong>${team.product_owner_name || "—"}</strong></div>
      <div><span style="font-size:12px;color:#6b7280">Scrum Master</span><br><strong>${team.scrum_master_name || "—"}</strong></div>
      <div><span style="font-size:12px;color:#6b7280">Total Members</span><br><strong>${team.member_count}</strong></div>
    </div>
    <div class="team-roles-summary">${roleChips}</div>
    <div class="page-header" style="margin-bottom:12px">
      <div class="page-title" style="font-size:15px">Members</div>
      <div class="page-header-actions">
        <button class="btn btn-primary btn-sm" onclick="openAddMemberModal('${team.id}')">+ Add Member</button>
      </div>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Name</th><th>Emp #</th><th>Title</th><th>Seniority</th><th>Team Role</th><th></th></tr></thead>
        <tbody>${memberRows || `<tr><td colspan="6"><div class="empty-state"><p>No members yet</p></div></td></tr>`}</tbody>
      </table>
    </div>
  `;
}

document.getElementById("btn-scrum-list-view").addEventListener("click", () => {
  document.getElementById("scrum-list-view").style.display = "";
  document.getElementById("scrum-detail-view").style.display = "none";
  document.getElementById("btn-scrum-list-view").style.display = "none";
  document.getElementById("btn-add-scrum").style.display = "";
  state.currentScrumTeam = null;
});

document.getElementById("btn-add-scrum").addEventListener("click", () => openScrumModal(null));

async function openScrumModal(team) {
  state.editingScrumId = team ? team.id : null;
  document.getElementById("modal-scrum-title").textContent = team ? "Edit Scrum Team" : "New Scrum Team";
  const form = document.getElementById("form-scrum");
  form.reset();

  const employees = state.employees.length ? state.employees : await api("GET", "/api/employees").catch(() => []);
  fillSelect(form.querySelector("[name=product_owner_id]"), employees, "id", "name", team?.product_owner_id);
  fillSelect(form.querySelector("[name=scrum_master_id]"), employees, "id", "name", team?.scrum_master_id);

  if (team) {
    ["name", "description"].forEach(f => {
      const el = form.querySelector(`[name=${f}]`);
      if (el && team[f]) el.value = team[f];
    });
    if (team.product_owner_id) form.querySelector("[name=product_owner_id]").value = team.product_owner_id;
    if (team.scrum_master_id) form.querySelector("[name=scrum_master_id]").value = team.scrum_master_id;
  }
  openModal("modal-scrum");
}

async function editScrum(id) {
  try {
    const team = await api("GET", `/api/scrum-teams/${id}`);
    openScrumModal(team);
  } catch (e) { toast(e.message, true); }
}

document.getElementById("btn-save-scrum").addEventListener("click", async () => {
  const form = document.getElementById("form-scrum");
  if (!form.reportValidity()) return;
  const payload = formToObj(form);
  try {
    if (state.editingScrumId) {
      await api("PATCH", `/api/scrum-teams/${state.editingScrumId}`, payload);
      toast("Team updated");
    } else {
      await api("POST", "/api/scrum-teams", payload);
      toast("Team created");
    }
    closeModal("modal-scrum");
    loadScrumTeams();
  } catch (e) { toast(e.message, true); }
});

async function deleteScrum(id, name) {
  if (!confirm(`Delete team "${name}"? Members will be removed from the team.`)) return;
  try {
    await api("DELETE", `/api/scrum-teams/${id}`);
    toast("Team deleted");
    loadScrumTeams();
    document.getElementById("scrum-list-view").style.display = "";
    document.getElementById("scrum-detail-view").style.display = "none";
    document.getElementById("btn-scrum-list-view").style.display = "none";
    document.getElementById("btn-add-scrum").style.display = "";
  } catch (e) { toast(e.message, true); }
}

/* ── Add member ────────────────────────────────────────────────────────────── */
async function openAddMemberModal(teamId) {
  state.addMemberToTeamId = teamId;
  const form = document.getElementById("form-member");
  form.reset();
  const employees = state.employees.length ? state.employees : await api("GET", "/api/employees").catch(() => []);
  fillSelect(form.querySelector("[name=person_id]"), employees, "id", "name", null);
  openModal("modal-member");
}

document.getElementById("btn-save-member").addEventListener("click", async () => {
  const form = document.getElementById("form-member");
  if (!form.reportValidity()) return;
  const payload = formToObj(form);
  try {
    await api("POST", `/api/scrum-teams/${state.addMemberToTeamId}/members`, payload);
    toast("Member added");
    closeModal("modal-member");
    viewScrumTeam(state.addMemberToTeamId);
    loadScrumTeams();
  } catch (e) { toast(e.message, true); }
});

async function removeMember(teamId, personId, name) {
  if (!confirm(`Remove ${name} from this team?`)) return;
  try {
    await api("DELETE", `/api/scrum-teams/${teamId}/members/${personId}`);
    toast("Member removed");
    viewScrumTeam(teamId);
    loadScrumTeams();
  } catch (e) { toast(e.message, true); }
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/* REPORTS                                                                      */
/* ═══════════════════════════════════════════════════════════════════════════ */
let activeReport = "org";

document.querySelectorAll("[data-report]").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("[data-report]").forEach(b => b.classList.remove("active-report"));
    btn.classList.add("active-report");
    ["org", "scrum-teams", "managers"].forEach(r => {
      document.getElementById(`report-${r}`).style.display = r === btn.dataset.report ? "" : "none";
    });
    activeReport = btn.dataset.report;
  });
});

async function loadReports() {
  loadOrgReport();
  loadScrumReport();
  loadManagerReport();
}

async function loadOrgReport() {
  const el = document.getElementById("report-org");
  try {
    const data = await api("GET", "/api/reports/org-structure");
    const byLevel = { department: [], sub_department: [], team: [] };
    data.units.forEach(u => (byLevel[u.level] || []).push(u));

    let html = `<div class="report-grid">`;
    html += buildBarCard("Headcount by Department",
      byLevel.department.map(d => ({ group: d.name, count: d.member_count }))
    ).outerHTML;

    html += `</div>`;

    // Hierarchy table
    html += `<div class="table-wrap" style="margin-bottom:24px"><table>
      <thead><tr><th>Unit Name</th><th>Level</th><th>Manager</th><th>Members</th></tr></thead>
      <tbody>`;
    ["department","sub_department","team"].forEach(lvl => {
      byLevel[lvl].forEach(u => {
        html += `<tr>
          <td style="padding-left:${lvl==='department'?14:lvl==='sub_department'?28:42}px">
            ${lvl==='team'?'↳ ':lvl==='sub_department'?'· ':''}${u.name}
          </td>
          <td>${badge(lvl, LEVEL_BADGE[lvl])}</td>
          <td>${u.manager_name || "—"}</td>
          <td>${u.member_count}</td>
        </tr>`;
      });
    });
    html += `</tbody></table></div>`;

    html += `<p style="color:#9ca3af;font-size:12px">${data.unassigned_employees} employee(s) not assigned to any org unit.</p>`;
    el.innerHTML = html;
  } catch (e) { el.innerHTML = `<p style="color:red">Error: ${e.message}</p>`; }
}

async function loadScrumReport() {
  const el = document.getElementById("report-scrum-teams");
  try {
    const data = await api("GET", "/api/reports/scrum-teams");
    if (!data.length) {
      el.innerHTML = `<div class="empty-state"><div class="icon">🏃</div><p>No scrum teams</p></div>`;
      return;
    }
    let html = "";
    data.forEach(team => {
      const memberRows = team.members.map(m => `
        <tr>
          <td>${m.person_name}</td>
          <td>${m.employee_number || ""}</td>
          <td>${m.title || ""}</td>
          <td>${badge(m.seniority, SENIORITY_BADGE[m.seniority])}</td>
          <td>${badge(m.role_in_team, "badge-blue")}</td>
        </tr>
      `).join("");

      const roleBreakdown = team.by_role.map(r =>
        `<span class="badge badge-blue">${r.group}: ${r.count}</span>`
      ).join(" ");
      const senBreakdown = team.by_seniority.map(s =>
        `<span class="badge ${SENIORITY_BADGE[s.group] || 'badge-gray'}">${s.group}: ${s.count}</span>`
      ).join(" ");

      html += `
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:20px;margin-bottom:20px">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
            <div>
              <div style="font-size:16px;font-weight:700">${team.team_name}</div>
              <div style="color:#6b7280;font-size:13px">${team.description || ""}</div>
            </div>
            <span class="badge badge-blue">${team.total_members} members</span>
          </div>
          <div style="display:flex;gap:20px;margin-bottom:12px;font-size:13px">
            <span>PO: <strong>${team.product_owner || "—"}</strong></span>
            <span>SM: <strong>${team.scrum_master || "—"}</strong></span>
          </div>
          <div style="margin-bottom:8px;display:flex;gap:6px;flex-wrap:wrap">${roleBreakdown}</div>
          <div style="margin-bottom:12px;display:flex;gap:6px;flex-wrap:wrap">${senBreakdown}</div>
          <div class="table-wrap"><table>
            <thead><tr><th>Name</th><th>Emp #</th><th>Title</th><th>Seniority</th><th>Team Role</th></tr></thead>
            <tbody>${memberRows || '<tr><td colspan="5" style="color:#9ca3af;text-align:center">No members</td></tr>'}</tbody>
          </table></div>
        </div>
      `;
    });
    el.innerHTML = html;
  } catch (e) { el.innerHTML = `<p style="color:red">Error: ${e.message}</p>`; }
}

async function loadManagerReport() {
  const el = document.getElementById("report-managers");
  try {
    const data = await api("GET", "/api/reports/managers");
    if (!data.length) {
      el.innerHTML = `<div class="empty-state"><div class="icon">👤</div><p>No managers found</p></div>`;
      return;
    }
    let html = "";
    data.forEach(mgr => {
      const repRows = mgr.reports.map(r => `
        <tr>
          <td>${r.name}</td>
          <td>${r.title || ""}</td>
          <td>${badge(r.seniority, SENIORITY_BADGE[r.seniority])}</td>
        </tr>
      `).join("");
      html += `
        <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:20px;margin-bottom:16px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
            <div>
              <strong style="font-size:15px">${mgr.name}</strong>
              <span style="color:#6b7280;font-size:13px;margin-left:8px">${mgr.title || ""}</span>
              <span style="color:#9ca3af;font-size:12px;margin-left:8px">${mgr.department || ""}</span>
            </div>
            <span class="badge badge-purple">${mgr.direct_reports} direct report${mgr.direct_reports !== 1 ? "s" : ""}</span>
          </div>
          <div class="table-wrap"><table>
            <thead><tr><th>Report</th><th>Title</th><th>Seniority</th></tr></thead>
            <tbody>${repRows}</tbody>
          </table></div>
        </div>
      `;
    });
    el.innerHTML = html;
  } catch (e) { el.innerHTML = `<p style="color:red">Error: ${e.message}</p>`; }
}

/* ── Report tab btn style ───────────────────────────────────────────────────── */
document.querySelectorAll("[data-report]").forEach(btn => {
  btn.style.cssText = "";
});

/* ═══════════════════════════════════════════════════════════════════════════ */
/* INIT                                                                         */
/* ═══════════════════════════════════════════════════════════════════════════ */
loadDashboard();
