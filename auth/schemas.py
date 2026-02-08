from datetime import datetime

from pydantic import BaseModel, field_validator, EmailStr, ConfigDict

from auth.models import Role

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role
    date_of_birth: datetime

    @field_validator("role", mode="before")
    @classmethod
    def convert_role_to_enum(cls, value) -> int | Role | None:
        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                return Role[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid role: {value}. Must be one of {[r.name for r in Role]}")

        return None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    date_of_birth: datetime

    model_config = ConfigDict(from_attributes=True)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

