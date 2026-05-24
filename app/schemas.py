from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import date, datetime

AllowedRole = Literal["Head", "Director", "Senior Manager", "Manager", "Specialist"]
AllowedSeniority = Literal["Intern", "Junior", "Mid", "Senior", "Lead", "Principal", "Staff"]
AllowedEmploymentType = Literal["Full-time", "Part-time", "Contractor", "Intern"]
AllowedStatus = Literal["Active", "On Leave", "Terminated"]
AllowedScrumRole = Literal[
    "Developer", "Senior Developer", "Lead Developer",
    "QA Engineer", "DevOps", "Designer", "Data Engineer",
    "Product Owner", "Scrum Master", "Architect", "Other"
]


# ── Person ─────────────────────────────────────────────────────────────────────

class PersonBase(BaseModel):
    name: str
    employee_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    sub_department: Optional[str] = None
    team: Optional[str] = None
    role: Optional[AllowedRole] = None
    seniority: Optional[AllowedSeniority] = None
    employment_type: Optional[AllowedEmploymentType] = None
    status: AllowedStatus = "Active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    manager_id: Optional[str] = None
    org_unit_id: Optional[str] = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    employee_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    sub_department: Optional[str] = None
    team: Optional[str] = None
    role: Optional[AllowedRole] = None
    seniority: Optional[AllowedSeniority] = None
    employment_type: Optional[AllowedEmploymentType] = None
    status: Optional[AllowedStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    cost_center: Optional[str] = None
    manager_id: Optional[str] = None
    org_unit_id: Optional[str] = None


class ScrumMembershipOut(BaseModel):
    scrum_team_id: str
    scrum_team_name: str
    role_in_team: Optional[str] = None

    class Config:
        from_attributes = True


class PersonOut(PersonBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    manager_name: Optional[str] = None
    scrum_teams: List[ScrumMembershipOut] = []

    class Config:
        from_attributes = True


# ── OrgUnit ────────────────────────────────────────────────────────────────────

class OrgUnitCreate(BaseModel):
    name: str
    level: str
    parent_unit_id: Optional[str] = None
    manager_id: Optional[str] = None


class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    parent_unit_id: Optional[str] = None
    manager_id: Optional[str] = None


class OrgUnitOut(BaseModel):
    id: str
    name: str
    level: str
    parent_unit_id: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None
    member_count: int = 0

    class Config:
        from_attributes = True


# ── ScrumTeam ──────────────────────────────────────────────────────────────────

class ScrumTeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    product_owner_id: Optional[str] = None
    scrum_master_id: Optional[str] = None


class ScrumTeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    product_owner_id: Optional[str] = None
    scrum_master_id: Optional[str] = None


class ScrumMemberOut(BaseModel):
    person_id: str
    person_name: str
    employee_number: Optional[str] = None
    title: Optional[str] = None
    seniority: Optional[str] = None
    role_in_team: Optional[str] = None

    class Config:
        from_attributes = True


class ScrumTeamOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    product_owner_id: Optional[str] = None
    scrum_master_id: Optional[str] = None
    product_owner_name: Optional[str] = None
    scrum_master_name: Optional[str] = None
    member_count: int = 0
    members: List[ScrumMemberOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScrumMemberAdd(BaseModel):
    person_id: str
    role_in_team: Optional[AllowedScrumRole] = None


class ScrumMemberUpdate(BaseModel):
    role_in_team: Optional[AllowedScrumRole] = None


# ── Reports ────────────────────────────────────────────────────────────────────

class HeadcountByGroup(BaseModel):
    group: str
    count: int


class ReportSummary(BaseModel):
    total_employees: int
    active_employees: int
    total_departments: int
    total_scrum_teams: int
    by_department: List[HeadcountByGroup]
    by_seniority: List[HeadcountByGroup]
    by_employment_type: List[HeadcountByGroup]
    by_status: List[HeadcountByGroup]


class ScrumTeamReport(BaseModel):
    team_id: str
    team_name: str
    description: Optional[str] = None
    product_owner: Optional[str] = None
    scrum_master: Optional[str] = None
    total_members: int
    by_role: List[HeadcountByGroup]
    by_seniority: List[HeadcountByGroup]
    members: List[ScrumMemberOut]


# ── Tree (legacy compat) ───────────────────────────────────────────────────────

class TreeNode(BaseModel):
    id: str
    parentId: Optional[str]
    type: Literal["unit", "person"]
    name: str
    title: Optional[str] = None
    department: Optional[str] = None
    sub_department: Optional[str] = None
    team: Optional[str] = None
    unit_level: Optional[str] = None
    manager_name: Optional[str] = None
    role: Optional[str] = None
