from __future__ import annotations
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, func
from typing import Optional, List
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

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
        remote_side=lambda: [OrgUnit.id],
        foreign_keys=lambda: [OrgUnit.parent_unit_id],
        back_populates="children",
        lazy="joined",
    )
    children: Mapped[List["OrgUnit"]] = relationship(
        "OrgUnit",
        foreign_keys=lambda: [OrgUnit.parent_unit_id],
        back_populates="parent",
        lazy="selectin",
    )

    manager: Mapped[Optional["Person"]] = relationship(
        "Person",
        foreign_keys=lambda: [OrgUnit.manager_id],
        back_populates="manages_units",
        lazy="joined",
    )

    members: Mapped[List["Person"]] = relationship(
        "Person",
        foreign_keys=lambda: [Person.org_unit_id],
        back_populates="org_unit",
        lazy="selectin",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Person(Base):
    __tablename__ = "people"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sub_department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    team: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # NEW: role/tag (Head, Director, Senior Manager, Manager, Specialist)
    role: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)

    manager_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("people.id", ondelete="SET NULL"), index=True, nullable=True
    )
    org_unit_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("org_units.id", ondelete="SET NULL"), index=True, nullable=True
    )

    manager: Mapped[Optional["Person"]] = relationship(
        "Person",
        remote_side=lambda: [Person.id],
        foreign_keys=lambda: [Person.manager_id],
        back_populates="reports",
        lazy="joined",
    )
    reports: Mapped[List["Person"]] = relationship(
        "Person",
        foreign_keys=lambda: [Person.manager_id],
        back_populates="manager",
        lazy="selectin",
    )

    org_unit: Mapped[Optional[OrgUnit]] = relationship(
        "OrgUnit",
        foreign_keys=lambda: [Person.org_unit_id],
        back_populates="members",
        lazy="joined",
    )

    manages_units: Mapped[List[OrgUnit]] = relationship(
        "OrgUnit",
        foreign_keys=lambda: [OrgUnit.manager_id],
        back_populates="manager",
        lazy="selectin",
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
