from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from auth.RoleChecker import RoleChecker
from auth.models import User, Role
from classes.schemas import CreateClassRequest, ClassResponse, AddStudentsRequest, ChangeClassStatusRequest, \
    AddSubjectsRequest
from classes.service import create_empty_class, add_students_to_class, change_class_status, add_subjects_to_class
from dependency import db_dependency

router = APIRouter(prefix="/classes", tags=["classes"])

teacher_or_principal_or_admin_dependency = Annotated[
    User,
    Depends(
        RoleChecker([
            Role.TEACHER,
            Role.PRINCIPAL,
            Role.ADMIN
        ]))]

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ClassResponse)
async def create_class(user: teacher_or_principal_or_admin_dependency, request: CreateClassRequest, db: db_dependency):
    new_class = await create_empty_class(request, db)
    return ClassResponse(
        name=new_class.name,
        year=new_class.year,
        teacher_id=new_class.teacher_id,
        students_ids=[s.id for s in new_class.students],
        archived=new_class.archived
    )

@router.post("/{class_id}/add-students", status_code=status.HTTP_200_OK)
async def add_students(user: teacher_or_principal_or_admin_dependency, class_id: int, request: AddStudentsRequest, db: db_dependency):
    await add_students_to_class(class_id, request, db)

@router.post("/{class_id}/status", status_code=status.HTTP_200_OK, response_model=ClassResponse)
async def change_status(user: teacher_or_principal_or_admin_dependency, class_id: int, request: ChangeClassStatusRequest, db: db_dependency):
    return change_class_status(request, class_id, db)


@router.post("/{class_id}/subjects", status_code=status.HTTP_200_OK, response_model=ClassResponse)
async def add_subjects(user: teacher_or_principal_or_admin_dependency, class_id: int, request: AddSubjectsRequest, db: db_dependency):
    return await add_subjects_to_class(user, class_id, request, db)
