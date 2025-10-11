import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from .db import SessionLocal, init_db
from .models import Person, OrgUnit
from .schemas import PersonCreate, PersonUpdate, PersonOut, OrgUnitOut, TreeNode

ADMIN_KEY = os.getenv("ADMIN_KEY")

app = FastAPI(title="STARK Org Chart")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

init_db()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- Pages ----------
@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")

@app.get("/admin", include_in_schema=False)
def admin():
    return FileResponse("static/admin.html")

# NEW: serve the edit person page at /edit.html and /edit
@app.get("/edit.html", include_in_schema=False)
def edit_html():
    return FileResponse("static/edit.html")

@app.get("/edit", include_in_schema=False)
def edit_alias():
    return FileResponse("static/edit.html")

# ---------- Public APIs ----------
@app.get("/api/people", response_model=List[PersonOut])
def list_people(db: Session = Depends(get_db)):
    return db.query(Person).all()

@app.get("/api/orgunits", response_model=List[OrgUnitOut])
def list_units(db: Session = Depends(get_db)):
    units = db.query(OrgUnit).all()
    out: List[OrgUnitOut] = []
    for u in units:
        out.append(OrgUnitOut(
            id=u.id, name=u.name, level=u.level, parent_unit_id=u.parent_unit_id,
            manager_id=u.manager_id, manager_name=(u.manager.name if u.manager else None)
        ))
    return out

@app.get("/api/tree", response_model=List[TreeNode])
def get_tree(db: Session = Depends(get_db)):
    units = db.query(OrgUnit).all()
    people = db.query(Person).all()
    nodes: List[TreeNode] = []

    for u in units:
        nodes.append(TreeNode(
            id=f"unit:{u.id}",
            parentId=(f"unit:{u.parent_unit_id}" if u.parent_unit_id else None),
            type="unit",
            name=u.name,
            unit_level=u.level,
            manager_name=(u.manager.name if u.manager else None)
        ))

    for p in people:
        parent = None
        if p.org_unit_id:
            parent = f"unit:{p.org_unit_id}"
        elif p.manager_id:
            parent = f"person:{p.manager_id}"
        nodes.append(TreeNode(
            id=f"person:{p.id}",
            parentId=parent,
            type="person",
            name=p.name,
            title=p.title,
            department=p.department,
            sub_department=p.sub_department,
            team=p.team,
            role=p.role
        ))

    return nodes

# ---------- Admin protection ----------
def require_admin(x_admin_key: Optional[str] = Header(None)):
    if not ADMIN_KEY:
        raise HTTPException(500, "Server not configured: ADMIN_KEY missing")
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(401, "Invalid admin key")
    return True

from .excel_import import import_excel_replace

# ---------- Admin APIs ----------
@app.post("/api/upload-excel")
def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db), ok: bool = Depends(require_admin)):
    content = file.file.read()
    try:
        import_excel_replace(db, content)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(400, f"Import failed: {e}")

@app.post("/api/people", response_model=PersonOut)
def add_person(payload: PersonCreate, db: Session = Depends(get_db), ok: bool = Depends(require_admin)):
    p = Person(**payload.dict())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p

@app.patch("/api/people/{pid}", response_model=PersonOut)
def update_person(pid: str, payload: PersonUpdate, db: Session = Depends(get_db), ok: bool = Depends(require_admin)):
    p = db.get(Person, pid)
    if not p:
        raise HTTPException(404, "Not found")
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p

@app.delete("/api/people/{pid}")
def delete_person(pid: str, db: Session = Depends(get_db), ok: bool = Depends(require_admin)):
    p = db.get(Person, pid)
    if not p:
        raise HTTPException(404, "Not found")
    for r in p.reports:
        r.manager_id = None
    db.delete(p)
    db.commit()
    return {"status": "ok"}
