from typing import List

from sqlalchemy import select

from dependency import db_dependency
from grades.models import Grade


def get_grades_by_subject(student_id: int, subject_id: int, db: db_dependency) -> List[Grade]:
    statement = select(Grade).where(Grade.subject_id == subject_id, Grade.student_id == student_id)
    return list(db.scalars(statement).all())





