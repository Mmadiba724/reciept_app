import uuid

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    business_name: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)


class SignupResponse(BaseModel):
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr


class VerifyRequest(BaseModel):
    token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
