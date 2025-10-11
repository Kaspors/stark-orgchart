import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from .models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set. Put it in your .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_people_name ON people (name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_org_units_name ON org_units (name)"))
        conn.execute(text("ALTER TABLE people ADD COLUMN IF NOT EXISTS sub_department TEXT"))
        conn.execute(text("ALTER TABLE people ADD COLUMN IF NOT EXISTS org_unit_id TEXT"))
        conn.execute(text("ALTER TABLE people ADD COLUMN IF NOT EXISTS role TEXT"))
