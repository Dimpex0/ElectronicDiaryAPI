import enum
from datetime import datetime

from sqlalchemy import ForeignKey, FLOAT, Enum, DateTime
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from database import Base
from subjects.models import Subject
from auth.models import User, Role

class GradeType(enum.Enum):
    HOMEWORK = 1
    PRESENTATION = 2
    EXAM = 3
    ACTIVE_PARTICIPATION = 4


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student: Mapped[User] = relationship(User)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    subject: Mapped[Subject] = relationship(Subject)

    grade: Mapped[float] = mapped_column(FLOAT)
    grade_type: Mapped[GradeType] = mapped_column(Enum(GradeType))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def type(self):
        return self.grade_type.name

    @validates("grade")
    def validate_grade(self, key, grade: float):
        if grade < 2 or grade > 6:
            raise ValueError("Grade must be between 2 and 6")
        return grade

    @validates("student")
    def validate_student(self, key, student: User):
        if student.role != Role.STUDENT:
            raise ValueError("Grades can be assigned only to students")
        return student
