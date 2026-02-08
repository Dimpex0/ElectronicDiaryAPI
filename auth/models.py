from typing import List

from pydantic import NameEmail, EmailStr
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy import Enum, String, DateTime, Table, Column, Integer, ForeignKey

import enum
from datetime import datetime

from database import Base

parent_student_association = Table(
    "parent_student",
    Base.metadata,
    Column("parent_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("student_id", Integer, ForeignKey("users.id"), primary_key=True),
)

class Role(enum.Enum):
    STUDENT = 1
    TEACHER = 2
    PRINCIPAL = 3
    PARENT = 4
    ADMIN = 5

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[EmailStr] = mapped_column(String, unique=True)
    hashed_password: Mapped[str] = mapped_column(String)
    full_name: Mapped[str] = mapped_column(String)
    role: Mapped[Role] = mapped_column(Enum(Role))
    date_of_birth: Mapped[datetime] = mapped_column(DateTime)

    __mapper_args__ = {
        "polymorphic_on": "role",
    }

class Student(User):
    __mapper_args__ = {
        "polymorphic_identity": Role.STUDENT,
    }

    parents: Mapped[List["Parent"]] = relationship(
        "Parent",
        secondary=parent_student_association,
        primaryjoin="Student.id == parent_student.c.student_id",
        secondaryjoin="Parent.id == parent_student.c.parent_id",
        back_populates="children",
        lazy="selectin"
    )

class Parent(User):
    __mapper_args__ = {
        "polymorphic_identity": Role.PARENT,
    }

    children: Mapped[List["Student"]] = relationship(
        "Student",
        secondary=parent_student_association,
        primaryjoin="Parent.id == parent_student.c.parent_id",
        secondaryjoin="Student.id == parent_student.c.student_id",
        back_populates="parents",
        lazy="selectin"
    )

class Admin(User):
    __mapper_args__ = {
        "polymorphic_identity": Role.ADMIN,
    }

class Teacher(User):
    __mapper_args__ = {
        "polymorphic_identity": Role.TEACHER,
    }

class Principal(User):
    __mapper_args__ = {
        "polymorphic_identity": Role.PRINCIPAL,
    }
