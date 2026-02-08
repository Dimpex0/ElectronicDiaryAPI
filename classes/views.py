from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status

from auth.RoleChecker import RoleChecker
from auth.models import User, Role
from classes.schemas import CreateClassRequest, ClassResponse, AddStudentsRequest, ChangeClassStatusRequest
from classes.service import create_empty_class, add_students_to_class, change_class_status
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

@router.post("/{id}/add-students", status_code=status.HTTP_200_OK)
async def add_students(user: teacher_or_principal_or_admin_dependency, id: int, request: AddStudentsRequest, db: db_dependency):
    await add_students_to_class(id, request, db)

@router.post("/{id}/status", status_code=status.HTTP_200_OK, response_model=ClassResponse)
async def change_status(user: teacher_or_principal_or_admin_dependency, id: int, request: ChangeClassStatusRequest, db: db_dependency):
    updated_class = change_class_status(request, id, db)
    return ClassResponse(
        name=updated_class.name,
        year=updated_class.year,
        teacher_id=updated_class.teacher_id,
        students_ids=[s.id for s in updated_class.students],
        archived=updated_class.archived
    )

