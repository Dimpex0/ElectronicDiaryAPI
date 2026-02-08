from datetime import datetime
from typing import List

from pydantic import BaseModel


class AddStudentsRequest(BaseModel):
    parent_id: int
    students_ids: List[int]

class RemoveStudentsRequests(BaseModel):
    parent_id: int
    students_ids: List[int]

class ParentProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    date_of_birth: datetime
    children_ids: List[int]
