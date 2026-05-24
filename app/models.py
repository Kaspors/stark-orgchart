from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Date, func, UniqueConstraint
from typing import Optional, List
from datetime import datetime, date
import uuid


class Base(DeclarativeBase):
    pass


class PersonScrumTeam(Base):
    __tablename__ = "person_scrum_teams"
    __table_args__ = (UniqueConstraint("person_id", "scrum_team_id", name="uq_person_scrum_team"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    person_id: Mapped[str] = mapped_column(
        String, ForeignKey("people.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scrum_team_id: Mapped[str] = mapped_column(
        String, ForeignKey("scrum_teams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_in_team: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    person: Mapped["Person"] = relationship("Person", back_populates="scrum_memberships", lazy="joined")
    scrum_team: Mapped["ScrumTeam"] = relationship("ScrumTeam", back_populates="memberships", lazy="joined")


class ScrumTeam(Base):
    __tablename__ = "scrum_teams"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    product_owner_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    scrum_master_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )

    product_owner: Mapped[Optional["Person"]] = relationship(
        "Person", foreign_keys="[ScrumTeam.product_owner_id]", lazy="joined"
    )
    scrum_master: Mapped[Optional["Person"]] = relationship(
        "Person", foreign_keys="[ScrumTeam.scrum_master_id]", lazy="joined"
    )
    memberships: Mapped[List["PersonScrumTeam"]] = relationship(
        "PersonScrumTeam",
        back_populates="scrum_team",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class OrgUnit(Base):
    __tablename__ = "org_units"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String, nullable=False)  # "department" | "sub_department" | "team"

    parent_unit_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("org_units.id", ondelete="SET NULL"), nullable=True
    )
    manager_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )

    parent: Mapped[Optional["OrgUnit"]] = relationship(
        "OrgUnit",
        remote_side="OrgUnit.id",
        foreign_keys="[OrgUnit.parent_unit_id]",
        back_populates="children",
        lazy="joined",
    )
    children: Mapped[List["OrgUnit"]] = relationship(
        "OrgUnit",
        foreign_keys="[OrgUnit.parent_unit_id]",
        back_populates="parent",
        lazy="selectin",
    )
    manager: Mapped[Optional["Person"]] = relationship(
        "Person",
        foreign_keys="[OrgUnit.manager_id]",
        back_populates="manages_units",
        lazy="joined",
    )
    members: Mapped[List["Person"]] = relationship(
        "Person",
        foreign_keys="[Person.org_unit_id]",
        back_populates="org_unit",
        lazy="selectin",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Person(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    employee_number: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sub_department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)

    seniority: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, server_default="Active")
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cost_center: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    manager_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("people.id", ondelete="SET NULL"), index=True, nullable=True
    )
    org_unit_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("org_units.id", ondelete="SET NULL"), index=True, nullable=True
    )

    manager: Mapped[Optional["Person"]] = relationship(
        "Person",
        remote_side="Person.id",
        foreign_keys="[Person.manager_id]",
        back_populates="reports",
        lazy="joined",
    )
    reports: Mapped[List["Person"]] = relationship(
        "Person",
        foreign_keys="[Person.manager_id]",
        back_populates="manager",
        lazy="selectin",
    )
    org_unit: Mapped[Optional[OrgUnit]] = relationship(
        "OrgUnit",
        foreign_keys="[Person.org_unit_id]",
        back_populates="members",
        lazy="joined",
    )
    manages_units: Mapped[List[OrgUnit]] = relationship(
        "OrgUnit",
        foreign_keys="[OrgUnit.manager_id]",
        back_populates="manager",
        lazy="selectin",
    )
    scrum_memberships: Mapped[List["PersonScrumTeam"]] = relationship(
        "PersonScrumTeam",
        back_populates="person",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
