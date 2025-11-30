"""Authentication request/response schemas."""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    expires_in: int


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: str | None = None


class RegisterResponse(BaseModel):
    message: str
