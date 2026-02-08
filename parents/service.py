from typing import List

from fastapi_mail import MessageSchema, MessageType
from pydantic import NameEmail
from starlette import status
from starlette.exceptions import HTTPException

from dependency import db_dependency
from auth.models import Parent, Student
from fastmail_conf import fm
from parents.schemas import AddStudentsRequest, RemoveStudentsRequests


async def add_students_to_parent(request: AddStudentsRequest, db: db_dependency) -> None:
    parent_id: int = request.parent_id
    students_ids: List[int] = request.students_ids

    parent: Parent | None = db.get(Parent, parent_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent ID {parent_id} not found"
        )
    students = db.query(Student).filter(Student.id.in_(students_ids)).all()
    if len(students) != len(request.students_ids):
        found_ids = {s.id for s in students}
        missing_ids = set(request.students_ids) - found_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Students with IDs {missing_ids} not found"
        )

    parent.children.extend(students)
    db.commit()

    students_names: List[str] = [str(s.full_name) for s in students]
    message = MessageSchema(
        subject="Added children to profile",
        recipients=[NameEmail(name="", email=parent.email)],
        body=f"The following children were added to your profile: {", ".join(students_names)}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)

async def remove_students_from_parent(request: RemoveStudentsRequests, db: db_dependency) -> None:
    parent_id: int = request.parent_id
    students_ids: List[int] = request.students_ids

    parent: Parent | None = db.get(Parent, parent_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent ID {parent_id} not found"
        )
    students_to_remove: List[Student] = db.query(Student).filter(Student.id.in_(students_ids)).all()
    for student in students_to_remove:
        if student in parent.children:
            parent.children.remove(student)

    db.commit()

    students_names = [s.full_name for s in students_to_remove]
    message = MessageSchema(
        subject="Removed children from profile",
        recipients=[NameEmail(name="", email=parent.email)],
        body=f"The following children were removed from your profile: {", ".join(students_names)}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)



