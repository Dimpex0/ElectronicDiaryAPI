from typing import List, Annotated

from fastapi import Depends
from starlette import status
from starlette.exceptions import HTTPException

from auth.models import Role, User
from auth.service import get_current_user


class RoleChecker:
    def __init__(self, allowed_roles: List[Role]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return user
