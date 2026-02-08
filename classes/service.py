from typing import List, cast

from fastapi_mail import MessageSchema, MessageType
from pydantic import NameEmail
from sqlalchemy import select
from starlette import status
from starlette.exceptions import HTTPException

from auth.models import User, Role, Student
from classes.models import Class
from classes.schemas import CreateClassRequest, AddStudentsRequest, ChangeClassStatusRequest, AddSubjectsRequest
from dependency import db_dependency
from fastmail_conf import fm
from subjects.models import Subject


async def create_empty_class(request: CreateClassRequest, db: db_dependency) -> Class:
    user: User | None = db.get(User, request.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with ID {request.user_id} not found"
        )

    if user.role not in (Role.TEACHER, Role.PRINCIPAL):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The assigned user must be a Teacher or a Principal"
        )

    if db.query(Class).filter(
            Class.name == request.name,
            Class.year == request.year,
            Class.archived.is_(False)
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplication of class"
        )

    new_class: Class = Class(
        name=request.name,
        year=request.year,
        teacher_id=request.user_id
    )
    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    message = MessageSchema(
        subject="Assigned to a class",
        recipients=[NameEmail(name="", email=user.email)],
        body=f"You have been assigned a class teacher to {request.name}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)

    return new_class

async def add_students_to_class(id: int, request: AddStudentsRequest, db: db_dependency):
    clas: Class | None = db.get(Class, id)
    if not clas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Couldn't find class with ID {id}"
        )

    students: List[Student] = db.query(Student).where(Student.id.in_(request.students_ids)).all()
    added_students = []
    for student in students:
        if student not in clas.students:
            clas.students.append(student)
            added_students.append(student)

    db.commit()

    recipients = [NameEmail(name="", email=s.email) for s in added_students]
    message = MessageSchema(
        subject=f"Added to class {clas.name}",
        recipients=recipients,
        body=f"You have been added to class {clas.name} of {clas.year} with teacher {clas.teacher.full_name}",
        subtype=MessageType(value="html")
    )

    await fm.send_message(message)

def change_class_status(request: ChangeClassStatusRequest, class_id: int, db: db_dependency) -> Class:
    clas: Class | None = db.get(Class, class_id)
    if not clas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with ID {class_id} not found"
        )

    if not request.status and clas.archived:
        if db.query(Class).filter(
            Class.name == clas.name,
            Class.teacher_id == clas.teacher_id,
            Class.year == clas.year,
            Class.archived.is_(False)
        ).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unarchiving this class will result in a duplication. Please archive the active one first."
            )

    clas.archived = request.status
    db.commit()
    return clas

async def add_subjects_to_class(user: User, class_id: int, request: AddSubjectsRequest, db: db_dependency) -> Class:
    clas: Class | None = db.get(Class, class_id)
    if not clas:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with ID {class_id} not found"
        )

    if user.role == Role.TEACHER and user.id != clas.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the teacher assigned to this class"
        )

    statement = select(Subject).where(Subject.id.in_(request.subjects_ids))
    subjects = db.scalars(statement).all()
    if len(subjects) != len(request.subjects_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find all subjects. Nothing was changed"
        )

    for subject in subjects:
        new_students = [
            cast(Student, student) for student in clas.students
            if student not in subject.students
        ]
        subject.students.extend(new_students)

    db.commit()

    return clas


