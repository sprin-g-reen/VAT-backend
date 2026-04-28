from __future__ import annotations
from datetime import datetime
from typing import List, Optional,Dict, Any
from pydantic import Field, field_validator
from .base import AppBaseModel
from .address import AddressEmbedded


class OrderItemEmbedded(AppBaseModel):
    """
    OrderItemEmbedded Schema

    Purpose:
    --------
    Represents a single item in an order.
    This is an embedded document stored inside the Order.

    It acts as a frozen snapshot of product details at the time of order placement.

    This ensures:
    - Product name remains unchanged even if updated later
    - Variant details remain consistent
    - Price at order time is preserved

    Fields:
    -------
    product_id : str
        Reference to the original product.

    product_name : Optional[str]
        Snapshot of product name at the time of order.

    product_variants : dict
        Snapshot of selected variant (size, color, etc.).

    order_quantity : int
        Quantity ordered.

    price_at_order : float
        Price of the product at the time of order.

    Behavior:
    ---------
    - Stored as embedded data for fast retrieval (no joins).
    - Prevents inconsistencies due to product updates.

    Edge Cases:
    -----------
    - product_variants structure may vary (no strict schema).
    - price_at_order must be correctly captured during order creation.
    - product_name may become outdated intentionally (snapshot behavior).
    """

    product_id: str
    product_name: Optional[str] = None
    product_variants: Dict[str, Any] = Field(default_factory=dict)
    order_quantity: int= Field( ge=1)
    price_at_order: float = Field( ge=0.0)


class OrderCreate(AppBaseModel):
    """
    OrderCreate Schema

    Purpose:
    --------
    Represents the request payload to place a new order.

    Note:
    -----
    - The actual order items are NOT provided here.
    - Items are automatically fetched from the user's cart on the server side.

    Fields:
    -------
    address : AddressEmbedded
        Delivery address for the order.

    Behavior:
    ---------
    - Triggers order creation using cart data.
    - Ensures address is provided and valid.

    Edge Cases:
    -----------
    - If cart is empty  order creation should fail.
    - Invalid user_id  error in service layer.
    - Missing or incomplete address  validation error.
    """

    address: AddressEmbedded


class OrderOut(AppBaseModel):
    """
    OrderOut Schema

    Purpose:
    --------
    Represents the order data returned from the database.

    Used in:
    - Order history APIs
    - Order tracking
    - Admin dashboards

    Fields:
    -------
    id : Optional[str]
        MongoDB document ID (mapped from '_id').

    items : List[OrderItemEmbedded]
        List of ordered items (embedded snapshots).

    total_amount : Optional[float]
        Total cost of the order.

    status : str
        Current status of the order.
        Default = "PENDING".

    address : Optional[AddressEmbedded]
        Delivery address snapshot.

    order_created_at : datetime
        Timestamp when the order was created.

    Behavior:
    ---------
    - Returns full order data in a single query.
    - Includes embedded item snapshots.

    Edge Cases:
    -----------
    - items may be empty if order creation fails improperly.
    - total_amount must be calculated correctly in service layer.
    - id may be None if not persisted.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    
    items: List[OrderItemEmbedded] = Field(default_factory=list)

    total_amount: Optional[float] = Field(default=0, ge=0)
    status: str = "PENDING"

    address: Optional[AddressEmbedded] = None
    order_created_at: datetime = Field(default_factory=datetime.utcnow)


class OrderStatusUpdate(AppBaseModel):
    """
    OrderStatusUpdate Schema

    Purpose:
    --------
    Represents the payload used to update the status of an order.

    Used in:
    - Admin order management
    - Order tracking updates

    Fields:
    -------
    status : str
        New status of the order.

    Allowed Values:
    ---------------
    - "PENDING"
    - "CONFIRMED"
    - "SHIPPED"
    - "DELIVERED"
    - "CANCELLED"

    Behavior:
    ---------
    - Validates that the status is one of the allowed values.
    - Prevents invalid or unsupported status updates.

    Edge Cases:
    -----------
    - Invalid status  raises ValueError.
    - Case-sensitive values (must match exactly).
    - Business rules (e.g., cannot go from DELIVERED  PENDING) must be handled separately.
    """

    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        allowed = {"PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v