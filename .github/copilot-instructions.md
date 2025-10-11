# Copilot Instructions for stark-orgchart

## Project Overview
- **Purpose:** Visualize and manage organizational charts via a FastAPI backend and static web frontend.
- **Architecture:**
  - **Backend:** FastAPI app (`app/main.py`) exposes REST API endpoints for CRUD operations on people and bulk import via Excel.
  - **Database:** PostgreSQL via SQLAlchemy ORM (`app/db.py`, `app/models.py`).
  - **Frontend:** Static HTML/JS/CSS in `static/`, using D3-based org chart (`static/lib/d3-org-chart.min.js`).

## Key Files & Data Flow
- `app/main.py`: FastAPI routes, admin key protection, static file serving.
- `app/db.py`: DB engine/session setup, auto-migration, index creation.
- `app/models.py`: SQLAlchemy models (Person, Base), relationships for org chart.
- `app/schemas.py`: Pydantic schemas for API validation.
- `app/excel_import.py`: Bulk import logic, flexible column mapping, wipes/replaces all people.
- `static/`: Frontend assets. `admin.html` for admin UI, `index.html` for chart display.

## Developer Workflows
- **Run server:**
  ```bash
  uvicorn app.main:app --reload
  ```
- **DB setup:** Requires `.env` with `DATABASE_URL` (PostgreSQL). Auto-migration on startup.
- **Bulk import:** POST Excel file to `/api/upload-excel` (admin key required).
- **Admin key:** Set `ADMIN_KEY` in `.env` for protected endpoints.

## Patterns & Conventions
- **Person model:** Self-referential `manager_id` for hierarchy, `reports` relationship for direct reports.
- **Excel import:** Flexible column names (case/spacing/locale), wipes all existing people before import.
- **API security:** All mutating endpoints require `x-admin-key` header matching `ADMIN_KEY`.
- **Frontend:** Org chart rendered client-side from `/api/people` data.

## Integration Points
- **Dependencies:** See `requirements.txt` (FastAPI, SQLAlchemy, pandas, openpyxl, psycopg, pydantic).
- **Environment:** `.env` required for DB and admin key.
- **Static files:** Served at `/static/*`.

## Example API Usage
- List people: `GET /api/people`
- Add person: `POST /api/people` (admin key)
- Update person: `PATCH /api/people/{pid}` (admin key)
- Delete person: `DELETE /api/people/{pid}` (admin key)
- Bulk import: `POST /api/upload-excel` (admin key, Excel file)

## Tips for AI Agents
- Always check for `.env` and required keys before running or testing.
- Use SQLAlchemy session via `SessionLocal` and `get_db()` dependency.
- For bulk import, ensure column mapping logic matches real-world Excel files.
- When updating `.github/copilot-instructions.md`, preserve actionable, project-specific advice.
