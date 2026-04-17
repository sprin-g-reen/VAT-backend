from db import db
from database.address import AddressEmbedded
from fastapi import HTTPException

async def add_address(user_id: str, address: AddressEmbedded):
    await db.users.update_one(
        {"_id": user_id},
        {"$push": {"addresses": address.model_dump()}}
    )

async def get_addresses(user_id: str):
    user = await db.users.find_one({"_id": user_id}, {"addresses": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.get("addresses", [])

async def update_address(user_id: str, address_index: int, address: AddressEmbedded):
    user = await db.users.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    addresses = user.get("addresses", [])
    if address_index < 0 or address_index >= len(addresses):
        raise HTTPException(status_code=404, detail="Address not found")

    update_key = f"addresses.{address_index}"
    await db.users.update_one(
        {"_id": user_id},
        {"$set": {update_key: address.model_dump()}}
    )

async def delete_address(user_id: str, address_index: int):
    # To delete by index in an array, we can use $unset followed by $pull
    # $unset will set the element at address_index to null
    # $pull will then remove all nulls from the array

    # First, verify user exists and index is valid
    user = await db.users.find_one({"_id": user_id}, {"addresses": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    addresses = user.get("addresses", [])
    if address_index < 0 or address_index >= len(addresses):
        raise HTTPException(status_code=404, detail="Address not found")

    # Step 1: Set the specific element to null
    unset_key = f"addresses.{address_index}"
    await db.users.update_one(
        {"_id": user_id},
        {"$unset": {unset_key: 1}}
    )

    # Step 2: Pull all null values from the addresses array
    await db.users.update_one(
        {"_id": user_id},
        {"$pull": {"addresses": None}}
    )
