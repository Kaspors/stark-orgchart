from pydantic import BaseModel
from typing import Optional, Literal, List

AllowedRole = Literal["Head", "Director", "Senior Manager", "Manager", "Specialist"]

class PersonBase(BaseModel):
    name: str
    title: Optional[str] = None
    department: Optional[str] = None
    sub_department: Optional[str] = None
    team: Optional[str] = None
    manager_id: Optional[str] = None
    org_unit_id: Optional[str] = None
    role: Optional[AllowedRole] = None   # NEW

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    sub_department: Optional[str] = None
    team: Optional[str] = None
    manager_id: Optional[str] = None
    org_unit_id: Optional[str] = None
    role: Optional[AllowedRole] = None   # NEW

class PersonOut(PersonBase):
    id: str
    class Config:
        from_attributes = True

class OrgUnitOut(BaseModel):
    id: str
    name: str
    level: str
    parent_unit_id: Optional[str] = None
    manager_id: Optional[str] = None
    manager_name: Optional[str] = None

class TreeNode(BaseModel):
    id: str
    parentId: Optional[str]
    type: Literal["unit", "person"]
    name: str
    title: Optional[str] = None
    department: Optional[str] = None
    sub_department: Optional[str] = None
    team: Optional[str] = None
    unit_level: Optional[str] = None     # <- relax type to plain str to avoid pylance complaints
    manager_name: Optional[str] = None
    role: Optional[AllowedRole] = None   # NEW
