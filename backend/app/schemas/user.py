from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator

from app.models.user import UserRole


# Data received from the client
class UserCreate(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="before")
    @classmethod
    def reject_role_fields(cls, value):
        if isinstance(value, dict) and "role" in value:
            raise ValueError("Role cannot be assigned during public registration")
        return value


# Data returned to the client
class UserResponse(BaseModel):

    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):

    email: EmailStr

    password: str = Field(min_length=1, max_length=128)

class UserRoleUpdate(BaseModel):
    role: UserRole


class UserProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    current_password: str | None = Field(default=None, min_length=1, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

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
        if (self.current_password is None) != (self.new_password is None):
            raise ValueError("Current and new password are both required to change password")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Name cannot be null")
        if "email" in self.model_fields_set and self.email is None:
            raise ValueError("Email cannot be null")
        if self.current_password is not None and self.new_password == self.current_password:
            raise ValueError("New password must be different from current password")
        return self
