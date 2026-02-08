from typing import List

from pydantic import BaseModel


class CreateClassRequest(BaseModel):
    name: str
    year: int
    user_id: int

class ClassResponse(BaseModel):
    name: str
    year: int
    teacher_id: int
    students_ids: List[int]
    archived: bool

class AddStudentsRequest(BaseModel):
    students_ids: List[int]

class ChangeClassStatusRequest(BaseModel):
    status: bool
