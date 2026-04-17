from fastapi import APIRouter, Depends
from database.address import AddressEmbedded
from database.base import SuccessResponse
from services import address_service
from utils.security import get_current_user
from typing import List

router = APIRouter(prefix="/address", tags=["address"])

@router.post("/add", response_model=SuccessResponse[dict], status_code=201)
async def add_address(address: AddressEmbedded, current_user_id: str = Depends(get_current_user)):
    await address_service.add_address(current_user_id, address)
    return SuccessResponse(message="Address added")

@router.get("/all", response_model=SuccessResponse[List[AddressEmbedded]])
async def get_addresses(current_user_id: str = Depends(get_current_user)):
    addresses = await address_service.get_addresses(current_user_id)
    return SuccessResponse(data=addresses)

@router.put("/update/{index}", response_model=SuccessResponse[dict])
async def update_address(index: int, address: AddressEmbedded, current_user_id: str = Depends(get_current_user)):
    await address_service.update_address(current_user_id, index, address)
    return SuccessResponse(message="Address updated")

@router.delete("/delete/{index}", response_model=SuccessResponse[dict])
async def delete_address(index: int, current_user_id: str = Depends(get_current_user)):
    await address_service.delete_address(current_user_id, index)
    return SuccessResponse(message="Address removed")
