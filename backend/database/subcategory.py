from __future__ import annotations
from typing import Optional
from pydantic import Field
from .base import AppBaseModel


class SubcategoryCreate(AppBaseModel):
    """
    SubcategoryCreate Schema

    Purpose:
    --------
    Represents the input payload required to create a new subcategory.

    Fields:
    -------
    subcategory_name : str
        Name of the subcategory (required).
    category_id : str
        ID of the parent category.
    """
    subcategory_name: str
    category_id: str


class SubcategoryOut(AppBaseModel):
    """
    SubcategoryOut Schema

    Purpose:
    --------
    Represents the subcategory data returned from the database.
    """
    id: Optional[str] = Field(default=None, alias="_id")
    subcategory_name: str
    category_id: str


class SubcategoryUpdate(AppBaseModel):
    """
    SubcategoryUpdate Schema
    """
    subcategory_name: Optional[str] = None
    category_id: Optional[str] = None
