import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orgchart.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def _safe_alter(conn, stmt: str):
    try:
        conn.execute(text(stmt))
    except Exception:
        pass


def init_db():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        # Indexes
        _safe_alter(conn, "CREATE INDEX IF NOT EXISTS ix_people_name ON people (name)")
        _safe_alter(conn, "CREATE INDEX IF NOT EXISTS ix_org_units_name ON org_units (name)")
        # Legacy columns (may already exist from old schema)
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN sub_department TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN org_unit_id TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN role TEXT")
        # New columns
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN employee_number TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN email TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN phone TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN seniority TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN employment_type TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN status TEXT DEFAULT 'Active'")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN start_date DATE")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN end_date DATE")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN location TEXT")
        _safe_alter(conn, "ALTER TABLE people ADD COLUMN cost_center TEXT")
