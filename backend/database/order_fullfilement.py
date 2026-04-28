from __future__ import annotations
from datetime import datetime
from typing import Dict, Any,Optional
from pydantic import Field, field_validator
from .base import AppBaseModel


class ReturnCreate(AppBaseModel):
    """
    ReturnCreate Schema

    Purpose:
    --------
    Represents the input payload required to raise a return request for an order.

    Used in:
    - Customer return requests
    - Order return workflow
    - Refund initiation process

    Fields:
    -------
    order_id : str
        ID of the order associated with the return.


    order_item : dict
        Snapshot of the specific item being returned.
        Includes product details such as name, variant, and price.

    return_quantity : int
        Quantity of the item being returned (must be >= 1).

    return_reason : Optional[str]
        Reason for return (e.g., damaged, wrong item, size issue).

    refund_amount : Optional[float]
        Expected refund amount for the return.

    Behavior:
    ---------
    - Captures return details at the time of request.
    - Uses snapshot data to avoid dependency on product changes.
    - Supports partial returns via return_quantity.

    Edge Cases:
    -----------
    - return_quantity < 1  validation error.
    - order_item structure is flexible  may lead to inconsistency if not standardized.
    - refund_amount mismatch with actual payment  must be validated in service layer.
    - Invalid order_id or user_id  must be handled externally.
    """

    
    order_id: str
    order_item: Dict[str, Any] = Field(default_factory=dict)
    return_quantity: int = Field(default=1, ge=1)
    return_reason: Optional[str] = None
    refund_amount: Optional[float] = None


class ReturnOut(AppBaseModel):
    """
    ReturnOut Schema

    Purpose:
    --------
    Represents the return request data stored in and retrieved from the database.

    Used in:
    - Return tracking APIs
    - Admin return management
    - Customer return status view

    Fields:
    -------
    id : Optional[str]
        MongoDB document ID (mapped from '_id').

    order_id : str
        ID of the associated order.


    order_item : dict
        Snapshot of the returned item.

    return_quantity : int
        Quantity being returned.

    return_reason : Optional[str]
        Reason for return.

    return_status : str
        Current status of the return.
        Default = "REQUESTED".

    refund_amount : Optional[float]
        Refund amount for the return.

    return_created_at : datetime
        Timestamp when return request was created.

    Behavior:
    ---------
    - Maps MongoDB '_id' to 'id'.
    - Tracks lifecycle of return request.
    - Includes snapshot of item for consistency.

    Edge Cases:
    -----------
    - id may be None if not persisted.
    - order_item may be empty or inconsistent.
    - return_status defaults to "REQUESTED".
    - refund_amount may be None if not calculated yet.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    order_id: str
    order_item: dict = {}
    return_quantity: int = 1
    return_reason: Optional[str] = None
    return_status: str = "REQUESTED"
    refund_amount: Optional[float] = None
    return_created_at: datetime = Field(default_factory=datetime.utcnow)


class ReturnStatusUpdate(AppBaseModel):
    """
    ReturnStatusUpdate Schema

    Purpose:
    --------
    Represents the payload used to update the status of a return request.

    Used in:
    - Admin return approval/rejection workflows
    - Return lifecycle management

    Fields:
    -------
    status : str
        New status of the return.

    Allowed Values:
    ---------------
    - "REQUESTED"
    - "APPROVED"
    - "REJECTED"
    - "COMPLETED"

    Behavior:
    ---------
    - Validates that the status is one of the allowed values.
    - Prevents invalid state transitions at schema level.

    Edge Cases:
    -----------
    - Invalid status  raises ValueError.
    - Case-sensitive values.
    - Business rules (e.g., APPROVED  COMPLETED only) must be handled in service layer.
    """

    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        allowed = {"REQUESTED", "APPROVED", "REJECTED", "COMPLETED"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v