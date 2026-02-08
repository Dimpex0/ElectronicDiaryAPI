import os
import uuid
from typing import Sequence, List

from fastapi import UploadFile
from fastapi_mail import MessageSchema, MessageType
from pydantic import NameEmail
from sqlalchemy import select
from starlette import status
from starlette.exceptions import HTTPException

from auth.models import User, Role, Student
from dependency import db_dependency
from fastmail_conf import fm
from subjects.models import Subject, SubjectMaterial
from subjects.schemas import CreateSubjectRequest, AddStudentsRequest, RemoveStudentsRequest, StatusRequest, \
    TeacherRequest, CreateSubjectMaterialRequest
from utils.media import save_file

UPLOAD_DIR = os.getenv("MEDIA_PATH", "./media")
MATERIALS_FOLDER = "materials"


async def create_subject(user: User, request: CreateSubjectRequest, db: db_dependency) -> Subject:
    if user.role == Role.TEACHER and user.id != request.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A teacher can't create subjects for other teachers"
        )

    if (db.query(Subject).filter(
            Subject.name == request.name,
            Subject.teacher_id == request.teacher_id,
            Subject.archived.is_(False)).first()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplication of subject"
        )

    teacher: User | None = db.get(User, request.teacher_id)
    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Couldn't find teacher with ID {request.teacher_id}"
        )

    if teacher.role not in [Role.TEACHER, Role.PRINCIPAL]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided user can't be a teacher"
        )

    statement = select(Student).where(Student.id.in_(request.students_ids))
    students: Sequence[Student] = db.scalars(statement).all()

    subject: Subject = Subject(
        name=request.name,
        teacher_id=request.teacher_id,
        students=list(students)
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)

    teacher_message = MessageSchema(
        subject="Assigned subject",
        recipients=[NameEmail(name="", email=teacher.email)],
        body=f"You have been assigned subject teacher to {request.name}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(teacher_message)

    students_message = MessageSchema(
        subject="Added to subject",
        recipients=[NameEmail(name="", email=s.email) for s in students],
        body=f"You have been added to subject {request.name} with teacher {teacher.full_name}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(students_message)

    return subject

async def add_students(user: User, request: AddStudentsRequest, subject_id: int, db: db_dependency) -> Subject:
    subject: Subject | None = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} was not found"
        )

    if user.role == Role.TEACHER and user.id != subject.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A teacher can't update subjects for other teachers"
        )

    statement = select(Student).where(Student.id.in_(request.students_ids))
    students: Sequence[Student] = db.scalars(statement).all()
    added_students = []
    for student in students:
        if student not in subject.students:
            subject.students.append(student)
            added_students.append(student)

    db.commit()

    message = MessageSchema(
        subject="Added to subject",
        recipients=[NameEmail(name="", email=s.email) for s in added_students],
        body=f"You have been added to subject {subject.name} with teacher {subject.teacher.full_name}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)

    return subject

async def remove_students(user: User, request: RemoveStudentsRequest, subject_id: int, db: db_dependency) -> Subject:
    subject: Subject | None = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} was not found"
        )

    if user.role == Role.TEACHER and user.id != subject.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A teacher can't update subjects for other teachers"
        )

    statement = select(Student).where(Student.id.in_(request.students_ids))
    students: Sequence[Student] = db.scalars(statement).all()
    removed_students = []
    for student in students:
        if student in subject.students:
            subject.students.remove(student)
            removed_students.append(student)

    db.commit()

    message = MessageSchema(
        subject="Removed from subject",
        recipients=[NameEmail(name="", email=s.email) for s in removed_students],
        body=f"You have been removed from subject {subject.name} with teacher {subject.teacher.full_name}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)

    return subject

async def change_status(user: User, subject_id: int, request: StatusRequest, db: db_dependency) -> Subject:
    subject: Subject | None = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} was not found"
        )

    if user.role == Role.TEACHER and user.id != subject.teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A teacher can't update subjects for other teachers"
        )

    if not request.status and subject.archived:
        if db.query(Subject).filter(
                Subject.name == subject.name,
                Subject.teacher_id == subject.teacher_id,
                Subject.archived.is_(False)
        ).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unarchiving this subject will result in subject duplication. Archive the active subject first."
            )

    subject.archived = request.status
    db.commit()

    message = MessageSchema(
        subject="Archived subject",
        recipients=[NameEmail(name="", email=subject.teacher.email)],
        body=f"Subject {subject.name} has been {"archived" if request.status else "unarchived"}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)

    return subject


async def change_teacher(request: TeacherRequest, subject_id: int, db: db_dependency) -> Subject:
    subject: Subject | None = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} was not found"
        )

    new_teacher: User | None = db.get(User, request.teacher_id)
    if new_teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Couldn't find teacher with ID {request.teacher_id}"
        )
    if new_teacher.role not in [Role.TEACHER, Role.PRINCIPAL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Provided user can't be a teacher"
        )

    if db.query(Subject).filter(
            Subject.name == subject.name,
            Subject.teacher_id == new_teacher.id,
            Subject.archived.is_(False)
    ).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This user already is assigned to an active subject with the same name"
        )

    old_teacher_email = NameEmail(name="", email=subject.teacher.email)
    new_teacher_email = NameEmail(name="", email=new_teacher.email)

    subject.teacher_id = new_teacher.id
    db.commit()

    old_teacher_message = MessageSchema(
        subject="Removed from subject",
        recipients=[old_teacher_email],
        body=f"You have been removed as teacher from {subject.name}",
        subtype=MessageType(value="html")
    )
    new_teacher_message = MessageSchema(
        subject="Added to subject",
        recipients=[new_teacher_email],
        body=f"You have been added as teacher to {subject.name}",
        subtype=MessageType(value="html")
    )

    await fm.send_message([old_teacher_message, new_teacher_message])

    return subject

async def create_subject_material(user: User, request: CreateSubjectMaterialRequest, file: UploadFile, subject_id: int, db: db_dependency) -> SubjectMaterial:
    subject: Subject | None = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found"
        )

    if user.role == Role.TEACHER and subject.teacher_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the teacher of this subject"
        )

    file_path = await save_file(file, MATERIALS_FOLDER)

    material = SubjectMaterial(
        title=request.title,
        file_path=file_path,
        subject_id=subject_id
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    students_emails = [NameEmail(name="", email=s.email) for s in subject.students]
    message = MessageSchema(
        subject="New material",
        recipients=students_emails,
        body=f"New material '{request.title}' has been added to {subject.name}.",
        subtype=MessageType(value="html")
    )

    await fm.send_message(message)

    return material

def get_authorized_subject(
        user: User,
        subject_id: int,
        db: db_dependency,
) -> Subject:
    subject: Subject | None = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {subject_id} not found",
        )

    match user.role:
        case Role.TEACHER:
            if subject.teacher_id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not the teacher of this subject",
                )

        case Role.STUDENT:
            if user.id not in {s.id for s in subject.students}:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not assigned to this subject",
                )

        case Role.PARENT:
            allowed_parent_ids = {
                p.id for s in subject.students for p in s.parents
            }
            if user.id not in allowed_parent_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have a child assigned to this subject",
                )

    return subject

def get_materials(user: User, subject_id, db: db_dependency) -> List[SubjectMaterial]:
    subject: Subject = get_authorized_subject(user, subject_id, db)
    statement = select(SubjectMaterial).where(
        SubjectMaterial.subject_id == subject.id
    )
    return list(db.scalars(statement).all())

def get_material(user: User, subject_id: int, material_id: int, db: db_dependency) -> SubjectMaterial:
    subject: Subject = get_authorized_subject(user, subject_id, db)

    for material in subject.materials:
        if material_id == material.id:
            return material

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Material with ID {material_id} not found"
    )