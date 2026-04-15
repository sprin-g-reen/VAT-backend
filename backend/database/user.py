from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import Field, EmailStr
from .base import AppBaseModel, PyObjectId
from .address import AddressEmbedded


class UserCreate(AppBaseModel):
    """
    UserCreate Schema
    """
    users_name: str
    password:   str                
    email:      EmailStr
    phone_no:   Optional[str] = Field(default=None, max_length=20)
    DOB:        Optional[datetime] = None


class UserOut(AppBaseModel):
    """
    UserOut Schema
    """
    id:              Optional[PyObjectId] = Field(default=None, alias="_id")
    users_name:      str
    email:           EmailStr
    phone_no:        Optional[str] = None
    DOB:             Optional[datetime] = None
    addresses:       List[AddressEmbedded] = []
    user_created_at: datetime = Field(default_factory=datetime.utcnow)
    user_is_active:  bool = True


class UserUpdate(AppBaseModel):
    """
    UserUpdate Schema
    """
    users_name:     Optional[str] = None
    phone_no:       Optional[str] = None
    DOB:            Optional[datetime] = None
    user_is_active: Optional[bool] = None


class SignupRequest(AppBaseModel):
    name: str
    phone: str
    email: EmailStr
    password: str = Field(min_length=6)


class SigninRequest(AppBaseModel):
    identifier: str   # email OR phone
    password: str


class ForgotPasswordRequest(AppBaseModel):
    email: EmailStr


class ResetPasswordRequest(AppBaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(min_length=6)


class ProfileUpdateRequest(AppBaseModel):
    name: str
    phone: str
    email: EmailStr
    address: str
