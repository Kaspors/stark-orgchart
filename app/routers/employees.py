from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ..db import SessionLocal
from ..models import Person, PersonScrumTeam
from ..schemas import PersonCreate, PersonUpdate, PersonOut, ScrumMembershipOut

router = APIRouter(prefix="/api/employees", tags=["employees"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_out(p: Person) -> PersonOut:
    scrum_teams = [
        ScrumMembershipOut(
            scrum_team_id=m.scrum_team_id,
            scrum_team_name=m.scrum_team.name if m.scrum_team else "",
            role_in_team=m.role_in_team,
        )
        for m in (p.scrum_memberships or [])
    ]
    return PersonOut(
        id=p.id,
        name=p.name,
        employee_number=p.employee_number,
        email=p.email,
        phone=p.phone,
        title=p.title,
        department=p.department,
        sub_department=p.sub_department,
        team=p.team,
        role=p.role,
        seniority=p.seniority,
        employment_type=p.employment_type,
        status=p.status or "Active",
        start_date=p.start_date,
        end_date=p.end_date,
        location=p.location,
        cost_center=p.cost_center,
        manager_id=p.manager_id,
        org_unit_id=p.org_unit_id,
        manager_name=p.manager.name if p.manager else None,
        created_at=p.created_at,
        updated_at=p.updated_at,
        scrum_teams=scrum_teams,
    )


@router.get("", response_model=List[PersonOut])
def list_employees(
    search: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    seniority: Optional[str] = Query(None),
    scrum_team_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Person)
    if search:
        q = q.filter(Person.name.ilike(f"%{search}%"))
    if department:
        q = q.filter(Person.department == department)
    if status:
        q = q.filter(Person.status == status)
    if seniority:
        q = q.filter(Person.seniority == seniority)
    if scrum_team_id:
        q = q.join(PersonScrumTeam, PersonScrumTeam.person_id == Person.id).filter(
            PersonScrumTeam.scrum_team_id == scrum_team_id
        )
    people = q.order_by(Person.name).all()
    return [_build_out(p) for p in people]


@router.get("/{pid}", response_model=PersonOut)
def get_employee(pid: str, db: Session = Depends(get_db)):
    p = db.get(Person, pid)
    if not p:
        raise HTTPException(404, "Employee not found")
    return _build_out(p)


@router.post("", response_model=PersonOut, status_code=201)
def create_employee(payload: PersonCreate, db: Session = Depends(get_db)):
    p = Person(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return _build_out(p)


@router.patch("/{pid}", response_model=PersonOut)
def update_employee(pid: str, payload: PersonUpdate, db: Session = Depends(get_db)):
    p = db.get(Person, pid)
    if not p:
        raise HTTPException(404, "Employee not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _build_out(p)


@router.delete("/{pid}")
def delete_employee(pid: str, db: Session = Depends(get_db)):
    p = db.get(Person, pid)
    if not p:
        raise HTTPException(404, "Employee not found")
    for r in p.reports:
        r.manager_id = None
    db.delete(p)
    db.commit()
    return {"status": "ok"}
