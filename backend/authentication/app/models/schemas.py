"""
Pydantic schemas for Authentication Service
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """Schema for user creation"""
    email: EmailStr
    password: str = Field(..., min_length=2)
    full_name: str
    organization: Optional[str] = None
    role: str = Field(..., pattern="^(clinic_admin|gcf_coordinator|super_admin)$")

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user response"""
    id: str
    email: str
    full_name: str
    organization: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    """Schema for token refresh"""
    refresh_token: str

class LoginResponse(BaseModel):
    """Schema for login response"""
    user: UserResponse
    token: Token

class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=6)

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int
