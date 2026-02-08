import enum
from datetime import time

from sqlalchemy import ForeignKey, Enum, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from classes.classes import Class
from subjects.models import Subject


class DayOfWeek(enum.Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7

class TimetableEntry(Base):
    __tablename__ = "timetable_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"))
    class_: Mapped[Class] = relationship(Class)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    subject: Mapped[Subject] = relationship(Subject)

    day: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek))
    start: Mapped[time] = mapped_column(Time)
    end: Mapped[time] = mapped_column(Time)
