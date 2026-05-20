from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.common import NonEmptyStr, strip_and_validate


class EmployeeCreate(BaseModel):
    full_name: NonEmptyStr
    position: NonEmptyStr
    hired_at: date | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return strip_and_validate(value, "full_name")

    @field_validator("position")
    @classmethod
    def validate_position(cls, value: str) -> str:
        return strip_and_validate(value, "position")


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: date | None
    created_at: datetime
