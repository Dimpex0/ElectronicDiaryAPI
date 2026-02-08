from typing import Annotated, List

from fastapi import APIRouter, Depends, UploadFile, BackgroundTasks
from starlette import status

from audit.service import log
from auth.RoleChecker import RoleChecker
from auth.models import User, Role
from dependency import db_dependency
from subjects.schemas import CreateSubjectRequest, SubjectResponse, AddStudentsRequest, RemoveStudentsRequest, \
    StatusRequest, TeacherRequest, SubjectMaterialResponse, CreateSubjectMaterialRequest
from subjects.service import create_subject, add_students, remove_students, change_status, change_teacher, \
    create_subject_material, get_materials, get_material

router = APIRouter(prefix="/subjects", tags=["subjects"])

user_dependency = Annotated[
    User,
    Depends(RoleChecker(list(Role)))]

teacher_or_principal_or_admin_dependency = Annotated[
    User,
    Depends(RoleChecker(
        [
            Role.TEACHER,
            Role.PRINCIPAL,
            Role.ADMIN
        ]))]

principal_or_admin_dependency = Annotated[
    User,
    Depends(RoleChecker(
        [
            Role.PRINCIPAL,
            Role.ADMIN
        ]))]

@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create(user: teacher_or_principal_or_admin_dependency, request: CreateSubjectRequest, db: db_dependency, tasks: BackgroundTasks):
    subject = await create_subject(user, request, db)
    log(tasks, user.id, f"Created subject {request.name}")
    return subject

@router.post("/{subject_id}/add-students", status_code=status.HTTP_200_OK, response_model=SubjectResponse)
async def add(user: teacher_or_principal_or_admin_dependency, subject_id: int, request: AddStudentsRequest, db: db_dependency, tasks: BackgroundTasks):
    subject = await add_students(user, request, subject_id, db)
    log(tasks, user_id=user.id, action=f"Added students: {request.students_ids} to subject {subject_id}")
    return subject

@router.post("/{subject_id}/remove-students", status_code=status.HTTP_200_OK, response_model=SubjectResponse)
async def remove(user: teacher_or_principal_or_admin_dependency, subject_id: int, request: RemoveStudentsRequest, db: db_dependency, tasks: BackgroundTasks):
    subject = await remove_students(user, request, subject_id, db)
    log(tasks, user_id=user.id, action=f"Removed students: {request.students_ids} from subject {subject_id}")
    return subject

@router.post("/{subject_id}/status", status_code=status.HTTP_200_OK, response_model=SubjectResponse)
async def update_status(user: teacher_or_principal_or_admin_dependency, subject_id: int, request: StatusRequest, db: db_dependency, tasks: BackgroundTasks):
    subject = await change_status(user, subject_id, request, db)
    log(tasks, user_id=user.id, action=f"Changed the status of subject {subject_id} to {request.status}")
    return subject

@router.post("/{subject_id}/change-teacher", status_code=status.HTTP_200_OK, response_model=SubjectResponse)
async def update_teacher(user: principal_or_admin_dependency, subject_id: int, request: TeacherRequest, db: db_dependency, tasks: BackgroundTasks):
    subject = await change_teacher(request, subject_id, db)
    log(tasks, user_id=user.id, action=f"Changed the teacher of subject {subject_id} to {subject.teacher_id}")
    return subject


@router.post("/{subject_id}/materials", status_code=status.HTTP_201_CREATED, response_model=SubjectMaterialResponse)
async def create_material(user: teacher_or_principal_or_admin_dependency, subject_id: int, request: CreateSubjectMaterialRequest, file: UploadFile, db: db_dependency, tasks: BackgroundTasks):
    material = await create_subject_material(user, request, file, subject_id, db)
    log(tasks, user_id=user.id, action=f"Added material {material.id} to subject {subject_id}")
    return material


@router.get("/{subject_id}/materials", status_code=status.HTTP_200_OK, response_model=List[SubjectMaterialResponse])
async def materials(user: user_dependency, subject_id: int, db: db_dependency):
    return get_materials(user, subject_id, db)

@router.get("/{subject_id}/materials/{material_id}", status_code=status.HTTP_200_OK, response_model=SubjectMaterialResponse)
async def material(user: user_dependency, subject_id: int, material_id: int, db: db_dependency):
    return get_material(user, subject_id, material_id, db)