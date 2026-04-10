from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import Field
from .base import AppBaseModel, PyObjectId
from .address import AddressEmbedded


class UserCreate(AppBaseModel):
    """
    UserCreate Schema

    Purpose:
    --------
    Represents the input payload required to create a new user.
    This schema is typically used in user registration APIs.

    Fields:
    -------
    users_name : str
        Name of the user (required).

    password : str
        Raw password provided by the user.
        NOTE: This must be hashed before storing in the database.

    email : EmailStr
        Valid email address of the user (required).
        Automatically validated by Pydantic.

    phone_no : Optional[str]
        Optional phone number (max length = 20 characters).

    DOB : Optional[datetime]
        Optional date of birth.

    Edge Cases:
    -----------
    - Invalid email format will raise validation error.
    - Missing required fields will raise validation error.
    - Password is not hashed automatically (must be handled in service layer).
    - Duplicate email should be handled at database level (unique constraint).
    """
    users_name: str
    password:   str                
    email: str = Field(pattern=r".+@.+\..+")
    phone_no:   Optional[str] = Field(default=None, max_length=20)
    DOB:        Optional[datetime] = None


class UserOut(AppBaseModel):
    """
    UserOut Schema

    Purpose:
    --------
    Represents the user data returned from the database.
    Used in API responses to send user information to clients.

    Fields:
    -------
    id : Optional[PyObjectId]
        MongoDB document ID (mapped from '_id').

    users_name : str
        Name of the user.

    email : EmailStr
        User email address.

    phone_no : Optional[str]
        Phone number of the user.

    DOB : Optional[datetime]
        Date of birth.

    addresses : List[AddressEmbedded]
        List of embedded addresses associated with the user.

    user_created_at : datetime
        Timestamp when the user was created.

    user_is_active : bool
        Indicates whether the user account is active.

    Behavior:
    ---------
    - Automatically maps MongoDB '_id' to 'id'.
    - Provides clean output format for APIs.
    - Does NOT include sensitive fields like password.

    Edge Cases:
    -----------
    - 'id' may be None if object is not persisted.
    - Invalid ObjectId may cause serialization issues.
    - 'addresses' defaults to empty list (safe fallback).
    """
    id:              Optional[PyObjectId] = Field(default=None, alias="_id")
    users_name:      str
    email: str = Field(pattern=r".+@.+\..+")
    phone_no:        Optional[str] = None
    DOB:             Optional[datetime] = None
    addresses:       List[AddressEmbedded] = []
    user_created_at: datetime = Field(default_factory=datetime.utcnow)
    user_is_active:  bool = True


class UserUpdate(AppBaseModel):
    """
    UserUpdate Schema

    Purpose:
    --------
    Represents a partial update payload for a user.
    Used in update/profile edit APIs.

    All fields are optional, allowing PATCH-style updates.

    Fields:
    -------
    users_name : Optional[str]
        Updated name of the user.

    phone_no : Optional[str]
        Updated phone number.

    DOB : Optional[datetime]
        Updated date of birth.

    user_is_active : Optional[bool]
        Activate or deactivate user account.

    Behavior:
    ---------
    - Only provided fields will be updated.
    - Prevents overwriting existing values unintentionally.
    - Suitable for partial updates.

    Edge Cases:
    -----------
    - Empty payload results in no changes.
    - Invalid data types will raise validation errors.
    - Email and password are not included (must be handled separately).
    """
    users_name:     Optional[str] = None
    phone_no:       Optional[str] = None
    DOB:            Optional[datetime] = None
    user_is_active: Optional[bool] = None
