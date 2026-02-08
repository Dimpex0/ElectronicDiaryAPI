from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from database import Base
from models.homeworks import Homework
from auth.models import User


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)

    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    student: Mapped[User] = relationship(User)

    homework_id: Mapped[int] = mapped_column(ForeignKey("homeworks.id"))
    homework: Mapped[Homework] = relationship(Homework, back_populates="submissions")

    file_path: Mapped[str] = mapped_column(String)

    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
