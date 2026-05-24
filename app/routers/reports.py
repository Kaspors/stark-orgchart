from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import Counter
from typing import List

from ..db import SessionLocal
from ..models import Person, OrgUnit, ScrumTeam
from ..schemas import (
    ReportSummary, ScrumTeamReport, HeadcountByGroup, ScrumMemberOut,
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _counter_to_list(counter: Counter) -> List[HeadcountByGroup]:
    return [
        HeadcountByGroup(group=k or "Unspecified", count=v)
        for k, v in sorted(counter.items(), key=lambda x: -x[1])
    ]


@router.get("/summary", response_model=ReportSummary)
def get_summary(db: Session = Depends(get_db)):
    people = db.query(Person).all()
    total = len(people)
    active = sum(1 for p in people if (p.status or "Active") == "Active")
    dept_count = db.query(OrgUnit).filter(OrgUnit.level == "department").count()
    team_count = db.query(ScrumTeam).count()

    by_dept = Counter(p.department for p in people)
    by_seniority = Counter(p.seniority for p in people)
    by_emp_type = Counter(p.employment_type for p in people)
    by_status = Counter((p.status or "Active") for p in people)

    return ReportSummary(
        total_employees=total,
        active_employees=active,
        total_departments=dept_count,
        total_scrum_teams=team_count,
        by_department=_counter_to_list(by_dept),
        by_seniority=_counter_to_list(by_seniority),
        by_employment_type=_counter_to_list(by_emp_type),
        by_status=_counter_to_list(by_status),
    )


@router.get("/scrum-teams", response_model=List[ScrumTeamReport])
def get_scrum_team_reports(db: Session = Depends(get_db)):
    teams = db.query(ScrumTeam).order_by(ScrumTeam.name).all()
    result = []
    for t in teams:
        members = [
            ScrumMemberOut(
                person_id=m.person_id,
                person_name=m.person.name if m.person else "",
                employee_number=m.person.employee_number if m.person else None,
                title=m.person.title if m.person else None,
                seniority=m.person.seniority if m.person else None,
                role_in_team=m.role_in_team,
            )
            for m in (t.memberships or [])
        ]
        by_role = Counter(m.role_in_team for m in t.memberships)
        by_seniority = Counter(
            (m.person.seniority if m.person else None) for m in t.memberships
        )
        result.append(
            ScrumTeamReport(
                team_id=t.id,
                team_name=t.name,
                description=t.description,
                product_owner=t.product_owner.name if t.product_owner else None,
                scrum_master=t.scrum_master.name if t.scrum_master else None,
                total_members=len(members),
                by_role=_counter_to_list(by_role),
                by_seniority=_counter_to_list(by_seniority),
                members=members,
            )
        )
    return result


@router.get("/org-structure")
def get_org_structure(db: Session = Depends(get_db)):
    units = db.query(OrgUnit).all()
    people = db.query(Person).all()

    unit_map = {u.id: u for u in units}
    result = []

    for u in units:
        members = [
            {
                "id": p.id,
                "name": p.name,
                "title": p.title,
                "seniority": p.seniority,
                "role": p.role,
                "employee_number": p.employee_number,
            }
            for p in u.members
        ]
        result.append(
            {
                "id": u.id,
                "name": u.name,
                "level": u.level,
                "parent_unit_id": u.parent_unit_id,
                "manager_name": u.manager.name if u.manager else None,
                "member_count": len(members),
                "members": members,
            }
        )

    orphans = [p for p in people if not p.org_unit_id]
    return {"units": result, "unassigned_employees": len(orphans)}


@router.get("/managers")
def get_manager_report(db: Session = Depends(get_db)):
    people = db.query(Person).all()
    managers = [p for p in people if p.reports]
    return [
        {
            "id": m.id,
            "name": m.name,
            "title": m.title,
            "department": m.department,
            "direct_reports": len(m.reports),
            "reports": [
                {"id": r.id, "name": r.name, "title": r.title, "seniority": r.seniority}
                for r in m.reports
            ],
        }
        for m in sorted(managers, key=lambda x: -len(x.reports))
    ]
