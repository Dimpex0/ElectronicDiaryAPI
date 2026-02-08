from datetime import datetime
from typing import List

from sqlalchemy import Text, DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base
from subjects.models import Subject


class Homework(Base):
    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)

    due_date: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id"))
    subject: Mapped[Subject] = relationship(Subject)

    submissions: Mapped[List["HomeworkSubmission"]] = relationship(
        "HomeworkSubmission", back_populates="homework"
    )
