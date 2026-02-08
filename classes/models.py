from typing import List

from sqlalchemy import String, Boolean, Integer, ForeignKey, Column, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from database import Base
from auth.models import User, Role
from subjects.models import Subject

class_students = Table(
    "class_students",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id"), primary_key=True),
    Column("user_id", ForeignKey("users.id"), primary_key=True),
)

class_subjects = Table(
    "class_subjects",
    Base.metadata,
    Column("class_id", ForeignKey("classes.id"), primary_key=True),
    Column("subject_id", ForeignKey("subjects.id"), primary_key=True),
)

class Class(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    teacher: Mapped[User] = relationship(User)
    students: Mapped[List[User]] = relationship(
        User,
        secondary=class_students,
        lazy="selectin"
    )
    subjects: Mapped[List["Subject"]] = relationship(
        "Subject",
        secondary=class_subjects,
        lazy="selectin"
    )
    archived: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def students_ids(self) -> list[int]:
        return [s.id for s in self.students]

    @property
    def subjects_ids(self) -> list[int]:
        return [s.id for s in self.subjects]

    @validates("teacher")
    def validate_teacher(self, key, user: User):
        if user.role not in (Role.TEACHER, Role.PRINCIPAL):
            raise ValueError("Assigned user must be a teacher or principle")
        return user
