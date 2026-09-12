from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthUserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    roles: list[str]
    permissions: list[str]


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: AuthUserResponse


class UserResponse(AuthUserResponse):
    is_active: bool
    created_at: datetime


class UserCreateRequest(BaseModel):
    email: str = Field(min_length=1, max_length=320)
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=6)
    role_ids: list[UUID] = Field(default_factory=list)


class UserUpdateRequest(BaseModel):
    email: str | None = Field(default=None, min_length=1, max_length=320)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role_ids: list[UUID] | None = None
    is_active: bool | None = None


class PasswordResetRequest(BaseModel):
    password: str = Field(min_length=6)


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    permissions: list[str]


class RoleCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = None
    permission_ids: list[UUID] = Field(default_factory=list)


class RoleUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    permission_ids: list[UUID] | None = None


class PermissionResponse(BaseModel):
    id: UUID
    name: str
    description: str | None


class PermissionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = None


class PermissionUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None