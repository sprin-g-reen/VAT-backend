from __future__ import annotations
from typing import Optional
from pydantic import Field
from .base import AppBaseModel


class AddressEmbedded(AppBaseModel):
    """
    AddressEmbedded Schema

    Purpose:
    --------
    Represents an embedded address structure used within other documents.
    This model does NOT have its own collection or ID.

    It is typically embedded inside:
    - User (for storing multiple user addresses)
    - Order (as a snapshot of delivery address)
    - Shipping (for shipment details)

    Fields:
    -------
    street : Optional[str]
        Street name or house/building information.

    city : Optional[str]
        City name.

    state : Optional[str]
        State or region.

    country : Optional[str]
        Country name.

    zipcode : Optional[str]
        Postal/ZIP code (maximum length: 12 characters).

    is_active : bool
        Indicates whether the address is active.
        Useful for enabling/disabling addresses without deleting them.

    Behavior:
    ---------
    - Used as an EmbeddedDocument (no separate MongoDB collection).
    - Stored within parent documents (User, Order, etc.).
    - Lightweight and efficient for read-heavy operations.

    Edge Cases:
    -----------
    - All fields are optional  incomplete addresses are allowed.
    - zipcode exceeding 12 characters will raise validation error.
    - Since it's embedded, updating requires updating the parent document.
    - No unique constraints  duplicate addresses possible unless handled manually.

    Usage Example:
    --------------
    address = AddressEmbedded(
        address_id="uuid-string",
        street="123 Main St",
        city="Chennai",
        state="Tamil Nadu",
        country="India",
        zipcode="600001"
    )
    """
    address_id: Optional[str] = None
    street:    Optional[str] = None
    city:      Optional[str] = None
    state:     Optional[str] = None
    country:   Optional[str] = None
    zipcode:   Optional[str] = Field(default=None, max_length=12)
    is_active: bool = True
