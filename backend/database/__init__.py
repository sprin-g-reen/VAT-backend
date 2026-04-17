"""
models/__init__.py

Purpose:
--------
This file acts as a central import hub for all models in the application.

It allows you to import all schemas and utilities from a single place
instead of importing from multiple individual files.

Example:
--------
Instead of writing:
    from models.user import UserCreate
    
    from models.product import ProductOut

You can simply write:
    from models import UserCreate, ProductOut

Benefits:
---------
1. Simplifies imports across the project.
2. Improves code readability and maintainability.
3. Provides a single source of truth for all model exports.
4. Helps avoid long and repetitive import statements.
5. Makes refactoring easier (change import paths in one place).

How It Works:
-------------
- Imports all required classes/functions from individual modules.
- Exposes them via the `__all__` list.
- Ensures only intended components are accessible when using:
      from models import *

__all__:
--------
Defines the public API of the models package.
Only the names listed here will be exported when importing the module.

Structure:
----------
- Base utilities (AppBaseModel, str, responses)
- Embedded models (Address, Variants, etc.)
- Schema models (User, Product, Cart, Order, etc.)
- Request/Response DTOs

Edge Cases:
-----------
- Missing import in this file → cannot be accessed via `from models import ...`
- Circular imports may occur if not structured properly.
- Using `import *` is generally discouraged unless controlled via __all__.

Best Practice:
--------------
Always update this file when:
- Adding a new model/schema
- Renaming existing classes
- Removing unused components
"""

from .base import AppBaseModel, SuccessResponse, ErrorResponse

from .address import AddressEmbedded

from .user import UserCreate, UserOut, UserUpdate

from .category import CategoryCreate, CategoryOut, CategoryUpdate

from .subcategory import SubcategoryCreate, SubcategoryOut, SubcategoryUpdate

from .product import (
    VariantEmbedded,
    ProductImageEmbedded,
    ProductCreate,
    ProductOut,
    ProductUpdate,
)

from .wishlist import WishlistCreate, WishlistOut

from .cart import CartItemEmbedded, CartOut, AddToCartRequest, RemoveFromCartRequest

from .purchase_intent import OrderItemEmbedded, OrderCreate, OrderOut, OrderStatusUpdate

from .payment import PaymentCreate, PaymentOut

from .review import ReviewCreate, ReviewOut

from .order_fullfilement import ReturnCreate, ReturnOut, ReturnStatusUpdate


__all__ = [
    # base
    "AppBaseModel", "str", "SuccessResponse", "ErrorResponse",
    # address
    "AddressEmbedded",
    # user
    "UserCreate", "UserOut", "UserUpdate",
    # category
    "CategoryCreate", "CategoryOut", "CategoryUpdate",
    # subcategory
    "SubcategoryCreate", "SubcategoryOut", "SubcategoryUpdate",
    # product
    "VariantEmbedded", "ProductImageEmbedded",
    "ProductCreate", "ProductOut", "ProductUpdate",
    # wishlist
    "WishlistCreate", "WishlistOut",
    # cart
    "CartItemEmbedded", "CartOut", "AddToCartRequest", "RemoveFromCartRequest",
    # order
    "OrderItemEmbedded", "OrderCreate", "OrderOut", "OrderStatusUpdate",
    # payment
    "PaymentCreate", "PaymentOut",
    # shipping
    "ShippingCreate", "ShippingOut", "ShippingStatusUpdate",
    # review
    "ReviewCreate", "ReviewOut",
    # return
    "ReturnCreate", "ReturnOut", "ReturnStatusUpdate",
    # refund
    "RefundCreate", "RefundOut",
]
