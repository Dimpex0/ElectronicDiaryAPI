from typing import List, Annotated

from fastapi import APIRouter, Depends
from starlette import status

from auth.RoleChecker import RoleChecker
from auth.models import User, Role
from dependency import db_dependency
from grades.schemas import GradeResponse, GradeCreateRequest
from grades.service import get_all_grades, get_grade, create_grade

router = APIRouter(prefix="/grades", tags=["grades"])

user_dependency = Annotated[
    User,
    Depends(RoleChecker(list(Role)))]

principal_or_admin_dependency = Annotated[
    User,
    Depends(RoleChecker(
        [
            Role.PRINCIPAL,
            Role.ADMIN
        ]))]

teacher_or_admin_dependency = Annotated[
    User,
    Depends(RoleChecker(
        [
            Role.TEACHER,
            Role.ADMIN
        ]))]

@router.get("/", status_code=status.HTTP_200_OK, response_model=List[GradeResponse])
async def get_all(user: principal_or_admin_dependency, db: db_dependency):
    return get_all_grades(db)

@router.get("/{grade_id}", status_code=status.HTTP_200_OK, response_model=GradeResponse)
async def get(user: user_dependency, grade_id: int, db: db_dependency):
    return get_grade(user, grade_id, db)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=GradeResponse)
async def create(user: teacher_or_admin_dependency, request: GradeCreateRequest, db: db_dependency):
    return await create_grade(user, request, db)





