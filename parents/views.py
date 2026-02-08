from typing import Annotated, cast

from fastapi import APIRouter, Depends
from starlette import status

from auth.models import Parent
from auth.views import admin_dependency, parent_dependency
from dependency import db_dependency
from .schemas import AddStudentsRequest, ParentProfileResponse, RemoveStudentsRequests
from .service import add_students_to_parent, remove_students_from_parent

router = APIRouter(prefix="/parents", tags=["parents"])

@router.post("/add-children", status_code=status.HTTP_200_OK)
async def add_children(user: admin_dependency, request: AddStudentsRequest, db: db_dependency):
    await add_students_to_parent(request, db)

@router.post("/remove-children", status_code=status.HTTP_200_OK)
async def remove_children(user: admin_dependency, request: RemoveStudentsRequests, db:db_dependency):
    await remove_students_from_parent(request, db)

@router.get("/profile", response_model=ParentProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(user: parent_dependency):
    parent: Parent = cast(Parent, user)
    return ParentProfileResponse(
        id=parent.id,
        email=parent.email,
        full_name=parent.full_name,
        role=parent.role.name,
        date_of_birth= parent.date_of_birth,
        children_ids=[s.id for s in parent.children]
    )
