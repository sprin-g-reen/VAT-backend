from __future__ import annotations
from datetime import datetime
from typing import Optional,Dict, Any
from pydantic import Field, field_validator
from .base import AppBaseModel


class ReviewCreate(AppBaseModel):
    """
    ReviewCreate Schema

    Purpose:
    --------
    Represents the input payload required to submit a product review.

    Used in:
    - Product review APIs
    - Customer feedback systems
    - Rating and review features in ecommerce platforms

    Fields:
    -------
    product_id : str
        ID of the product being reviewed.

    rating : float
        Rating given by the user.
        Must be between 1.0 and 5.0.

    comment : Optional[str]
        Optional textual feedback provided by the user.

    order_item : dict
        Snapshot of the purchased item being reviewed.
        Helps verify purchase and maintain consistency.

    verified_purchase : bool
        Indicates whether the review is from a verified purchase.

    Behavior:
    ---------
    - Validates rating range (1.0 to 5.0).
    - Supports optional comments.
    - Stores snapshot of order item for integrity.

    Edge Cases:
    -----------
    - rating < 1.0 or > 5.0  validation error.
    - order_item structure is flexible  may lead to inconsistency.
    - verified_purchase must be set based on actual order data (service layer).
    - Duplicate reviews by same user for same product should be prevented externally.
    """

    product_id: str
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None
    order_item: Dict[str, Any] = Field(default_factory=dict)
    verified_purchase: bool = False


class ReviewOut(AppBaseModel):
    """
    ReviewOut Schema

    Purpose:
    --------
    Represents the review data returned from the database.

    Used in:
    - Product detail pages (display reviews)
    - Review listing APIs
    - Admin moderation panels

    Fields:
    -------
    id : Optional[str]
        MongoDB document ID (mapped from '_id').

    product_id : str
        ID of the reviewed product.

    order_item : dict
        Snapshot of the reviewed item.

    verified_purchase : bool
        Indicates whether the review is verified.

    rating : float
        Rating value.

    comment : Optional[str]
        User's review comment.

    review_at : datetime
        Timestamp when the review was created.

    Behavior:
    ---------
    - Maps MongoDB '_id' to 'id'.
    - Returns review details along with timestamp.
    - Includes verification flag for credibility.

    Edge Cases:
    -----------
    - id may be None if not persisted.
    - order_item may be empty or inconsistent.
    - verified_purchase must be correctly set to avoid misleading users.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    product_id: str
    order_item: dict = {}
    verified_purchase: bool = False
    rating: float
    comment: Optional[str] = None
    review_at: datetime = Field(default_factory=datetime.utcnow)