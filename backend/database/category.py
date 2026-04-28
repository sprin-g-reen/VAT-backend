from __future__ import annotations
from typing import Optional
from pydantic import Field
from .base import AppBaseModel


class CategoryCreate(AppBaseModel):
    """
    CategoryCreate Schema

    Purpose:
    --------
    Represents the input payload required to create a new product category.

    Used in:
    - Admin APIs for category management
    - Product classification systems

    Fields:
    -------
    category_name : str
        Name of the category (required).

    Behavior:
    ---------
    - Ensures category_name is provided and is a valid string.
    - Used to validate input before inserting into the database.

    Edge Cases:
    -----------
    - Missing or empty category_name  validation error.
    - Duplicate category names should be handled at database level (unique constraint).
    - No built-in validation for format or length unless added explicitly.

    Example:
    --------
    category = CategoryCreate(category_name="Electronics")
    """

    category_name: str


class CategoryUpdate(AppBaseModel):
    """
    CategoryUpdate Schema
    """
    category_name: Optional[str] = None


class CategoryOut(AppBaseModel):
    """
    CategoryOut Schema

    Purpose:
    --------
    Represents the category data returned from the database.

    Used in:
    - API responses
    - Product listings (to display category info)
    - Admin dashboards

    Fields:
    -------
    id : Optional[str]
        MongoDB document ID (mapped from '_id').

    category_name : str
        Name of the category.

    Behavior:
    ---------
    - Maps MongoDB '_id' to 'id' for clean API output.
    - Ensures consistent response structure.

    Edge Cases:
    -----------
    - 'id' may be None if object is not persisted.
    - Invalid ObjectId may cause serialization errors.
    - No additional metadata (timestamps, status) included.

    Example:
    --------
    category_out = CategoryOut(category_name="Electronics")
    """

    id: Optional[str] = Field(default=None, alias="_id")
    category_name: str