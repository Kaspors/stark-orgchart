from __future__ import annotations
import pandas as pd
import re
from io import BytesIO
from sqlalchemy.orm import Session
from .models import Person, OrgUnit

ALLOWED_ROLES = {
    "head": "Head",
    "headoffunction": "Head",
    "director": "Director",
    "srmanager": "Senior Manager",
    "senior manager": "Senior Manager",
    "senior_manager": "Senior Manager",
    "manager": "Manager",
    "specialist": "Specialist",
    "individualcontributor": "Specialist",
}

def _norm(s: str) -> str:
    return re.sub(r"[\W_]+", "", s.strip().lower())

def _find_col(cols, candidates):
    normcols = { _norm(str(c)): str(c) for c in cols }
    for cand in candidates:
        if cand in normcols:
            return normcols[cand]
    return None

def _get_or_create_unit(db: Session, cache: dict, name: str, level: str, parent: OrgUnit | None):
    name = name.strip()
    key = (level, name.lower(), parent.id if parent else None)
    if key in cache:
        return cache[key]
    u = OrgUnit(name=name, level=level, parent=parent)
    db.add(u)
    db.flush()
    cache[key] = u
    return u

def _normalize_role(x) -> str | None:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s:
        return None
    k = _norm(s)
    return ALLOWED_ROLES.get(k, None)

def import_excel_replace(db: Session, file_bytes: bytes):
    df = pd.read_excel(BytesIO(file_bytes))

    name_col  = _find_col(df.columns, ["name","fullname","navn"]) or "Name"
    mgr_col   = _find_col(df.columns, ["manager","peopleleader","leder","managername"]) or "Manager"
    dept_col  = _find_col(df.columns, ["department","function","funktion","afdeling"]) or "Department"
    subd_col  = _find_col(df.columns, ["subdepartment","sub-department","subdept","subdep","subfunction","businessunit","bu","area","division","subafdeling"]) or "SubDepartment"
    team_col  = _find_col(df.columns, ["team","squad"]) or "Team"
    title_col = _find_col(df.columns, ["title","jobtitle","newjobtitle","role_title","role","stilling"]) or "Title"
    role_col  = _find_col(df.columns, ["tag","level","role","seniority","managementlevel","positionlevel","peoplelevel","orgrole"])

    dept_mgr_col = _find_col(df.columns, ["departmentmanager","deptmanager","departmenthead","headdepartment"])
    subd_mgr_col = _find_col(df.columns, ["subdepartmentmanager","subdeptmanager","subdepartmenthead","headsubdepartment"])
    team_mgr_col = _find_col(df.columns, ["teammanager","squadmanager","teamlead","teamleader"])

    if name_col not in df.columns:
        raise ValueError("Excel must contain a Name column")

    db.query(Person).delete()
    db.query(OrgUnit).delete()
    db.flush()

    staged_people = []
    for _, r in df.iterrows():
        name = str(r.get(name_col)).strip() if pd.notna(r.get(name_col)) else None
        if not name:
            continue
        p = Person(
            name=name,
            title=(str(r.get(title_col)).strip() if title_col in df.columns and pd.notna(r.get(title_col)) else None),
            department=(str(r.get(dept_col)).strip() if dept_col in df.columns and pd.notna(r.get(dept_col)) else None),
            sub_department=(str(r.get(subd_col)).strip() if subd_col in df.columns and pd.notna(r.get(subd_col)) else None),
            team=(str(r.get(team_col)).strip() if team_col in df.columns and pd.notna(r.get(team_col)) else None),
            role=_normalize_role(r.get(role_col)) if role_col else None,
        )
        db.add(p)
        staged_people.append((
            p,
            str(r.get(mgr_col)).strip() if mgr_col in df.columns and pd.notna(r.get(mgr_col)) else None,
            str(r.get(dept_mgr_col)).strip() if dept_mgr_col and pd.notna(r.get(dept_mgr_col)) else None,
            str(r.get(subd_mgr_col)).strip() if subd_mgr_col and pd.notna(r.get(subd_mgr_col)) else None,
            str(r.get(team_mgr_col)).strip() if team_mgr_col and pd.notna(r.get(team_mgr_col)) else None,
        ))

    db.flush()

    name_to_id = {}
    for p, *_ in staged_people:
        if p.name not in name_to_id:
            name_to_id[p.name] = p.id
    lower_map = { k.lower(): v for k, v in name_to_id.items() }

    unit_cache: dict[tuple, OrgUnit] = {}
    for p, _, _, _, _ in staged_people:
        dept = (p.department or "").strip()
        subd = (p.sub_department or "").strip()
        team = (p.team or "").strip()

        parent_unit = None
        if dept:
            parent_unit = _get_or_create_unit(db, unit_cache, dept, "department", None)
        if subd:
            parent_unit = _get_or_create_unit(db, unit_cache, subd, "sub_department", parent_unit)
        if team:
            parent_unit = _get_or_create_unit(db, unit_cache, team, "team", parent_unit)

        if parent_unit:
            p.org_unit_id = parent_unit.id

    db.flush()

    for p, mgr_name, *_ in staged_people:
        if not mgr_name:
            continue
        pid = name_to_id.get(mgr_name) or lower_map.get(mgr_name.lower())
        if pid and pid != p.id:
            p.manager_id = pid

    db.flush()

    for p, _mgr, dept_mgr_name, subd_mgr_name, team_mgr_name in staged_people:
        def resolve(name: str | None) -> str | None:
            if not name: return None
            return name_to_id.get(name) or lower_map.get(name.lower())

        if p.department and dept_mgr_name:
            u = _get_or_create_unit(db, unit_cache, p.department.strip(), "department", None)
            rid = resolve(dept_mgr_name)
            if rid: u.manager_id = rid

        if p.department and p.sub_department and subd_mgr_name:
            parent = _get_or_create_unit(db, unit_cache, p.department.strip(), "department", None)
            u = _get_or_create_unit(db, unit_cache, p.sub_department.strip(), "sub_department", parent)
            rid = resolve(subd_mgr_name)
            if rid: u.manager_id = rid

        if p.team and team_mgr_name:
            parent = None
            if p.department:
                parent = _get_or_create_unit(db, unit_cache, p.department.strip(), "department", None)
            if p.sub_department:
                parent = _get_or_create_unit(db, unit_cache, p.sub_department.strip(), "sub_department", parent)
            u = _get_or_create_unit(db, unit_cache, p.team.strip(), "team", parent)
            rid = resolve(team_mgr_name)
            if rid: u.manager_id = rid

    db.commit()
