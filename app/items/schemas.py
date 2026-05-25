from pydantic import BaseModel, EmailStr, SecretStr, Field, field_validator, ConfigDict
from fastapi import HTTPException, status
from typing import Optional


class UserBase(BaseModel):
    # enable pydantic to read data directly from ORM objects.
    model_config = ConfigDict(from_attributes=True)
    username: str
    email: EmailStr


class CreateUser(UserBase):
    # SecretStr hides the text when printed (outputs as '**********')
    password: SecretStr = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def check_password_strength(cls, v: SecretStr) -> SecretStr:
        password_raw = v.get_secret_value()
        if not any(char.isdigit() for char in password_raw):
            raise ValueError("password must contain at least one number")
        if not any(char.isupper() for char in password_raw):
            raise ValueError(
                "password must contain at least one capital letter")
        return v


class UserResponse(UserBase):
    id: int
    username: str
    email: str


class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr = Field(..., min_length=8, max_length=100)
