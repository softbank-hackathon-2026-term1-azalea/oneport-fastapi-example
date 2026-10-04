from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        return stripped


class NoteUpdate(BaseModel):
    done: StrictBool


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    created_at: datetime
    done: bool
