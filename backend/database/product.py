from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import Field, field_validator
from .base import AppBaseModel
from .category import CategoryOut
from .subcategory import SubcategoryOut


class VariantEmbedded(AppBaseModel):
    """
    VariantEmbedded Schema

    Purpose:
    --------
    Represents a single product variant (e.g., size, color, SKU).
    This is embedded inside the Product document.

    Fields:
    -------
    sku : Optional[str]
        Stock Keeping Unit identifier.

    size : Optional[str]
        Size of the product (max length = 10).

    color : Optional[str]
        Color of the product.

    product_variants_price : Optional[float]
        Price specific to this variant.

    stock_quantity : int
        Available stock for this variant.

    Behavior:
    ---------
    - Stored as embedded data inside Product.
    - Allows multiple variants per product.
    - Ensures stock cannot be negative.

    Validation:
    -----------
    - stock_quantity must be >= 0.

    Edge Cases:
    -----------
    - stock_quantity < 0  raises validation error.
    - product_variants_price may be None (fallback to base product price).
    - Missing SKU may affect inventory tracking.
    """

    sku: Optional[str] = None
    size: Optional[str] = Field(default=None, max_length=10)
    color: Optional[str] = None
    product_variants_price: Optional[float] = None
    stock_quantity: int = 0

    @field_validator("stock_quantity")
    @classmethod
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError("stock_quantity cannot be negative")
        return v


class ProductImageEmbedded(AppBaseModel):
    """
    ProductImageEmbedded Schema

    Purpose:
    --------
    Represents a single product image.
    Stored as an embedded document inside Product.

    Fields:
    -------
    image_url : str
        URL of the product image.

    Behavior:
    ---------
    - Allows multiple images per product.
    - Stored directly inside Product for faster retrieval.

    Edge Cases:
    -----------
    - Invalid or broken URLs are not validated here.
    - Duplicate image URLs may exist unless handled externally.
    """

    image_url: str


class ProductCreate(AppBaseModel):
    """
    ProductCreate Schema

    Purpose:
    --------
    Represents the input payload required to create a new product.

    Used in:
    - Admin product creation APIs
    - Inventory management

    Fields:
    -------
    product_name : str
        Name of the product (required).

    description : Optional[str]
        Description of the product.

    price : Optional[float]
        Base price of the product.

    category_id : Optional[str]
        Reference to category.

    subcategory_id : Optional[str]
        Reference to subcategory.

    variants : List[VariantEmbedded]
        List of product variants.

    images : List[ProductImageEmbedded]
        List of product images.

    Behavior:
    ---------
    - Supports multiple variants and images.
    - Validates nested embedded documents.
    - Allows flexible product structure.

    Edge Cases:
    -----------
    - Empty variants list  product may not be purchasable.
    - price and variant price mismatch must be handled in service layer.
    - Invalid category_id or brand_id  must be validated separately.
    """

    product_name: str
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    variants: List[VariantEmbedded] = []
    images: List[ProductImageEmbedded] = []


class ProductOut(AppBaseModel):
    """
    ProductOut Schema

    Purpose:
    --------
    Represents the product data returned from the database.

    Used in:
    - Product listing APIs
    - Product detail pages
    - Admin dashboards

    Fields:
    -------
    id : Optional[str]
        MongoDB document ID (mapped from '_id').

    product_name : str
        Name of the product.

    description : Optional[str]
        Product description.

    price : Optional[float]
        Base product price.

    category : Optional[CategoryOut]
        Category details (populated).

    subcategory : Optional[SubcategoryOut]
        Subcategory details (populated).

    product_is_active : bool
        Indicates if the product is active.

    product_created_at : datetime
        Timestamp when product was created.

    variants : List[VariantEmbedded]
        List of product variants.

    images : List[ProductImageEmbedded]
        List of product images.

    Behavior:
    ---------
    - Maps MongoDB '_id' to 'id'.
    - Returns nested category and brand details.
    - Includes embedded variants and images.

    Edge Cases:
    -----------
    - id may be None if not persisted.
    - category/brand may be None if not populated.
    - variants list may be empty.
    """

    id: Optional[str] = Field(default=None, alias="_id")
    product_name: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[CategoryOut] = None
    subcategory: Optional[SubcategoryOut] = None
    product_is_active: bool = True
    product_created_at: datetime = Field(default_factory=datetime.utcnow)
    variants: List[VariantEmbedded] = []
    images: List[ProductImageEmbedded] = []


class ProductUpdate(AppBaseModel):
    """
    ProductUpdate Schema

    Purpose:
    --------
    Represents a partial update payload for a product.

    Used in:
    - Admin product update APIs
    - Inventory updates

    Fields:
    -------
    product_name : Optional[str]
        Updated product name.

    description : Optional[str]
        Updated description.

    price : Optional[float]
        Updated base price.

    category_id : Optional[str]
        Updated category reference.

    subcategory_id : Optional[str]
        Updated subcategory reference.

    product_is_active : Optional[bool]
        Activate or deactivate product.

    Behavior:
    ---------
    - Supports partial updates (PATCH-like behavior).
    - Only provided fields will be updated.

    Edge Cases:
    -----------
    - Empty payload  no changes.
    - Invalid ObjectId  validation error.
    - Deactivating product may affect cart/order logic (handled elsewhere).
    """

    product_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    product_is_active: Optional[bool] = None