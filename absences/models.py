from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base
from subjects.models import Subject
from auth.models import User


class Absence(Base):
    __tablename__ = "absences"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student: Mapped[User] = relationship(User)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    subject: Mapped[Subject] = relationship(Subject)

    date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_excused: Mapped[bool] = mapped_column(Boolean, default=False)
