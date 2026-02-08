import os
from datetime import timedelta, datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi_mail import MessageSchema, MessageType
from jose import jwt, JWTError  # type: ignore[import-untyped]
from pwdlib import PasswordHash
from pydantic import EmailStr, NameEmail
from starlette import status
from starlette.exceptions import HTTPException

from auth.schemas import CreateUserRequest, ChangePasswordRequest
from database import SessionLocal
from dependency import db_dependency
from auth.models import User
from fastmail_conf import fm

SECRET_KEY: str | None = os.getenv("SECRET_KEY")
ALGORITHM: str | None = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRATION_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRATION_MINUTES", 30))

password_hash = PasswordHash.recommended()
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")

token_dependency = Annotated[str, Depends(oauth2_bearer)]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def authenticate_user(email: str, password: str, db: db_dependency) -> User | None:
    user: User | None = db.query(User).filter(User.email == email).first()
    if not user or not password_hash.verify(password, user.hashed_password):
        return None

    return user

def create_access_token(email: str, user_id: int):
    encode = {"sub": email, "id": user_id}
    expires = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRATION_MINUTES)
    encode.update({"exp": int(expires.timestamp())})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: token_dependency, db: db_dependency) -> User | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: NameEmail = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user"
            )

        return db.query(User).filter(User.id == user_id).first()

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )

def create_user(request: CreateUserRequest, db: db_dependency) -> User:
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email=request.email,
        hashed_password=password_hash.hash(request.password),
        full_name=request.full_name,
        role=request.role,
        date_of_birth=request.date_of_birth
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

async def send_email_for_password_change(email: EmailStr, token: str):
    message = MessageSchema(
        subject="Change password",
        recipients=[NameEmail(name="", email=email)],
        body=f"Change password at http://127.0.0.1:8000/change-password/{token}",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)

async def send_email_for_new_user(email: EmailStr, full_name: str, password: str):
    message = MessageSchema(
        subject=f"Welcome {full_name}",
        recipients=[NameEmail(name="", email=email)],
        body=f"Welcome to the platform! The password for the account: {email} is {password}."
             f"You are going to receive an email with a link to change the password.",
        subtype=MessageType(value="html")
    )
    await fm.send_message(message)

def change_password(token: str, request: ChangePasswordRequest, db: db_dependency):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user: User | None = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not password_hash.verify(request.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password does not match")

    user.hashed_password = password_hash.hash(request.new_password)
    db.add(user)
    db.commit()
