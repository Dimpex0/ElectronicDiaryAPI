from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext  # type: ignore[import-untyped]
from starlette import status
from starlette.exceptions import HTTPException

from audit.service import log
from auth.RoleChecker import RoleChecker
from auth.schemas import CreateUserRequest, Token, LoginRequest, UserResponse, ChangePasswordRequest
from auth.service import create_user, authenticate_user, create_access_token, \
    send_email_for_password_change, send_email_for_new_user, change_password
from dependency import db_dependency
from auth.models import User, Parent, Role

router = APIRouter(prefix="/auth", tags=["auth"])

user_dependency = Annotated[User, Depends(RoleChecker(list(Role)))]
admin_dependency = Annotated[User, Depends(RoleChecker([Role.ADMIN]))]
parent_dependency = Annotated[User, Depends(RoleChecker([Role.PARENT]))]
student_dependency = Annotated[User, Depends(RoleChecker([Role.STUDENT]))]
teacher_dependency = Annotated[User, Depends(RoleChecker([Role.TEACHER]))]
principal_dependency = Annotated[User, Depends(RoleChecker([Role.PRINCIPAL]))]

@router.post("/create-user", response_model=UserResponse)
async def create(user: admin_dependency, db: db_dependency, request: CreateUserRequest, tasks: BackgroundTasks):
    new_user: User = create_user(request, db)
    await send_email_for_new_user(new_user.email, new_user.full_name, request.password)

    token = create_access_token(new_user.email, new_user.id)
    await send_email_for_password_change(new_user.email, token)

    log(tasks, user_id=user.id, action=f"Created user with ID {new_user.id}")

    return new_user

@router.post("/change-password/{token}")
async def change_user_password(token: str,
                               request: ChangePasswordRequest,
                               db: db_dependency):
    change_password(token, request, db)

@router.post("/login", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: db_dependency
):
    user: User | None = authenticate_user(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )

    email = user.email
    user_id = user.id
    token = create_access_token(email, user_id)

    return {"access_token": token, "token_type": "bearer"}
