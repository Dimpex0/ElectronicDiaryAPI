from typing import List, Annotated

from fastapi import APIRouter, Depends
from starlette import status

from auth.RoleChecker import RoleChecker
from auth.models import Role, User
from dependency import db_dependency
from grades.schemas import GradeResponse
from student.service import get_grades_by_subject

router = APIRouter(prefix="/students", tags=["students"])

student_dependency = Annotated[User, Depends(RoleChecker([Role.STUDENT]))]

@router.get("/grades/{subject_id}", status_code=status.HTTP_200_OK, response_model=List[GradeResponse])
async def get_grades(user: student_dependency, subject_id: int, db: db_dependency):
    return get_grades_by_subject(user.id, subject_id, db)