from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime

from grades.models import GradeType


class GradeResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    grade: float
    type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class GradeCreateRequest(BaseModel):
    student_id: int
    subject_id: int
    grade: float
    type: GradeType


    @field_validator("type", mode="before")
    @classmethod
    def convert_role_to_enum(cls, value) -> int | GradeType | None:
        if isinstance(value, int):
            return value

        if isinstance(value, str):
            try:
                return GradeType[value.upper()]
            except KeyError:
                raise ValueError(f"Invalid grade type: {value}. Must be one of {[t.name for t in GradeType]}")

        return None