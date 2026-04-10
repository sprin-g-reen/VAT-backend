from __future__ import annotations
from typing import Optional
from pydantic import Field
from .base import AppBaseModel, PyObjectId


class BrandCreate(AppBaseModel):
    """ BrandCreate Schema

    Purpose:
    --------
    Represents the input payload required to create a new brand.

    Used in:
    - Admin APIs for adding new brands
    - Product management systems

    Fields:
    -------
    brand_name : str
        Name of the brand (required).

    Behavior:
    ---------
    - Validates that brand_name is provided.
    - Ensures correct data type before database insertion.

    Edge Cases:
    -----------
    - Empty or missing brand_name → validation error.
    - Duplicate brand names should be handled at database level (unique constraint).
    - No additional validation (like length or format) unless explicitly added.

    Example:
    --------
    brand = BrandCreate(brand_name="Nike")
    """
   
    brand_name: str


class BrandOut(AppBaseModel):
    """
    BrandOut Schema

    Purpose:
    --------
    Represents the brand data returned from the database.

    Used in:
    - API responses
    - Product listings (to show brand info)
    - Admin dashboards

    Fields:
    -------
    id : Optional[PyObjectId]
        MongoDB document ID (mapped from '_id').

    brand_name : str
        Name of the brand.

    Behavior:
    ---------
    - Maps MongoDB '_id' to 'id' for cleaner API output.
    - Ensures consistent response format.

    Edge Cases:
    -----------
    - 'id' may be None if the object is not yet stored in the database.
    - Invalid ObjectId may cause serialization errors.
    - No additional metadata (like timestamps) included by default.

    Example:
    --------
    brand_out = BrandOut(
        brand_name="Nike"
    )
    """
    id:         Optional[PyObjectId] = Field(default=None, alias="_id")
    brand_name: str
