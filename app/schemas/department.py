from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import NonEmptyStr, strip_and_validate
from app.schemas.employee import EmployeeRead


class DepartmentCreate(BaseModel):
    name: NonEmptyStr
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return strip_and_validate(value, "name")


class DepartmentUpdate(BaseModel):
    name: NonEmptyStr | None = None
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return strip_and_validate(value, "name")


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None
    created_at: datetime


class DepartmentTreeNode(BaseModel):
    department: DepartmentRead
    employees: list[EmployeeRead] = Field(default_factory=list)
    children: list["DepartmentTreeNode"] = Field(default_factory=list)


DepartmentTreeNode.model_rebuild()
