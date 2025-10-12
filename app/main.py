from __future__ import annotations
import os, json, uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ------------- load .env early -------------
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass  # ok if not present; env may already be set

# ------------- config / paths -------------
ADMIN_KEY = os.getenv("ADMIN_KEY", "stark123")

DB_URL = (
    os.getenv("DATABASE_URL")
    or os.getenv("NEON_DATABASE_URL")
    or os.getenv("DB_URL")
    or ""
).strip()

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"     # your frontend is in ./static
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CANON_JSON = DATA_DIR / "people.json"

app = FastAPI(title="STARK Org Chart")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# ============ admin key helpers ============
def _extract_admin_key(request: Request, body: Optional[Dict[str, Any]] = None) -> str:
    key = request.headers.get("X-Admin-Key") or request.query_params.get("adminKey")
    if not key and isinstance(body, dict):
        key = body.get("adminKey")
    return (key or "").strip()

def _require_admin(request: Request, body: Optional[Dict[str, Any]] = None) -> None:
    key = _extract_admin_key(request, body)
    if ADMIN_KEY and key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: invalid admin key")

# ============ storage: Postgres (Neon) or JSON fallback ============
USING_PG = bool(DB_URL)

if USING_PG:
    import psycopg
    from psycopg.rows import dict_row

    def _pg_dsn() -> str:
        dsn = DB_URL
        # Ensure sslmode=require (Neon)
        if "sslmode=" not in dsn:
            dsn += "&sslmode=require" if "?" in dsn else "?sslmode=require"
        return dsn

    def _pg_connect():
        return psycopg.connect(_pg_dsn(), row_factory=dict_row)

    def _pg_init():
        # Create table and add missing columns if needed
        with _pg_connect() as conn, conn.cursor() as cur:
            cur.execute("""
                create table if not exists people (
                    id             text primary key,
                    name           text not null,
                    title          text default '',
                    department     text default '',
                    subdepartment  text default '',
                    team           text default '',
                    role           text default '',
                    manager_id     text
                )
            """)
            # Add columns if they don't exist (safe on repeat)
            cur.execute("alter table if exists people add column if not exists title text default ''")
            cur.execute("alter table if exists people add column if not exists department text default ''")
            cur.execute("alter table if exists people add column if not exists subdepartment text default ''")
            cur.execute("alter table if exists people add column if not exists team text default ''")
            cur.execute("alter table if exists people add column if not exists role text default ''")
            cur.execute("alter table if exists people add column if not exists manager_id text")
            conn.commit()

    def pg_list() -> List[Dict[str, Any]]:
        with _pg_connect() as conn, conn.cursor() as cur:
            cur.execute("select * from people order by name")
            return list(cur.fetchall())

    def pg_get(pid: str) -> Dict[str, Any]:
        with _pg_connect() as conn, conn.cursor() as cur:
            cur.execute("select * from people where id=%s", (pid,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Not found")
            return row

    def pg_create(payload: Dict[str, Any]) -> Dict[str, Any]:
        data = dict(payload)
        data.pop("adminKey", None)
        if not data.get("name"):
            raise HTTPException(status_code=400, detail="Name is required")
        if not data.get("id"):
            data["id"] = str(uuid.uuid4())
        if "parentId" in data and not data.get("managerId"):
            data["managerId"] = data["parentId"]

        with _pg_connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                insert into people (id, name, title, department, subdepartment, team, role, manager_id)
                values (%s,%s,%s,%s,%s,%s,%s,%s)
                returning *
                """,
                (
                    data["id"],
                    data.get("name", ""),
                    data.get("title", ""),
                    data.get("department", ""),
                    data.get("subdepartment", ""),
                    data.get("team", ""),
                    data.get("role", ""),
                    data.get("managerId"),
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return row

    def pg_update(pid: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        existing = pg_get(pid)
        merged = {**existing, **payload}
        merged.pop("adminKey", None)
        merged["id"] = pid
        if "parentId" in merged and not merged.get("managerId"):
            merged["managerId"] = merged["parentId"]

        with _pg_connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                update people
                   set name=%s, title=%s, department=%s, subdepartment=%s, team=%s, role=%s, manager_id=%s
                 where id=%s
                 returning *
                """,
                (
                    merged.get("name", ""),
                    merged.get("title", ""),
                    merged.get("department", ""),
                    merged.get("subdepartment", ""),
                    merged.get("team", ""),
                    merged.get("role", ""),
                    merged.get("managerId"),
                    pid,
                ),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Not found")
            conn.commit()
            return row

    def pg_delete(pid: str) -> None:
        with _pg_connect() as conn, conn.cursor() as cur:
            cur.execute("select 1 from people where manager_id=%s limit 1", (pid,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Cannot delete: person has direct reports")
            cur.execute("delete from people where id=%s", (pid,))
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Not found")
            conn.commit()

    # Initialize DB at import
    try:
        _pg_init()
        print("[orgchart] Using Postgres:", DB_URL.split('@')[-1].split('?')[0])
    except Exception as e:
        print("[orgchart] Postgres init failed:", repr(e))
        USING_PG = False  # fallback to JSON if init fails

# ---- JSON fallback (dev only) ----
def json_load() -> List[Dict[str, Any]]:
    if CANON_JSON.exists():
        try:
            with CANON_JSON.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    seed = [
        {"id": "1", "name": "Morten S.", "title": "Head of Architecture", "managerId": None},
        {"id": "2", "name": "João",      "title": "Engineer",             "managerId": "1"},
        {"id": "3", "name": "Ernesto",   "title": "Engineer",             "managerId": "1"},
    ]
    json_save(seed)
    return seed

def json_save(items: List[Dict[str, Any]]) -> None:
    with CANON_JSON.open("w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def json_get(pid: str) -> Dict[str, Any]:
    for it in json_load():
        if str(it.get("id")) == str(pid):
            return it
    raise HTTPException(status_code=404, detail="Not found")

def json_create(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = json_load()
    data = dict(payload)
    data.pop("adminKey", None)
    if not data.get("name"):
        raise HTTPException(status_code=400, detail="Name is required")
    if not data.get("id"):
        data["id"] = str(uuid.uuid4())
    if "parentId" in data and not data.get("managerId"):
        data["managerId"] = data["parentId"]
    items.append(data)
    json_save(items)
    return data

def json_update(pid: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    items = json_load()
    for i, it in enumerate(items):
        if str(it.get("id")) == str(pid):
            merged = {**it, **payload}
            merged.pop("adminKey", None)
            merged["id"] = pid
            if "parentId" in merged and not merged.get("managerId"):
                merged["managerId"] = merged["parentId"]
            items[i] = merged
            json_save(items)
            return merged
    raise HTTPException(status_code=404, detail="Not found")

def json_delete(pid: str) -> None:
    items = json_load()
    if any(str(p.get("managerId")) == str(pid) for p in items):
        raise HTTPException(status_code=400, detail="Cannot delete: person has direct reports")
    new_items = [p for p in items if str(p.get("id")) != str(pid)]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail="Not found")
    json_save(new_items)

# ============ pages ============
@app.get("/")
async def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/admin")
async def admin_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")

@app.get("/edit.html")
async def edit_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "edit.html")

# ============ API: people ============
@app.get("/api/people")
async def api_people_list() -> List[Dict[str, Any]]:
    return pg_list() if USING_PG else json_load()

@app.get("/api/people/{person_id}")
async def api_people_get(person_id: str) -> Dict[str, Any]:
    return pg_get(person_id) if USING_PG else json_get(person_id)

@app.post("/api/people", status_code=201)
async def api_people_create(request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
    _require_admin(request, payload)
    return pg_create(payload) if USING_PG else json_create(payload)

@app.put("/api/people/{person_id}")
async def api_people_update(person_id: str, request: Request, payload: Dict[str, Any]) -> Dict[str, Any]:
    _require_admin(request, payload)
    return pg_update(person_id, payload) if USING_PG else json_update(person_id, payload)

@app.delete("/api/people/{person_id}", status_code=204)
async def api_people_delete(person_id: str, request: Request):
    _require_admin(request)
    if USING_PG:
        pg_delete(person_id)
    else:
        json_delete(person_id)
    return {}

# ============ API: tree ============
def _clean_parent(x: Any) -> Optional[str]:
    if x in (None, "", "null", "undefined"):
        return None
    return str(x)

@app.get("/api/tree")
async def api_tree() -> List[Dict[str, Any]]:
    rows = pg_list() if USING_PG else json_load()
    return [
        {
            "id": str(p.get("id")),
            "parentId": _clean_parent(p.get("manager_id") or p.get("managerId") or p.get("parentId")),
            "name": p.get("name") or str(p.get("id")),
            "title": p.get("title") or p.get("role") or "",
        }
        for p in rows
    ]

# ============ simple health/debug ============
@app.get("/api/health")
async def api_health():
    return {
        "using_postgres": USING_PG,
        "has_db_url": bool(DB_URL),
        "static_dir": str(STATIC_DIR),
    }

# local run (Codespaces uses runapp)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
