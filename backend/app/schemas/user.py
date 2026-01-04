from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserCreate(BaseModel):
    full_name: str = Field(..., max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.viewer


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserSummary(BaseModel):
    id: UUID
    full_name: str
    email: str
    role: UserRole

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

