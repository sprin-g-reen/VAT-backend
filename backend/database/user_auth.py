from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignupRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr
    password: str = Field(min_length=6)


class SigninRequest(BaseModel):
    identifier: str   # email OR phone
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=6)


class ProfileUpdateRequest(BaseModel):
    name: str
    phone: str
    email: EmailStr
    address: str