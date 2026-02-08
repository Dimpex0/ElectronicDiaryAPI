import os
import shutil
import uuid

from fastapi import UploadFile
from starlette import status
from starlette.exceptions import HTTPException

UPLOAD_DIR = os.getenv("MEDIA_PATH", "./media")


async def save_file(file: UploadFile, folder: str) -> str:
    os.makedirs(os.path.join(UPLOAD_DIR, folder), exist_ok=True)

    original_filename = file.filename or "unknown_file"
    extension = os.path.splitext(original_filename)[1]
    unique_filename = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(UPLOAD_DIR, folder, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
    finally:
        await file.close()

    return os.path.join(folder, unique_filename)