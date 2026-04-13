from __future__ import annotations
from datetime import datetime
from typing import Optional,Dict, Any,List
from pydantic import Field,BaseModel
from .base import AppBaseModel, PyObjectId
from .product import ProductOut


class WishlistCreate(AppBaseModel):
    """
    WishlistCreate Schema

    Purpose:
    --------
    Represents the input payload required to add a product to a user's wishlist.

    Used in:
    - Wishlist APIs
    - User personalization features
    - Save-for-later functionality

    Fields:
    -------
    user_id : PyObjectId
        ID of the user adding the product.

    product_id : PyObjectId
        ID of the product to be added to wishlist.

    product_variant : dict
        Snapshot of selected product variant (e.g., size, color).

    Behavior:
    ---------
    - Stores a reference to product along with variant snapshot.
    - Allows users to save specific variants of products.
    - Flexible structure for variant data.

    Edge Cases:
    -----------
    - product_variant structure may vary (no strict schema).
    - Duplicate wishlist entries (same user + product) should be prevented at DB level.
    - Invalid user_id or product_id must be handled in service layer.
    """

    user_id: PyObjectId
    product_id: PyObjectId
    product_variant: Dict[str, Any] = Field(default_factory=dict)


class AddToWishlistBulkRequest(BaseModel):
    user_id: str
    product_ids: List[str]

class WishlistOut(AppBaseModel):
    """
    WishlistOut Schema

    Purpose:
    --------
    Represents a wishlist entry returned from the database.

    Used in:
    - Wishlist display APIs
    - User dashboard
    - Personalized product recommendations

    Fields:
    -------
    id : Optional[PyObjectId]
        MongoDB document ID (mapped from '_id').

    user_id : PyObjectId
        ID of the user who owns the wishlist entry.

    product : Optional[ProductOut]
        Populated product details.

    product_variant : dict
        Snapshot of selected product variant.

    wishlist_created : datetime
        Timestamp when the item was added to wishlist.

    Behavior:
    ---------
    - Maps MongoDB '_id' to 'id'.
    - Includes product details for easy display.
    - Stores variant snapshot for consistency.

    Edge Cases:
    -----------
    - product may be None if not populated.
    - product_variant may be empty or inconsistent.
    - id may be None if not persisted.
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId
    product: Optional[ProductOut] = None
    product_variant: dict = {}
    wishlist_created: datetime = Field(default_factory=datetime.utcnow)