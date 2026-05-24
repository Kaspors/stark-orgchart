from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import SessionLocal
from ..models import OrgUnit, Person
from ..schemas import OrgUnitCreate, OrgUnitUpdate, OrgUnitOut

router = APIRouter(prefix="/api/departments", tags=["departments"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_out(u: OrgUnit) -> OrgUnitOut:
    return OrgUnitOut(
        id=u.id,
        name=u.name,
        level=u.level,
        parent_unit_id=u.parent_unit_id,
        manager_id=u.manager_id,
        manager_name=u.manager.name if u.manager else None,
        member_count=len(u.members),
    )


@router.get("", response_model=List[OrgUnitOut])
def list_departments(db: Session = Depends(get_db)):
    units = db.query(OrgUnit).order_by(OrgUnit.level, OrgUnit.name).all()
    return [_build_out(u) for u in units]


@router.get("/{uid}", response_model=OrgUnitOut)
def get_department(uid: str, db: Session = Depends(get_db)):
    u = db.get(OrgUnit, uid)
    if not u:
        raise HTTPException(404, "Department not found")
    return _build_out(u)


@router.post("", response_model=OrgUnitOut, status_code=201)
def create_department(payload: OrgUnitCreate, db: Session = Depends(get_db)):
    u = OrgUnit(**payload.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)
    return _build_out(u)


@router.patch("/{uid}", response_model=OrgUnitOut)
def update_department(uid: str, payload: OrgUnitUpdate, db: Session = Depends(get_db)):
    u = db.get(OrgUnit, uid)
    if not u:
        raise HTTPException(404, "Department not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return _build_out(u)


@router.delete("/{uid}")
def delete_department(uid: str, db: Session = Depends(get_db)):
    u = db.get(OrgUnit, uid)
    if not u:
        raise HTTPException(404, "Department not found")
    for member in u.members:
        member.org_unit_id = None
    for child in u.children:
        child.parent_unit_id = None
    db.delete(u)
    db.commit()
    return {"status": "ok"}
