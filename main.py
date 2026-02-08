from dotenv import load_dotenv

load_dotenv()

import os

import grades.views

import subjects.views

# pylint: disable=wrong-import-position

from contextlib import asynccontextmanager

from starlette import status
from starlette.exceptions import HTTPException

import classes.views
import auth
import parents.views
from auth.views import user_dependency
from database import engine, Base

from fastapi.responses import FileResponse

from fastapi import FastAPI

from auth.models import *
from classes.models import *
from subjects.models import *
from grades.models import *
from audit.models import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.views.router)
app.include_router(parents.views.router)
app.include_router(classes.views.router)
app.include_router(subjects.views.router)
app.include_router(grades.views.router)

UPLOAD_DIR = os.getenv("MEDIA_PATH", "./media")


@app.get("/")
async def root(user: user_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )

    return {"message": "Hello World"}


@app.get("/media/{file_path:path}")
async def media(file_path: str):
    full_path = os.path.join(UPLOAD_DIR, file_path)

    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File was not found"
        )

    return FileResponse(full_path)
