from typing import List

from pydantic import BaseModel, ConfigDict


class CreateClassRequest(BaseModel):
    name: str
    year: int
    user_id: int

class ClassResponse(BaseModel):
    name: str
    year: int
    teacher_id: int
    students_ids: List[int]
    subjects_ids: List[int]
    archived: bool

    model_config = ConfigDict(from_attributes=True)

class AddStudentsRequest(BaseModel):
    students_ids: List[int]

class ChangeClassStatusRequest(BaseModel):
    status: bool

class AddSubjectsRequest(BaseModel):
    subjects_ids: List[int]
