"""User schemas used across auth and routers."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

RoleType = Literal["admin", "user"]


class UserBase(BaseModel):
    username: str
    email: str | None = None
    role: RoleType = Field(default="user")

    model_config = ConfigDict(from_attributes=True)


class UserPublic(UserBase):
    id: int
    is_active: bool = True


class UserInDB(UserPublic):
    hashed_password: str
    created_at: datetime
