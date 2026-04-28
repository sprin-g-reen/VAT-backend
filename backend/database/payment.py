from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import Field
from .base import AppBaseModel


class PaymentCreate(AppBaseModel):
    """
    PaymentCreate Schema

    Purpose:
    --------
    Represents the input payload required to record a payment for an order.

    Used in:
    - Checkout flow
    - Payment gateway integration (UPI, Card, COD, etc.)
    - Order completion process

    Fields:
    -------
    order_id : str
        ID of the order associated with the payment.

    amount_paid : float
        Total amount paid by the user.

    payment_method : Optional[str]
        Method used for payment (e.g., "UPI", "Card", "COD").

    transaction_id : Optional[str]
        Transaction reference ID from the payment gateway.

    Behavior:
    ---------
    - Used to validate payment details before storing in database.
    - Supports multiple payment methods.
    - transaction_id is optional (e.g., not needed for COD).

    Edge Cases:
    -----------
    - Invalid order_id  should be handled in service layer.
    - amount_paid should match order total (must be validated separately).
    - Missing transaction_id for online payments  may cause tracking issues.
    - Negative or zero amount_paid  should be validated in service layer.
    """

    order_id: str
    amount_paid: float = Field(gt=0)
    payment_method: Optional[str] = None
    transaction_id: Optional[str] = None


class PaymentOut(AppBaseModel):
    """
    PaymentOut Schema

    Purpose:
    --------
    Represents the payment data returned from the database.

    Used in:
    - Payment history APIs
    - Order tracking
    - Admin dashboards

    Fields:
    -------
    id : Optional[str]
        MongoDB document ID (mapped from '_id').

    order_id : str
        ID of the associated order.

    amount_paid : float
        Amount paid by the user.

    payment_method : Optional[str]
        Method used for payment.

    payment_status : str
        Status of the payment.
        Default = "SUCCESS".

    transaction_id : Optional[str]
        Payment gateway transaction reference.

    paid_at : datetime
        Timestamp when payment was recorded.

    Behavior:
    ---------
    - Maps MongoDB '_id' to 'id'.
    - Automatically assigns current timestamp if not provided.
    - Default payment status is set to "SUCCESS".

    Edge Cases:
    -----------
    - payment_status is always "SUCCESS" by default (no failure handling here).
    - id may be None if object is not persisted.
    - transaction_id may be None (e.g., COD payments).
    - Incorrect timestamps may occur if system time is misconfigured.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    order_id: str
    amount_paid: float
    payment_method: Optional[str] = None
    payment_status: str = "SUCCESS"
    transaction_id: Optional[str] = None
    paid_at: datetime = Field(default_factory=datetime.utcnow)