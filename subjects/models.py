from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Boolean, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.sql import func

from database import Base
from auth.models import User, Role, Student

subject_students = Table(
    "subject_students",
    Base.metadata,
    Column("subject_id", ForeignKey("subjects.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)

class SubjectMaterial(Base):
    __tablename__ = "subject_materials"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String)

    file_path: Mapped[str] = mapped_column(String, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    subject: Mapped["Subject"] = relationship("Subject", back_populates="materials")


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    teacher: Mapped[User] = relationship(User)
    students: Mapped[List[Student]] = relationship(
        Student,
        secondary=subject_students,
        lazy="selectin"
    )
    materials: Mapped[List["SubjectMaterial"]] = relationship(
        "SubjectMaterial",
        back_populates="subject",
        cascade="all, delete-orphan"
    )
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def students_ids(self) -> list[int]:
        return [s.id for s in self.students]

    @property
    def materials_ids(self) -> list[int]:
        return [m.id for m in self.materials]

    @validates("teacher")
    def validate_teacher(self, key, user):
        if user.role not in (Role.TEACHER, Role.PRINCIPAL):
            raise ValueError("Assigned user must be a teacher or principle")
        return user
