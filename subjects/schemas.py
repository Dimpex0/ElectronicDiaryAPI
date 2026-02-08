from datetime import datetime

from typing import List

from pydantic import BaseModel, ConfigDict


class CreateSubjectRequest(BaseModel):
    name: str
    teacher_id: int
    students_ids: List[int]

class SubjectResponse(BaseModel):
    id: int
    name: str
    teacher_id: int
    students_ids: List[int]
    materials_ids: List[int]
    archived: bool

    model_config = ConfigDict(from_attributes=True)

class AddStudentsRequest(BaseModel):
    students_ids: List[int]

class RemoveStudentsRequest(BaseModel):
    students_ids: List[int]

class StatusRequest(BaseModel):
    status: bool

class TeacherRequest(BaseModel):
    teacher_id: int

class SubjectMaterialResponse(BaseModel):
    id: int
    title: str
    file_path: str
    uploaded_at: datetime
    subject_id: int

    model_config = ConfigDict(from_attributes=True)

class CreateSubjectMaterialRequest(BaseModel):
    title: str
