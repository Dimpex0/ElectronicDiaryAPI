from typing import List, cast

from fastapi_mail import MessageSchema, MessageType
from pydantic import NameEmail
from sqlalchemy import select
from starlette import status
from starlette.exceptions import HTTPException

from auth.models import User, Role, Parent, Student
from dependency import db_dependency
from fastmail_conf import fm
from grades.models import Grade
from grades.schemas import GradeCreateRequest
from subjects.models import Subject


def get_all_grades(db: db_dependency) -> List[Grade]:
    statement = select(Grade)
    return list(db.scalars(statement).all())

def get_grade(user: User, grade_id: int, db: db_dependency) -> Grade:
    grade: Grade | None = db.get(Grade, grade_id)
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade with ID: {grade_id} was not found"
        )

    if user.role == Role.STUDENT and grade.student_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can't see that grade"
        )

    if user.role == Role.PARENT:
        user = cast(Parent, user)
        if grade.student_id not in [c.id for c in user.children]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can't see that grade"
            )

    return grade

async def create_grade(user: User, request: GradeCreateRequest, db: db_dependency) -> Grade:
    subject: Subject | None = db.get(Subject, request.subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID: {request.subject_id} was not  found"
        )

    if user.role == Role.TEACHER:
        if user.id != subject.teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can't grade when not a teacher of the subject"
            )

    if request.student_id not in subject.students_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student is not part of the subject"
        )

    student: Student | None = db.get(Student, request.student_id)
    if student is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided student is not actually a student"
        )

    if request.grade < 2 or request.grade > 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid grade"
        )

    grade = Grade(
        student_id=request.student_id,
        subject_id=request.subject_id,
        grade=request.grade,
        grade_type=request.type
    )
    db.add(grade)
    db.commit()
    db.refresh(grade)

    emails = ([NameEmail(name="", email=student.email)] +
              [NameEmail(name="", email=p.email) for p in student.parents])

    message = MessageSchema(
        subject="New grade",
        recipients=emails,
        body=f"You received a grade {request.grade}, {request.type.name} in {subject.name}",
        subtype=MessageType(value="html")
    )

    await fm.send_message(message)

    return grade

