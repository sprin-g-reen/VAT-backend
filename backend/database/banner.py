from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import Field
from .base import AppBaseModel

class BannerBase(AppBaseModel):
    title: str
    image_url: str
    link_url: Optional[str] = None
    order: int = 1
    status: str = "active" # "active" or "inactive"

class BannerCreate(BannerBase):
    pass

class BannerUpdate(AppBaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    order: Optional[int] = None
    status: Optional[str] = None

class BannerOut(BannerBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
