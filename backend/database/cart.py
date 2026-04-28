from __future__ import annotations
from typing import List, Optional,Dict,Any
from pydantic import Field,BaseModel
from .base import AppBaseModel


class CartItemEmbedded(AppBaseModel):
    """
    CartItemEmbedded Schema

    Purpose:
    --------
    Represents a single item in the cart.
    This is an embedded document stored inside the Cart.

    It acts as a snapshot of:
    - Product details
    - Selected variant
    - Quantity

    Fields:
    -------
    product_id : str
        Reference to the product.

    product_name : Optional[str]
        Snapshot of product name at the time of adding to cart.
        Helps avoid additional lookups.

    product_variants : dict
        Snapshot of selected variant (e.g., size, color, price).

    cart_quantity : int
        Quantity of the product in the cart.
        Must be >= 1.

    Behavior:
    ---------
    - Stored as embedded data inside Cart (no separate collection).
    - Avoids joins by keeping snapshot data.
    - Supports multiple variants of same product.

    Edge Cases:
    -----------
    - cart_quantity < 1  validation error.
    - product_variants is flexible but may lead to inconsistency if structure varies.
    - product_name may become outdated if product changes later.
    """

    product_id: str
    product_name: Optional[str] = None
    product_variants: Dict[str, Any] = Field(default_factory=dict)
    cart_quantity: int = Field(default=1, ge=1)


class CartOut(AppBaseModel):
    """
    CartOut Schema

    Purpose:
    --------
    Represents the cart data returned from the database.

    Used in:
    - Cart APIs (get cart)
    - Checkout flow

    Fields:
    -------
    id : Optional[str]
        MongoDB document ID (mapped from '_id'), which is the User ID.

    items : List[CartItemEmbedded]
        List of cart items (embedded).

    Behavior:
    ---------
    - Returns full cart in a single query.
    - Includes embedded items for fast retrieval.

    Edge Cases:
    -----------
    - items defaults to empty list if cart is empty.
    - id may be None if not persisted.
    - Invalid ObjectId may cause serialization issues.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    items: List[CartItemEmbedded] = Field(default_factory=list)




class AddToCartBulkRequest(BaseModel):
    product_ids: List[str]


class AddToCartRequest(AppBaseModel):
    """
    AddToCartRequest Schema

    Purpose:
    --------
    Represents the request payload to add an item to the cart.

    Used in:
    - Add to cart API endpoint

    Fields:
    -------
    product_id : str
        ID of the product to add.

    variant_data : dict
        Selected variant details (e.g., size, color, price).

    quantity : int
        Number of items to add (must be >= 1).

    Behavior:
    ---------
    - Validates quantity before processing.
    - Allows flexible variant structure.

    Edge Cases:
    -----------
    - quantity < 1  validation error.
    - Missing product_id  validation error.
    - variant_data may be empty  may cause issues if variant is required.
    """

    product_id: str
    variant_data: Dict[str, Any] = Field(default_factory=dict)
    quantity: int = Field(default=1, ge=1)


class RemoveFromCartRequest(AppBaseModel):
    """
    RemoveFromCartRequest Schema

    Purpose:
    --------
    Represents the request payload to remove an item from the cart.

    Used in:
    - Remove from cart API endpoint

    Fields:
    -------
    product_id : str
        ID of the product to remove from the cart.

    Behavior:
    ---------
    - Removes all matching items with the given product_id.
    - Simpler than removing by variant.

    Edge Cases:
    -----------
    - If product does not exist in cart  no change.
    - Does not handle variant-specific removal (may remove multiple items).
    """

    product_id: str

class UpdateCartQuantityRequest(AppBaseModel):
    """
    Update quantity of cart item
    """

    product_id: str
    quantity: int = Field(ge=1)