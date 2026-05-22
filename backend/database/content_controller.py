from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Any
from pydantic import Field
from .base import AppBaseModel

class ContentControllerBase(AppBaseModel):
    section_name: str # header, featured_categories, trending, footer, general
    content_key: str
    content_value: Any
    is_active: bool = True
    display_order: int = 0

class ContentControllerCreate(ContentControllerBase):
    pass

class ContentControllerUpdate(AppBaseModel):
    section_name: Optional[str] = None
    content_key: Optional[str] = None
    content_value: Optional[Any] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None

class ContentControllerOut(ContentControllerBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
