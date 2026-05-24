from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import SessionLocal
from ..models import ScrumTeam, PersonScrumTeam, Person
from ..schemas import (
    ScrumTeamCreate, ScrumTeamUpdate, ScrumTeamOut,
    ScrumMemberAdd, ScrumMemberUpdate, ScrumMemberOut,
)

router = APIRouter(prefix="/api/scrum-teams", tags=["scrum-teams"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_member(m: PersonScrumTeam) -> ScrumMemberOut:
    return ScrumMemberOut(
        person_id=m.person_id,
        person_name=m.person.name if m.person else "",
        employee_number=m.person.employee_number if m.person else None,
        title=m.person.title if m.person else None,
        seniority=m.person.seniority if m.person else None,
        role_in_team=m.role_in_team,
    )


def _build_out(t: ScrumTeam, include_members: bool = True) -> ScrumTeamOut:
    members = [_build_member(m) for m in (t.memberships or [])] if include_members else []
    return ScrumTeamOut(
        id=t.id,
        name=t.name,
        description=t.description,
        product_owner_id=t.product_owner_id,
        scrum_master_id=t.scrum_master_id,
        product_owner_name=t.product_owner.name if t.product_owner else None,
        scrum_master_name=t.scrum_master.name if t.scrum_master else None,
        member_count=len(t.memberships or []),
        members=members,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("", response_model=List[ScrumTeamOut])
def list_scrum_teams(db: Session = Depends(get_db)):
    teams = db.query(ScrumTeam).order_by(ScrumTeam.name).all()
    return [_build_out(t) for t in teams]


@router.get("/{tid}", response_model=ScrumTeamOut)
def get_scrum_team(tid: str, db: Session = Depends(get_db)):
    t = db.get(ScrumTeam, tid)
    if not t:
        raise HTTPException(404, "Scrum team not found")
    return _build_out(t)


@router.post("", response_model=ScrumTeamOut, status_code=201)
def create_scrum_team(payload: ScrumTeamCreate, db: Session = Depends(get_db)):
    t = ScrumTeam(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return _build_out(t)


@router.patch("/{tid}", response_model=ScrumTeamOut)
def update_scrum_team(tid: str, payload: ScrumTeamUpdate, db: Session = Depends(get_db)):
    t = db.get(ScrumTeam, tid)
    if not t:
        raise HTTPException(404, "Scrum team not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return _build_out(t)


@router.delete("/{tid}")
def delete_scrum_team(tid: str, db: Session = Depends(get_db)):
    t = db.get(ScrumTeam, tid)
    if not t:
        raise HTTPException(404, "Scrum team not found")
    db.delete(t)
    db.commit()
    return {"status": "ok"}


@router.get("/{tid}/members", response_model=List[ScrumMemberOut])
def list_members(tid: str, db: Session = Depends(get_db)):
    t = db.get(ScrumTeam, tid)
    if not t:
        raise HTTPException(404, "Scrum team not found")
    return [_build_member(m) for m in t.memberships]


@router.post("/{tid}/members", response_model=ScrumMemberOut, status_code=201)
def add_member(tid: str, payload: ScrumMemberAdd, db: Session = Depends(get_db)):
    if not db.get(ScrumTeam, tid):
        raise HTTPException(404, "Scrum team not found")
    if not db.get(Person, payload.person_id):
        raise HTTPException(404, "Person not found")
    existing = (
        db.query(PersonScrumTeam)
        .filter_by(person_id=payload.person_id, scrum_team_id=tid)
        .first()
    )
    if existing:
        raise HTTPException(409, "Person is already a member of this team")
    m = PersonScrumTeam(
        person_id=payload.person_id,
        scrum_team_id=tid,
        role_in_team=payload.role_in_team,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return _build_member(m)


@router.patch("/{tid}/members/{pid}", response_model=ScrumMemberOut)
def update_member_role(tid: str, pid: str, payload: ScrumMemberUpdate, db: Session = Depends(get_db)):
    m = db.query(PersonScrumTeam).filter_by(person_id=pid, scrum_team_id=tid).first()
    if not m:
        raise HTTPException(404, "Membership not found")
    if payload.role_in_team is not None:
        m.role_in_team = payload.role_in_team
    db.commit()
    db.refresh(m)
    return _build_member(m)


@router.delete("/{tid}/members/{pid}")
def remove_member(tid: str, pid: str, db: Session = Depends(get_db)):
    m = db.query(PersonScrumTeam).filter_by(person_id=pid, scrum_team_id=tid).first()
    if not m:
        raise HTTPException(404, "Membership not found")
    db.delete(m)
    db.commit()
    return {"status": "ok"}
