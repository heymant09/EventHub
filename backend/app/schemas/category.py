from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic import model_validator

class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def trim_name(cls, value):
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Name must contain at least 2 non-whitespace characters")
        return value


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value):
        if value is not None:
            value = value.strip()
            if len(value) < 2:
                raise ValueError("Name must contain at least 2 non-whitespace characters")
        return value

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self
    description: str | None = None


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None

    model_config = ConfigDict(from_attributes=True)
