from typing import Annotated

from pydantic import Field


def strip_and_validate(value: str, field_name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{field_name} must not be empty")
    if len(stripped) > 200:
        raise ValueError(f"{field_name} must be at most 200 characters")
    return stripped


NonEmptyStr = Annotated[str, Field(min_length=1, max_length=200)]
